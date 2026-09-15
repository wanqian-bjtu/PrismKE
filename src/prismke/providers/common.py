"""Shared conversion from provider payloads to domain claims."""

from __future__ import annotations

from typing import Any

from prismke.core.ids import stable_id
from prismke.domain import CandidateClaim, EntityMention, Modality


def candidate_from_payload(
    item: dict[str, Any], evidence_id: str, context: str
) -> CandidateClaim:
    subject_name = str(item["subject"]).strip()
    object_name = str(item["object"]).strip()
    subject_type = str(item.get("subject_type", "Unknown")).strip()
    object_type = item.get("object_type")
    subject = EntityMention(
        id=stable_id("mention", subject_name, subject_type, evidence_id),
        name=subject_name,
        entity_type=subject_type,
        context=context,
        modality=Modality.TEXT,
        evidence_ids=[evidence_id],
    )
    if object_type:
        obj: EntityMention | str = EntityMention(
            id=stable_id("mention", object_name, object_type, evidence_id),
            name=object_name,
            entity_type=str(object_type),
            context=context,
            modality=Modality.TEXT,
            evidence_ids=[evidence_id],
        )
    else:
        obj = object_name
    relation = str(item["relation"]).strip()
    return CandidateClaim(
        id=stable_id("candidate", subject.id, relation, object_name, evidence_id),
        subject=subject,
        relation=relation,
        object=obj,
        confidence=float(item.get("confidence", 0.5)),
        evidence_ids=[evidence_id],
        qualifiers=dict(item.get("qualifiers", {})),
    )
