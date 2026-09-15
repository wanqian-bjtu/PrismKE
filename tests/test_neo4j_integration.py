from __future__ import annotations

import os
from uuid import uuid4

import pytest

from prismke.core.errors import GraphIntegrityError
from prismke.core.settings import Settings
from prismke.domain import (
    CanonicalEntity,
    Claim,
    EvidenceKind,
    EvidenceRef,
    GraphChange,
    GraphCommit,
    GraphDocument,
    GraphRevision,
    Modality,
)
from prismke.persistence import Neo4jGraphStore

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
