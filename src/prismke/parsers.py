"""Document parsers that preserve evidence location and source identity."""

from __future__ import annotations

import mimetypes
from pathlib import Path

import pymupdf
from PIL import Image

from prismke.errors import UnsupportedDocumentError
from prismke.ids import file_sha256, stable_id
from prismke.interfaces import ParserAdapter
from prismke.models import (
    BBox,
    DocumentIR,
    EvidenceKind,
    EvidenceRef,
    MediaAsset,
    Modality,
    SourceDocument,
    TextBlock,
)

TEXT_TYPES = {"text/plain", "text/markdown"}
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


def detect_media_type(path: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    suffix_map = {".md": "text/markdown", ".pdf": "application/pdf"}
    return suffix_map.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or ""


class TextParser:
    def supports(self, media_type: str) -> bool:
        return media_type in TEXT_TYPES

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        content = path.read_text(encoding="utf-8")
        source_hash = file_sha256(path)
        document_id = stable_id("doc", source_hash)
        blocks: list[TextBlock] = []
        evidence: list[EvidenceRef] = []
        cursor = 0
        for paragraph in content.splitlines(keepends=True):
            text = paragraph.rstrip("\r\n")
            start = cursor
            end = start + len(text)
            cursor += len(paragraph)
            if not text.strip():
                continue
            evidence_id = stable_id("ev", document_id, start, end)
            block_id = stable_id("block", document_id, start, end)
            blocks.append(
                TextBlock(
                    id=block_id,
                    text=text,
                    char_start=start,
                    char_end=end,
                    evidence_id=evidence_id,
                )
            )
            evidence.append(
                EvidenceRef(
                    id=evidence_id,
                    kind=EvidenceKind.TEXT_SPAN,
                    document_id=document_id,
                    source_hash=source_hash,
                    modality=Modality.TEXT,
                    char_start=start,
                    char_end=end,
                )
            )
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type=detect_media_type(path, source.media_type),
            text_blocks=blocks,
            evidence=evidence,
        )


class PDFParser:
    def supports(self, media_type: str) -> bool:
        return media_type == "application/pdf"

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        document_id = stable_id("doc", source_hash)
        blocks: list[TextBlock] = []
        evidence: list[EvidenceRef] = []
        warnings: list[str] = []
        with pymupdf.open(path) as pdf:  # type: ignore[no-untyped-call]
            for page_index, page in enumerate(pdf):
                page_number = page_index + 1
                page_dict = page.get_text("dict")
                page_has_text = False
                for raw_block in page_dict.get("blocks", []):
                    if raw_block.get("type") != 0:
                        continue
                    text = "".join(
                        span.get("text", "")
                        for line in raw_block.get("lines", [])
                        for span in line.get("spans", [])
                    ).strip()
                    if not text:
                        continue
                    page_has_text = True
                    bbox = BBox(
                        **dict(zip(("x0", "y0", "x1", "y1"), raw_block["bbox"], strict=True))
                    )
                    evidence_id = stable_id("ev", document_id, page_number, *raw_block["bbox"])
                    block_id = stable_id("block", document_id, page_number, *raw_block["bbox"])
                    blocks.append(
                        TextBlock(
                            id=block_id,
                            text=text,
                            page_number=page_number,
                            bbox=bbox,
                            evidence_id=evidence_id,
                        )
                    )
                    evidence.append(
                        EvidenceRef(
                            id=evidence_id,
                            kind=EvidenceKind.PDF_BBOX,
                            document_id=document_id,
                            source_hash=source_hash,
                            modality=Modality.TEXT,
                            page_number=page_number,
                            bbox=bbox,
                        )
                    )
                if not page_has_text:
                    warnings.append(f"ocr_required:page={page_number}")
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type="application/pdf",
            text_blocks=blocks,
            evidence=evidence,
            warnings=warnings,
        )


class ImageParser:
    def supports(self, media_type: str) -> bool:
        return media_type in IMAGE_TYPES

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        document_id = stable_id("doc", source_hash)
        media_type = detect_media_type(path, source.media_type)
        with Image.open(path) as image:
            width, height = image.size
        asset_id = stable_id("media", document_id, source_hash)
        evidence_id = stable_id("ev", document_id, asset_id)
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type=media_type,
            media_assets=[
                MediaAsset(
                    id=asset_id,
                    path=str(path),
                    media_type=media_type,
                    width=width,
                    height=height,
                    evidence_id=evidence_id,
                )
            ],
            evidence=[
                EvidenceRef(
                    id=evidence_id,
                    kind=EvidenceKind.IMAGE,
                    document_id=document_id,
                    source_hash=source_hash,
                    modality=Modality.IMAGE,
                    media_asset_id=asset_id,
                )
            ],
            warnings=["visual_extraction_not_enabled"],
        )


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: list[ParserAdapter] = [TextParser(), PDFParser(), ImageParser()]

    async def parse(self, source: SourceDocument) -> DocumentIR:
        media_type = detect_media_type(source.path, source.media_type)
        for parser in self._parsers:
            if parser.supports(media_type):
                return await parser.parse(source)
        raise UnsupportedDocumentError(f"unsupported media type: {media_type or 'unknown'}")
