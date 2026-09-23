"""Per-item structure quarantine without storing raw model responses."""

from __future__ import annotations

import math
from typing import Any

from src.core.ids import stable_id
from src.domain import ValidationIssue
from src.governance.validation import ValidationService

FIELDS = (
    "subject",
    "subject_type",
    "relation",
    "object",
    "object_type",
    "evidence_id",
    "confidence",
)


def summarize(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"item_type": type(item).__name__}
    return {
        k: v[:200] if isinstance(v, str) else v
        for k in FIELDS
        if isinstance(v := item.get(k), (str, int, float, bool))
        and (not isinstance(v, str) or not v.startswith(("data:", "Bearer ", "sk-")))
        and (not isinstance(v, float) or math.isfinite(v))
    }


def validate_item(
    item: Any, operation_id: str, index: int, target_type: Any = "candidate"
) -> ValidationIssue | None:
    field = ""
    if not isinstance(item, dict):
        field = "item"
    else:
        for key in ("subject", "relation", "object", "subject_type"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                field = key
                break
        confidence = item.get("confidence", 0.5)
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 1
        ):
            field = "confidence"
        if "qualifiers" in item and not isinstance(item["qualifiers"], dict):
            field = "qualifiers"
        if item.get("object_type") is not None and (
            not isinstance(item["object_type"], str) or not item["object_type"].strip()
        ):
            field = "object_type"
        if "evidence_id" in item and (
            not isinstance(item["evidence_id"], str) or not item["evidence_id"].strip()
        ):
            field = "evidence_id"
        if "evidence_ids" in item and (
            not isinstance(item["evidence_ids"], list)
            or not item["evidence_ids"]
            or any(not isinstance(e, str) or not e for e in item["evidence_ids"])
        ):
            field = "evidence_ids"
    if not field:
        return None
    return ValidationService.issue(
        "INVALID_CANDIDATE_STRUCTURE",
        "structure",
        target_type,
        stable_id("invalid-candidate", operation_id, index),
        f"claims[{index}].{field}",
        "候选字段结构不合法，原始批次中的其他候选仍保留",
        summary=summarize(item),
    )
