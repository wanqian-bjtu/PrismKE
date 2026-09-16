"""Deterministic, auditable cross-modal candidate alignment."""

from __future__ import annotations

from collections import defaultdict

from prismke.core.ids import stable_id
from prismke.domain import (
    AlignmentRecord,
    CandidateClaim,
    EntityMention,
    Modality,
    SchemaIndex,
    normalize_label,
)


def _object_key(candidate: CandidateClaim) -> str:
    value = (
        candidate.object.name if isinstance(candidate.object, EntityMention) else candidate.object
    )
    return normalize_label(value)


def _relation_key(candidate: CandidateClaim, schema: SchemaIndex) -> str:
    relation = schema.relation(candidate.relation)
    return relation.id if relation else normalize_label(candidate.relation)


def _signature(candidate: CandidateClaim, schema: SchemaIndex) -> tuple[str, str, str]:
    return (
        normalize_label(candidate.subject.name),
        _relation_key(candidate, schema),
        _object_key(candidate),
    )


class MultimodalAlignmentService:
    def align(
        self,
        text_candidates: list[CandidateClaim],
        visual_candidates: list[CandidateClaim],
        schema: SchemaIndex,
    ) -> tuple[list[CandidateClaim], list[AlignmentRecord]]:
        all_candidates = [*text_candidates, *visual_candidates]
        groups: dict[tuple[str, str, str], list[CandidateClaim]] = defaultdict(list)
        for candidate in all_candidates:
            groups[_signature(candidate, schema)].append(candidate)
        aligned: list[CandidateClaim] = []
        records: list[AlignmentRecord] = []
        for signature, members in groups.items():
            modalities = sorted({modality for item in members for modality in item.modalities})
            cross_modal = (
                Modality.IMAGE in modalities and Modality.TEXT in modalities
            )
            if len(members) == 1:
                aligned.append(members[0])
                records.append(
                    AlignmentRecord(
                        id=stable_id("alignment", members[0].id),
                        candidate_ids=[members[0].id],
                        modalities=modalities,
                        decision="independent",
                        confidence_before=[members[0].confidence],
                        confidence_after=members[0].confidence,
                        reasons=["no_equivalent_candidate"],
                    )
                )
                continue
            primary = members[0].model_copy(deep=True)
            primary.evidence_ids = sorted(
                {value for item in members for value in item.evidence_ids}
            )
            primary.visual_observation_ids = sorted(
                {value for item in members for value in item.visual_observation_ids}
            )
            primary.modalities = modalities
            primary.confidence = min(
                0.99, max(item.confidence for item in members) + (0.05 if cross_modal else 0.0)
            )
            primary.id = stable_id("candidate", *signature, *sorted(item.id for item in members))
            primary.cross_modal_support = cross_modal
            primary.coarse_visual_evidence = all(item.coarse_visual_evidence for item in members)
            primary.context_only_visual_claim = any(
                item.context_only_visual_claim for item in members
            )
            primary.uncalibrated_visual_confidence = any(
                item.uncalibrated_visual_confidence for item in members
            )
            aligned.append(primary)
            records.append(
                AlignmentRecord(
                    id=stable_id("alignment", *sorted(item.id for item in members)),
                    candidate_ids=[item.id for item in members],
                    modalities=modalities,
                    decision="support",
                    confidence_before=[item.confidence for item in members],
                    confidence_after=primary.confidence,
                    reasons=["canonical_candidate_signature_match"],
                )
            )
        by_subject_relation: dict[tuple[str, str], list[CandidateClaim]] = defaultdict(list)
        for candidate in all_candidates:
            sig = _signature(candidate, schema)
            by_subject_relation[sig[:2]].append(candidate)
        for members in by_subject_relation.values():
            objects = {_object_key(item) for item in members}
            modality_set = {modality for item in members for modality in item.modalities}
            if (
                len(objects) > 1
                and Modality.IMAGE in modality_set
                and ({Modality.TEXT, Modality.OCR} & modality_set)
            ):
                records.append(
                    AlignmentRecord(
                        id=stable_id("alignment-conflict", *sorted(item.id for item in members)),
                        candidate_ids=[item.id for item in members],
                        modalities=sorted(modality_set),
                        decision="conflict",
                        confidence_before=[item.confidence for item in members],
                        reasons=["same_subject_relation_different_object"],
                    )
                )
        for text_candidate in text_candidates:
            for visual_candidate in visual_candidates:
                if normalize_label(text_candidate.subject.name) != normalize_label(
                    visual_candidate.subject.name
                ):
                    continue
                if _relation_key(text_candidate, schema) == _relation_key(
                    visual_candidate, schema
                ):
                    continue
                pair = sorted([text_candidate.id, visual_candidate.id])
                modalities = sorted(
                    {
                        *text_candidate.modalities,
                        *visual_candidate.modalities,
                    }
                )
                records.append(
                    AlignmentRecord(
                        id=stable_id("alignment-related", *pair),
                        candidate_ids=pair,
                        modalities=modalities,
                        decision="related",
                        confidence_before=[
                            text_candidate.confidence,
                            visual_candidate.confidence,
                        ],
                        reasons=["shared_subject_different_relation"],
                    )
                )
        return aligned, records
