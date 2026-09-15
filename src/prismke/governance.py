"""Deterministic entity, claim, conflict, and risk governance."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from prismke.errors import SchemaValidationError
from prismke.ids import stable_id
from prismke.models import (
    CandidateClaim,
    CanonicalEntity,
    Claim,
    ClaimStatus,
    ConflictSet,
    EntityMention,
    ReviewTask,
)
from prismke.schema import SchemaIndex, normalize_label


@dataclass(frozen=True)
class ResolutionBundle:
    entities: list[CanonicalEntity]
    mention_to_entity: dict[str, str]
    review_reasons: dict[str, list[str]]


class EntityResolver:
    def __init__(self, schema: SchemaIndex, existing: list[CanonicalEntity]) -> None:
        self.schema = schema
        self.entities: dict[str, CanonicalEntity] = {item.id: item for item in existing}
        self.lookup: dict[tuple[str, str], CanonicalEntity] = {}
        for entity in [*existing]:
            self._index(entity)
        for item in schema.schema.entity_catalog:
            entity = CanonicalEntity(
                id=item.id, name=item.name, entity_type=item.type, aliases=item.aliases
            )
            self.entities.setdefault(entity.id, entity)
            self._index(entity)

    def _index(self, entity: CanonicalEntity) -> None:
        for name in [entity.name, *entity.aliases]:
            self.lookup[(normalize_label(name), entity.entity_type)] = entity

    def resolve(self, mentions: list[EntityMention]) -> ResolutionBundle:
        mapping: dict[str, str] = {}
        review_reasons: dict[str, list[str]] = {}
        for mention in mentions:
            entity_type = self.schema.entity_type(mention.entity_type)
            if entity_type is None:
                if self.schema.schema.strict:
                    raise SchemaValidationError(
                        f"unknown entity type: {mention.entity_type}"
                    )
                entity_type = mention.entity_type
                review_reasons[mention.id] = ["ontology_addition"]
            key = (normalize_label(mention.name), entity_type)
            entity = self.lookup.get(key)
            if entity is None:
                entity = CanonicalEntity(
                    id=stable_id("entity", entity_type, key[0]),
                    name=mention.name.strip(),
                    entity_type=entity_type,
                    aliases=[],
                )
                self.entities[entity.id] = entity
                self._index(entity)
            mapping[mention.id] = entity.id
        return ResolutionBundle(
            entities=list(self.entities.values()),
            mention_to_entity=mapping,
            review_reasons=review_reasons,
        )


def collect_mentions(candidates: list[CandidateClaim]) -> list[EntityMention]:
    result: dict[str, EntityMention] = {}
    for candidate in candidates:
        result[candidate.subject.id] = candidate.subject
        if isinstance(candidate.object, EntityMention):
            result[candidate.object.id] = candidate.object
    return list(result.values())


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
        if relation and relation.domain and subject_type not in relation.domain:
            raise SchemaValidationError(
                f"relation {relation.id} does not accept subject type {subject_type}"
            )
        object_entity_id: str | None = None
        object_literal: str | None = None
        if isinstance(candidate.object, EntityMention):
            object_entity_id = mention_to_entity[candidate.object.id]
            object_type = entities[object_entity_id].entity_type
            if relation and relation.range and object_type not in relation.range:
                raise SchemaValidationError(
                    f"relation {relation.id} does not accept object type {object_type}"
                )
            object_key = object_entity_id
        else:
            object_literal = candidate.object.strip()
            object_key = normalize_label(object_literal)
        claims.append(
            Claim(
                id=stable_id(
                    "claim", subject_id, relation_id, object_key, candidate.qualifiers
                ),
                subject_id=subject_id,
                relation_id=relation_id,
                object_entity_id=object_entity_id,
                object_literal=object_literal,
                confidence=candidate.confidence,
                evidence_ids=candidate.evidence_ids,
                source_candidate_ids=[candidate.id],
                qualifiers=candidate.qualifiers,
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
    return list(merged.values())


def detect_conflicts(new_claims: list[Claim], existing_claims: list[Claim]) -> list[ConflictSet]:
    groups: dict[tuple[str, str, str], list[Claim]] = defaultdict(list)
    for claim in [*existing_claims, *new_claims]:
        qualifier_key = repr(sorted(claim.qualifiers.items()))
        groups[(claim.subject_id, claim.relation_id, qualifier_key)].append(claim)
    conflicts: list[ConflictSet] = []
    for group_key, group in groups.items():
        object_values = {
            claim.object_entity_id or f"literal:{claim.object_literal}" for claim in group
        }
        claim_ids = sorted({claim.id for claim in group})
        if len(object_values) > 1 and len(claim_ids) > 1:
            conflicts.append(
                ConflictSet(
                    id=stable_id("conflict", *group_key, *claim_ids),
                    claim_ids=claim_ids,
                    reason="incompatible_objects_for_same_subject_relation_scope",
                )
            )
    return conflicts


def route_by_risk(
    run_id: str,
    claims: list[Claim],
    conflicts: list[ConflictSet],
) -> tuple[list[Claim], list[ReviewTask]]:
    conflict_claims = {claim_id for conflict in conflicts for claim_id in conflict.claim_ids}
    reviews: list[ReviewTask] = []
    for claim in claims:
        if claim.status in {ClaimStatus.APPROVED, ClaimStatus.REJECTED}:
            continue
        reasons: list[str] = []
        if claim.id in conflict_claims:
            reasons.append("conflicting_claim")
        if claim.confidence < 0.55:
            claim.status = ClaimStatus.REJECTED
        elif claim.confidence < 0.85:
            reasons.append("medium_confidence")
            claim.status = ClaimStatus.REVIEW_REQUIRED
        elif reasons:
            claim.status = ClaimStatus.REVIEW_REQUIRED
        else:
            claim.status = ClaimStatus.AUTO_APPROVED
        if claim.status == ClaimStatus.REVIEW_REQUIRED:
            reviews.append(
                ReviewTask(
                    id=stable_id("review", run_id, claim.id, *reasons),
                    run_id=run_id,
                    claim_id=claim.id,
                    reasons=reasons,
                )
            )
    return claims, reviews
