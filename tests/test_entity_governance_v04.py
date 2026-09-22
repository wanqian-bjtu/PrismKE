from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from validated_fixtures import JSONGraphStore, prepare_fixture_commit

from src.api import create_app
from src.core.errors import GraphIntegrityError
from src.core.ids import canonical_hash
from src.core.settings import Settings
from src.domain import (
    CanonicalEntity,
    Claim,
    EntityEmbedding,
    EntityMention,
    GraphCommit,
    GraphRevision,
    SchemaIndex,
    load_schema,
)
from src.governance import (
    EntityGovernanceService,
    SemanticEntityResolver,
    rebuild_entity_index,
)
from src.governance.entity_resolution import entity_embedding_text
from src.persistence import EntityGovernanceRepository
from src.providers import DisabledEmbeddingProvider, MockEmbeddingProvider
from src.workflow import PrismKEService


class ContextEmbeddingProvider:
    def fingerprint(self) -> str:
        return "embedding:test-context"

    async def encode(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "cloud" in text.lower() else [0.0, 1.0] for text in texts]


class BrokenEmbeddingProvider:
    def fingerprint(self) -> str:
        return "embedding:test-broken"

    async def encode(self, texts: list[str]) -> list[list[float]]:
        del texts
        raise RuntimeError("embedding backend unavailable")


@pytest.mark.asyncio
async def test_exact_alias_with_strong_context_conflict_requires_review(
    tmp_path: Path, schema_path: Path
) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    entity = CanonicalEntity(
        id="entity:aurora",
        name="Aurora",
        entity_type="Organization",
        context_summary="cloud database infrastructure",
    )
    await store.commit(
        GraphCommit(entities=[entity], revision=GraphRevision(id="seed", run_id="seed"))
    )
    provider = ContextEmbeddingProvider()
    await rebuild_entity_index(store, provider, backend="json", batch_size=32, dry_run=False)
    resolver = SemanticEntityResolver(
        SchemaIndex(load_schema(schema_path)),
        store,
        provider,
        run_id="conflicting-context",
    )
    mention = EntityMention(
        id="mention:aurora-health",
        name="Aurora",
        entity_type="Organization",
        context="clinical medicine research",
        evidence_ids=["evidence:health"],
    )
    result = await resolver.resolve([mention])
    assert result.review_tasks and "strong_context_conflict" in result.review_tasks[0].reasons
    assert mention.id not in result.mention_to_entity


@pytest.mark.asyncio
async def test_ambiguous_exact_name_proposes_distinct_nil(
    tmp_path: Path, schema_path: Path
) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    entities = [
        CanonicalEntity(id="entity:first", name="Atlas", entity_type="Software"),
        CanonicalEntity(id="entity:second", name="Atlas", entity_type="Software"),
    ]
    await store.commit(
        GraphCommit(entities=entities, revision=GraphRevision(id="seed", run_id="seed"))
    )
    resolver = SemanticEntityResolver(
        SchemaIndex(load_schema(schema_path)),
        store,
        DisabledEmbeddingProvider(),
        run_id="ambiguous",
    )
    mention = EntityMention(
        id="mention:atlas",
        name="Atlas",
        entity_type="Software",
        context="a newly developed astronomy application",
        evidence_ids=["evidence:atlas"],
    )
    bundle = await resolver.resolve([mention])
    assert bundle.review_tasks and len(bundle.review_tasks) == 1
    assert bundle.review_tasks[0].proposed_entity_id not in {item.id for item in entities}
    assert mention.id not in bundle.mention_to_entity


@pytest.mark.asyncio
async def test_split_does_not_overwrite_existing_target(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await seed_graph(store)
    governance = EntityGovernanceService(
        store,
        EntityGovernanceRepository(tmp_path / "governance.json"),
        DisabledEmbeddingProvider(),
    )
    existing = await store.get_entity("entity:b")
    assert existing is not None
    before = store.path.read_bytes()
    with pytest.raises(ValueError, match="new entity ids"):
        await governance.propose_split(
            "entity:a", [existing], {"claim:1": existing.id}, ["test split"]
        )
    assert store.path.read_bytes() == before


@pytest.mark.asyncio
async def test_entity_content_update_invalidates_derived_vector(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await seed_graph(store)
    provider = MockEmbeddingProvider()
    await rebuild_entity_index(store, provider, backend="json", batch_size=32, dry_run=False)
    source = await store.get_entity("entity:a")
    assert source is not None
    transaction = GraphCommit(
        entities=[source.model_copy(update={"aliases": ["New alias"]})],
        revision=GraphRevision(id="update", run_id="update", parent_id="revision:seed"),
    )
    await prepare_fixture_commit(store, transaction)
    await store.commit(transaction)
    embeddings = await store.list_entity_embeddings()
    assert "entity:a" not in {item.entity_id for item in embeddings}


async def seed_graph(store: JSONGraphStore) -> None:
    entities = [
        CanonicalEntity(id="entity:a", name="PrismKE", entity_type="Software"),
        CanonicalEntity(id="entity:b", name="Prism Knowledge", entity_type="Software"),
        CanonicalEntity(id="entity:o", name="OpenAI", entity_type="Organization"),
    ]
    claims = [
        Claim(
            id="claim:1",
            subject_id="entity:a",
            relation_id="developed_by",
            object_entity_id="entity:o",
            confidence=0.95,
            evidence_ids=["evidence:1"],
        ),
        Claim(
            id="claim:2",
            subject_id="entity:a",
            relation_id="related_to",
            object_entity_id="entity:o",
            confidence=0.9,
            evidence_ids=["evidence:2"],
        ),
    ]
    transaction = GraphCommit(
        entities=entities,
        claims=claims,
        revision=GraphRevision(
            id="revision:seed",
            run_id="seed",
            entity_ids=[item.id for item in entities],
            claim_ids=[item.id for item in claims],
        ),
    )
    await prepare_fixture_commit(store, transaction)
    await store.commit(transaction)


@pytest.mark.asyncio
async def test_json_vector_search_and_semantic_resolution(
    tmp_path: Path, schema_path: Path
) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await seed_graph(store)
    provider = MockEmbeddingProvider()
    entity = await store.get_entity("entity:a")
    assert entity is not None
    text = entity_embedding_text(entity)
    vector = (await provider.encode([text]))[0]
    await store.upsert_entity_embeddings(
        [
            EntityEmbedding(
                entity_id=entity.id,
                model_fingerprint=provider.fingerprint(),
                text_hash=canonical_hash(text),
                dimension=len(vector),
                vector=vector,
            )
        ]
    )
    assert await store.search_entities(vector, "Software", 10, "embedding:outdated") == []
    resolver = SemanticEntityResolver(
        SchemaIndex(load_schema(schema_path)),
        store,
        provider,
        run_id="run:semantic",
        auto_link_threshold=0.0,
        review_threshold=0.0,
        min_margin=0.0,
    )
    mention = EntityMention(
        id="mention:semantic",
        name="Prism knowledge extraction",
        entity_type="Software",
        context="multimodal knowledge graph construction",
        evidence_ids=["evidence:mention"],
    )
    result = await resolver.resolve([mention])
    assert result.mention_to_entity[mention.id] == "entity:a"
    assert result.decisions is not None
    assert result.decisions[0].method == "vector"
    assert result.decisions[0].candidates[0].entity_id == "entity:a"


@pytest.mark.asyncio
async def test_same_name_different_type_requires_review(tmp_path: Path, schema_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await store.commit(
        GraphCommit(
            entities=[
                CanonicalEntity(id="entity:wrong-type", name="OpenAI", entity_type="Software")
            ],
            revision=GraphRevision(
                id="revision:type", run_id="type", entity_ids=["entity:wrong-type"]
            ),
        )
    )
    resolver = SemanticEntityResolver(
        SchemaIndex(load_schema(schema_path)),
        store,
        MockEmbeddingProvider(),
        run_id="run:type-conflict",
    )
    result = await resolver.resolve(
        [
            EntityMention(
                id="mention:openai",
                name="OpenAI",
                entity_type="Organization",
                evidence_ids=["evidence:openai"],
            )
        ]
    )
    assert result.review_tasks is not None
    assert result.review_tasks[0].status == "pending"
    assert "entity_type_conflict" in result.review_tasks[0].reasons
    assert "mention:openai" not in result.mention_to_entity


@pytest.mark.asyncio
async def test_same_name_same_type_uses_context_vector_reranking(
    tmp_path: Path, schema_path: Path
) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await store.commit(
        GraphCommit(
            entities=[
                CanonicalEntity(
                    id="entity:cloud",
                    name="Aurora",
                    entity_type="Organization",
                    context_summary="cloud database infrastructure",
                ),
                CanonicalEntity(
                    id="entity:health",
                    name="Aurora",
                    entity_type="Organization",
                    context_summary="clinical medicine research",
                ),
            ],
            revision=GraphRevision(
                id="revision:homonym",
                run_id="homonym",
                entity_ids=["entity:cloud", "entity:health"],
            ),
        )
    )
    provider = ContextEmbeddingProvider()
    await rebuild_entity_index(store, provider, backend="json", batch_size=32, dry_run=False)
    resolver = SemanticEntityResolver(
        SchemaIndex(load_schema(schema_path)),
        store,
        provider,
        run_id="run:homonym",
        auto_link_threshold=0.0,
        review_threshold=0.0,
        min_margin=0.0,
    )
    result = await resolver.resolve(
        [
            EntityMention(
                id="mention:aurora",
                name="Aurora",
                entity_type="Organization",
                context="The cloud database provider expanded its infrastructure.",
                evidence_ids=["evidence:aurora"],
            )
        ]
    )
    assert result.mention_to_entity["mention:aurora"] == "entity:cloud"
    assert result.decisions is not None
    assert result.decisions[0].method == "vector"


@pytest.mark.asyncio
async def test_embedding_failure_routes_ambiguous_mention_to_review(
    tmp_path: Path, schema_path: Path
) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await store.commit(
        GraphCommit(
            entities=[
                CanonicalEntity(
                    id=f"entity:{index}",
                    name="Aurora",
                    entity_type="Organization",
                )
                for index in range(2)
            ],
            revision=GraphRevision(
                id="revision:embedding-failure",
                run_id="embedding-failure",
                entity_ids=["entity:0", "entity:1"],
            ),
        )
    )
    resolver = SemanticEntityResolver(
        SchemaIndex(load_schema(schema_path)),
        store,
        BrokenEmbeddingProvider(),
        run_id="run:embedding-failure",
    )
    result = await resolver.resolve(
        [
            EntityMention(
                id="mention:failure",
                name="Aurora",
                entity_type="Organization",
                evidence_ids=["evidence:failure"],
            )
        ]
    )
    assert result.review_tasks is not None
    assert result.review_tasks[0].status == "pending"
    assert "embedding_retrieval_unavailable" in result.review_tasks[0].reasons


@pytest.mark.parametrize("case_index", range(1, 6))
@pytest.mark.asyncio
async def test_merge_is_reviewed_atomic_and_reversible(tmp_path: Path, case_index: int) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await seed_graph(store)
    repository = EntityGovernanceRepository(tmp_path / "entity-governance.json")
    governance = EntityGovernanceService(store, repository, MockEmbeddingProvider())
    task = await governance.propose_merge(
        ["entity:a", "entity:b"], "entity:a", [f"merge:{case_index:02d} duplicate software"]
    )
    assert task.status == "pending"
    revision = await governance.resolve_operation(task.id, True, "reviewer")
    assert revision is not None
    entities = {item.id: item for item in await store.list_entities()}
    assert entities["entity:a"].active is True
    assert entities["entity:b"].active is False
    assert "Prism Knowledge" in entities["entity:a"].aliases
    snapshot = store.snapshot()
    assert snapshot["entity_operations"][task.operation_id]["status"] == "applied"

    await store.rollback_revision(revision.id)
    restored = {item.id: item for item in await store.list_entities()}
    assert restored["entity:b"].active is True
    assert store.snapshot()["entity_operations"][task.operation_id]["status"] == "rolled_back"


@pytest.mark.asyncio
async def test_stale_merge_proposal_cannot_be_applied(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await seed_graph(store)
    repository = EntityGovernanceRepository(tmp_path / "entity-governance.json")
    governance = EntityGovernanceService(store, repository, MockEmbeddingProvider())
    task = await governance.propose_merge(["entity:a", "entity:b"], "entity:a", ["duplicate"])
    entity = await store.get_entity("entity:a")
    assert entity is not None
    await store.commit(
        GraphCommit(
            entities=[entity.model_copy(update={"aliases": ["new reviewed alias"]})],
            revision=GraphRevision(
                id="revision:changed-after-proposal",
                run_id="changed-after-proposal",
                parent_id="revision:seed",
                entity_ids=[entity.id],
            ),
        )
    )
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match="proposal is stale"):
        await governance.resolve_operation(task.id, True, "reviewer")
    assert store.path.read_bytes() == before
    assert repository.get_task(task.id).status == "pending"  # type: ignore[union-attr]


@pytest.mark.parametrize("case_index", range(1, 6))
@pytest.mark.asyncio
async def test_split_reassigns_selected_claims_and_rolls_back(
    tmp_path: Path, case_index: int
) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await seed_graph(store)
    repository = EntityGovernanceRepository(tmp_path / "entity-governance.json")
    governance = EntityGovernanceService(store, repository, MockEmbeddingProvider())
    targets = [
        CanonicalEntity(id="entity:split-1", name="PrismKE Core", entity_type="Software"),
        CanonicalEntity(id="entity:split-2", name="PrismKE UI", entity_type="Software"),
    ]
    task = await governance.propose_split(
        "entity:a",
        targets,
        {"claim:1": "entity:split-1", "claim:2": "entity:split-2"},
        [f"split:{case_index:02d} claims refer to two products"],
    )
    revision = await governance.resolve_operation(task.id, True, "reviewer")
    assert revision is not None
    claims = {item.id: item for item in await store.list_claims()}
    assert claims["claim:1"].subject_id == "entity:split-1"
    assert claims["claim:2"].subject_id == "entity:split-2"
    assert (await store.get_entity("entity:a")).active is False  # type: ignore[union-attr]

    await store.rollback_revision(revision.id)
    claims = {item.id: item for item in await store.list_claims()}
    assert claims["claim:1"].subject_id == "entity:a"
    assert claims["claim:2"].subject_id == "entity:a"


def test_entity_search_and_merge_review_api(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        embedding_provider="mock",
    )
    service = PrismKEService(settings)
    asyncio.run(seed_graph(service.graph_store))
    asyncio.run(
        rebuild_entity_index(
            service.graph_store,
            service.embedding_provider(),
            backend="json",
            batch_size=2,
            dry_run=False,
        )
    )
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        search = client.get(
            "/api/v1/entities/search",
            params={"q": "Prism knowledge", "entity_type": "Software"},
        )
        assert search.status_code == 200
        assert search.json()

        proposal = client.post(
            "/api/v1/entities/merge-proposals",
            json={
                "source_entity_ids": ["entity:a", "entity:b"],
                "target_entity_id": "entity:a",
                "reasons": ["duplicate"],
            },
        )
        assert proposal.status_code == 202
        task_id = proposal.json()["id"]
        pending = client.get("/api/v1/entity-reviews", params={"status": "pending"})
        assert any(item["id"] == task_id for item in pending.json())

        approved = client.post(
            f"/api/v1/entity-reviews/{task_id}",
            json={"action": "approve", "reviewer": "tester"},
        )
        assert approved.status_code == 200
        history = client.get("/api/v1/entities/entity:a/history")
        assert history.status_code == 200
        assert any(item["run_id"].startswith("governance:") for item in history.json())


@pytest.mark.asyncio
async def test_entity_review_pauses_and_resumes_workflow(tmp_path: Path, schema_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        embedding_provider="mock",
    )
    service = PrismKEService(settings)
    await service.graph_store.commit(
        GraphCommit(
            entities=[
                CanonicalEntity(id="entity:openai-software", name="OpenAI", entity_type="Software")
            ],
            revision=GraphRevision(
                id="revision:wrong-type",
                run_id="wrong-type",
                entity_ids=["entity:openai-software"],
            ),
        )
    )
    document = tmp_path / "sample.md"
    document.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n",
        encoding="utf-8",
    )
    state = await service.run(document, schema_path, "mock")
    assert state.status == "awaiting_review"
    task = state.entity_review_tasks[0]
    reviewed = await service.review_entity(state.run_id, task.id, "create", reviewer="tester")
    assert reviewed.status == "running"
    completed = await service.resume(state.run_id)
    assert completed.status == "completed"
    assert completed.mention_to_entity[task.mention_id] == task.proposed_entity_id
    embeddings = {
        item.entity_id: item for item in await service.graph_store.list_entity_embeddings()
    }
    assert task.proposed_entity_id in embeddings
    run_payload = next(settings.runs_dir.glob("*.json")).read_text(encoding="utf-8")
    assert '"vector"' not in run_payload
    await service.close()
