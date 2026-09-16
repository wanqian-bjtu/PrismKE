import csv
import json

from prismke.evaluation.document_review import (
    document_coverage,
    evidence_match,
    export_document_review,
    review_document_state,
)


def test_normalized_bbox_coverage_uses_unit_canvas_not_pixel_dimensions():
    state = {
        "status": "awaiting_review",
        "document": {
            "id": "doc",
            "source_path": "source",
            "source_hash": "a" * 64,
            "media_type": "image/png",
            "evidence": [
                {
                    "id": "ev",
                    "kind": "visual_region",
                    "document_id": "doc",
                    "source_hash": "a" * 64,
                    "modality": "image",
                    "bbox": {"x0": 0, "y0": 0, "x1": 1.2, "y1": 0.9},
                    "coordinate_space": "normalized",
                    "canvas_width": 800,
                    "canvas_height": 600,
                }
            ],
        },
    }
    assert document_coverage(state)["invalid_bbox_ids"] == ["ev"]
    state["document"]["evidence"][0]["bbox"]["x1"] = 1
    assert document_coverage(state)["invalid_bbox_ids"] == []


def test_failed_document_is_never_reported_as_fully_processed():
    assert document_coverage({"status": "failed"})["processing_complete"] is False


def test_pdf_surface_on_another_page_does_not_validate_gold_position():
    gold = {"evidence": {"coordinate_system": "pdf_points", "page": 1, "bbox": [0, 0, 10, 10]}}
    actual = {
        "coordinate_space": "pdf_points",
        "page_number": 2,
        "bbox": {"x0": 0, "y0": 0, "x1": 10, "y1": 10},
    }
    assert evidence_match(gold, actual, "") == "different_page"
    actual["page_number"] = 1
    assert evidence_match(gold, actual, "") == "pdf_block_overlap"


def test_surface_presence_does_not_count_as_correct_link():
    gold = [
        {
            "id": "M1",
            "document_id": "D1",
            "name": "OneKE",
            "entity_type": "SoftwareSystem",
            "cluster_id": "E1",
            "expected_entity_id": "E1",
        }
    ]
    state = {
        "status": "awaiting_review",
        "candidates": [
            {
                "subject": {"id": "m", "name": "OneKE", "entity_type": "Paper", "evidence_ids": []},
            }
        ],
    }
    row = review_document_state(state, gold)[0]
    assert row["surface_found"] is True
    assert row["observed_mentions"][0]["type_matches"] is False
    assert row["automatic_link_correctness"] == "requires_evidence_and_identity_review"


def test_missing_mention_is_kept_in_review_table():
    gold = [
        {
            "id": "M1",
            "document_id": "D1",
            "name": "Example",
            "entity_type": "Person",
            "cluster_id": "E1",
        }
    ]
    assert review_document_state({}, gold)[0]["surface_found"] is False


def test_export_preserves_unexecuted_annotations_and_chinese_csv_headers(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"cases": [{"id": "D1", "status": "failed"}]}))
    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps(
            {
                "mentions": [
                    {
                        "id": "M1",
                        "document_id": "D1",
                        "name": "A",
                        "entity_type": "Person",
                        "cluster_id": "E1",
                    },
                    {
                        "id": "M2",
                        "document_id": "D2",
                        "name": "B",
                        "entity_type": "Person",
                        "cluster_id": "E2",
                    },
                ]
            }
        )
    )
    original = answers.read_bytes()
    rows = export_document_review([report], answers, tmp_path / "output")
    assert len(rows) == 2
    assert rows[1]["run_status"] == "not_started"
    assert answers.read_bytes() == original
    with (tmp_path / "output/annotated-mention-review.csv").open(encoding="utf-8-sig") as stream:
        assert len(list(csv.DictReader(stream))) == 2
