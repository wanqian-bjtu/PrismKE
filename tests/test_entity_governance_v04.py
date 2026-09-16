from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prismke.api import create_app
from prismke.core.ids import canonical_hash
from prismke.core.settings import Settings
from prismke.domain import (
    CanonicalEntity,
    Claim,
    EntityEmbedding,
    EntityMention,
    GraphCommit,
    GraphRevision,
    SchemaIndex,
    load_schema,
)
from prismke.governance import (
    EntityGovernanceService,
    SemanticEntityResolver,
    rebuild_entity_index,
)
from prismke.governance.entity_resolution import entity_embedding_text
from prismke.persistence import EntityGovernanceRepository, JSONGraphStore
from prismke.providers import MockEmbeddingProvider
from prismke.workflow import PrismKEService


class ContextEmbeddingProvider:
    def fingerprint(self) -> str:
        return "embedding:test-context"

    async def encode(self, texts: list[str]) -> list[list[float]]:
        return [
            [1.0, 0.0] if "cloud" in text.lower() else [0.0, 1.0]
            for text in texts
        ]


class BrokenEmbeddingProvider:
    def fingerprint(self) -> str:
        return "embedding:test-broken"

    async def encode(self, texts: list[str]) -> list[list[float]]:
        del texts
        raise RuntimeError("embedding backend unavailable")


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
    await store.commit(
        GraphCommit(
            entities=entities,
            claims=claims,
            revision=GraphRevision(
                id="revision:seed",
                run_id="seed",
                entity_ids=[item.id for item in entities],
                claim_ids=[item.id for item in claims],
            ),
        )
    )


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
async def test_same_name_different_type_requires_review(
    tmp_path: Path, schema_path: Path
) -> None:
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
    await rebuild_entity_index(
        store, provider, backend="json", batch_size=32, dry_run=False
    )
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


@pytest.mark.asyncio
async def test_merge_is_reviewed_atomic_and_reversible(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    await seed_graph(store)
    repository = EntityGovernanceRepository(tmp_path / "entity-governance.json")
    governance = EntityGovernanceService(store, repository, MockEmbeddingProvider())
    task = await governance.propose_merge(
        ["entity:a", "entity:b"], "entity:a", ["same real-world software"]
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
async def test_split_reassigns_selected_claims_and_rolls_back(tmp_path: Path) -> None:
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
        ["claims refer to two products"],
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
async def test_entity_review_pauses_and_resumes_workflow(
    tmp_path: Path, schema_path: Path
) -> None:
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
    reviewed = await service.review_entity(state.run_id, task.id, "create")
    assert reviewed.status == "running"
    completed = await service.resume(state.run_id)
    assert completed.status == "completed"
    assert completed.mention_to_entity[task.mention_id] == task.proposed_entity_id
    embeddings = {
        item.entity_id: item
        for item in await service.graph_store.list_entity_embeddings()
    }
    assert task.proposed_entity_id in embeddings
    run_payload = next(settings.runs_dir.glob("*.json")).read_text(encoding="utf-8")
    assert '"vector"' not in run_payload
    await service.close()
