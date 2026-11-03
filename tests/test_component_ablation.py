from __future__ import annotations

from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter
from src.evaluation.component_ablation import (
    _adjacent_variant_pairs,
    _bootstrap_f1,
    _stratified_ids_mnre,
    _stratified_ids_twitter,
    aggregate_mnre,
    aggregate_twitter,
    mnre_prompt,
    reflection_prompt,
    twitter_prompt,
)


def _twitter_case(index: int = 1, valid: bool = True) -> twitter.TwitterCase:
    text = f"Maya Chen joined AtlasVision {index}"
    return twitter.TwitterCase(
        id=f"twitter-{index}",
        split="validation",
        tokens=text.split(),
        text=text,
        text_sha256=f"text-{index}",
        image_path="image.jpg",
        image_sha256=f"image-{index}" if valid else None,
        image_valid=valid,
        invalid_image_reason=None if valid else "empty",
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


def _mnre_case(index: int = 1, relation: str = "MemberOf") -> mnre.MNRECase:
    label = mnre.CANONICAL_TO_DATASET[relation]
    return mnre.MNRECase(
        id=f"validation:{index:05d}",
        split="validation",
        line_number=index,
        tokens=["Maya", "Chen", "joined", "AtlasVision"],
        text="Maya Chen joined AtlasVision",
        text_sha256=f"text-{index}",
        source_sha256=f"source-{index}",
        head=mnre.EntityMention(text="Maya Chen", start=0, end=2),
        tail=mnre.EntityMention(text="AtlasVision", start=3, end=4),
        image_path="image.jpg",
        image_sha256=f"image-{index}",
        relation=relation,
        dataset_label=label,
        head_type="Person" if relation != mnre.NO_RELATION else None,
        tail_type="Organization" if relation != mnre.NO_RELATION else None,
    )


def test_twitter_prompt_feature_isolation() -> None:
    case = _twitter_case()
    schema = {"entity_types": [{"id": "Person", "definition": "named person"}]}
    vanilla = twitter_prompt("vanilla", schema, case)
    guided = twitter_prompt("schema", schema, case)
    multimodal = twitter_prompt("multimodal", schema, case, description="Two people.")
    full = twitter_prompt(
        "full",
        schema,
        case,
        description="Two people.",
        examples=[{"source": "example", "answer": {"entities": []}}],
    )
    assert "LABEL_INVENTORY:" in vanilla
    assert "SCHEMA:" not in vanilla
    assert "VISUAL:" not in vanilla
    assert "EXAMPLES:" not in vanilla
    assert "SCHEMA:" in guided and "VISUAL:" not in guided and "EXAMPLES:" not in guided
    assert "SCHEMA:" in multimodal and "VISUAL:" in multimodal
    assert "EXAMPLES:" not in multimodal
    assert all(marker in full for marker in ("SCHEMA:", "VISUAL:", "EXAMPLES:"))
    assert "PER" not in vanilla


def test_mnre_prompt_feature_isolation_and_no_gold_relation() -> None:
    case = _mnre_case()
    schema = {"relations": [{"id": "MemberOf", "definition": "membership"}]}
    vanilla = mnre_prompt("vanilla", schema, case)
    guided = mnre_prompt("schema", schema, case)
    multimodal = mnre_prompt("multimodal", schema, case, description="A group photo.")
    full = mnre_prompt(
        "full",
        schema,
        case,
        description="A group photo.",
        examples=[{"source": "example", "answer": {"relation": "NoRelation"}}],
    )
    assert "LABEL_INVENTORY:" in vanilla and "SCHEMA:" not in vanilla
    assert "/per/org/member_of" not in vanilla
    assert "SCHEMA:" in guided and "VISUAL:" not in guided
    assert "VISUAL:" in multimodal and "EXAMPLES:" not in multimodal
    assert all(marker in full for marker in ("SCHEMA:", "VISUAL:", "EXAMPLES:"))


def test_reflection_prompt_is_one_explicit_bounded_pass() -> None:
    prompt = reflection_prompt(
        "mnre-v2",
        '{"relation":"NoRelation"}',
        ["relation_not_in_schema"],
        "original",
    )
    assert prompt.count("REFLECTION_PASS") == 1
    assert "FIRST_RESPONSE" in prompt
    assert "DETERMINISTIC_VALIDATION" in prompt
    assert "ORIGINAL_TASK" in prompt


def test_stratified_subsets_are_fixed_and_complete() -> None:
    twitter_cases = [_twitter_case(index, valid=index % 5 != 0) for index in range(1, 101)]
    mnre_cases = [
        _mnre_case(index, "MemberOf" if index % 3 else mnre.NO_RELATION)
        for index in range(1, 101)
    ]
    assert _stratified_ids_twitter(twitter_cases, 20) == _stratified_ids_twitter(
        twitter_cases, 20
    )
    assert len(_stratified_ids_twitter(twitter_cases, 20)) == 20
    assert _stratified_ids_mnre(mnre_cases, 20) == _stratified_ids_mnre(mnre_cases, 20)
    assert len(_stratified_ids_mnre(mnre_cases, 20)) == 20


def test_twitter_aggregate_and_bootstrap_are_reproducible() -> None:
    records = [
        {
            "id": "one",
            "gold": [{"text": "Maya", "start": 0, "end": 4, "type": "Person"}],
            "predicted": [
                {"text": "Maya", "start": 0, "end": 4, "type": "Person"}
            ],
            "metrics": {"tp": 1, "fp": 0, "fn": 0},
            "errors": [],
            "image_valid": True,
        },
        {
            "id": "two",
            "gold": [{"text": "Atlas", "start": 0, "end": 5, "type": "Organization"}],
            "predicted": [],
            "metrics": {"tp": 0, "fp": 0, "fn": 1},
            "errors": [],
            "image_valid": False,
        },
    ]
    metrics = aggregate_twitter(records)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["micro_f1"] == 0.666667
    assert metrics["valid_image_subset"]["micro_f1"] == 1.0
    assert _bootstrap_f1(records) == _bootstrap_f1(records)


def test_mnre_macro_f1_distinguishes_present_and_all_schema_labels() -> None:
    records = [
        {
            "id": "one",
            "gold": "MemberOf",
            "predicted": "MemberOf",
            "metrics": mnre._result_metrics(_mnre_case(), "MemberOf"),
            "errors": [],
        },
        {
            "id": "two",
            "gold": "NoRelation",
            "predicted": "NoRelation",
            "metrics": mnre._result_metrics(
                _mnre_case(2, mnre.NO_RELATION), mnre.NO_RELATION
            ),
            "errors": [],
        },
    ]
    metrics = aggregate_mnre(records)
    assert metrics["micro_f1"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["macro_f1_all_schema_relations"] < 1.0


def test_four_variants_produce_three_adjacent_bootstrap_comparisons() -> None:
    assert _adjacent_variant_pairs() == (
        ("vanilla", "schema"),
        ("schema", "multimodal"),
        ("multimodal", "full"),
    )
