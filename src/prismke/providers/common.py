"""Shared conversion from provider payloads to domain claims."""

from __future__ import annotations

from typing import Any

from prismke.core.ids import stable_id
from prismke.domain import (
    CandidateClaim,
    EntityMention,
    Modality,
    OutputSchema,
    SchemaIndex,
    normalize_label,
)


def _source_surface_name(
    value: str,
    entity_type: str,
    context: str,
    output_schema: OutputSchema | None,
) -> str:
    if output_schema is None or not context:
        return value
    normalized_context = normalize_label(context)
    normalized_value = normalize_label(value)
    if not normalized_value.startswith("entity:") and normalized_value in normalized_context:
        return value

    canonical_type = SchemaIndex(output_schema).entity_type(entity_type) or entity_type
    matches: dict[str, list[str]] = {}
    for entity in output_schema.entity_catalog:
        if entity.type != canonical_type:
            continue
        for surface in [entity.name, *entity.aliases]:
            if normalize_label(surface) in normalized_context:
                matches.setdefault(entity.id, []).append(surface)
    if len(matches) != 1:
        return value
    return max(next(iter(matches.values())), key=len)


def candidate_from_payload(
    item: dict[str, Any],
    evidence_id: str,
    context: str,
    *,
    modality: Modality = Modality.TEXT,
    source_tool: str = "text_extraction",
    visual_observation_ids: list[str] | None = None,
    output_schema: OutputSchema | None = None,
) -> CandidateClaim:
    subject_name = str(item["subject"]).strip()
    object_name = str(item["object"]).strip()
    subject_type = str(item.get("subject_type", "Unknown")).strip()
    object_type = item.get("object_type")
    subject_name = _source_surface_name(
        subject_name, subject_type, context, output_schema
    )
    if object_type:
        object_name = _source_surface_name(
            object_name, str(object_type), context, output_schema
        )
    subject = EntityMention(
        id=stable_id("mention", subject_name, subject_type, evidence_id),
        name=subject_name,
        entity_type=subject_type,
        context=context,
        modality=modality,
        evidence_ids=[evidence_id],
    )
    if object_type:
        obj: EntityMention | str = EntityMention(
            id=stable_id("mention", object_name, object_type, evidence_id),
            name=object_name,
            entity_type=str(object_type),
            context=context,
            modality=modality,
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
        modalities=[modality],
        source_tool=source_tool,
        visual_observation_ids=visual_observation_ids or [],
    )
