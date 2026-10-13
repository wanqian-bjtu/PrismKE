from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path
from typing import Any

import httpx
import orjson
import pymupdf
import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.core.errors import MinerUEvidenceError, MinerUUnavailableError
from src.core.execution_control import current_execution
from src.core.ids import file_sha256
from src.core.settings import Settings
from src.domain import (
    Modality,
    PDFComplexityThresholds,
    PDFParseDecision,
    PDFParseMode,
    PDFParserName,
    SourceDocument,
)
from src.domain.execution import ExecutionTask
from src.parsing import ParserRegistry
from src.parsing.mineru import MinerUV1Client, convert_mineru_document
from src.parsing.pdf_complexity import inspect_pdf
from src.persistence import FileEvidenceStore
from src.persistence.execution import ExecutionRepository
from src.workflow import PrismKEService


def _pdf(path: Path, *, text: str = "", drawings: int = 0) -> None:
    document = pymupdf.open()
    page = document.new_page(width=200, height=300)
    if text:
        page.insert_textbox(pymupdf.Rect(10, 10, 190, 260), text)
    for index in range(drawings):
        y = 30 + index * 10
        page.draw_line((10, y), (190, y))
    document.save(path)
    document.close()


def _middle_json() -> bytes:
    return orjson.dumps(
        {
            "schema": "docvortex.middle",
            "schema_version": "2.0",
            "metadata": {"producer": {"name": "mineru", "version": "4.0.12"}},
            "extensions": {
                "mineru": {"tier": "standard", "parse_mode": "ocr"},
                "docvortex_layout": {"pages": [{"page_idx": 0, "width_pt": 200, "height_pt": 300}]},
            },
            "is_full_document": True,
            "pages": [
                {
                    "page_idx": 0,
                    "blocks": [
                        {
                            "type": "text",
                            "bbox": [0.05, 0.033333, 0.95, 0.116667],
                            "content": "Auditable PDF evidence",
                        },
                        {
                            "type": "table",
                            "bbox": [0.05, 0.15, 0.95, 0.4],
                            "content": [
                                {"content": "Metric | Value"},
                                {
                                    "content": (
                                        '<table><tr><td><img src="table.png"></td></tr></table>'
                                    )
                                },
                            ],
                        },
                        {
                            "type": "formula",
                            "bbox": [0.05, 0.433333, 0.95, 0.533333],
                            "content": "E = mc^2",
                        },
                        {
                            "type": "image",
                            "bbox": [0.05, 0.566667, 0.95, 0.933333],
                            "content": [{"src": "figure.png"}],
                        },
                    ],
                }
            ],
        }
    )


def _package_zip() -> bytes:
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("images/table.png", b"table-image")
        archive.writestr("images/figure.png", b"figure-image")
        archive.writestr("images/page_0_formula_2.jpg", b"formula-image")
    return target.getvalue()


def _mineru_transport(calls: dict[str, int]) -> httpx.MockTransport:
    outputs = {
        "middle": _middle_json(),
        "structured": b"{}",
        "markdown": b"# Preview only",
        "zip": _package_zip(),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        route = f"{request.method} {request.url.path}"
        calls[route] = calls.get(route, 0) + 1
        if route == "GET /v1/health":
            return httpx.Response(200, json={"status": "ok"})
        if route == "POST /v1/uploads":
            return httpx.Response(
                200,
                json={
                    "id": "upload-1",
                    "status": "pending",
                    "upload_url": "/upload-bytes",
                    "upload_headers": {},
                },
            )
        if route == "PUT /upload-bytes":
            return httpx.Response(200)
        if route == "POST /v1/uploads/upload-1/complete":
            return httpx.Response(
                200,
                json={"id": "upload-1", "status": "completed", "file": {"id": "source"}},
            )
        if route == "POST /v1/parse/jobs":
            return httpx.Response(200, json={"job_id": "job-1"})
        if route == "GET /v1/parse/jobs/job-1":
            return httpx.Response(
                200,
                json={
                    "status": "completed",
                    "files": [
                        {
                            "output_files": {
                                "middle_json": {"file_id": "middle"},
                                "structured_content": {"file_id": "structured"},
                                "markdown": {"file_id": "markdown"},
                                "zip": {"file_id": "zip"},
                            }
                        }
                    ],
                },
            )
        prefix = "/v1/files/"
        suffix = "/content"
        if request.method == "GET" and request.url.path.startswith(prefix):
            file_id = request.url.path.removeprefix(prefix).removesuffix(suffix)
            return httpx.Response(200, content=outputs[file_id])
        return httpx.Response(404)

    return httpx.MockTransport(handler)


class _MemoryControl:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def check(self) -> None:
        return None

    def node(self, name: str) -> None:
        return None

    def commit_started(self, revision_id: str) -> None:
        return None

    def commit_finished(self) -> None:
        return None

    def begin_request(self, key: str, metadata: dict[str, Any]) -> dict[str, Any] | None:
        return self.values.get(key)

    def finish_request(
        self,
        key: str,
        status: str,
        payload: dict[str, Any] | None,
        usage_known: bool,
    ) -> None:
        if payload is not None:
            self.values[key] = payload

    def result(self, key: str) -> dict[str, Any] | None:
        return self.values.get(key)

    def put_result(self, key: str, value: dict[str, Any]) -> None:
        self.values[key] = value


@pytest.mark.asyncio
async def test_auto_routes_simple_pdf_to_pymupdf(tmp_path: Path) -> None:
    source = tmp_path / "native.pdf"
    _pdf(source, text="A normal native PDF paragraph with enough readable text.")
    document = await ParserRegistry(pdf_parse_mode=PDFParseMode.AUTO).parse(
        SourceDocument(path=source)
    )
    assert document.pdf_parse_decision is not None
    assert document.pdf_parse_decision.actual_parser == PDFParserName.PYMUPDF
    assert document.pdf_parse_decision.reason_codes == ["LIGHTWEIGHT_PDF"]


def test_complexity_report_routes_drawing_dense_pdf(tmp_path: Path) -> None:
    source = tmp_path / "drawing.pdf"
    _pdf(source, text="Native text", drawings=5)
    report = inspect_pdf(source, PDFComplexityThresholds())
    assert report.drawing_dense_pages == [1]
    assert "DRAWING_DENSE" in report.reason_codes


def test_complexity_report_detects_table_and_multicolumn(tmp_path: Path) -> None:
    source = tmp_path / "layout.pdf"
    document = pymupdf.open()
    page = document.new_page(width=600, height=800)
    for index in range(4):
        x = 30 if index % 2 == 0 else 320
        y = 50 + (index // 2) * 200
        word = "left " if x < 300 else "right "
        page.insert_textbox(pymupdf.Rect(x, y, x + 240, y + 150), word * 20)
    for x in (30, 150, 270):
        page.draw_line((x, 500), (x, 700))
    for y in (500, 550, 600, 650, 700):
        page.draw_line((30, y), (270, y))
    for row in range(4):
        for column in range(2):
            page.insert_text((40 + column * 120, 530 + row * 50), f"{row}-{column}")
    document.save(source)
    document.close()
    report = inspect_pdf(source, PDFComplexityThresholds())
    assert report.table_candidate_pages == [1]
    assert report.unstable_multicolumn_pages == [1]
    assert {"TABLE_DENSE", "MULTICOLUMN_ORDER_UNSTABLE"} <= set(report.reason_codes)


@pytest.mark.asyncio
async def test_auto_blocks_when_mineru_is_unavailable(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    _pdf(source)
    unavailable = MinerUV1Client(
        "http://127.0.0.1:1",
        tmp_path / "unavailable-derived",
        request_timeout=0.1,
    )
    with pytest.raises(MinerUUnavailableError) as caught:
        await ParserRegistry(
            pdf_parse_mode=PDFParseMode.AUTO,
            mineru_client=unavailable,
        ).parse(SourceDocument(path=source))
    assert caught.value.code == "MINERU_UNAVAILABLE"
    assert caught.value.decision.actual_parser == PDFParserName.MINERU
    assert caught.value.decision.mineru_status == "unavailable"


@pytest.mark.asyncio
async def test_forced_pymupdf_never_auto_upgrades(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    _pdf(source)
    document = await ParserRegistry(pdf_parse_mode=PDFParseMode.PYMUPDF).parse(
        SourceDocument(path=source)
    )
    assert document.pdf_parse_decision is not None
    assert document.pdf_parse_decision.actual_parser == PDFParserName.PYMUPDF
    assert document.pages[0].requires_ocr


@pytest.mark.asyncio
async def test_mineru_v1_lifecycle_resume_and_evidence_integrity(tmp_path: Path) -> None:
    source = tmp_path / "complex.pdf"
    _pdf(source)
    calls: dict[str, int] = {}
    client = MinerUV1Client(
        "http://mineru.test",
        tmp_path / "derived",
        transport=_mineru_transport(calls),
        poll_interval=0,
    )
    control = _MemoryControl()
    token = current_execution.set(control)
    try:
        first = await client.parse(SourceDocument(path=source))
        second = await client.parse(SourceDocument(path=source))
    finally:
        current_execution.reset(token)
    assert first.job_id == second.job_id == "job-1"
    assert calls["POST /v1/uploads"] == 1
    assert calls["POST /v1/parse/jobs"] == 1

    report = inspect_pdf(source, PDFComplexityThresholds())
    decision = PDFParseDecision(
        requested_mode=PDFParseMode.MINERU,
        actual_parser=PDFParserName.MINERU,
        complexity=report,
        reason_codes=["USER_FORCED_MINERU"],
        parser_version="4.0.12",
        parser_fingerprint=client.fingerprint(),
        config_fingerprint="config",
        mineru_job_id=first.job_id,
        mineru_status="completed",
        artifact_manifest_hash=first.manifest_hash,
    )
    document = convert_mineru_document(SourceDocument(path=source), first, decision)
    assert {block.modality for block in document.text_blocks} >= {
        Modality.TEXT,
        Modality.TABLE,
        Modality.FORMULA,
    }
    assert all(ref.source_hash == file_sha256(source) for ref in document.evidence)
    assert all(ref.derivation_id for ref in document.evidence)
    assert all(ref.source_locator for ref in document.evidence)
    assert all(ref.bbox is None or ref.bbox.x1 > 1 for ref in document.evidence)
    assert "mineru_formula" in {asset.origin for asset in document.media_assets}

    store = FileEvidenceStore(tmp_path / "evidence")
    await store.put_document(document)
    assert all([await store.verify(ref.id) for ref in document.evidence])
    derived_hash = str(document.evidence[0].source_locator["derived_hash"])
    blob = store.blobs_dir / derived_hash[:2] / derived_hash
    blob.write_bytes(b"tampered")
    assert not await store.verify(document.evidence[0].id)


def test_mineru_rejects_invalid_middle_json(tmp_path: Path) -> None:
    source = tmp_path / "complex.pdf"
    _pdf(source)
    derived = tmp_path / "derived"
    derived.mkdir()
    middle = derived / "middle.json"
    middle.write_bytes(orjson.dumps({"schema": "not-middle"}))
    manifest = derived / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    from src.parsing.mineru import MinerUArtifacts

    artifacts = MinerUArtifacts(
        job_id="job",
        status="completed",
        directory=derived,
        middle_json=middle,
        structured_content=None,
        markdown=None,
        manifest_path=manifest,
        manifest_hash=file_sha256(manifest),
    )
    decision = PDFParseDecision(
        requested_mode=PDFParseMode.MINERU,
        actual_parser=PDFParserName.MINERU,
        complexity=inspect_pdf(source, PDFComplexityThresholds()),
        parser_version="4.0.12",
        parser_fingerprint="parser",
        config_fingerprint="config",
    )
    with pytest.raises(MinerUEvidenceError):
        convert_mineru_document(SourceDocument(path=source), artifacts, decision)


def test_persisted_mineru_job_is_recoverable_not_unknown(tmp_path: Path) -> None:
    repository = ExecutionRepository(tmp_path / "execution.sqlite")
    repository.register(ExecutionTask(run_id="run-1", input_hash="input", schema_hash="schema"))
    repository.begin_request("run-1", "request-1", {"provider": "mineru"})
    assert repository.unknown("run-1") == 1
    repository.put_result("run-1", "request-1", {"job_id": "job-1"})
    assert repository.unknown("run-1") == 0
    assert repository.requests("run-1")[0]["recoverable"] is True


def test_api_reports_block_and_fallback_is_idempotent(tmp_path: Path, schema_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    _pdf(source)
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        mineru_base_url="http://127.0.0.1:9",
        mineru_request_timeout=0.05,
    )
    service = PrismKEService(settings)
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        accepted = client.post(
            "/api/v1/runs",
            files={
                "document": ("scan.pdf", source.read_bytes(), "application/pdf"),
                "schema": ("schema.yaml", schema_path.read_bytes(), "application/yaml"),
            },
            data={"provider": "mock", "pdf_parse_mode": "auto"},
        )
        assert accepted.status_code == 202
        run_id = accepted.json()["run_id"]
        for _ in range(200):
            execution = client.get(f"/api/v1/runs/{run_id}/execution").json()
            if not execution["active"]:
                break
            time.sleep(0.01)
        assert execution["status"] == "parser_blocked"
        parse_view = client.get(f"/api/v1/runs/{run_id}/pdf-parse")
        assert parse_view.status_code == 200
        assert parse_view.json()["decision"]["actual_parser"] == "mineru"
        request = {
            "operator": "管理员",
            "reason": "本地高精度服务不可用，确认使用轻量解析继续",
            "request_id": "fallback-1",
            "expected_execution_version": execution["version"],
        }
        first = client.post(f"/api/v1/runs/{run_id}/pdf-parser-fallback", json=request)
        assert first.status_code == 202
        repeated = client.post(f"/api/v1/runs/{run_id}/pdf-parser-fallback", json=request)
        assert repeated.status_code == 202
        conflict = client.post(
            f"/api/v1/runs/{run_id}/pdf-parser-fallback",
            json={**request, "reason": "changed"},
        )
        assert conflict.status_code == 409
    assert len(service.executions.repository.pdf_fallbacks(run_id)) == 1
