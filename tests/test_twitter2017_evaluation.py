from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.evaluation.twitter2017 import (
    CANONICAL_TYPES,
    BudgetStop,
    CNYBudgetLedger,
    GoldEntity,
    PredictedEntity,
    TwitterCase,
    _leakage_reasons,
    _parse_entities,
    generate_captions,
    retrieval_text,
    stratified_validation_split,
    validate_prediction,
)


def _case(sample_id: str, label: str, valid: bool = True) -> TwitterCase:
    text = f"Maya Chen {sample_id}"
    return TwitterCase(
        id=sample_id,
        split="validation",
        tokens=text.split(),
        text=text,
        text_sha256="text",
        image_path="image.jpg",
        image_sha256="image" if valid else None,
        image_valid=valid,
        invalid_image_reason=None if valid else "empty",
        entities=[
            GoldEntity(
                text="Maya Chen",
                start=0,
                end=9,
                type=CANONICAL_TYPES[label],
                dataset_label=label,
            )
        ],
    )


def test_bio_conversion_preserves_multiword_boundaries_and_punctuation() -> None:
    tokens = ["Meet", "Maya", "Chen", ",", "in", "New", "York", "🗽"]
    labels = ["O", "B-PER", "I-PER", "O", "O", "B-LOC", "I-LOC", "O"]
    entities = _parse_entities(tokens, labels)
    assert [(item.text, item.start, item.end, item.type) for item in entities] == [
        ("Maya Chen", 5, 14, "Person"),
        ("New York", 20, 28, "Location"),
    ]


def test_prediction_requires_schema_type_and_exact_source_boundary() -> None:
    case = _case("sample", "PER")
    valid, errors = validate_prediction(
        case,
        {
            "entities": [
                {"text": "Maya Chen", "start": 0, "end": 9, "type": "Person"},
                {"text": "Maya", "start": 0, "end": 9, "type": "Person"},
                {"text": "sample", "start": 10, "end": 16, "type": "PER"},
            ]
        },
    )
    assert valid == [PredictedEntity(text="Maya Chen", start=0, end=9, type="Person")]
    assert errors == ["surface_boundary_mismatch:1", "type_not_in_schema:2"]


def test_retrieval_text_never_contains_gold_labels() -> None:
    case = _case("sample", "PER")
    text = retrieval_text(case, "Two people at an event.")
    assert text == "TEXT: Maya Chen sample\nVISUAL: Two people at an event."
    assert "Person" not in text
    assert "PER" not in text


def test_validation_split_is_fixed_disjoint_and_complete() -> None:
    cases = [
        _case(
            f"id-{index:03d}",
            ("PER", "ORG", "LOC", "MISC")[index % 4],
            index % 7 != 0,
        )
        for index in range(723)
    ]
    first = stratified_validation_split(cases)
    second = stratified_validation_split(cases)
    assert first == second
    assert len(first["prompt_dev"]) == 100
    assert len(first["prompt_holdout"]) == 623
    assert not set(first["prompt_dev"]) & set(first["prompt_holdout"])


def test_valid_image_hash_leakage_is_detected_but_invalid_hash_is_ignored() -> None:
    valid = _case("train-valid", "PER")
    invalid = _case("train-invalid", "PER", valid=False)
    assert _leakage_reasons(valid, set(), set(), {"image"}) == ["valid_image_sha256"]
    assert _leakage_reasons(invalid, set(), set(), {"image"}) == []


def test_budget_ledger_stops_before_crossing_limit(tmp_path: Path) -> None:
    ledger = CNYBudgetLedger(tmp_path / "budget.json", limit_cny=0.02)
    ledger.authorize("one", reserve_cny=0.01)
    ledger.record(
        "one",
        ProviderCallRecord(
            id="call",
            provider="llm",
            operation_id="one",
            requested_model="qwen3.7-flash",
            input_tokens=100,
            output_tokens=100,
            total_tokens=200,
            latency_ms=1,
            status="succeeded",
            prompt_version="test",
            estimated_cost_cny=0.015,
            pricing_snapshot="test",
        )
    )
    with pytest.raises(BudgetStop, match="could exceed"):
        ledger.authorize("two", reserve_cny=0.01)


def test_invalid_image_caption_is_free_and_resume_is_idempotent(tmp_path: Path) -> None:
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    case = _case("invalid", "PER", valid=False)
    (prepared / "train_cases.json").write_text(
        case.model_dump_json().join(["[", "]"]), encoding="utf-8"
    )
    first = asyncio.run(
        generate_captions(prepared, Settings(), split="train", budget_limit_cny=80.0)
    )
    second = asyncio.run(
        generate_captions(prepared, Settings(), split="train", budget_limit_cny=80.0)
    )
    assert first["completed"] == 1
    assert second["resumed"] == 1
    assert first["estimated_cost_cny"] == 0
