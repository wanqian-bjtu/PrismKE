from __future__ import annotations

import json

import pytest

from src.evaluation import component_ablation as v1
from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter
from src.evaluation.shared_vanilla import (
    MNRE_LABELS,
    TWITTER_LABELS,
    _assert_report,
    mnre_prompt,
    twitter_prompt,
)


def _twitter_case() -> twitter.TwitterCase:
    return twitter.TwitterCase(
        id="test:00001",
        split="test",
        tokens=["Maya", "joined", "AtlasVision"],
        text="Maya joined AtlasVision",
        text_sha256="text",
        image_path="image.jpg",
        image_sha256="image",
        image_valid=True,
        invalid_image_reason=None,
        entities=[
            twitter.GoldEntity(
                text="Maya",
                start=0,
                end=4,
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


def test_shared_twitter_prompt_has_only_canonical_inventory_and_basic_protocol() -> None:
    prompt = twitter_prompt(_twitter_case())
    assert all(label in prompt for label in TWITTER_LABELS)
    assert '"PER"' not in prompt and '"ORG"' not in prompt
    assert "SCHEMA:" not in prompt
    assert "VISUAL" not in prompt
    assert "EXAMPLE" not in prompt
    assert "AGENT" not in prompt
    assert "strip" not in prompt and "normalize" not in prompt
    assert "SOURCE[start:end]" in prompt


def test_shared_mnre_prompt_has_canonical_labels_without_raw_path_leakage() -> None:
    case = _mnre_case()
    prompt = mnre_prompt(case)
    assert all(label in prompt for label in MNRE_LABELS)
    assert case.dataset_label not in prompt
    assert "SCHEMA:" not in prompt
    assert "domain" not in prompt and "range" not in prompt
    assert "symmetric" not in prompt
    assert "VISUAL" not in prompt and "EXAMPLE" not in prompt and "AGENT" not in prompt
    assert "Never exchange HEAD and TAIL" in prompt


def test_shared_output_parsers_use_canonical_protocol() -> None:
    twitter_raw = json.dumps(
        {"entities": [{"text": "Maya", "start": 0, "end": 4, "type": "Person"}]}
    )
    entities, errors = v1._parse_twitter_prediction(_twitter_case(), twitter_raw, [])
    assert errors == [] and entities[0].type == "Person"
    relation, errors = v1._parse_mnre_prediction('{"relation":"MemberOf"}', [])
    assert errors == [] and relation == "MemberOf"


def test_shared_mnre_parser_rejects_official_raw_label() -> None:
    relation, errors = v1._parse_mnre_prediction(
        json.dumps({"relation": mnre.CANONICAL_TO_DATASET["MemberOf"]}), []
    )
    assert relation == mnre.NO_RELATION
    assert errors == ["relation_not_in_schema"]


def test_shared_gate_requires_complete_counts_and_zero_endpoint_swaps() -> None:
    _assert_report(
        {
            "stage": "main",
            "dataset": "twitter2017",
            "metrics": {"cases": 723},
            "endpoint_swaps": 0,
        }
    )
    with pytest.raises(RuntimeError, match="missing cases"):
        _assert_report(
            {
                "stage": "main",
                "dataset": "twitter2017",
                "metrics": {"cases": 722},
                "endpoint_swaps": 0,
            }
        )
    with pytest.raises(RuntimeError, match="ordered MNRE endpoints"):
        _assert_report(
            {
                "stage": "main",
                "dataset": "mnre-v2",
                "metrics": {"cases": 1614},
                "endpoint_swaps": 1,
            }
        )
