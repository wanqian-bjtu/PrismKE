"""Run the real MinerU v0.12 acceptance against synthetic PDFs only."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

import orjson
import pymupdf

from src.core.ids import file_sha256
from src.domain import Modality, PDFParseDecision, PDFParseMode, PDFParserName, SourceDocument
from src.domain.pdf import PDFComplexityThresholds
from src.parsing.mineru import MinerUV1Client, convert_mineru_document
from src.parsing.pdf_complexity import inspect_pdf
from src.persistence import FileEvidenceStore


def _native_text(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((54, 72), "PrismKE native text validation", fontsize=18)
    page.insert_text((54, 108), "Auditable PDF evidence with page coordinates.", fontsize=11)
    page.insert_text(
        (54, 144), "中文原生文本：知识图谱证据可追溯。", fontname="china-s", fontsize=11
    )
    document.save(path)
    document.close()


def _scanned_text(path: Path) -> None:
    source = pymupdf.open()
    page = source.new_page(width=595, height=842)
    page.insert_text((54, 100), "Scanned bilingual evidence", fontsize=22)
    page.insert_text(
        (54, 145), "扫描中英文页面：PrismKE 证据校验。", fontname="china-s", fontsize=16
    )
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
    image = pixmap.tobytes("png")
    source.close()

    document = pymupdf.open()
    target = document.new_page(width=595, height=842)
    target.insert_image(target.rect, stream=image)
    document.save(path)
    document.close()


def _complex_layout(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((40, 48), "Multicolumn, table and chart validation", fontsize=16)
    left = pymupdf.Rect(40, 75, 275, 310)
    right = pymupdf.Rect(320, 75, 555, 310)
    page.insert_textbox(left, "Left column evidence. " * 18, fontsize=9)
    page.insert_textbox(right, "Right column evidence. " * 18, fontsize=9)

    x0, y0, cell_w, cell_h = 40, 350, 130, 34
    for row in range(4):
        for column in range(4):
            rect = pymupdf.Rect(
                x0 + column * cell_w,
                y0 + row * cell_h,
                x0 + (column + 1) * cell_w,
                y0 + (row + 1) * cell_h,
            )
            page.draw_rect(rect, width=0.8)
            page.insert_text((rect.x0 + 5, rect.y0 + 21), f"R{row + 1}C{column + 1}", fontsize=9)

    chart_base = 570
    page.draw_line((40, chart_base), (300, chart_base), width=1)
    page.draw_line((40, chart_base), (40, chart_base - 120), width=1)
    for index, height in enumerate((35, 78, 52, 104)):
        page.draw_rect(
            pymupdf.Rect(65 + index * 55, chart_base - height, 95 + index * 55, chart_base),
            color=(0.1, 0.35, 0.8),
            fill=(0.2, 0.55, 0.9),
        )
    page.insert_text((40, 620), "Formula region: E = mc^2", fontsize=12)

    raster_source = pymupdf.open()
    raster_page = raster_source.new_page(width=320, height=150)
    raster_page.insert_text((18, 24), "Embedded chart image", fontsize=13)
    for index, height in enumerate((28, 64, 42, 88)):
        raster_page.draw_rect(
            pymupdf.Rect(30 + index * 65, 130 - height, 70 + index * 65, 130),
            color=(0.85, 0.38, 0.08),
            fill=(0.95, 0.62, 0.12),
        )
    raster = raster_page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
    page.insert_image(pymupdf.Rect(330, 650, 555, 755), stream=raster.tobytes("png"))
    raster_source.close()
    document.save(path)
    document.close()


def _decision(
    path: Path, client: MinerUV1Client, job_id: str, manifest_hash: str
) -> PDFParseDecision:
    report = inspect_pdf(path, PDFComplexityThresholds())
    return PDFParseDecision(
        requested_mode=PDFParseMode.MINERU,
        actual_parser=PDFParserName.MINERU,
        reason_codes=["USER_FORCED_MINERU"],
        complexity=report,
        parser_version="4.0.12",
        parser_fingerprint=client.fingerprint(),
        config_fingerprint="server-standard-onnx-llama-cpp",
        mineru_job_id=job_id,
        mineru_status="completed",
        artifact_manifest_hash=manifest_hash,
    )


async def _validate_one(path: Path, client: MinerUV1Client, evidence_root: Path) -> dict[str, Any]:
    source = SourceDocument(path=path, media_type="application/pdf")
    artifacts = await client.parse(source)
    middle = orjson.loads(artifacts.middle_json.read_bytes())
    document = convert_mineru_document(
        source,
        artifacts,
        _decision(path, client, artifacts.job_id, artifacts.manifest_hash),
    )
    store = FileEvidenceStore(evidence_root / path.stem)
    await store.put_document(document)
    verified = [await store.verify(reference.id) for reference in document.evidence]
    if not verified or not all(verified):
        raise RuntimeError(f"evidence verification failed for {path.name}")
    modality_counts = {
        modality.value: sum(block.modality == modality for block in document.text_blocks)
        for modality in Modality
        if any(block.modality == modality for block in document.text_blocks)
    }
    if path.name == "table-multicolumn-chart.pdf":
        if not {Modality.TABLE.value, Modality.CHART.value}.issubset(modality_counts):
            raise RuntimeError("complex sample lost table or chart evidence")
        if not document.media_assets:
            raise RuntimeError("complex sample lost the embedded image asset")
    return {
        "name": path.name,
        "source_hash": file_sha256(path),
        "job_id": artifacts.job_id,
        "middle_schema": middle.get("schema"),
        "middle_schema_version": middle.get("schema_version"),
        "pages": len(document.pages),
        "text_blocks": len(document.text_blocks),
        "media_assets": len(document.media_assets),
        "text_block_modalities": modality_counts,
        "evidence_refs": len(document.evidence),
        "verified_evidence_refs": sum(verified),
        "manifest_hash": artifacts.manifest_hash,
    }


async def _main(base_url: str, root: Path) -> None:
    inputs = root / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    generators = {
        "native-text.pdf": _native_text,
        "scanned-bilingual.pdf": _scanned_text,
        "table-multicolumn-chart.pdf": _complex_layout,
    }
    for name, generator in generators.items():
        generator(inputs / name)

    client = MinerUV1Client(base_url, root / "derived", poll_interval=1.0, max_polls=1800)
    status = await client.status()
    if not status.get("available") or status.get("version") != "4.0.12":
        raise RuntimeError("MinerU 4.0.12 service is unavailable")
    results = [await _validate_one(inputs / name, client, root / "evidence") for name in generators]
    report = {
        "service": {"available": True, "version": status.get("version"), "tier": "standard"},
        "samples": results,
    }
    report_path = root / "validation-report.json"
    report_path.write_bytes(orjson.dumps(report, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))
    print(orjson.dumps(report, option=orjson.OPT_INDENT_2).decode("utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18020")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runtime/validation/mineru-v012"),
    )
    arguments = parser.parse_args()
    asyncio.run(_main(arguments.base_url, arguments.output_dir.resolve()))
