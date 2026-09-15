"""Schema-aware claim normalization and supporting-evidence merging."""

from __future__ import annotations

from prismke.core.errors import SchemaValidationError
from prismke.core.ids import stable_id
from prismke.domain import (
    CandidateClaim,
    CanonicalEntity,
    Claim,
    EntityMention,
    SchemaIndex,
    normalize_label,
)


def collect_mentions(candidates: list[CandidateClaim]) -> list[EntityMention]:
    result: dict[str, EntityMention] = {}
    for candidate in candidates:
        result[candidate.subject.id] = candidate.subject
        if isinstance(candidate.object, EntityMention):
            result[candidate.object.id] = candidate.object
    return list(result.values())


def _fact_identity(
    schema: SchemaIndex,
    subject_id: str,
    relation_id: str,
    object_entity_id: str | None,
    object_literal: str | None,
    qualifiers: object,
) -> tuple[object, ...]:
    relation = schema.relation_by_id(relation_id)
    object_key = object_entity_id or f"literal:{normalize_label(object_literal or '')}"
    canonical_subject = subject_id
    canonical_relation = relation_id
    canonical_object = object_key
    if relation and relation.symmetric and object_entity_id:
        canonical_subject, canonical_object = sorted((subject_id, object_entity_id))
    elif relation and relation.inverse_relation and object_entity_id:
        canonical_relation = min(relation_id, relation.inverse_relation)
        if relation_id != canonical_relation:
            canonical_subject, canonical_object = object_entity_id, subject_id
    return canonical_subject, canonical_relation, canonical_object, qualifiers


def normalize_claims(
    candidates: list[CandidateClaim],
    schema: SchemaIndex,
    entities: dict[str, CanonicalEntity],
    mention_to_entity: dict[str, str],
) -> list[Claim]:
    claims: list[Claim] = []
    for candidate in candidates:
        relation = schema.relation(candidate.relation)
        if relation is None:
            if schema.schema.strict:
                raise SchemaValidationError(f"unknown relation: {candidate.relation}")
            relation_id = candidate.relation.strip()
        else:
            relation_id = relation.id
        subject_id = mention_to_entity[candidate.subject.id]
        subject_type = entities[subject_id].entity_type
        object_entity_id: str | None = None
        object_literal: str | None = None
        object_type: str | None = None
        if isinstance(candidate.object, EntityMention):
            object_entity_id = mention_to_entity[candidate.object.id]
            object_type = entities[object_entity_id].entity_type
        else:
            object_literal = candidate.object.strip()
        if relation and object_type:
            subject_matches = not relation.domain or subject_type in relation.domain
            object_matches = not relation.range or object_type in relation.range
            if not (subject_matches and object_matches) and relation.inverse_relation:
                inverse = schema.relation_by_id(relation.inverse_relation)
                if inverse:
                    inverse_subject_matches = (
                        not inverse.domain or subject_type in inverse.domain
                    )
                    inverse_object_matches = not inverse.range or object_type in inverse.range
                    if inverse_subject_matches and inverse_object_matches:
                        relation = inverse
                        relation_id = inverse.id
        if relation and relation.domain and subject_type not in relation.domain:
            raise SchemaValidationError(
                f"relation {relation.id} does not accept subject type {subject_type}"
            )
        if relation and object_type and relation.range and object_type not in relation.range:
            raise SchemaValidationError(
                f"relation {relation.id} does not accept object type {object_type}"
            )
        identity = _fact_identity(
            schema,
            subject_id,
            relation_id,
            object_entity_id,
            object_literal,
            candidate.qualifiers,
        )
        claims.append(
            Claim(
                id=stable_id("claim", *identity),
                subject_id=subject_id,
                relation_id=relation_id,
                object_entity_id=object_entity_id,
                object_literal=object_literal,
                confidence=candidate.confidence,
                evidence_ids=candidate.evidence_ids,
                source_candidate_ids=[candidate.id],
                qualifiers=candidate.qualifiers,
                cross_modal_support=candidate.cross_modal_support,
                coarse_visual_evidence=candidate.coarse_visual_evidence,
            )
        )
    return merge_supporting_claims(claims)


def merge_supporting_claims(claims: list[Claim]) -> list[Claim]:
    merged: dict[str, Claim] = {}
    for claim in claims:
        current = merged.get(claim.id)
        if current is None:
            merged[claim.id] = claim
            continue
        current.evidence_ids = sorted(set(current.evidence_ids + claim.evidence_ids))
        current.source_candidate_ids = sorted(
            set(current.source_candidate_ids + claim.source_candidate_ids)
        )
        current.confidence = max(current.confidence, claim.confidence)
        current.cross_modal_support = current.cross_modal_support or claim.cross_modal_support
        current.coarse_visual_evidence = (
            current.coarse_visual_evidence and claim.coarse_visual_evidence
        )
    return list(merged.values())
