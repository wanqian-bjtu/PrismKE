from __future__ import annotations

from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter
from src.evaluation.component_ablation_v4 import (
    VISUALLY_ELIGIBLE_RELATIONS,
    _parse_mnre_visual,
    _parse_twitter_prediction_v4,
    _parse_twitter_visual,
    _span_signature,
    apply_twitter_visual_gate,
    mnre_text_prompt,
    mnre_visual_prompt,
    twitter_reflection_prompt,
    twitter_text_prompt,
    twitter_visual_prompt,
)


def _twitter_case() -> twitter.TwitterCase:
    return twitter.TwitterCase(
        id="twitter-1",
        split="validation",
        tokens=["@", "Maya", "Chen", "joined", "AtlasVision"],
        text="@ Maya Chen joined AtlasVision",
        text_sha256="text",
        image_path="image.jpg",
        image_sha256="image",
        image_valid=True,
        invalid_image_reason=None,
        entities=[
            twitter.GoldEntity(
                text="Maya Chen",
                start=2,
                end=11,
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


def test_v4_twitter_text_prompt_isolates_target_visual_information() -> None:
    case = _twitter_case()
    schema = {"entity_types": [{"id": "Person", "definition": "person"}]}
    vanilla = twitter_text_prompt("vanilla", schema, case)
    guided = twitter_text_prompt("schema", schema, case)
    full = twitter_text_prompt(
        "full", schema, case, [{"source": "Maya", "answer": {"entities": []}}]
    )
    assert "LABEL_INVENTORY:" in vanilla and "SCHEMA:" not in vanilla
    assert "SCHEMA:" in guided and "GOLD_TRAINING_EXAMPLES:" not in guided
    assert "GOLD_TRAINING_EXAMPLES:" in full
    assert "VISUAL:" not in vanilla + guided + full
    assert "strip" in vanilla and "@" in vanilla and "#" in vanilla


def test_v4_twitter_visual_prompt_forbids_entity_source_and_boundary_changes() -> None:
    case = _twitter_case()
    candidate = twitter.PredictedEntity(text="Maya Chen", start=2, end=11, type="Person")
    prompt = twitter_visual_prompt({}, case, [candidate])
    assert "Visual context is not an entity source" in prompt
    assert "Never add, delete, merge, split" in prompt
    assert '"candidate_id": 0' in prompt


def test_v4_twitter_gate_can_change_only_type() -> None:
    candidate = twitter.PredictedEntity(text="Maya Chen", start=2, end=11, type="Person")
    evidence, errors = _parse_twitter_visual(
        '{"candidates":[{"candidate_id":0,"visible":"yes",'
        '"suggested_type":"Organization","visual_support":"supports"}]}',
        [],
        1,
    )
    assert errors == []
    updated, accepted, rejected = apply_twitter_visual_gate([candidate], evidence)
    assert accepted == 1 and rejected == 0
    assert updated[0].type == "Organization"
    assert _span_signature(updated) == _span_signature([candidate])


def test_v4_twitter_reflection_declares_immutable_spans() -> None:
    case = _twitter_case()
    candidate = twitter.PredictedEntity(text="Maya Chen", start=2, end=11, type="Person")
    prompt = twitter_reflection_prompt({}, case, [candidate], [])
    assert "immutable" in prompt
    assert "Any span change will be rejected" in prompt


def test_v4_twitter_empty_shape_is_audited_and_normalized() -> None:
    for raw in ("{}", "[]"):
        predicted, errors = _parse_twitter_prediction_v4(_twitter_case(), raw, [])
        assert predicted == []
        assert errors == ["empty_shape_repaired"]


def test_v4_mnre_text_prompt_does_not_expose_gold_label() -> None:
    case = _mnre_case()
    prompt = mnre_text_prompt("vanilla", {}, case)
    assert case.dataset_label not in prompt
    assert "head_type" not in prompt and "tail_type" not in prompt
    assert "Never exchange head and tail" in prompt


def test_v4_mnre_visual_prompt_never_requests_a_relation_label() -> None:
    prompt = mnre_visual_prompt({}, _mnre_case(), "NoRelation")
    assert "Do not output a relation ID" in prompt
    assert "visual_support" in prompt
    evidence, errors = _parse_mnre_visual(
        '{"head_visible":"yes","tail_visible":"yes",'
        '"observable_interaction":"standing together",'
        '"visual_support":"supports","confidence":"high"}',
        [],
    )
    assert errors == [] and evidence is not None


def test_v4_mnre_visual_parser_rejects_free_relation_output() -> None:
    evidence, errors = _parse_mnre_visual(
        '{"head_visible":"yes","tail_visible":"yes",'
        '"observable_interaction":"together","visual_support":"supports",'
        '"confidence":"high","relation":"MemberOf"}',
        [],
    )
    assert evidence is None and errors == ["forbidden_relation_field"]


def test_v4_visual_relation_allowlist_excludes_identity_and_membership() -> None:
    assert "PresentIn" in VISUALLY_ELIGIBLE_RELATIONS
    assert "MemberOf" not in VISUALLY_ELIGIBLE_RELATIONS
    assert "HasNationality" not in VISUALLY_ELIGIBLE_RELATIONS
