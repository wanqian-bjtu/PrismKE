"""Cardinality-aware and time-aware claim conflict detection."""

from __future__ import annotations

from collections import defaultdict

from prismke.core.ids import stable_id
from prismke.domain import Claim, ConflictSet, RelationDef, SchemaIndex


def _overlaps(left: Claim, right: Claim) -> bool:
    left_start, left_end = left.valid_from, left.valid_to
    right_start, right_end = right.valid_from, right.valid_to
    if left_end is not None and right_start is not None and left_end <= right_start:
        return False
    return not (right_end is not None and left_start is not None and right_end <= left_start)


def _scope_key(claim: Claim) -> str:
    return repr(sorted(claim.qualifiers.items()))


def _object_key(claim: Claim) -> str:
    return claim.object_entity_id or f"literal:{claim.object_literal}"


def _oriented_claims(claim: Claim, schema: SchemaIndex) -> list[tuple[str, str, str, Claim]]:
    result = [(claim.subject_id, claim.relation_id, _object_key(claim), claim)]
    relation = schema.relation_by_id(claim.relation_id)
    if relation and relation.inverse_relation and claim.object_entity_id:
        result.append(
            (claim.object_entity_id, relation.inverse_relation, claim.subject_id, claim)
        )
    return result


def _violating_claims(claims: list[tuple[str, Claim]], maximum: int) -> set[str]:
    violating: set[str] = set()
    for _, anchor in claims:
        active = [(value, claim) for value, claim in claims if _overlaps(anchor, claim)]
        if len({value for value, _ in active}) > maximum:
            violating.update(claim.id for _, claim in active)
    return violating


def detect_conflicts(
    new_claims: list[Claim], existing_claims: list[Claim], schema: SchemaIndex
) -> list[ConflictSet]:
    groups: dict[tuple[str, str, str], list[tuple[str, Claim]]] = defaultdict(list)
    for claim in [*existing_claims, *new_claims]:
        for subject_id, relation_id, object_key, original in _oriented_claims(claim, schema):
            groups[(subject_id, relation_id, _scope_key(claim))].append((object_key, original))

    conflicts: dict[str, ConflictSet] = {}
    for group_key, group in groups.items():
        relation: RelationDef | None = schema.relation_by_id(group_key[1])
        maximum = relation.max_cardinality if relation else None
        if maximum is None:
            continue
        claim_ids = sorted(_violating_claims(group, maximum))
        if len(claim_ids) < 2:
            continue
        conflict = ConflictSet(
            id=stable_id("conflict", *group_key, *claim_ids),
            claim_ids=claim_ids,
            reason=(
                "incompatible_objects_for_functional_relation"
                if maximum == 1
                else "relation_max_cardinality_exceeded"
            ),
        )
        conflicts[conflict.id] = conflict
    return list(conflicts.values())
