"""Deterministic projection from visual extraction state into reviewable media knowledge."""

from __future__ import annotations

from src.core.ids import canonical_hash, stable_id
from src.domain import (
    CandidateMediaRelation,
    CandidateVisualAssertion,
    EvidenceRef,
    GraphMediaContent,
    GraphMediaOccurrence,
    MediaKnowledgeType,
    MediaRelationType,
    Modality,
    VisualAssertionKind,
    VisualReviewTask,
    WorkflowState,
)

_STRUCTURED_ORIGINS = {
    "mineru_table": MediaKnowledgeType.TABLE,
    "mineru_formula": MediaKnowledgeType.FORMULA,
    "mineru_chart": MediaKnowledgeType.CHART,
    "mineru_page_render": MediaKnowledgeType.PAGE_RENDER,
}

_SPATIAL_PREDICATES = {
    "above",
    "below",
    "inside",
    "left_of",
    "near",
    "overlaps",
    "right_of",
}


def _asset_type(origin: str) -> MediaKnowledgeType:
    return _STRUCTURED_ORIGINS.get(origin, MediaKnowledgeType.IMAGE)


def _visual_evidence(state: WorkflowState) -> dict[str, EvidenceRef]:
    if state.document is None:
        return {}
    return {
        item.id: item
        for item in state.document.evidence
        if item.modality in {Modality.IMAGE, Modality.CHART, Modality.TABLE, Modality.FORMULA}
    }


def _assertion_kind(field: str, value_type: str) -> VisualAssertionKind:
    normalized = field.casefold()
    if normalized in _SPATIAL_PREDICATES:
        return VisualAssertionKind.SPATIAL_RELATION
    if value_type in {"integer", "number"} and "count" in normalized:
        return VisualAssertionKind.COUNT
    return VisualAssertionKind.ATTRIBUTE


class MediaKnowledgeProjector:
    """Build idempotent media candidates without granting graph-write authority."""

    def project(self, state: WorkflowState) -> WorkflowState:
        if state.document is None:
            return state
        evidence = {item.id: item for item in state.document.evidence}
        visual_evidence = _visual_evidence(state)
        referenced_assets = {
            item.media_asset_id
            for item in state.document.visual_observations
            if item.media_asset_id
        }
        referenced_evidence = {
            evidence_id
            for item in state.visual_candidates
            for evidence_id in item.evidence_ids
        }
        referenced_evidence.update(
            evidence_id
            for item in state.candidate_attributes
            for evidence_id in item.evidence_ids
        )
        referenced_assets.update(
            item.media_asset_id
            for evidence_id in referenced_evidence
            if (item := evidence.get(evidence_id)) is not None and item.media_asset_id
        )

        contents: dict[str, GraphMediaContent] = {item.id: item for item in state.media_contents}
        occurrences: dict[str, GraphMediaOccurrence] = {
            item.id: item for item in state.media_occurrences
        }
        occurrence_by_asset: dict[str, GraphMediaOccurrence] = {}
        for asset in state.document.media_assets:
            required = (
                asset.origin == "source_image"
                or asset.origin in {"mineru_table", "mineru_formula", "mineru_chart"}
                or asset.id in referenced_assets
            )
            if not required:
                exclusion = f"media_excluded:{asset.id}:unused_or_decorative"
                if exclusion not in state.warnings:
                    state.warnings.append(exclusion)
                continue
            if not asset.blob_hash:
                state.modality_errors["visual"] = f"media_blob_hash_missing:{asset.id}"
                continue
            ref = evidence.get(asset.evidence_id)
            if ref is None:
                state.modality_errors["visual"] = f"media_evidence_missing:{asset.id}"
                continue
            content_id = stable_id("media-content", asset.blob_hash)
            content = GraphMediaContent(
                id=content_id,
                content_hash=asset.blob_hash,
                blob_hash=asset.blob_hash,
                media_type=asset.media_type,
                asset_type=_asset_type(asset.origin),
                width=asset.width,
                height=asset.height,
            )
            contents[content.id] = content
            canvas_width = ref.canvas_width or (float(asset.width) if asset.width else None)
            canvas_height = ref.canvas_height or (float(asset.height) if asset.height else None)
            occurrence_id = stable_id(
                "media-occurrence",
                state.document.id,
                content.id,
                ref.page_number,
                ref.bbox.model_dump(mode="json") if ref.bbox else None,
                ref.id,
            )
            occurrence = GraphMediaOccurrence(
                id=occurrence_id,
                document_id=state.document.id,
                media_content_id=content.id,
                evidence_id=ref.id,
                page_number=ref.page_number,
                bbox=ref.bbox,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
                caption=asset.context_text,
                source_type=asset.origin,
            )
            occurrences[occurrence.id] = occurrence
            occurrence_by_asset[asset.id] = occurrence

        relations: dict[str, CandidateMediaRelation] = {
            item.id: item for item in state.candidate_media_relations
        }
        for mention in state.extracted_entities:
            if mention.modality is not Modality.IMAGE:
                continue
            matched_occurrence: GraphMediaOccurrence | None = None
            for evidence_id in mention.evidence_ids:
                ref = visual_evidence.get(evidence_id)
                if ref is not None and ref.media_asset_id in occurrence_by_asset:
                    matched_occurrence = occurrence_by_asset[ref.media_asset_id]
                    break
            if matched_occurrence is None:
                continue
            entity_id = state.mention_to_entity.get(mention.id)
            relation = CandidateMediaRelation(
                id=stable_id(
                    "candidate-media-relation",
                    matched_occurrence.id,
                    MediaRelationType.DEPICTS,
                    entity_id or mention.id,
                    *sorted(mention.evidence_ids),
                ),
                occurrence_id=matched_occurrence.id,
                relation_type=MediaRelationType.DEPICTS,
                target_entity_id=entity_id,
                target_mention_id=None if entity_id else mention.id,
                evidence_ids=mention.evidence_ids,
                confidence=mention.confidence or 0.0,
            )
            relations[relation.id] = relation

        attribute_defs = {
            item.id: item
            for item in (state.output_schema.attributes if state.output_schema else [])
        }
        assertions: dict[str, CandidateVisualAssertion] = {
            item.id: item for item in state.candidate_visual_assertions
        }
        for attribute in state.candidate_attributes:
            definition = attribute_defs.get(attribute.field)
            if definition is None:
                continue
            matched_occurrence = None
            for evidence_id in attribute.evidence_ids:
                ref = visual_evidence.get(evidence_id)
                if ref is not None and ref.media_asset_id in occurrence_by_asset:
                    matched_occurrence = occurrence_by_asset[ref.media_asset_id]
                    break
            if matched_occurrence is None:
                continue
            entity_id = state.mention_to_entity.get(attribute.subject.id)
            assertion = CandidateVisualAssertion(
                id=stable_id(
                    "candidate-visual-assertion",
                    matched_occurrence.id,
                    entity_id or attribute.subject.id,
                    attribute.field,
                    canonical_hash(attribute.value),
                    *sorted(attribute.evidence_ids),
                ),
                occurrence_id=matched_occurrence.id,
                subject_entity_id=entity_id,
                subject_mention_id=None if entity_id else attribute.subject.id,
                predicate=attribute.field,
                normalized_value=attribute.value,
                value_type=definition.value_type,
                assertion_kind=_assertion_kind(attribute.field, definition.value_type),
                evidence_ids=attribute.evidence_ids,
                confidence=attribute.confidence,
            )
            assertions[assertion.id] = assertion

        entities_by_evidence: dict[str, set[str]] = {}
        entities_by_occurrence: dict[str, set[str]] = {}
        for mention in state.extracted_entities:
            entity_id = state.mention_to_entity.get(mention.id)
            if entity_id is None or mention.modality is not Modality.IMAGE:
                continue
            for evidence_id in mention.evidence_ids:
                entities_by_evidence.setdefault(evidence_id, set()).add(entity_id)
                ref = visual_evidence.get(evidence_id)
                if ref is not None and ref.media_asset_id in occurrence_by_asset:
                    occurrence = occurrence_by_asset[ref.media_asset_id]
                    entities_by_occurrence.setdefault(occurrence.id, set()).add(entity_id)
        for observation in state.document.visual_observations:
            visual_occurrence = occurrence_by_asset.get(observation.media_asset_id)
            if visual_occurrence is None:
                continue
            entity_ids = entities_by_evidence.get(observation.evidence_id, set())
            if not entity_ids:
                entity_ids = entities_by_occurrence.get(visual_occurrence.id, set())
            if len(entity_ids) != 1:
                if observation.attributes:
                    warning = f"visual_attribute_subject_ambiguous:{observation.id}"
                    if warning not in state.warnings:
                        state.warnings.append(warning)
                continue
            entity_id = next(iter(entity_ids))
            for field, value in observation.attributes.items():
                definition = attribute_defs.get(field)
                if definition is None:
                    continue
                assertion = CandidateVisualAssertion(
                    id=stable_id(
                        "candidate-visual-assertion",
                        visual_occurrence.id,
                        entity_id,
                        field,
                        canonical_hash(value),
                        observation.evidence_id,
                    ),
                    occurrence_id=visual_occurrence.id,
                    subject_entity_id=entity_id,
                    predicate=field,
                    normalized_value=value,
                    value_type=definition.value_type,
                    assertion_kind=_assertion_kind(field, definition.value_type),
                    evidence_ids=[observation.evidence_id],
                    confidence=observation.confidence,
                )
                assertions[assertion.id] = assertion

        state.media_contents = list(contents.values())
        state.media_occurrences = list(occurrences.values())
        state.candidate_media_relations = list(relations.values())
        state.candidate_visual_assertions = list(assertions.values())

        conflicting_assertions: set[str] = set()
        for assertion in state.candidate_visual_assertions:
            for attribute in state.candidate_attributes:
                if attribute.field != assertion.predicate:
                    continue
                if state.mention_to_entity.get(attribute.subject.id) != assertion.subject_entity_id:
                    continue
                if any(evidence_id in visual_evidence for evidence_id in attribute.evidence_ids):
                    continue
                if canonical_hash(attribute.value) != canonical_hash(assertion.normalized_value):
                    conflicting_assertions.add(assertion.id)

        existing_targets = {task.target_id for task in state.visual_review_tasks}
        for target_type, candidates in (
            ("media_relation", state.candidate_media_relations),
            ("visual_assertion", state.candidate_visual_assertions),
        ):
            for candidate in candidates:
                entity_id = (
                    candidate.target_entity_id
                    if isinstance(candidate, CandidateMediaRelation)
                    else candidate.subject_entity_id
                )
                if entity_id is None:
                    continue
                if candidate.id in existing_targets:
                    continue
                reasons = ["visual_only_knowledge_requires_human_review"]
                if candidate.id in conflicting_assertions:
                    reasons.append("cross_modal_attribute_conflict")
                state.visual_review_tasks.append(
                    VisualReviewTask(
                        id=stable_id("visual-review", state.run_id, target_type, candidate.id),
                        run_id=state.run_id,
                        target_type=target_type,
                        target_id=candidate.id,
                        reasons=reasons,
                    )
                )
        if any(item.status == "pending" for item in state.visual_review_tasks):
            state.status = "awaiting_review"
        return state
