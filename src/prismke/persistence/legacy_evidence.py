"""Audited repair of historical integration-test claims in an isolated graph."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson

from prismke.core.errors import GraphIntegrityError
from prismke.core.ids import canonical_hash, stable_id
from prismke.domain import Claim, EvidenceRef, GraphChange, GraphCommit, GraphRevision
from prismke.persistence.file_evidence import FileEvidenceStore
from prismke.persistence.neo4j_graph import Neo4jGraphStore

SAMPLE_CLAIM_ID = "claim:10642a1c1645daf932251f03"
SAMPLE_EVIDENCE_ID = "ev:b0e5d9ab33c91f2358e2a3b5"
MAINTENANCE_RUN_ID = "maintenance:legacy-evidence-v092"


async def require_isolated_database(store: Neo4jGraphStore, expected_data_dir: Path) -> None:
    """Compare Neo4j's actual data directory, not merely the connection string."""
    async with store.driver.session(database=store.database) as session:
        result = await session.run(
            "CALL dbms.listConfig() YIELD name, value "
            "WHERE name = 'server.directories.data' RETURN value"
        )
        record = await result.single()
    if record is None or Path(str(record["value"])).resolve() != expected_data_dir.resolve():
        raise GraphIntegrityError("maintenance target is not the expected isolated data directory")


async def _graph_evidence(store: Neo4jGraphStore, evidence_id: str) -> EvidenceRef:
    evidence = await store.get_evidence(evidence_id)
    if evidence is None:
        raise GraphIntegrityError(f"missing graph evidence: {evidence_id}")
    return evidence


async def legacy_snapshot(
    store: Neo4jGraphStore, source: FileEvidenceStore
) -> dict[str, Any]:
    """Produce a small, non-sensitive manifest that pins every planned change."""
    claims = await store.list_claims()
    governance = sorted(
        (c for c in claims if c.id.startswith("claim:governance:")), key=lambda c: c.id
    )
    historical = sorted((c for c in claims if c.id.startswith("claim:test:")), key=lambda c: c.id)
    if len(governance) != 9 or len(historical) != 16:
        raise GraphIntegrityError("legacy test claim counts differ from the audited inventory")
    if any(c.tx_to is not None or c.status.value != "pending" for c in governance):
        raise GraphIntegrityError("governance fixture is no longer an active pending claim")
    if any(c.tx_to is None for c in historical):
        raise GraphIntegrityError("an historical test claim is unexpectedly active")

    async with store.driver.session(database=store.database) as session:
        result = await session.run(
            "MATCH (c:Claim)-[:SUPPORTED_BY]->(e:Evidence)<-[:CONTAINS]-(d:Document) "
            "WHERE c.id STARTS WITH 'claim:governance:' OR c.id STARTS WITH 'claim:test:' "
            "RETURN c.id AS claim_id, e.id AS evidence_id, d.filename AS filename, "
            "d.content_hash AS content_hash, e.payload AS evidence_payload"
        )
        rows = await result.data()
    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_id.setdefault(str(row["claim_id"]), []).append(row)
    for claim in governance:
        matching = by_id.get(claim.id, [])
        suffix = claim.id.removeprefix("claim:governance:")
        if (
            len(matching) != 1
            or claim.evidence_ids != [f"evidence:governance:{suffix}"]
            or matching[0]["evidence_id"] != claim.evidence_ids[0]
            or matching[0]["filename"] != "governance.md"
            or matching[0]["content_hash"] != "c" * 64
            or EvidenceRef.model_validate(orjson.loads(matching[0]["evidence_payload"])).source_hash
            != "c" * 64
            or claim.relation_id != "described_as"
        ):
            raise GraphIntegrityError(f"fixture provenance mismatch: {claim.id}")
    for claim in historical:
        matching = by_id.get(claim.id, [])
        suffix = claim.id.removeprefix("claim:test:")
        if (
            len(matching) != 1
            or claim.evidence_ids != [f"evidence:test:{suffix}"]
            or matching[0]["evidence_id"] != claim.evidence_ids[0]
            or matching[0]["filename"] != "test.md"
            or matching[0]["content_hash"] != "b" * 64
            or EvidenceRef.model_validate(orjson.loads(matching[0]["evidence_payload"])).source_hash
            != "b" * 64
            or claim.relation_id != "name"
        ):
            raise GraphIntegrityError(f"historical fixture provenance mismatch: {claim.id}")

    sample = next((c for c in claims if c.id == SAMPLE_CLAIM_ID), None)
    if sample is None or sample.tx_to is not None or sample.evidence_ids != [SAMPLE_EVIDENCE_ID]:
        raise GraphIntegrityError("the retained sample claim differs from the audited inventory")
    graph_ref = await _graph_evidence(store, SAMPLE_EVIDENCE_ID)
    if (
        not await source.verify(SAMPLE_EVIDENCE_ID)
        or await source.get(SAMPLE_EVIDENCE_ID) != graph_ref
    ):
        raise GraphIntegrityError("the original sample evidence is unavailable or differs")
    latest = await store.latest_revision()
    if latest is None:
        raise GraphIntegrityError("maintenance requires an existing graph revision")
    return {
        "parent_id": latest.id,
        "governance": [
            {"id": c.id, "fingerprint": canonical_hash(c.model_dump(mode="json"))}
            for c in governance
        ],
        "historical_closed_ids": [c.id for c in historical],
        "retained_claim_id": sample.id,
        "retained_evidence_id": graph_ref.id,
        "retained_evidence_hash": graph_ref.source_hash,
        "active_claim_count": sum(c.tx_to is None for c in claims),
    }


def closure_commit(manifest: dict[str, Any], claims: list[Claim]) -> GraphCommit:
    by_id = {claim.id: claim for claim in claims}
    timestamp = datetime.now(UTC)
    closed: list[Claim] = []
    changes: list[GraphChange] = []
    for item in manifest["governance"]:
        claim = by_id.get(item["id"])
        if (
            claim is None
            or claim.tx_to is not None
            or canonical_hash(claim.model_dump(mode="json")) != item["fingerprint"]
        ):
            raise GraphIntegrityError("maintenance claim changed since preview")
        updated = claim.model_copy(update={"tx_to": timestamp})
        closed.append(updated)
        changes.append(
            GraphChange(
                resource_type="claim",
                resource_id=claim.id,
                action="close",
                before=claim.model_dump(mode="json"),
                after=updated.model_dump(mode="json"),
            )
        )
    return GraphCommit(
        claims=closed,
        revision=GraphRevision(
            id=stable_id("revision", MAINTENANCE_RUN_ID, manifest["parent_id"]),
            run_id=MAINTENANCE_RUN_ID,
            parent_id=manifest["parent_id"],
            claim_ids=[claim.id for claim in closed],
            changes=changes,
        ),
    )


async def restore_sample_evidence(
    store: Neo4jGraphStore, source: FileEvidenceStore, target: FileEvidenceStore
) -> None:
    evidence = await _graph_evidence(store, SAMPLE_EVIDENCE_ID)
    if not await source.verify(evidence.id) or await source.get(evidence.id) != evidence:
        raise GraphIntegrityError("source sample evidence failed verification")
    blob = await source.get_blob(evidence.source_hash)
    if await target.put_blob(blob, "application/octet-stream") != evidence.source_hash:
        raise GraphIntegrityError("copied sample blob hash mismatch")
    await target.put_ref(evidence)
    if not await target.verify(evidence.id) or await target.get(evidence.id) != evidence:
        raise GraphIntegrityError("copied sample evidence failed verification")


async def verify_active_claims(
    store: Neo4jGraphStore,
    target: FileEvidenceStore,
    *,
    exclude_ids: set[str] | None = None,
) -> int:
    active = [
        claim for claim in await store.list_claims()
        if claim.tx_to is None and claim.id not in (exclude_ids or set())
    ]
    for claim in active:
        for evidence_id in claim.evidence_ids:
            graph_ref = await _graph_evidence(store, evidence_id)
            if not await target.verify(evidence_id) or await target.get(evidence_id) != graph_ref:
                raise GraphIntegrityError(f"active claim evidence failed verification: {claim.id}")
    return len(active)


async def existing_maintenance(store: Neo4jGraphStore) -> GraphRevision | None:
    async with store.driver.session(database=store.database) as session:
        result = await session.run(
            "MATCH (r:Revision {run_id: $run_id}) RETURN r.payload AS payload",
            run_id=MAINTENANCE_RUN_ID,
        )
        records = await result.data()
    if len(records) > 1:
        raise GraphIntegrityError("multiple legacy maintenance revisions found")
    return GraphRevision.model_validate(orjson.loads(records[0]["payload"])) if records else None


def read_manifest(path: Path) -> dict[str, Any]:
    value = orjson.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise GraphIntegrityError("invalid maintenance manifest")
    return value
