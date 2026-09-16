from __future__ import annotations

from pathlib import Path

import pytest
from validated_fixtures import JSONGraphStore

from prismke.domain import (
    CanonicalEntity,
    Claim,
    GraphChange,
    GraphCommit,
    GraphRevision,
)
from prismke.persistence import migrate_json_graph


def versioned_transaction() -> GraphCommit:
    entity = CanonicalEntity(id="entity:migration", name="A", entity_type="Thing")
    claim = Claim(
        id="claim:migration",
        subject_id=entity.id,
        relation_id="name",
        object_literal="A",
        confidence=0.9,
        evidence_ids=["evidence:migration"],
    )
    changes = [
        GraphChange(
            resource_type="entity",
            resource_id=entity.id,
            action="create",
            after=entity.model_dump(mode="json"),
        )
    ]
    revision = GraphRevision(
        id="revision:migration",
        run_id="run:migration",
        entity_ids=[entity.id],
        claim_ids=[claim.id],
        changes=changes,
    )
    return GraphCommit(entities=[entity], claims=[claim], revision=revision)


@pytest.mark.asyncio
async def test_json_migration_dry_run_does_not_require_target(tmp_path: Path) -> None:
    source = JSONGraphStore(tmp_path / "source")
    await source.commit(versioned_transaction())
    report = await migrate_json_graph(source.path, None, dry_run=True)
    assert report.dry_run
    assert report.revisions == 1
    assert report.claims == 1


@pytest.mark.asyncio
async def test_json_migration_is_idempotent(tmp_path: Path) -> None:
    source = JSONGraphStore(tmp_path / "source")
    await source.commit(versioned_transaction())
    target = JSONGraphStore(tmp_path / "target")
    target.evidence_store = source.evidence_store
    first = await migrate_json_graph(source.path, target)
    second = await migrate_json_graph(source.path, target)
    assert first.committed_revisions == 1
    assert second.committed_revisions == 1
    assert len(await target.list_revisions()) == 1
