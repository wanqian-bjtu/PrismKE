"""Exact compensation and optimistic resource guards shared by graph backends."""

from typing import Any

from prismke.core.errors import GraphIntegrityError
from prismke.core.ids import canonical_hash
from prismke.domain import GraphCommit


def verify_correction(transaction: GraphCommit, resources: dict[str, Any]) -> None:
    guard = transaction.correction_guard
    if guard is None:
        return
    if transaction.revision.correction_guard != guard:
        raise GraphIntegrityError("CORRECTION_GUARD_MISMATCH")
    for key, expected in guard.expected_resources.items():
        current = resources.get(key)
        actual = canonical_hash(current) if current is not None else None
        if actual != expected:
            raise GraphIntegrityError(f"STALE_CORRECTION_RESOURCE: {key}")
    changed = {f"entity:{e.id}": e.model_dump(mode="json") for e in transaction.entities}
    changed.update({f"claim:{c.id}": c.model_dump(mode="json") for c in transaction.claims})
    snapshots = {f"{c.resource_type}:{c.resource_id}": c for c in transaction.revision.changes}
    if transaction.conflicts or transaction.entity_operations or transaction.entity_embeddings:
        raise GraphIntegrityError("CORRECTION_UNSUPPORTED_RESOURCE")
    if set(changed) != set(snapshots):
        raise GraphIntegrityError("CORRECTION_SNAPSHOT_MISMATCH")
    for key, after in changed.items():
        if key not in guard.expected_resources:
            raise GraphIntegrityError(f"CORRECTION_MISSING_RESOURCE_GUARD: {key}")
        change = snapshots[key]
        if (
            key.startswith("claim:")
            and change.before is not None
            and set(change.before.get("source_run_ids", [])) != {transaction.revision.run_id}
        ):
            raise GraphIntegrityError(f"SHARED_OR_LEGACY_CLAIM: {key}")
        if change.before != resources.get(key) or change.after != after:
            raise GraphIntegrityError(f"CORRECTION_SNAPSHOT_MISMATCH: {key}")
