from __future__ import annotations

import pytest

from src.evaluation import component_ablation as v1
from src.evaluation import component_ablation_v4 as v4
from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter
from src.evaluation.component_ablation_v5 import (
    _assert_mnre_identity,
    _assert_twitter_identity,
    _cache_usable,
    _visual_input_hash,
)


def _entity(entity_type: str = "Person") -> twitter.PredictedEntity:
    return twitter.PredictedEntity(text="Maya Chen", start=0, end=9, type=entity_type)


def _twitter_case() -> twitter.TwitterCase:
    return twitter.TwitterCase(
        id="twitter-1",
        split="test",
        tokens=["Maya", "Chen"],
        text="Maya Chen",
        text_sha256="text",
        image_path="image.jpg",
        image_sha256="image",
        image_valid=True,
        invalid_image_reason=None,
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
        id="test:00001",
        split="test",
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


def test_v5_no_visual_edit_preserves_twitter_schema_prediction() -> None:
    baseline = [_entity()]
    final = [_entity()]
    assert _assert_twitter_identity(baseline, final, accepted=0) == []


def test_v5_twitter_allows_only_accepted_type_changes() -> None:
    baseline = [_entity("Person")]
    final = [_entity("Organization")]
    assert _assert_twitter_identity(baseline, final, accepted=1) == [0]
    with pytest.raises(RuntimeError, match="without an accepted"):
        _assert_twitter_identity(baseline, final, accepted=0)


def test_v5_twitter_rejects_span_mutation_even_when_edit_is_accepted() -> None:
    baseline = [_entity()]
    final = [twitter.PredictedEntity(text="Maya", start=0, end=4, type="Person")]
    with pytest.raises(RuntimeError, match="changed an entity span"):
        _assert_twitter_identity(baseline, final, accepted=1)


def test_v5_mnre_requires_accepted_fusion_for_relation_change() -> None:
    _assert_mnre_identity("NoRelation", "NoRelation", fusion_accepted=False)
    _assert_mnre_identity("NoRelation", "PresentIn", fusion_accepted=True)
    with pytest.raises(RuntimeError, match="without an accepted"):
        _assert_mnre_identity("NoRelation", "PresentIn", fusion_accepted=False)


def test_v5_visual_cache_requires_exact_baseline_and_clean_visual_result() -> None:
    old = {
        "text_predicted": [{"text": "Maya Chen", "start": 0, "end": 9, "type": "Person"}],
        "visual_errors": [],
        "raw_visual": '{"candidates":[]}',
    }
    assert _cache_usable(old, old["text_predicted"], "raw_visual")
    assert not _cache_usable(old, [], "raw_visual")
    assert not _cache_usable(
        {**old, "visual_errors": ["invalid"]}, old["text_predicted"], "raw_visual"
    )


def test_v5_visual_input_fingerprint_changes_with_any_material_input() -> None:
    original = _visual_input_hash("prompt", "image", "schema", "model")
    assert original != _visual_input_hash("changed", "image", "schema", "model")
    assert original != _visual_input_hash("prompt", "changed", "schema", "model")
    assert original != _visual_input_hash("prompt", "image", "changed", "model")
    assert original != _visual_input_hash("prompt", "image", "schema", "changed")


def test_v5_prompts_do_not_expose_gold_targets() -> None:
    twitter_case = _twitter_case()
    twitter_prompt = v4.twitter_visual_prompt({}, twitter_case, [_entity("Organization")])
    assert "dataset_label" not in twitter_prompt
    mnre_case = _mnre_case()
    mnre_prompt = v4.mnre_visual_prompt({}, mnre_case, "NoRelation")
    assert mnre_case.dataset_label not in mnre_prompt
    assert mnre_case.relation not in mnre_prompt


def test_v5_mnre_visual_parser_still_rejects_free_relation_output() -> None:
    evidence, errors = v4._parse_mnre_visual(
        '{"head_visible":"yes","tail_visible":"yes",'
        '"observable_interaction":"together","visual_support":"supports",'
        '"confidence":"high","relation":"MemberOf"}',
        [],
    )
    assert evidence is None
    assert errors == ["forbidden_relation_field"]


def test_paired_bootstrap_caps_identical_predictions_at_probability_one() -> None:
    records = [
        {
            "id": "sample-1",
            "metrics": {"tp": 1, "fp": 0, "fn": 0},
        },
        {
            "id": "sample-2",
            "metrics": {"tp": 0, "fp": 1, "fn": 1},
        },
    ]
    result = v1._paired_bootstrap_delta(records, records)
    assert result == {
        "mean_delta": 0.0,
        "lower": 0.0,
        "upper": 0.0,
        "two_sided_p": 1.0,
    }
