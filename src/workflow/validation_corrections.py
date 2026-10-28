"""Deterministic candidate corrections for validation review.

This module never invokes a model and never writes to the graph store.  It only
projects a reviewed candidate replacement inside an existing run checkpoint.
"""

from __future__ import annotations

from typing import Any

from src.core.ids import canonical_hash, stable_id
from src.domain import CandidateClaim, EntityMention, ValidationAction


def corrected_candidate(
    candidate: CandidateClaim,
    action: ValidationAction,
    replacement: dict[str, Any],
) -> CandidateClaim | None:
    if action in {"exclude", "defer"}:
        return None
    payload = candidate.model_dump(mode="python")
    if action == "swap_endpoints":
        if not isinstance(candidate.object, EntityMention):
            raise ValueError("literal-object candidate cannot swap endpoints")
        payload["subject"], payload["object"] = payload["object"], payload["subject"]
    elif action == "replace_relation":
        relation = str(replacement.get("relation") or "").strip()
        if not relation:
            raise ValueError("replacement relation is required")
        payload["relation"] = relation
    elif action == "replace_entity_type":
        endpoint = str(replacement.get("endpoint") or "")
        entity_type = str(replacement.get("entity_type") or "").strip()
        if endpoint not in {"subject", "object"} or not entity_type:
            raise ValueError("endpoint and entity_type are required")
        if endpoint == "object" and not isinstance(candidate.object, EntityMention):
            raise ValueError("literal object has no entity type")
        payload[endpoint]["entity_type"] = entity_type
    elif action == "replace_entity_link":
        # Entity linking does not alter the extracted relation candidate itself.
        return candidate.model_copy(deep=True)
    else:
        raise ValueError("unsupported validation correction action")
    payload["id"] = stable_id(
        "candidate",
        candidate.id,
        action,
        canonical_hash({"replacement": replacement, "payload": payload}),
    )
    return CandidateClaim.model_validate(payload)


def replace_candidate(
    candidates: list[CandidateClaim], target_id: str, replacement: CandidateClaim
) -> list[CandidateClaim]:
    return [replacement if item.id == target_id else item for item in candidates]

