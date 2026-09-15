from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from prismke.core.errors import GraphIntegrityError
from prismke.domain import CanonicalEntity, Claim, GraphCommit, GraphRevision
from prismke.persistence import JSONGraphStore


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
