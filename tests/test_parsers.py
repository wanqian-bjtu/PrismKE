from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from prismke.domain import EvidenceKind, SourceDocument
from prismke.parsing import ParserRegistry


@pytest.mark.asyncio
async def test_text_parser_preserves_character_spans(tmp_path: Path) -> None:
    path = tmp_path / "sample.md"
    path.write_text("Heading\n\nFact line\n", encoding="utf-8")
    document = await ParserRegistry().parse(SourceDocument(path=path))
    assert [block.text for block in document.text_blocks] == ["Heading", "Fact line"]
    assert document.text_blocks[1].char_start == 9
    assert document.evidence[0].kind == EvidenceKind.TEXT_SPAN


@pytest.mark.asyncio
async def test_pdf_parser_preserves_page_and_bbox(tmp_path: Path) -> None:
    path = tmp_path / "sample.pdf"
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "PrismKE evidence")
    pdf.save(path)
    pdf.close()
    document = await ParserRegistry().parse(SourceDocument(path=path))
    assert document.text_blocks[0].page_number == 1
    assert document.text_blocks[0].bbox is not None
    assert document.evidence[0].kind == EvidenceKind.PDF_BBOX


@pytest.mark.asyncio
async def test_scanned_pdf_is_marked_for_ocr(tmp_path: Path) -> None:
    path = tmp_path / "scan.pdf"
    pdf = pymupdf.open()
    pdf.new_page()
    pdf.save(path)
    pdf.close()
    document = await ParserRegistry().parse(SourceDocument(path=path))
    assert "ocr_required:page=1" in document.warnings


@pytest.mark.asyncio
async def test_image_becomes_evidence_asset(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    Image.new("RGB", (32, 16), "white").save(path)
    document = await ParserRegistry().parse(SourceDocument(path=path))
    assert document.media_assets[0].width == 32
    assert document.media_assets[0].height == 16
    assert document.evidence[0].kind == EvidenceKind.IMAGE
    assert "visual_extraction_not_enabled" in document.warnings


@pytest.mark.asyncio
async def test_repeated_import_has_stable_document_id(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("stable", encoding="utf-8")
    registry = ParserRegistry()
    first = await registry.parse(SourceDocument(path=path))
    second = await registry.parse(SourceDocument(path=path))
    assert first.id == second.id
    assert first.source_hash == second.source_hash
