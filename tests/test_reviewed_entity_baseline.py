from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from openpyxl import Workbook, load_workbook
from PIL import Image
from typer.testing import CliRunner

from prismke.domain import EntityCandidate, EntityResolutionDecision
from prismke.evaluation import evaluate_entity_linking_manifest
from prismke.evaluation.annotations import export_reviewed_annotations
from prismke.governance.entity_resolution import ResolutionBundle, SemanticEntityResolver
from prismke.providers import MockEmbeddingProvider


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def package_fixture(tmp_path: Path) -> tuple[Path, Path]:
    package = tmp_path / "materials_package"
    original = package / "materials/D01/original.txt"
    original.parent.mkdir(parents=True)
    original.write_text("Alpha Beta", encoding="utf-8")
    digest = hashlib.sha256(original.read_bytes()).hexdigest()
    entities = [
        {"id": "E1", "name": "Alpha", "entity_type": "Organization"},
        {"id": "E2", "name": "Beta", "entity_type": "Person"},
        {"id": "E3", "name": "Gamma", "entity_type": "Organization"},
    ]
    mention = {
        "mention_id": "M1",
        "document_id": "D01",
        "surface": "Alpha",
        "entity_type": "Organization",
        "gold_entity_id": "E1",
        "modality": "text",
        "context": "Alpha Beta",
        "evidence": {"id": "B1", "char_start": 0, "char_end": 5},
    }
    write_json(
        package / "annotations/answer_key.json",
        {"entities": entities, "mentions": [mention]},
    )
    write_json(package / "annotations/initial_kb.json", {"entities": [entities[0]]})
    write_json(
        package / "sources.json",
        [
            {
                "document_id": "D01",
                "original_file": "materials/D01/original.txt",
                "sha256": digest,
                "assets": [],
            }
        ],
    )
    write_json(package / "materials/D01/blocks.json", [{"id": "B1", "text": "Alpha Beta"}])
    wb = Workbook()
    ws = wb.active
    ws.title = "实体提及"
    ws.append(
        [
            "提及ID",
            "文档ID",
            "原始名称",
            "实体类型",
            "初版实体ID",
            "复核状态",
            "人工实体ID",
            "人工动作",
            "复核人",
            "复核意见",
        ]
    )
    ws.append(["M1", "D01", "Alpha", "Organization", "E1", "已确认", None, None, None, None])
    pending = wb.create_sheet("待复核")
    pending.append(["事项ID", "人工结论"])
    pending.append(["Q1", "同人，缺少依据"])
    path = package / "annotations/reviewed.xlsx"
    wb.save(path)
    return package, path


def edit(path: Path, cell: str, value: Any) -> None:
    workbook = load_workbook(path)
    workbook["实体提及"][cell] = value
    workbook.save(path)


def test_export_is_read_only_and_preserves_inputs(tmp_path: Path) -> None:
    package, workbook = package_fixture(tmp_path)
    before = workbook.read_bytes()
    summary = export_reviewed_annotations(workbook, package, tmp_path / "export")
    assert workbook.read_bytes() == before
    assert summary["confirmed"] == 1
    manifest = json.loads((tmp_path / "export/manifest.json").read_text(encoding="utf-8"))
    assert manifest["mentions"][0]["expected_entity_id"] == "E1"
    assert len(manifest["entities"]) == 1


def test_human_answer_changes_only_labels(tmp_path: Path) -> None:
    package, workbook = package_fixture(tmp_path)
    export_reviewed_annotations(workbook, package, tmp_path / "one")
    edit(workbook, "G2", "E3")
    edit(workbook, "H2", "创建新实体")
    export_reviewed_annotations(workbook, package, tmp_path / "two")
    first = json.loads((tmp_path / "one/manifest.json").read_text(encoding="utf-8"))
    second = json.loads((tmp_path / "two/manifest.json").read_text(encoding="utf-8"))
    assert first["entities"] == second["entities"]
    for key in ["name", "entity_type", "context", "evidence_ids"]:
        assert first["mentions"][0][key] == second["mentions"][0][key]
    assert second["mentions"][0]["expected_entity_id"] is None


@pytest.mark.parametrize(
    ("cell", "value"),
    [
        ("G2", "unknown"),
        ("F2", "待人工复核"),
        ("D2", "Person"),
        ("C2", "Other"),
    ],
)
def test_invalid_workbook_stops_before_output(tmp_path: Path, cell: str, value: str) -> None:
    package, workbook = package_fixture(tmp_path)
    edit(workbook, cell, value)
    with pytest.raises(ValueError, match="Excel row 2"):
        export_reviewed_annotations(workbook, package, tmp_path / "export")
    assert not (tmp_path / "export").exists()


def test_duplicate_rows_rejected(tmp_path: Path) -> None:
    package, workbook = package_fixture(tmp_path)
    book = load_workbook(workbook)
    sheet = book["实体提及"]
    sheet.append([cell.value for cell in sheet[2]])
    book.save(workbook)
    with pytest.raises(ValueError, match="duplicate"):
        export_reviewed_annotations(workbook, package, tmp_path / "export")


def test_hash_tampering_stops_export(tmp_path: Path) -> None:
    package, workbook = package_fixture(tmp_path)
    (package / "materials/D01/original.txt").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        export_reviewed_annotations(workbook, package, tmp_path / "export")


def test_display_wrapping_does_not_change_mentions(tmp_path: Path) -> None:
    package, workbook = package_fixture(tmp_path)
    edit(workbook, "C2", "Alpha\n")
    summary = export_reviewed_annotations(workbook, package, tmp_path / "export")
    assert summary["confirmed"] == 1


def test_invalid_span_stops_export(tmp_path: Path) -> None:
    package, workbook = package_fixture(tmp_path)
    answer_path = package / "annotations/answer_key.json"
    data = json.loads(answer_path.read_text())
    data["mentions"][0]["evidence"]["char_end"] = 99
    write_json(answer_path, data)
    with pytest.raises(ValueError, match="invalid text span"):
        export_reviewed_annotations(workbook, package, tmp_path / "export")


def test_visual_bbox_and_hash_are_checked(tmp_path: Path) -> None:
    package, workbook = package_fixture(tmp_path)
    path = package / "materials/D01/image.png"
    Image.new("RGB", (100, 100), "white").save(path)
    data = json.loads((package / "annotations/answer_key.json").read_text())
    item = data["mentions"][0]
    item["modality"] = "image"
    item["evidence"] = {
        "asset_file": "materials/D01/image.png",
        "blob_hash": hashlib.sha256(path.read_bytes()).hexdigest(),
        "canvas_width": 100,
        "canvas_height": 100,
        "bbox": [0, 0, 101, 20],
    }
    write_json(package / "annotations/answer_key.json", data)
    with pytest.raises(ValueError, match="bbox out of bounds"):
        export_reviewed_annotations(workbook, package, tmp_path / "bad")
    item["evidence"]["bbox"] = [0, 0, 50, 20]
    write_json(package / "annotations/answer_key.json", data)
    assert export_reviewed_annotations(workbook, package, tmp_path / "good")["confirmed"] == 1


def test_exclude_preserves_original_record(tmp_path: Path) -> None:
    package, workbook = package_fixture(tmp_path)
    original = package / "annotations/answer_key.json"
    before = original.read_bytes()
    edit(workbook, "F2", "排除")
    with pytest.raises(ValueError, match="no confirmed"):
        export_reviewed_annotations(workbook, package, tmp_path / "export")
    assert original.read_bytes() == before


def evaluation_manifest(tmp_path: Path) -> Path:
    path = tmp_path / "manifest.json"
    write_json(
        path,
        {
            "version": "test",
            "entities": [
                {
                    "id": "E1",
                    "name": "Alpha",
                    "entity_type": "Organization",
                }
            ],
            "mentions": [
                {
                    "id": "M1",
                    "name": "Beta",
                    "entity_type": "Person",
                    "cluster_id": "E2",
                    "expected_entity_id": None,
                },
                {
                    "id": "M2",
                    "name": "Beta",
                    "entity_type": "Person",
                    "cluster_id": "E2",
                    "expected_entity_id": None,
                },
            ],
            "governance": [],
        },
    )
    return path


@pytest.mark.asyncio
async def test_fixed_does_not_insert_new_entities(tmp_path: Path) -> None:
    report = await evaluate_entity_linking_manifest(
        evaluation_manifest(tmp_path),
        MockEmbeddingProvider(),
    )
    assert report.denominators["predicted_nil"] == 2
    assert report.created_entities == 0


@pytest.mark.asyncio
async def test_sequential_inserts_only_system_generated_entities(tmp_path: Path) -> None:
    report = await evaluate_entity_linking_manifest(
        evaluation_manifest(tmp_path),
        MockEmbeddingProvider(),
        protocol="sequential",
    )
    assert report.created_entities == 1
    assert report.details[0]["method"] == "nil"
    assert report.details[1]["method"] == "exact"
    assert report.details[1]["predicted_entity_id"] != "E2"
    assert report.b_cubed_f1 == 1.0


@pytest.mark.asyncio
async def test_review_results_are_not_inserted(tmp_path: Path, monkeypatch: Any) -> None:
    counts = []

    async def review(self: SemanticEntityResolver, mentions: Any) -> ResolutionBundle:
        counts.append(len(await self.graph_store.list_entities()))
        return ResolutionBundle(
            entities=[],
            mention_to_entity={},
            review_reasons={},
            decisions=[
                EntityResolutionDecision(
                    mention_id=mentions[0].id, method="review", confidence=0.7, requires_review=True
                ),
            ],
        )

    monkeypatch.setattr(SemanticEntityResolver, "resolve", review)
    report = await evaluate_entity_linking_manifest(
        evaluation_manifest(tmp_path),
        MockEmbeddingProvider(),
        protocol="sequential",
    )
    assert counts == [1, 1]
    assert report.created_entities == 0
    assert report.auto_link_coverage == 0.0


@pytest.mark.asyncio
async def test_embedding_failure_is_not_reported_as_success(tmp_path: Path) -> None:
    class Broken(MockEmbeddingProvider):
        async def encode(self, texts: list[str]) -> list[list[float]]:
            raise RuntimeError("offline model unavailable")

    with pytest.raises(RuntimeError, match="unavailable"):
        await evaluate_entity_linking_manifest(evaluation_manifest(tmp_path), Broken())


@pytest.mark.asyncio
async def test_correct_review_ranking_is_not_auto_success(tmp_path: Path, monkeypatch: Any) -> None:
    path = evaluation_manifest(tmp_path)
    data = json.loads(path.read_text())
    data["mentions"] = [
        {
            "id": "M1",
            "name": "Alpha",
            "entity_type": "Organization",
            "cluster_id": "E1",
            "expected_entity_id": "E1",
        }
    ]
    write_json(path, data)

    async def review(self: SemanticEntityResolver, mentions: Any) -> ResolutionBundle:
        return ResolutionBundle(
            entities=[],
            mention_to_entity={},
            review_reasons={},
            decisions=[
                EntityResolutionDecision(
                    mention_id=mentions[0].id,
                    method="review",
                    confidence=0.7,
                    requires_review=True,
                    candidates=[
                        EntityCandidate(
                            entity_id="E1",
                            retrieval_score=0.8,
                            name_score=1,
                            context_score=0.6,
                            final_score=0.7,
                        )
                    ],
                ),
            ],
        )

    monkeypatch.setattr(SemanticEntityResolver, "resolve", review)
    report = await evaluate_entity_linking_manifest(path, MockEmbeddingProvider())
    assert report.top_1_accuracy == 1.0
    assert report.auto_link_coverage == 0.0
    assert report.details[0]["decision_correct"] is None


def test_cli_evaluation_does_not_initialize_application_service(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    import prismke.cli as cli

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("production application must not be initialized")

    monkeypatch.setattr(cli, "PrismKEService", forbidden)
    result = CliRunner().invoke(
        cli.app,
        [
            "evaluate-entities",
            str(evaluation_manifest(tmp_path)),
            "--output",
            str(tmp_path / "report.json"),
            "--embedding-provider",
            "mock",
            "--protocol",
            "fixed",
        ],
    )
    assert result.exit_code == 0, result.output


@pytest.mark.asyncio
async def test_baseline_report_exports_readable_candidate_table(tmp_path: Path) -> None:
    import csv

    from prismke.evaluation.baseline_report import write_baseline_report

    report = await evaluate_entity_linking_manifest(
        evaluation_manifest(tmp_path), MockEmbeddingProvider(), protocol="fixed"
    )
    output = tmp_path / "report.md"
    write_baseline_report([report], output)
    with (tmp_path / "fixed-对照表.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == report.cases
    assert "候选得分明细" in rows[0]
    assert "API调用：0" in output.read_text(encoding="utf-8")
