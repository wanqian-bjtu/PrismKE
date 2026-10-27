"""Read-only projections for explaining and exporting extraction results."""

from __future__ import annotations

import unicodedata
from collections import defaultdict
from typing import Any

from src.core.ids import stable_id
from src.domain import EntityMention, EvidenceRef, WorkflowState


def _normalized_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _evidence_lookup(state: WorkflowState) -> dict[str, EvidenceRef]:
    evidence: dict[str, EvidenceRef] = {}
    if state.document is not None:
        evidence.update({item.id: item for item in state.document.evidence})
    if state.extraction_result is not None:
        evidence.update({item.id: item for item in state.extraction_result.evidence})
    return evidence


def _latest_review_decisions(state: WorkflowState) -> dict[str, str]:
    if state.extraction_result is None:
        return {}
    return {item.target_id: item.decision for item in state.extraction_result.review_events}


def _mention_group_ids(state: WorkflowState) -> dict[str, str]:
    result = state.extraction_result
    if result is None:
        return {}
    groups: dict[str, str] = {}
    for mention in result.entities:
        canonical_id = result.mention_to_entity.get(mention.id)
        groups[mention.id] = canonical_id or stable_id(
            "mention-group",
            mention.entity_type,
            _normalized_name(mention.name),
        )
    return groups


def aggregate_entity_mentions(state: WorkflowState) -> list[dict[str, Any]]:
    """Aggregate mentions without pretending same-name groups are canonical entities."""

    result = state.extraction_result
    if result is None:
        return []
    evidence = _evidence_lookup(state)
    decisions = _latest_review_decisions(state)
    group_ids = _mention_group_ids(state)
    canonical = {item.id: item for item in result.canonical_entities}
    grouped: dict[str, list[EntityMention]] = defaultdict(list)
    for mention in result.entities:
        grouped[group_ids[mention.id]].append(mention)

    records: list[dict[str, Any]] = []
    for group_id, mentions in grouped.items():
        canonical_entity = canonical.get(group_id)
        confidences = [item.confidence for item in mentions if item.confidence is not None]
        evidence_ids = list(
            dict.fromkeys(evidence_id for item in mentions for evidence_id in item.evidence_ids)
        )
        modalities = {
            item.modality.value for item in mentions
        } | {
            evidence[item_id].modality.value for item_id in evidence_ids if item_id in evidence
        }
        pages = sorted(
            {
                item.page_number
                for item_id in evidence_ids
                if (item := evidence.get(item_id)) is not None and item.page_number is not None
            }
        )
        statuses = {decisions.get(item.id, "candidate") for item in mentions}
        records.append(
            {
                "group_id": group_id,
                "canonical_entity_id": canonical_entity.id if canonical_entity else None,
                "grouping": "canonical_entity" if canonical_entity else "same_name_mentions",
                "name": canonical_entity.name if canonical_entity else mentions[0].name,
                "entity_type": (
                    canonical_entity.entity_type if canonical_entity else mentions[0].entity_type
                ),
                "occurrence_count": len(mentions),
                "confidence_average": (
                    round(sum(confidences) / len(confidences), 6) if confidences else None
                ),
                "confidence_max": max(confidences) if confidences else None,
                "modalities": sorted(modalities),
                "pages": pages,
                "review_status": statuses.pop() if len(statuses) == 1 else "mixed",
                "mention_ids": [item.id for item in mentions],
                "evidence_ids": evidence_ids,
            }
        )
    return sorted(records, key=lambda item: (str(item["entity_type"]), str(item["name"])))


def mention_occurrences(state: WorkflowState) -> list[dict[str, Any]]:
    """Expand each mention to its evidence occurrences for page-level traceability."""

    result = state.extraction_result
    if result is None:
        return []
    evidence = _evidence_lookup(state)
    decisions = _latest_review_decisions(state)
    group_ids = _mention_group_ids(state)
    records: list[dict[str, Any]] = []
    for mention in result.entities:
        evidence_ids = mention.evidence_ids or [""]
        for evidence_id in evidence_ids:
            reference = evidence.get(evidence_id)
            records.append(
                {
                    "group_id": group_ids[mention.id],
                    "mention_id": mention.id,
                    "name": mention.name,
                    "entity_type": mention.entity_type,
                    "context": mention.context,
                    "confidence": mention.confidence,
                    "review_status": decisions.get(mention.id, "candidate"),
                    "evidence_id": evidence_id,
                    "modality": (
                        reference.modality.value
                        if reference is not None
                        else mention.modality.value
                    ),
                    "page_number": reference.page_number if reference is not None else None,
                    "char_start": (
                        reference.char_start if reference is not None else mention.char_start
                    ),
                    "char_end": reference.char_end if reference is not None else mention.char_end,
                    "bbox": (
                        reference.bbox.model_dump(mode="json")
                        if reference is not None and reference.bbox is not None
                        else None
                    ),
                    "coordinate_space": (
                        reference.coordinate_space.value
                        if reference is not None and reference.coordinate_space is not None
                        else None
                    ),
                }
            )
    return records


def run_insight(state: WorkflowState) -> dict[str, Any]:
    """Return a sanitized, user-facing explanation of extraction coverage."""

    result = state.extraction_result
    document = state.document
    grouped = aggregate_entity_mentions(state)
    evidence = list(_evidence_lookup(state).values())
    modality_counts: dict[str, int] = defaultdict(int)
    for item in evidence:
        modality_counts[item.modality.value] += 1
    asset_counts: dict[str, int] = defaultdict(int)
    media_type_counts: dict[str, int] = defaultdict(int)
    if document is not None:
        for asset in document.media_assets:
            asset_counts[asset.origin] += 1
            asset_type = {
                "mineru_table": "table",
                "mineru_formula": "formula",
                "mineru_chart": "chart",
                "pdf_page_render": "page_render",
                "mineru_page_render": "page_render",
            }.get(asset.origin, "image")
            media_type_counts[asset_type] += 1
    if result is not None and not media_type_counts:
        for content in result.media_contents:
            media_type_counts[content.asset_type.value] += 1
    vlm_calls = [item for item in state.provider_calls if item.provider == "vlm"]
    ocr_used = bool(
        state.modality_status.get("ocr") == "succeeded"
        or any(item.modality.value == "ocr" for item in evidence)
    )
    decision = state.pdf_parse_decision or (document.pdf_parse_decision if document else None)
    return {
        "run_id": state.run_id,
        "task_mode": state.task_mode.value,
        "task_mode_scope": {
            "entity_extraction": "entities_only",
            "relation_extraction": "relations_only",
            "schema_information_extraction": "entities_relations_attributes_events",
            "joint_entity_relation_extraction": "entities_and_relations",
            "joint_entity_relation_disambiguation": "entities_relations_and_disambiguation",
            "knowledge_graph_construction": "reviewed_graph_commit",
        }[state.task_mode.value],
        "page_count": len(document.pages) if document else 0,
        "text_block_count": len(document.text_blocks) if document else 0,
        "media_asset_count": len(document.media_assets) if document else 0,
        "media_asset_origins": dict(sorted(asset_counts.items())),
        "media_type_counts": dict(sorted(media_type_counts.items())),
        "entity_mention_count": len(result.entities) if result else 0,
        "aggregated_entity_count": len(grouped),
        "relation_count": len(result.relations) if result else 0,
        "attribute_count": len(result.attributes) if result else 0,
        "event_count": len(result.events) if result else 0,
        "media_occurrence_count": len(result.media_occurrences) if result else 0,
        "visual_assertion_count": len(result.candidate_visual_assertions) if result else 0,
        "validation_issue_count": len(result.validation_issues) if result else 0,
        "review_required_count": len(result.review_required_ids) if result else 0,
        "evidence_modality_counts": dict(sorted(modality_counts.items())),
        "pdf_requested_mode": decision.requested_mode.value if decision else None,
        "pdf_actual_parser": decision.actual_parser.value if decision else None,
        "pdf_route_reasons": decision.reason_codes if decision else [],
        "ocr_provider": state.ocr_provider_name,
        "ocr_used": ocr_used,
        "vlm_provider": state.vlm_provider_name,
        "vlm_called": bool(vlm_calls),
        "vlm_call_count": len(vlm_calls),
        "modality_status": dict(state.modality_status),
        "warnings": list(result.warnings if result else state.warnings),
    }


def candidate_graph(state: WorkflowState) -> dict[str, Any]:
    """Project extraction candidates into a read-only graph with traceable details."""

    result = state.extraction_result
    if result is None:
        return {"semantics": "candidate_only", "nodes": [], "edges": [], "details": {}}
    groups = aggregate_entity_mentions(state)
    group_ids = _mention_group_ids(state)
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    details: dict[str, dict[str, Any]] = {}
    for group in groups:
        node_id = str(group["group_id"])
        node = {
            "id": node_id,
            "kind": "entity",
            "label": group["name"],
            "entity_type": group["entity_type"],
            "occurrence_count": group["occurrence_count"],
            "grouping": group["grouping"],
        }
        nodes[node_id] = node
        details[node_id] = group

    def mention_node(mention: EntityMention) -> str:
        node_id = group_ids.get(mention.id)
        if node_id is None:
            node_id = stable_id(
                "mention-group", mention.entity_type, _normalized_name(mention.name)
            )
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "kind": "entity",
                "label": mention.name,
                "entity_type": mention.entity_type,
                "occurrence_count": 1,
                "grouping": "same_name_mentions",
            }
            details[node_id] = mention.model_dump(mode="json")
        return node_id

    for relation in result.relations:
        source = mention_node(relation.subject)
        if isinstance(relation.object, EntityMention):
            target = mention_node(relation.object)
        else:
            target = stable_id("literal", relation.id, relation.object)
            nodes[target] = {
                "id": target,
                "kind": "literal",
                "label": str(relation.object),
            }
            details[target] = {"value": relation.object, "source_relation_id": relation.id}
        edge_id = f"relation:{relation.id}"
        edge = {
            "id": edge_id,
            "kind": "relation",
            "source": source,
            "target": target,
            "label": relation.relation,
            "confidence": relation.confidence,
        }
        edges[edge_id] = edge
        details[edge_id] = relation.model_dump(mode="json")

    content_by_id = {item.id: item for item in result.media_contents}
    for occurrence in result.media_occurrences:
        content = content_by_id.get(occurrence.media_content_id)
        label = occurrence.caption.strip() or (
            content.asset_type.value if content is not None else occurrence.source_type
        )
        nodes[occurrence.id] = {
            "id": occurrence.id,
            "kind": "media",
            "label": label,
            "media_type": content.asset_type.value if content is not None else None,
        }
        details[occurrence.id] = occurrence.model_dump(mode="json")

    for media_relation in result.candidate_media_relations:
        media_target = media_relation.target_entity_id
        if media_target is None and media_relation.target_mention_id is not None:
            media_target = group_ids.get(media_relation.target_mention_id)
        if media_target is None and media_relation.target_claim_id is not None:
            media_target = f"claim:{media_relation.target_claim_id}"
            nodes.setdefault(
                media_target,
                {
                    "id": media_target,
                    "kind": "claim",
                    "label": media_relation.target_claim_id,
                },
            )
        if media_target is None:
            continue
        if media_target not in nodes:
            entity = next(
                (item for item in result.canonical_entities if item.id == media_target),
                None,
            )
            nodes[media_target] = {
                "id": media_target,
                "kind": "entity",
                "label": entity.name if entity else media_target,
                "entity_type": entity.entity_type if entity else None,
            }
        edge_id = f"media-relation:{media_relation.id}"
        edges[edge_id] = {
            "id": edge_id,
            "kind": "media_relation",
            "source": media_relation.occurrence_id,
            "target": media_target,
            "label": media_relation.relation_type.value,
            "confidence": media_relation.confidence,
        }
        details[edge_id] = media_relation.model_dump(mode="json")

    for assertion in result.candidate_visual_assertions:
        assertion_id = f"visual-assertion:{assertion.id}"
        nodes[assertion_id] = {
            "id": assertion_id,
            "kind": "visual_assertion",
            "label": f"{assertion.predicate} = {assertion.normalized_value}",
        }
        details[assertion_id] = assertion.model_dump(mode="json")
        source_edge = f"visual-source:{assertion.id}"
        edges[source_edge] = {
            "id": source_edge,
            "kind": "visual_assertion",
            "source": assertion.occurrence_id,
            "target": assertion_id,
            "label": "VISUAL_ASSERTION",
            "confidence": assertion.confidence,
        }
        details[source_edge] = assertion.model_dump(mode="json")
        subject = assertion.subject_entity_id
        if subject is None and assertion.subject_mention_id is not None:
            subject = group_ids.get(assertion.subject_mention_id)
        if subject is not None:
            if subject not in nodes:
                nodes[subject] = {
                    "id": subject,
                    "kind": "entity",
                    "label": subject,
                }
            about_edge = f"visual-about:{assertion.id}"
            edges[about_edge] = {
                "id": about_edge,
                "kind": "visual_assertion",
                "source": assertion_id,
                "target": subject,
                "label": "ABOUT",
                "confidence": assertion.confidence,
            }
            details[about_edge] = assertion.model_dump(mode="json")
    return {
        "semantics": "candidate_only",
        "task_mode": state.task_mode.value,
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "details": details,
    }
