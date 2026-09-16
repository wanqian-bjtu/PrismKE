from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from validated_fixtures import prepare_fixture_commit

from prismke.core.errors import GraphIntegrityError
from prismke.core.settings import Settings
from prismke.domain import (
    CanonicalEntity,
    Claim,
    EntityEmbedding,
    EvidenceKind,
    EvidenceRef,
    GraphChange,
    GraphCommit,
    GraphDocument,
    GraphRevision,
    Modality,
)
from prismke.governance import EntityGovernanceService
from prismke.persistence import EntityGovernanceRepository, Neo4jGraphStore
from prismke.providers import MockEmbeddingProvider

pytestmark = pytest.mark.neo4j


@pytest.mark.skipif(
    os.getenv("PRISMKE_TEST_NEO4J") != "1",
    reason="set PRISMKE_TEST_NEO4J=1 for live Neo4j tests",
)
@pytest.mark.asyncio
async def test_live_neo4j_commit_query_and_rollback() -> None:
    settings = Settings()
    assert settings.neo4j_password is not None
    store = Neo4jGraphStore(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    suffix = uuid4().hex
    entity = CanonicalEntity(id=f"entity:test:{suffix}", name="Test", entity_type="Thing")
    document = GraphDocument(
        id=f"document:test:{suffix}",
        filename="test.md",
        content_hash="b" * 64,
        media_type="text/markdown",
    )
    evidence = EvidenceRef(
        id=f"evidence:test:{suffix}",
        kind=EvidenceKind.TEXT_SPAN,
        document_id=document.id,
        source_hash=document.content_hash,
        modality=Modality.TEXT,
    )
    claim = Claim(
        id=f"claim:test:{suffix}",
        subject_id=entity.id,
        relation_id="name",
        object_literal="Test",
        confidence=0.99,
        evidence_ids=[evidence.id],
    )
    changes = [
        GraphChange(
            resource_type="entity",
            resource_id=entity.id,
            action="create",
            after=entity.model_dump(mode="json"),
        ),
        GraphChange(
            resource_type="claim",
            resource_id=claim.id,
            action="create",
            after=claim.model_dump(mode="json"),
        ),
    ]
    try:
        parent = await store.latest_revision()
        revision = GraphRevision(
            id=f"revision:test:{suffix}",
            run_id=f"run:test:{suffix}",
            parent_id=parent.id if parent else None,
            entity_ids=[entity.id],
            claim_ids=[claim.id],
            changes=changes,
        )
        transaction = GraphCommit(
            documents=[document],
            evidence=[evidence],
            entities=[entity],
            claims=[claim],
            revision=revision,
        )
        await prepare_fixture_commit(store, transaction)
        await store.commit(transaction)
        await store.commit(transaction)
        assert (await store.healthcheck()).healthy
        assert await store.get_evidence(evidence.id) == evidence
        assert (await store.get_neighborhood(entity.id)).claims[0].id == claim.id
        with pytest.raises(GraphIntegrityError, match="parent mismatch"):
            stale = transaction.model_copy(deep=True)
            stale.revision.id += ":stale"
            await store.commit(stale)
        compensation = await store.rollback_revision(revision.id)
        assert compensation.parent_id == revision.id
        assert (await store.get_claim(claim.id)).tx_to is not None  # type: ignore[union-attr]
        assert await store.rollback_revision(revision.id) == compensation
    finally:
        await store.close()


@pytest.mark.skipif(
    os.getenv("PRISMKE_TEST_NEO4J") != "1",
    reason="set PRISMKE_TEST_NEO4J=1 for live Neo4j tests",
)
@pytest.mark.asyncio
async def test_live_neo4j_vector_index_search() -> None:
    settings = Settings()
    assert settings.neo4j_password is not None
    store = Neo4jGraphStore(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    suffix = uuid4().hex
    entity_type = f"VectorTest-{suffix}"
    entity = CanonicalEntity(
        id=f"entity:vector:{suffix}", name="Vector Test", entity_type=entity_type
    )
    vector = [1.0, *([0.0] * 1023)]
    try:
        parent = await store.latest_revision()
        revision = GraphRevision(
            id=f"revision:vector:{suffix}",
            run_id=f"run:vector:{suffix}",
            parent_id=parent.id if parent else None,
            entity_ids=[entity.id],
        )
        await store.commit(
            GraphCommit(
                entities=[entity],
                entity_embeddings=[
                    EntityEmbedding(
                        entity_id=entity.id,
                        model_fingerprint="test-bge-m3",
                        text_hash="a" * 64,
                        dimension=1024,
                        vector=vector,
                    )
                ],
                revision=revision,
            )
        )
        query = [0.8, 0.6, *([0.0] * 1022)]
        matches = await store.search_entities(query, entity_type, 1)
        assert matches[0][0].id == entity.id
        assert matches[0][1] == pytest.approx(0.8, abs=1e-8)
    finally:
        await store.close()


@pytest.mark.skipif(
    os.getenv("PRISMKE_TEST_NEO4J") != "1",
    reason="set PRISMKE_TEST_NEO4J=1 for live Neo4j tests",
)
@pytest.mark.asyncio
async def test_live_neo4j_entity_merge_split_and_rollback(tmp_path: Path) -> None:
    settings = Settings()
    assert settings.neo4j_password is not None
    store = Neo4jGraphStore(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    suffix = uuid4().hex
    source = CanonicalEntity(
        id=f"entity:governance:{suffix}:source",
        name="Prism Knowledge",
        entity_type="Software",
    )
    survivor = CanonicalEntity(
        id=f"entity:governance:{suffix}:survivor",
        name="PrismKE",
        entity_type="Software",
    )
    document = GraphDocument(
        id=f"document:governance:{suffix}",
        filename="governance.md",
        content_hash="c" * 64,
        media_type="text/markdown",
    )
    evidence = EvidenceRef(
        id=f"evidence:governance:{suffix}",
        kind=EvidenceKind.TEXT_SPAN,
        document_id=document.id,
        source_hash=document.content_hash,
        modality=Modality.TEXT,
    )
    claim = Claim(
        id=f"claim:governance:{suffix}",
        subject_id=source.id,
        relation_id="described_as",
        object_literal="knowledge extraction system",
        confidence=0.99,
        evidence_ids=[evidence.id],
    )
    try:
        parent = await store.latest_revision()
        seed = GraphRevision(
            id=f"revision:governance:{suffix}",
            run_id=f"run:governance:{suffix}",
            parent_id=parent.id if parent else None,
            entity_ids=[source.id, survivor.id],
            claim_ids=[claim.id],
        )
        transaction = GraphCommit(
            documents=[document],
            evidence=[evidence],
            entities=[source, survivor],
            claims=[claim],
            revision=seed,
        )
        await prepare_fixture_commit(store, transaction)
        await store.commit(transaction)
        governance = EntityGovernanceService(
            store,
            EntityGovernanceRepository(tmp_path / "entity-governance.json"),
            MockEmbeddingProvider(),
        )
        merge_task = await governance.propose_merge(
            [source.id, survivor.id], survivor.id, ["duplicate entities"]
        )
        merge_revision = await governance.resolve_operation(merge_task.id, True, "integration-test")
        assert merge_revision is not None
        assert (await store.get_entity(source.id)).active is False  # type: ignore[union-attr]
        assert (await store.get_claim(claim.id)).subject_id == survivor.id  # type: ignore[union-attr]
        async with store.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                "MATCH ()-[r:MERGED_INTO {operation_id: $operation_id}]->() "
                "RETURN count(r) AS count",
                operation_id=merge_task.operation_id,
            )
            assert (await result.single())["count"] == 1
        await store.rollback_revision(merge_revision.id)
        assert (await store.get_entity(source.id)).active is True  # type: ignore[union-attr]
        assert (await store.get_claim(claim.id)).subject_id == source.id  # type: ignore[union-attr]
        async with store.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                "MATCH ()-[r:MERGED_INTO {operation_id: $operation_id}]->() "
                "RETURN count(r) AS count",
                operation_id=merge_task.operation_id,
            )
            assert (await result.single())["count"] == 0

        split_target = CanonicalEntity(
            id=f"entity:governance:{suffix}:split",
            name="Prism Knowledge Legacy",
            entity_type="Software",
        )
        split_task = await governance.propose_split(
            source.id,
            [split_target],
            {claim.id: split_target.id},
            ["separate legacy product"],
        )
        split_revision = await governance.resolve_operation(split_task.id, True, "integration-test")
        assert split_revision is not None
        assert (await store.get_claim(claim.id)).subject_id == split_target.id  # type: ignore[union-attr]
        await store.rollback_revision(split_revision.id)
        assert (await store.get_claim(claim.id)).subject_id == source.id  # type: ignore[union-attr]
    finally:
        await store.close()
