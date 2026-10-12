from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pymupdf
import pytest
from docx import Document
from fastapi.testclient import TestClient
from PIL import Image

from src.api import create_app
from src.core.errors import DocumentConversionError, UnsupportedDocumentError
from src.core.ids import canonical_hash
from src.core.settings import Settings
from src.domain import (
    BatchItemStatus,
    BatchStatus,
    EntitySourceMode,
    ProvidedEntity,
    SourceDocument,
    TaskMode,
)
from src.parsing import ParserRegistry
from src.parsing.adapters import LegacyDOCParser
from src.persistence import FileEvidenceStore
from src.workflow import PrismKEService


def _fact(path: Path, name: str = "sample.txt") -> Path:
    source = path / name
    source.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n",
        encoding="utf-8",
    )
    return source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "task_mode",
    [
        TaskMode.ENTITY_EXTRACTION,
        TaskMode.RELATION_EXTRACTION,
        TaskMode.SCHEMA_INFORMATION_EXTRACTION,
        TaskMode.JOINT_ENTITY_RELATION_EXTRACTION,
        TaskMode.JOINT_ENTITY_RELATION_DISAMBIGUATION,
    ],
)
async def test_extraction_modes_never_write_graph(
    tmp_path: Path, schema_path: Path, task_mode: TaskMode
) -> None:
    source = _fact(tmp_path)
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    kwargs = {}
    if task_mode == TaskMode.RELATION_EXTRACTION:
        kwargs = {
            "entity_source_mode": EntitySourceMode.PROVIDED,
            "provided_entities": [
                ProvidedEntity(name="PrismKE", entity_type="Software"),
                ProvidedEntity(name="OpenAI", entity_type="Organization"),
            ],
        }
    try:
        state = await service.run(
            source,
            schema_path,
            "mock",
            task_mode=task_mode,
            **kwargs,
        )
        assert state.status in {"completed", "awaiting_review"}
        assert await service.graph_store.list_revisions() == []
        if state.status == "completed":
            assert state.extraction_result is not None
            assert state.extraction_result.task_mode == task_mode
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_provided_entity_is_grounded_and_ambiguous_match_requires_review(
    tmp_path: Path, schema_path: Path
) -> None:
    source = tmp_path / "ambiguous.txt"
    source.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\nPrismKE is auditable.\n",
        encoding="utf-8",
    )
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        state = await service.run(
            source,
            schema_path,
            "mock",
            task_mode=TaskMode.RELATION_EXTRACTION,
            entity_source_mode=EntitySourceMode.PROVIDED,
            provided_entities=[
                ProvidedEntity(name="PrismKE", entity_type="Software"),
                ProvidedEntity(name="OpenAI", entity_type="Organization"),
            ],
        )
        assert state.status == "awaiting_review"
        assert state.extraction_result is not None
        assert len(state.extraction_result.review_required_ids) == 1
        target_id = state.extraction_result.review_required_ids[0]
        target = next(item for item in state.extraction_result.entities if item.id == target_id)
        assert target.name == "PrismKE"
        assert target.confidence is None
        assert target.evidence_ids

        reviewed = service.review_extraction_result(
            state.run_id,
            "entity",
            target_id,
            "approve",
            "tester",
            "confirmed repeated references are the same supplied entity",
            "provided-entity-review-1",
            0,
        )
        assert reviewed.version == 1
        assert service.show_run(state.run_id).status == "completed"
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_missing_provided_entity_fails_before_model_call(
    tmp_path: Path, schema_path: Path
) -> None:
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        with pytest.raises(ValueError, match="PROVIDED_ENTITY_NOT_FOUND:Missing"):
            await service.run(
                _fact(tmp_path),
                schema_path,
                "mock",
                task_mode=TaskMode.RELATION_EXTRACTION,
                entity_source_mode=EntitySourceMode.PROVIDED,
                provided_entities=[ProvidedEntity(name="Missing", entity_type="Software")],
            )
        task_files = list((tmp_path / "runtime" / "requests").rglob("*.json"))
        assert task_files == []
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_knowledge_graph_mode_keeps_existing_commit_behavior(
    tmp_path: Path, schema_path: Path
) -> None:
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        state = await service.run(_fact(tmp_path), schema_path, "mock")
        assert state.task_mode == TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION
        assert state.revision is not None
        assert state.extraction_result is not None
        assert len(await service.graph_store.list_revisions()) == 1
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_json_parser_emits_verifiable_jsonpath_evidence(tmp_path: Path) -> None:
    source = tmp_path / "nested.json"
    source.write_text(
        json.dumps({"name": "PrismKE", "items": [{"year": 2026}, None]}),
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    document = await ParserRegistry(asset_dir=runtime / "assets").parse(SourceDocument(path=source))
    assert [item.json_path for item in document.evidence] == [
        "$.name",
        "$.items[0].year",
        "$.items[1]",
    ]
    store = FileEvidenceStore(runtime / "evidence")
    await store.put_document(document)
    assert all([await store.verify(item.id) for item in document.evidence])
    ref = document.evidence[0]
    ref_path = store._ref_path(ref.id)
    wrapper = json.loads(ref_path.read_text(encoding="utf-8"))
    wrapper["record"]["json_value_hash"] = "0" * 64
    wrapper["checksum"] = canonical_hash(wrapper["record"])
    ref_path.write_text(json.dumps(wrapper), encoding="utf-8")
    assert not await store.verify(ref.id)


@pytest.mark.asyncio
async def test_supported_document_parsers_cover_v011_formats(tmp_path: Path) -> None:
    (tmp_path / "sample.txt").write_text("plain", encoding="utf-8")
    (tmp_path / "sample.md").write_text("markdown", encoding="utf-8")
    (tmp_path / "sample.html").write_text("<p>html</p>", encoding="utf-8")
    (tmp_path / "sample.json").write_text('{"key":"value"}', encoding="utf-8")
    document = Document()
    document.add_paragraph("docx")
    document.save(tmp_path / "sample.docx")
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "pdf")
    pdf.save(tmp_path / "sample.pdf")
    pdf.close()
    image_formats = [
        ("png", "PNG"),
        ("jpg", "JPEG"),
        ("webp", "WEBP"),
        ("tiff", "TIFF"),
        ("bmp", "BMP"),
    ]
    for suffix, image_format in image_formats:
        Image.new("RGB", (96, 96), "white").save(tmp_path / f"sample.{suffix}", format=image_format)
    registry = ParserRegistry(asset_dir=tmp_path / "assets")
    for source in sorted(tmp_path.glob("sample.*")):
        parsed = await registry.parse(SourceDocument(path=source))
        assert parsed.source_filename == source.name
        assert parsed.source_hash


@pytest.mark.asyncio
async def test_legacy_doc_requires_explicit_converter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "legacy.doc"
    source.write_bytes(b"not-a-word-document")
    parser = LegacyDOCParser(
        derived_dir=tmp_path / "derived",
        libreoffice_bin=tmp_path / "missing-soffice",
    )
    monkeypatch.setattr("src.parsing.adapters.shutil.which", lambda _: None)
    with pytest.raises(DocumentConversionError, match="LIBREOFFICE_NOT_FOUND"):
        await parser.parse(SourceDocument(path=source))


@pytest.mark.libreoffice
@pytest.mark.skipif(
    os.getenv("PRISMKE_TEST_LIBREOFFICE") != "1",
    reason="set PRISMKE_TEST_LIBREOFFICE=1 for the real conversion test",
)
@pytest.mark.asyncio
async def test_real_legacy_doc_conversion_preserves_derivation(tmp_path: Path) -> None:
    executable_value = os.getenv("PRISMKE_LIBREOFFICE_BIN") or shutil.which("soffice")
    if not executable_value:
        pytest.fail("PRISMKE_TEST_LIBREOFFICE=1 requires LibreOffice")
    executable = Path(executable_value)
    source_docx = tmp_path / "legacy-source.docx"
    document = Document()
    document.add_paragraph("PrismKE legacy DOC conversion test")
    document.save(source_docx)
    profile = tmp_path / "source-profile"
    profile.mkdir()
    converted = subprocess.run(
        [
            str(executable),
            f"-env:UserInstallation={profile.as_uri()}",
            "--headless",
            "--convert-to",
            "doc:MS Word 97",
            "--outdir",
            str(tmp_path),
            str(source_docx),
        ],
        capture_output=True,
        check=False,
        timeout=120,
    )
    source_doc = tmp_path / "legacy-source.doc"
    assert converted.returncode == 0 and source_doc.is_file()
    parsed = await ParserRegistry(
        asset_dir=tmp_path / "assets",
        derived_dir=tmp_path / "derived",
        libreoffice_bin=executable,
    ).parse(SourceDocument(path=source_doc))
    assert any("PrismKE legacy DOC" in block.text for block in parsed.text_blocks)
    assert len(parsed.derivations) == 1
    derivation = parsed.derivations[0]
    assert derivation.source_hash == parsed.source_hash
    assert derivation.source_hash != derivation.derived_hash
    assert derivation.tool == "libreoffice" and derivation.tool_version


@pytest.mark.asyncio
async def test_batch_reuses_duplicate_content_and_exposes_results(
    tmp_path: Path, schema_path: Path
) -> None:
    first = _fact(tmp_path, "first.txt")
    duplicate = tmp_path / "duplicate.txt"
    duplicate.write_bytes(first.read_bytes())
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        batch, created = service.create_batch(
            [first, duplicate],
            schema_path,
            task_mode=TaskMode.JOINT_ENTITY_RELATION_EXTRACTION,
        )
        assert created
        assert batch.items[1].status == BatchItemStatus.REUSED
        assert batch.items[0].run_id == batch.items[1].run_id
        assert batch.items[0].run_id is not None
        await service.execute_run(batch.items[0].run_id)
        refreshed = service.refresh_batch(batch.id)
        assert refreshed.status == BatchStatus.COMPLETED
        results = service.batch_results(batch.id)
        assert len(results) == 2
        assert all(item.result is not None for item in results)
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_batch_failure_blocks_fusion_until_excluded(
    tmp_path: Path, schema_path: Path
) -> None:
    good = _fact(tmp_path, "good.txt")
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"unsupported")
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        await service.executions.start(persistent=True)
        batch, _ = service.create_batch(
            [good, bad],
            schema_path,
            task_mode=TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION,
        )
        for run_id in dict.fromkeys(item.run_id for item in batch.items if item.run_id):
            state = service.show_run(run_id)
            if state.input_path == str(good.resolve()):
                completed = await service.execute_run(run_id)
                assert completed.status == "completed"
            else:
                with pytest.raises(UnsupportedDocumentError, match="unsupported media type"):
                    await service.execute_run(run_id)
        refreshed = service.refresh_batch(batch.id)
        assert refreshed.status == BatchStatus.BLOCKED
        failed = next(item for item in refreshed.items if item.status == BatchItemStatus.FAILED)
        excluded = service.exclude_batch_item(batch.id, failed.id, "tester", "unsupported fixture")
        assert excluded.status == BatchStatus.AWAITING_COMMIT
        assert await service.graph_store.list_revisions() == []
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_cross_document_conflict_blocks_commit_until_source_is_excluded(
    tmp_path: Path,
) -> None:
    schema = tmp_path / "functional.yaml"
    schema.write_text(
        """
schema_id: functional
version: "1"
strict: true
entity_types:
  - id: Software
  - id: Organization
relations:
  - id: developed_by
    domain: [Software]
    range: [Organization]
    max_cardinality: 1
entity_catalog:
  - id: entity:prismke
    name: PrismKE
    type: Software
""".strip(),
        encoding="utf-8",
    )
    first = tmp_path / "first.txt"
    first.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n",
        encoding="utf-8",
    )
    second = tmp_path / "second.txt"
    second.write_text(
        "PrismKE | developed_by | Acme | Software | Organization | 0.93\n",
        encoding="utf-8",
    )
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        await service.executions.start(persistent=True)
        batch, _ = service.create_batch([first, second], schema)
        for run_id in dict.fromkeys(item.run_id for item in batch.items if item.run_id):
            await service.execute_run(run_id)
        assert service.refresh_batch(batch.id).status == BatchStatus.AWAITING_COMMIT
        with pytest.raises(ValueError, match="BATCH_CROSS_DOCUMENT_CONFLICT"):
            await service.confirm_batch_commit(batch.id, "tester")
        blocked = service.refresh_batch(batch.id)
        assert blocked.status == BatchStatus.BLOCKED
        assert blocked.errors[0].startswith("cross_document_conflict:")
        excluded = service.exclude_batch_item(
            blocked.id,
            blocked.items[1].id,
            "tester",
            "conflicting source requires separate review",
        )
        assert excluded.status == BatchStatus.AWAITING_COMMIT
        committed = await service.confirm_batch_commit(batch.id, "tester")
        assert committed.status == BatchStatus.COMPLETED
        assert committed.revision_id is not None
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_extraction_review_is_versioned_and_idempotent(
    tmp_path: Path, schema_path: Path
) -> None:
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        state = await service.run(
            _fact(tmp_path),
            schema_path,
            "mock",
            task_mode=TaskMode.JOINT_ENTITY_RELATION_EXTRACTION,
        )
        assert state.extraction_result is not None
        target = state.extraction_result.relations[0]
        reviewed = service.review_extraction_result(
            state.run_id,
            "relation",
            target.id,
            "approve",
            "tester",
            "",
            "request-1",
            0,
        )
        repeated = service.review_extraction_result(
            state.run_id,
            "relation",
            target.id,
            "approve",
            "tester",
            "",
            "request-1",
            0,
        )
        assert reviewed.version == repeated.version == 1
        with pytest.raises(ValueError, match="STALE_RESULT_VERSION"):
            service.review_extraction_result(
                state.run_id,
                "relation",
                target.id,
                "reject",
                "tester",
                "incorrect",
                "request-2",
                0,
            )
    finally:
        await service.close()


def test_batch_api_exposes_results_and_blocks_non_graph_commit(
    tmp_path: Path, schema_path: Path
) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    app = create_app(settings, service, mount_ui=False)
    files = [
        (
            "documents",
            ("first.txt", _fact(tmp_path, "first.txt").read_bytes(), "text/plain"),
        ),
        (
            "documents",
            ("second.md", _fact(tmp_path, "second.md").read_bytes(), "text/markdown"),
        ),
        (
            "schema",
            ("schema.yaml", schema_path.read_bytes(), "application/yaml"),
        ),
    ]
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/batches",
            files=files,
            data={
                "provider": "mock",
                "task_mode": "joint_entity_relation_extraction",
            },
        )
        assert created.status_code == 202
        batch_id = created.json()["batch"]["id"]
        for _ in range(500):
            batch = client.get(f"/api/v1/batches/{batch_id}").json()
            if batch["status"] not in {"queued", "running"}:
                break
            time.sleep(0.02)
        assert batch["status"] == "completed"
        results = client.get(f"/api/v1/batches/{batch_id}/results")
        assert results.status_code == 200
        assert len(results.json()) == 2
        assert all(
            item["result"]["task_mode"] == "joint_entity_relation_extraction"
            for item in results.json()
        )
        run_id = batch["items"][0]["run_id"]
        assert client.get(f"/api/v1/runs/{run_id}/results").status_code == 200
        rejected = client.post(
            f"/api/v1/batches/{batch_id}/confirm-commit",
            json={"reviewer": "tester"},
        )
        assert rejected.status_code == 409
        assert rejected.json()["detail"]["code"] == "TASK_MODE_NO_GRAPH_COMMIT"
