from __future__ import annotations

from pathlib import Path

import pytest

from prismke.models import CanonicalEntity, Claim, GraphRevision
from prismke.stores import JSONGraphStore


@pytest.mark.asyncio
async def test_graph_store_is_idempotent(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path)
    entity = CanonicalEntity(id="entity:1", name="A", entity_type="Thing")
    claim = Claim(
        id="claim:1",
        subject_id=entity.id,
        relation_id="r",
        object_literal="value",
        confidence=0.9,
        evidence_ids=["ev:1"],
    )
    revision = GraphRevision(id="rev:1", run_id="run:1", claim_ids=[claim.id])
    await store.upsert_entity(entity)
    await store.upsert_entity(entity)
    await store.append_claim(claim)
    await store.append_claim(claim)
    await store.commit_revision(revision)
    await store.commit_revision(revision)
    assert len(await store.list_entities()) == 1
    assert len(await store.list_claims()) == 1
    assert (await store.latest_revision()).id == "rev:1"  # type: ignore[union-attr]
