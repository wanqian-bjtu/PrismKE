from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from validated_fixtures import JSONGraphStore

from src.core.errors import GraphIntegrityError
from src.domain import (
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


def transaction(revision_id: str = "rev:1", parent_id: str | None = None) -> GraphCommit:
    entity = CanonicalEntity(id=f"entity:{revision_id}", name="A", entity_type="Thing")
    claim = Claim(
        id=f"claim:{revision_id}",
        subject_id=entity.id,
        relation_id="r",
        object_literal="value",
        confidence=0.9,
        evidence_ids=["ev:1"],
    )
    revision = GraphRevision(
        id=revision_id,
        run_id=f"run:{revision_id}",
        parent_id=parent_id,
        entity_ids=[entity.id],
        claim_ids=[claim.id],
    )
    return GraphCommit(entities=[entity], claims=[claim], revision=revision)


@pytest.mark.asyncio
async def test_graph_transaction_is_idempotent(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path)
    commit = transaction()
    await store.commit(commit)
    await store.commit(commit)
    assert len(await store.list_entities()) == 1
    assert len(await store.list_claims()) == 1
    assert (await store.latest_revision()).id == "rev:1"  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_failed_atomic_write_preserves_previous_graph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = JSONGraphStore(tmp_path)
    before = store.path.read_bytes()

    def fail_write(payload: object) -> None:
        del payload
        raise OSError("simulated disk failure")

    monkeypatch.setattr(store, "_write_atomic", fail_write)
    with pytest.raises(OSError, match="simulated disk failure"):
        await store.commit(transaction())
    assert store.path.read_bytes() == before


@pytest.mark.asyncio
async def test_concurrent_stale_parent_is_rejected_without_corruption(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path)
    results = await asyncio.gather(
        store.commit(transaction("rev:1")),
        store.commit(transaction("rev:2")),
        return_exceptions=True,
    )
    assert sum(isinstance(result, GraphIntegrityError) for result in results) == 1
    assert len(await store.list_claims()) == 1
    assert await store.latest_revision() is not None


def versioned_transaction(
    revision_id: str = "rev:versioned", parent_id: str | None = None
) -> GraphCommit:
    entity = CanonicalEntity(id="entity:versioned", name="PrismKE", entity_type="Software")
    evidence = EvidenceRef(
        id="evidence:versioned",
        kind=EvidenceKind.TEXT_SPAN,
        document_id="document:versioned",
        source_hash="a" * 64,
        modality=Modality.TEXT,
    )
    claim = Claim(
        id="claim:versioned",
        subject_id=entity.id,
        relation_id="version",
        object_literal="0.3",
        confidence=0.95,
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
    return GraphCommit(
        documents=[
            GraphDocument(
                id="document:versioned",
                filename="sample.md",
                content_hash="a" * 64,
                media_type="text/markdown",
            )
        ],
        evidence=[evidence],
        entities=[entity],
        claims=[claim],
        revision=GraphRevision(
            id=revision_id,
            run_id="run:versioned",
            parent_id=parent_id,
            entity_ids=[entity.id],
            claim_ids=[claim.id],
            changes=changes,
        ),
    )


@pytest.mark.asyncio
async def test_graph_stores_documents_evidence_and_neighborhood(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path)
    commit = versioned_transaction()
    await store.commit(commit)
    assert await store.get_evidence("evidence:versioned") == commit.evidence[0]
    neighborhood = await store.get_neighborhood("entity:versioned")
    assert [item.id for item in neighborhood.entities] == ["entity:versioned"]
    assert [item.id for item in neighborhood.claims] == ["claim:versioned"]
    assert (await store.healthcheck()).healthy


@pytest.mark.asyncio
async def test_revision_diff_and_compensating_rollback(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path)
    first = versioned_transaction()
    await store.commit(first)
    second = transaction("rev:second", first.revision.id)
    second.revision.changes = [
        GraphChange(
            resource_type="entity",
            resource_id=second.entities[0].id,
            action="create",
            after=second.entities[0].model_dump(mode="json"),
        ),
        GraphChange(
            resource_type="claim",
            resource_id=second.claims[0].id,
            action="create",
            after=second.claims[0].model_dump(mode="json"),
        ),
    ]
    await store.commit(second)
    diff = await store.diff_revisions(first.revision.id, second.revision.id)
    assert len(diff.changes) == 2
    compensation = await store.rollback_revision(second.revision.id)
    assert compensation.parent_id == second.revision.id
    assert (await store.get_claim(second.claims[0].id)).tx_to is not None  # type: ignore[union-attr]
    assert len(await store.list_revisions()) == 3


@pytest.mark.asyncio
async def test_legacy_revision_cannot_be_rolled_back(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path)
    await store.commit(transaction())
    with pytest.raises(GraphIntegrityError, match="legacy revision"):
        await store.rollback_revision("rev:1")
