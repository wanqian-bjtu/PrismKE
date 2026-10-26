from __future__ import annotations

import json
from pathlib import Path

import pymupdf

from data.tools.generate_synthetic import generate
from src.domain import PDFComplexityThresholds
from src.parsing.pdf_complexity import inspect_pdf


def test_synthetic_dataset_is_deterministic_and_covers_required_formats(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_manifest = generate(first)
    second_manifest = generate(second)
    first_records = {item["path"]: item["sha256"] for item in first_manifest["files"]}
    second_records = {item["path"]: item["sha256"] for item in second_manifest["files"]}
    assert first_records == second_records
    assert {
        "native/research-brief.txt",
        "native/research-brief.md",
        "native/research-brief.html",
        "native/research-brief.docx",
        "native/research-brief.pdf",
        "scanned/bilingual-scan.pdf",
        "complex/multimodal-evaluation.pdf",
        "images/atlasvision-x1.png",
        "images/atlasvision-x1.jpg",
        "json/nested-research-data.json",
        "expected/expected-results.json",
    } <= first_records.keys()


def test_synthetic_pdf_routing_signals(tmp_path: Path) -> None:
    root = tmp_path / "synthetic"
    generate(root)
    thresholds = PDFComplexityThresholds()
    native = inspect_pdf(root / "native" / "research-brief.pdf", thresholds)
    scanned = inspect_pdf(root / "scanned" / "bilingual-scan.pdf", thresholds)
    complex_report = inspect_pdf(root / "complex" / "multimodal-evaluation.pdf", thresholds)
    assert native.reason_codes == []
    assert "NO_NATIVE_TEXT_RATIO" in scanned.reason_codes
    assert set(complex_report.reason_codes) & {"TABLE_DENSE", "DRAWING_DENSE"}
    with pymupdf.open(root / "scanned" / "bilingual-scan.pdf") as document:
        assert document[0].get_text().strip() == ""


def test_nested_json_preserves_array_order_and_expected_paths(tmp_path: Path) -> None:
    root = tmp_path / "synthetic"
    generate(root)
    payload = json.loads((root / "json" / "nested-research-data.json").read_text())
    assert [item["name"] for item in payload["organization"]["researchers"]] == [
        "Lin Yue",
        "Maya Chen",
    ]
    assert payload["products"][0]["metrics"]["notes"] is None
    expected = json.loads((root / "expected" / "expected-results.json").read_text())
    assert "$.products[0].metrics.accuracy" in expected["json_paths"]
