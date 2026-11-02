from __future__ import annotations

from pathlib import Path

from src.evaluation.mnre_v2 import (
    CANONICAL_TO_DATASET,
    DATASET_TO_CANONICAL,
    EntityMention,
    MNRECase,
    _aggregate,
    _relation_types,
    marked_text,
    parse_annotation_split,
    retrieval_text,
    stratified_validation_split,
    validate_prediction,
)


def _case(
    sample_id: str,
    relation: str = "MemberOf",
    dataset_label: str = "/per/org/member_of",
) -> MNRECase:
    tokens = ["Maya", "Chen", "joined", "AtlasVision", "X1"]
    return MNRECase(
        id=sample_id,
        split="validation",
        line_number=int(sample_id.rsplit(":", 1)[-1]),
        tokens=tokens,
        text=" ".join(tokens),
        text_sha256="text-hash",
        source_sha256="source-hash",
        head=EntityMention(text="Maya Chen", start=0, end=2),
        tail=EntityMention(text="AtlasVision X1", start=3, end=5),
        image_path="image.jpg",
        image_sha256="image-hash",
        relation=relation,
        dataset_label=dataset_label,
        head_type="Person" if relation != "NoRelation" else None,
        tail_type="Organization" if relation != "NoRelation" else None,
    )


def test_relation_mapping_is_complete_and_bidirectional() -> None:
    assert len(DATASET_TO_CANONICAL) == 23
    assert len(CANONICAL_TO_DATASET) == 23
    assert CANONICAL_TO_DATASET["FellowAlumni"] == "/per/per/alumi"
    assert DATASET_TO_CANONICAL["None"] == "NoRelation"
    assert _relation_types("/per/org/member_of") == ("Person", "Organization")
    assert _relation_types("None") == (None, None)


def test_annotation_parser_preserves_ordered_token_spans(tmp_path: Path) -> None:
    annotations = tmp_path / "mnre.txt"
    annotations.write_text(
        repr(
            {
                "token": ["Maya", "Chen", "joined", "AtlasVision", "X1"],
                "h": {"name": "Maya Chen", "pos": [0, 2]},
                "t": {"name": "AtlasVision X1", "pos": [3, 5]},
                "img_id": "sample.jpg",
                "relation": "/per/org/member_of",
            }
        ),
        encoding="utf-8",
    )
    images = tmp_path / "images"
    images.mkdir()
    (images / "sample.jpg").write_bytes(b"not-decoded-by-parser")
    parsed = parse_annotation_split(annotations, images, "train")
    assert len(parsed) == 1
    assert parsed[0].head == EntityMention(text="Maya Chen", start=0, end=2)
    assert parsed[0].tail == EntityMention(text="AtlasVision X1", start=3, end=5)
    assert parsed[0].relation == "MemberOf"
    assert parsed[0].head_type == "Person"
    assert parsed[0].tail_type == "Organization"


def test_retrieval_text_marks_direction_without_gold_relation() -> None:
    case = _case("validation:00001")
    text = retrieval_text(case, "Two people stand near a logo.")
    assert "[HEAD] Maya Chen [/HEAD]" in text
    assert "[TAIL] AtlasVision X1 [/TAIL]" in text
    assert "PAIR: head=Maya Chen; tail=AtlasVision X1" in text
    assert "MemberOf" not in text
    assert "/per/org/member_of" not in text


def test_marked_text_keeps_head_and_tail_order() -> None:
    assert marked_text(_case("validation:00001")) == (
        "[HEAD] Maya Chen [/HEAD] joined [TAIL] AtlasVision X1 [/TAIL]"
    )


def test_prediction_accepts_only_canonical_schema_relations() -> None:
    assert validate_prediction({"relation": "MemberOf"}) == ("MemberOf", [])
    assert validate_prediction({"relation": "/per/org/member_of"}) == (
        "NoRelation",
        ["relation_not_in_schema"],
    )
    assert validate_prediction({"relation": "InventedRelation"}) == (
        "NoRelation",
        ["relation_not_in_schema"],
    )


def test_validation_split_is_fixed_disjoint_and_complete() -> None:
    cases = []
    relations = [
        ("MemberOf", "/per/org/member_of"),
        ("PeerWith", "/per/per/peer"),
        ("NoRelation", "None"),
    ]
    for index in range(1623):
        relation, label = relations[index % len(relations)]
        cases.append(_case(f"validation:{index + 1:05d}", relation, label))
    first = stratified_validation_split(cases)
    second = stratified_validation_split(cases)
    assert first == second
    assert len(first["prompt_dev"]) == 200
    assert len(first["prompt_holdout"]) == 1423
    assert not set(first["prompt_dev"]) & set(first["prompt_holdout"])


def test_positive_micro_metrics_exclude_no_relation_from_true_positives() -> None:
    positive = _case("validation:00001")
    negative = _case("validation:00002", "NoRelation", "None")
    schema_relations = {
        "MemberOf": {"symmetric": False},
        "NoRelation": {"symmetric": False},
    }
    results = [
        {
            "metrics": {
                "gold": positive.relation,
                "predicted": "MemberOf",
                "true_positive": 1,
                "false_positive": 0,
                "false_negative": 0,
                "correct": 1,
            },
            "errors": [],
            "schema_relations": schema_relations,
        },
        {
            "metrics": {
                "gold": negative.relation,
                "predicted": "NoRelation",
                "true_positive": 0,
                "false_positive": 0,
                "false_negative": 0,
                "correct": 1,
            },
            "errors": [],
            "schema_relations": schema_relations,
        },
    ]
    metrics = _aggregate(results)
    assert metrics["true_positive"] == 1
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["micro_f1"] == 1.0
    assert metrics["accuracy_all_classes"] == 1.0
