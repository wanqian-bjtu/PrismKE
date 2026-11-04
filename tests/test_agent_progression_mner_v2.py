from __future__ import annotations

from src.core.ids import canonical_hash
from src.evaluation import twitter2017 as twitter
from src.evaluation.agent_progression import _parse_twitter_governance
from src.evaluation.agent_progression_mner_v2 import (
    _can_reuse_v1_fusion,
    apply_reject_only_gate,
)


def _entity(
    text: str = "Maya Chen",
    start: int = 0,
    end: int = 9,
    entity_type: str = "Person",
) -> twitter.PredictedEntity:
    return twitter.PredictedEntity(
        text=text,
        start=start,
        end=end,
        type=entity_type,
    )


def test_high_confidence_reject_is_accepted() -> None:
    final, audit = apply_reject_only_gate(
        [_entity()],
        {0: {"action": "reject", "confidence": "high", "type": None}},
    )
    assert final == []
    assert audit["accepted_high_rejects"] == 1
    assert audit["decision_audit"][0]["accepted"] is True


def test_medium_and_low_rejects_are_blocked() -> None:
    candidates = [_entity(), _entity("AtlasVision", 17, 28, "Organization")]
    final, audit = apply_reject_only_gate(
        candidates,
        {
            0: {"action": "reject", "confidence": "medium", "type": None},
            1: {"action": "reject", "confidence": "low", "type": None},
        },
    )
    assert final == candidates
    assert audit["accepted_high_rejects"] == 0
    assert audit["blocked_low_confidence_rejects"] == 2


def test_all_type_changes_are_blocked_and_retained_entity_is_byte_exact() -> None:
    candidate = _entity(entity_type="Organization")
    final, audit = apply_reject_only_gate(
        [candidate],
        {
            0: {
                "action": "change_type",
                "confidence": "high",
                "type": "Person",
            }
        },
    )
    assert final == [candidate]
    assert final[0].model_dump(mode="json") == candidate.model_dump(mode="json")
    assert audit["blocked_type_changes"] == 1


def test_missing_or_invalid_governance_response_falls_back_to_extraction() -> None:
    candidates = [_entity()]
    missing, missing_audit = apply_reject_only_gate(candidates, {})
    decisions, errors = _parse_twitter_governance("not-json", [], len(candidates))
    invalid, invalid_audit = apply_reject_only_gate(candidates, decisions)
    assert missing == candidates and invalid == candidates
    assert missing_audit["accepted_high_rejects"] == 0
    assert invalid_audit["accepted_high_rejects"] == 0
    assert errors


def test_exact_duplicates_are_removed_without_mutating_retained_entities() -> None:
    candidate = _entity()
    final, audit = apply_reject_only_gate([candidate, candidate.model_copy()], {})
    assert final == [candidate]
    assert audit["governance_deduplications"] == 1


def test_fusion_cache_requires_complete_request_fingerprint() -> None:
    predicted = [_entity().model_dump(mode="json")]
    input_record = {"predicted": predicted}
    old_governance = {"predicted": predicted}
    old_fusion = {
        "prompt_hash": "prompt",
        "input_prediction_hash": canonical_hash(predicted),
        "retrieved_case_ids": ["case-1", "case-2"],
    }
    assert _can_reuse_v1_fusion(
        input_record,
        old_governance,
        old_fusion,
        "prompt",
        ["case-1", "case-2"],
    )
    assert not _can_reuse_v1_fusion(
        input_record,
        old_governance,
        old_fusion,
        "changed-prompt",
        ["case-1", "case-2"],
    )
    assert not _can_reuse_v1_fusion(
        input_record,
        old_governance,
        old_fusion,
        "prompt",
        ["case-2", "case-1"],
    )
    changed = {"predicted": [{**predicted[0], "type": "Location"}]}
    assert not _can_reuse_v1_fusion(
        changed,
        old_governance,
        old_fusion,
        "prompt",
        ["case-1", "case-2"],
    )
