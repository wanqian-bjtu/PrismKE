"""Shared candidate correction policy, including legacy checkpoint reconstruction."""

from collections.abc import Iterable

from src.domain import CandidateClaim, EntityMention, ValidationAction, ValidationIssue

APPROVAL_REQUIRED = "VALIDATION_APPROVAL_REQUIRED"


def candidate_actions(
    candidate: CandidateClaim, issues: Iterable[ValidationIssue]
) -> list[ValidationAction]:
    values = list(issues)
    if not values or any(item.target_type != "candidate" for item in values):
        return []
    actions: list[ValidationAction] = ["approve", "exclude", "defer"]
    # Evidence/structural failures cannot be repaired by changing schema fields.
    if any(item.stage != "schema" and item.code != APPROVAL_REQUIRED for item in values):
        return actions
    codes = {item.code for item in values}
    if "SCHEMA_DOMAIN_RANGE" in codes:
        actions.extend(["replace_relation", "replace_entity_type", "replace_entity_link"])
        if isinstance(candidate.object, EntityMention):
            actions.append("swap_endpoints")
    if "UNKNOWN_RELATION" in codes and "replace_relation" not in actions:
        actions.append("replace_relation")
    if "UNKNOWN_ENTITY_TYPE" in codes and "replace_entity_type" not in actions:
        actions.append("replace_entity_type")
    return actions
