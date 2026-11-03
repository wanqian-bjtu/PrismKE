from __future__ import annotations

import pytest

from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter
from src.evaluation.agent_progression import (
    _json_keyed_visual_evidence,
    _parse_mnre_governance,
    _parse_mnre_vanilla,
    _parse_twitter_governance,
    _parse_twitter_vanilla,
    _select_prompt,
    _structural_gate,
    apply_mnre_governance,
    apply_twitter_governance,
    mnre_fusion_prompt,
    mnre_governance_prompt,
    mnre_vanilla_prompt,
    twitter_fusion_prompt,
    twitter_governance_prompt,
    twitter_vanilla_prompt,
)


def test_visual_evidence_uses_json_string_keys() -> None:
    evidence = {0: {"visible": "yes", "suggested_type": "Person"}}
    converted = _json_keyed_visual_evidence(evidence)
    assert converted == {"0": {"visible": "yes", "suggested_type": "Person"}}


def _twitter_case() -> twitter.TwitterCase:
    return twitter.TwitterCase(
        id="twitter-1",
        split="validation",
        tokens=["Maya", "Chen", "joined", "AtlasVision"],
        text="Maya Chen joined AtlasVision",
        text_sha256="text",
        image_path="image.jpg",
        image_sha256="image",
        image_valid=True,
        entities=[
            twitter.GoldEntity(
                text="Maya Chen",
                start=0,
                end=9,
                type="Person",
                dataset_label="PER",
            )
        ],
    )


def _mnre_case() -> mnre.MNRECase:
    return mnre.MNRECase(
        id="validation:00001",
        split="validation",
        line_number=1,
        tokens=["Maya", "joined", "AtlasVision"],
        text="Maya joined AtlasVision",
        text_sha256="text",
        source_sha256="source",
        head=mnre.EntityMention(text="Maya", start=0, end=1),
        tail=mnre.EntityMention(text="AtlasVision", start=2, end=3),
        image_path="image.jpg",
        image_sha256="image",
        relation="MemberOf",
        dataset_label=mnre.CANONICAL_TO_DATASET["MemberOf"],
        head_type="Person",
        tail_type="Organization",
    )


def test_vanilla_prompts_have_only_text_and_label_ids() -> None:
    twitter_prompt = twitter_vanilla_prompt(_twitter_case())
    mnre_prompt = mnre_vanilla_prompt(_mnre_case())
    combined = twitter_prompt + mnre_prompt
    assert "LABEL_IDS:" in twitter_prompt and "PER" in twitter_prompt
    assert mnre.CANONICAL_TO_DATASET["MemberOf"] in mnre_prompt
    for forbidden in ("SCHEMA:", "VISUAL:", "GOLD_TRAINING_EXAMPLES", "_AGENT"):
        assert forbidden not in combined


def test_vanilla_adapters_map_dataset_labels_to_canonical_types() -> None:
    entities, errors = _parse_twitter_vanilla(
        _twitter_case(),
        '{"entities":[{"text":"Maya Chen","start":0,"end":9,"type":"PER"}]}',
        [],
    )
    assert errors == [] and entities[0].type == "Person"
    relation, errors = _parse_mnre_vanilla(
        '{"relation":"/per/org/member_of"}', []
    )
    assert errors == [] and relation == "MemberOf"


def test_twitter_governance_has_no_cases_and_preserves_spans() -> None:
    case = _twitter_case()
    candidate = twitter.PredictedEntity(text="Maya Chen", start=0, end=9, type="Organization")
    prompt = twitter_governance_prompt("v2", {}, case, [candidate], None)
    assert "Do not add entities" in prompt
    assert "GOLD_TRAINING_EXAMPLES" not in prompt
    decisions, errors = _parse_twitter_governance(
        '{"decisions":[{"candidate_id":0,"action":"change_type",'
        '"type":"Person","confidence":"high","reason_code":"person_name"}]}',
        [],
        1,
    )
    assert errors == []
    updated, accepted, rejected = apply_twitter_governance([candidate], decisions)
    assert accepted == 1 and rejected == 0 and updated[0].type == "Person"
    assert (updated[0].text, updated[0].start, updated[0].end) == (
        candidate.text,
        candidate.start,
        candidate.end,
    )


def test_twitter_fusion_is_the_only_stage_with_cases() -> None:
    prompt = twitter_fusion_prompt(
        "v1",
        {},
        _twitter_case(),
        [],
        [{"source": "example", "answer": {"entities": []}}],
    )
    assert "KNOWLEDGE_FUSION_AND_REVIEW_AGENT" in prompt
    assert "GOLD_TRAINING_EXAMPLES" in prompt
    assert "exact non-overlapping SOURCE substring" in prompt


def test_mnre_governance_keeps_endpoints_and_accepts_only_high_confidence() -> None:
    case = _mnre_case()
    prompt = mnre_governance_prompt("v3", {}, case, "NoRelation", None)
    assert "HEAD and TAIL are immutable" in prompt
    assert "GOLD_TRAINING_EXAMPLES" not in prompt
    decision, errors = _parse_mnre_governance(
        '{"action":"change_relation","relation":"MemberOf",'
        '"confidence":"high","reason_code":"membership"}',
        [],
    )
    assert errors == []
    relation, changed = apply_mnre_governance("NoRelation", decision)
    assert changed and relation == "MemberOf"
    assert "HEAD:" in prompt and "TAIL:" in prompt


def test_mnre_fusion_uses_cases_but_has_no_endpoint_output() -> None:
    prompt = mnre_fusion_prompt(
        "v1",
        {},
        _mnre_case(),
        "NoRelation",
        [{"source": "example", "answer": {"relation": "MemberOf"}}],
    )
    assert "GOLD_TRAINING_EXAMPLES" in prompt
    assert "must not be exchanged" in prompt
    assert '{"relation":"MemberOf"}' in prompt


def test_prompt_selection_uses_micro_f1_then_earliest_version() -> None:
    reports = [
        {"prompt_version": "v1", "metrics": {"micro_f1": 0.5}},
        {"prompt_version": "v2", "metrics": {"micro_f1": 0.6}},
        {"prompt_version": "v3", "metrics": {"micro_f1": 0.6}},
    ]
    assert _select_prompt(reports) == "v2"


def test_structural_gate_rejects_hash_mismatch_and_span_mutation() -> None:
    base = {
        "dataset": "twitter2017",
        "variant": "governance",
        "metrics": {"cases": 100, "errors": {}},
        "input_hashes_present": 100,
        "input_hash_mismatches": 0,
        "span_mutations": 0,
        "endpoint_swaps": 0,
    }
    _structural_gate(base)
    with pytest.raises(RuntimeError, match="input hash"):
        _structural_gate({**base, "input_hash_mismatches": 1})
    with pytest.raises(RuntimeError, match="span"):
        _structural_gate({**base, "span_mutations": 1})
