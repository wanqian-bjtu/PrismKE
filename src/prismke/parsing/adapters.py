"""Built-in document parsers with multimodal asset provenance."""

from __future__ import annotations

import base64
import mimetypes
import re
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
import pymupdf
from bs4 import BeautifulSoup
from docx import Document
from PIL import Image

from prismke.core.ids import file_sha256, stable_id
from prismke.domain import (
    BBox,
    CoordinateSpace,
    DocumentIR,
    DocumentPage,
    EvidenceKind,
    EvidenceRef,
    LocalizationLevel,
    MediaAsset,
    Modality,
    SourceDocument,
    TextBlock,
)

TEXT_TYPES = {"text/plain"}
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
MARKDOWN_TYPES = {"text/markdown"}
HTML_TYPES = {"text/html"}
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIN_ASSET_EDGE = 64
MARKDOWN_IMAGE = re.compile(r"!\[(?P<alt>[^]]*)]\((?P<src>[^ )]+)(?:\s+['\"][^'\"]*['\"])?\)")


def detect_media_type(path: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    suffix_map = {
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".pdf": "application/pdf",
        ".html": "text/html",
        ".htm": "text/html",
        ".docx": DOCX_TYPE,
    }
    return suffix_map.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or ""


class AssetWriter:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or Path("runtime/assets")
        self.directory.mkdir(parents=True, exist_ok=True)

    def write(self, content: bytes, suffix: str) -> tuple[Path, str]:
        digest = sha256(content).hexdigest()
        path = self.directory / digest[:2] / f"{digest}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(content)
        return path.resolve(), digest


def _text_block(
    document_id: str,
    source_hash: str,
    text: str,
    ordinal: int,
    *,
    page_number: int | None = None,
    bbox: BBox | None = None,
    char_start: int | None = None,
    char_end: int | None = None,
) -> tuple[TextBlock, EvidenceRef]:
    evidence_id = stable_id("ev", document_id, "text", page_number, ordinal, text)
    block = TextBlock(
        id=stable_id("block", document_id, page_number, ordinal, text),
        text=text,
        page_number=page_number,
        bbox=bbox,
        evidence_id=evidence_id,
        char_start=char_start,
        char_end=char_end,
    )
    evidence = EvidenceRef(
        id=evidence_id,
        kind=EvidenceKind.PDF_BBOX if bbox else EvidenceKind.TEXT_SPAN,
        document_id=document_id,
        source_hash=source_hash,
        modality=Modality.TEXT,
        page_number=page_number,
        bbox=bbox,
        char_start=char_start,
        char_end=char_end,
        localization_level=LocalizationLevel.REGION if bbox else LocalizationLevel.TEXT_SPAN,
        coordinate_space=CoordinateSpace.PDF_POINTS if bbox else None,
    )
    return block, evidence


def _asset(
    writer: AssetWriter,
    document_id: str,
    content: bytes,
    media_type: str,
    origin: str,
    source_ref: str,
    context: str = "",
    page_number: int | None = None,
    requires_ocr: bool = False,
) -> tuple[MediaAsset | None, EvidenceRef | None, str | None]:
    suffix = mimetypes.guess_extension(media_type) or ".bin"
    path, digest = writer.write(content, suffix)
    try:
        with Image.open(path) as image:
            width, height = image.size
    except (OSError, ValueError):
        return None, None, f"image_decode_failed:{source_ref}"
    if min(width, height) < MIN_ASSET_EDGE:
        return None, None, f"decorative_image_skipped:{source_ref}"
    asset_id = stable_id("media", document_id, origin, source_ref, digest)
    evidence_id = stable_id("ev", document_id, asset_id, "asset")
    asset = MediaAsset(
        id=asset_id,
        path=str(path),
        media_type=media_type,
        width=width,
        height=height,
        page_number=page_number,
        evidence_id=evidence_id,
        blob_hash=digest,
        origin=origin,
        source_ref=source_ref,
        context_text=context,
        requires_ocr=requires_ocr,
    )
    evidence = EvidenceRef(
        id=evidence_id,
        kind=EvidenceKind.IMAGE,
        document_id=document_id,
        source_hash=digest,
        modality=Modality.IMAGE,
        page_number=page_number,
        media_asset_id=asset_id,
        coordinate_space=CoordinateSpace.IMAGE_PIXELS,
        canvas_width=width,
        canvas_height=height,
        localization_level=LocalizationLevel.ASSET,
    )
    return asset, evidence, None


async def _resolve_image(
    source: str, base: Path, allow_remote: bool = False
) -> tuple[bytes, str, str] | None:
    if source.startswith("data:"):
        header, encoded = source.split(",", 1)
        media_type = header[5:].split(";", 1)[0] or "image/png"
        return base64.b64decode(encoded), media_type, "data-uri"
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        if not allow_remote:
            return None
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            response = await client.get(source)
            response.raise_for_status()
        media_type = response.headers.get("content-type", "image/png").split(";", 1)[0]
        return response.content, media_type, source
    candidate = (base / unquote(parsed.path)).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate.read_bytes(), detect_media_type(candidate), str(candidate)


class TextParser:
    def supports(self, media_type: str) -> bool:
        return media_type in TEXT_TYPES

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        content, source_hash = path.read_text(encoding="utf-8"), file_sha256(path)
        document_id = stable_id("doc", source_hash)
        blocks: list[TextBlock] = []
        evidence: list[EvidenceRef] = []
        cursor = 0
        for ordinal, raw_line in enumerate(content.splitlines(keepends=True)):
            paragraph = raw_line.rstrip("\r\n")
            if paragraph.strip():
                block, ref = _text_block(
                    document_id,
                    source_hash,
                    paragraph,
                    ordinal,
                    char_start=cursor,
                    char_end=cursor + len(paragraph),
                )
                blocks.append(block)
                evidence.append(ref)
            cursor += len(raw_line)
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type=detect_media_type(path, source.media_type),
            text_blocks=blocks,
            evidence=evidence,
        )


class MarkdownParser:
    def __init__(self, asset_dir: Path | None = None, allow_remote: bool = False) -> None:
        self.writer = AssetWriter(asset_dir)
        self.allow_remote = allow_remote

    def supports(self, media_type: str) -> bool:
        return media_type in MARKDOWN_TYPES

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        content, source_hash = path.read_text(encoding="utf-8"), file_sha256(path)
        document_id = stable_id("doc", source_hash)
        blocks: list[TextBlock] = []
        assets: list[MediaAsset] = []
        evidence: list[EvidenceRef] = []
        warnings: list[str] = []
        cursor = 0
        for ordinal, raw_line in enumerate(content.splitlines(keepends=True)):
            line = raw_line.rstrip("\r\n")
            clean = MARKDOWN_IMAGE.sub("", line).strip()
            if clean:
                start = cursor + line.find(clean)
                block, ref = _text_block(
                    document_id,
                    source_hash,
                    clean,
                    ordinal,
                    char_start=start,
                    char_end=start + len(clean),
                )
                blocks.append(block)
                evidence.append(ref)
            for match in MARKDOWN_IMAGE.finditer(line):
                src = match.group("src")
                resolved = await _resolve_image(src, path.parent, self.allow_remote)
                if resolved is None:
                    kind = (
                        "remote_asset_blocked"
                        if src.startswith(("http://", "https://"))
                        else "image_unavailable"
                    )
                    warnings.append(f"{kind}:{src}")
                    continue
                data, media_type, ref_name = resolved
                asset, ref, warning = _asset(
                    self.writer,
                    document_id,
                    data,
                    media_type,
                    "markdown_embedded",
                    ref_name,
                    match.group("alt"),
                )
                if warning:
                    warnings.append(warning)
                if asset and ref:
                    assets.append(asset)
                    evidence.append(ref)
            cursor += len(raw_line)
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type="text/markdown",
            text_blocks=blocks,
            media_assets=assets,
            evidence=evidence,
            warnings=warnings,
        )


class HTMLParser:
    def __init__(self, asset_dir: Path | None = None, allow_remote: bool = False) -> None:
        self.writer = AssetWriter(asset_dir)
        self.allow_remote = allow_remote

    def supports(self, media_type: str) -> bool:
        return media_type in HTML_TYPES

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        document_id = stable_id("doc", source_hash)
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        blocks: list[TextBlock] = []
        assets: list[MediaAsset] = []
        evidence: list[EvidenceRef] = []
        warnings: list[str] = []
        for ordinal, element in enumerate(
            soup.find_all(["p", "li", "h1", "h2", "h3", "figcaption"])
        ):
            text = element.get_text(" ", strip=True)
            if text:
                block, ref = _text_block(document_id, source_hash, text, ordinal)
                blocks.append(block)
                evidence.append(ref)
        for ordinal, image in enumerate(soup.find_all("img")):
            src = str(image.get("src", ""))
            resolved = await _resolve_image(src, path.parent, self.allow_remote)
            if resolved is None:
                kind = (
                    "remote_asset_blocked"
                    if src.startswith(("http://", "https://"))
                    else "image_unavailable"
                )
                warnings.append(f"{kind}:{src}")
                continue
            data, media_type, ref_name = resolved
            parent_text = image.parent.get_text(" ", strip=True) if image.parent else ""
            context = " ".join(filter(None, [str(image.get("alt", "")), parent_text]))
            asset, ref, warning = _asset(
                self.writer,
                document_id,
                data,
                media_type,
                "html_embedded",
                f"{ordinal}:{ref_name}",
                context,
            )
            if warning:
                warnings.append(warning)
            if asset and ref:
                assets.append(asset)
                evidence.append(ref)
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type="text/html",
            text_blocks=blocks,
            media_assets=assets,
            evidence=evidence,
            warnings=warnings,
        )


class DOCXParser:
    def __init__(self, asset_dir: Path | None = None) -> None:
        self.writer = AssetWriter(asset_dir)

    def supports(self, media_type: str) -> bool:
        return media_type == DOCX_TYPE

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        document_id = stable_id("doc", source_hash)
        document = Document(path)
        blocks: list[TextBlock] = []
        assets: list[MediaAsset] = []
        evidence: list[EvidenceRef] = []
        warnings: list[str] = []
        for ordinal, paragraph in enumerate(document.paragraphs):
            text = paragraph.text.strip()
            if text:
                block, ref = _text_block(document_id, source_hash, text, ordinal)
                blocks.append(block)
                evidence.append(ref)
            for blip in paragraph._element.xpath(".//*[local-name()='blip']"):
                rid = blip.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                )
                if not rid or rid not in document.part.related_parts:
                    continue
                part = document.part.related_parts[rid]
                asset, ref, warning = _asset(
                    self.writer,
                    document_id,
                    part.blob,
                    getattr(part, "content_type", "image/png"),
                    "docx_embedded",
                    f"paragraph={ordinal}:relation={rid}",
                    text,
                )
                if warning:
                    warnings.append(warning)
                if asset and ref:
                    assets.append(asset)
                    evidence.append(ref)
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type=DOCX_TYPE,
            text_blocks=blocks,
            media_assets=assets,
            evidence=evidence,
            warnings=warnings,
        )


class PDFParser:
    def __init__(self, asset_dir: Path | None = None) -> None:
        self.writer = AssetWriter(asset_dir)

    def supports(self, media_type: str) -> bool:
        return media_type == "application/pdf"

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        document_id = stable_id("doc", source_hash)
        blocks: list[TextBlock] = []
        assets: list[MediaAsset] = []
        evidence: list[EvidenceRef] = []
        pages: list[DocumentPage] = []
        warnings: list[str] = []
        with pymupdf.open(path) as pdf:  # type: ignore[no-untyped-call]
            for page_index, page in enumerate(pdf):
                page_number = page_index + 1
                page_blocks: list[str] = []
                page_assets: list[str] = []
                for ordinal, raw_block in enumerate(page.get_text("dict").get("blocks", [])):
                    if raw_block.get("type") != 0:
                        continue
                    text = "".join(
                        span.get("text", "")
                        for line in raw_block.get("lines", [])
                        for span in line.get("spans", [])
                    ).strip()
                    if not text:
                        continue
                    bbox = BBox(
                        **dict(zip(("x0", "y0", "x1", "y1"), raw_block["bbox"], strict=True))
                    )
                    block, ref = _text_block(
                        document_id, source_hash, text, ordinal, page_number=page_number, bbox=bbox
                    )
                    ref.canvas_width, ref.canvas_height = page.rect.width, page.rect.height
                    blocks.append(block)
                    evidence.append(ref)
                    page_blocks.append(block.id)
                seen_xrefs: set[int] = set()
                for index, info in enumerate(page.get_images(full=True)):
                    xref = int(info[0])
                    if xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)
                    extracted = pdf.extract_image(xref)
                    ext = extracted.get("ext", "png")
                    asset, ref, warning = _asset(
                        self.writer,
                        document_id,
                        extracted["image"],
                        f"image/{ext}",
                        "pdf_embedded",
                        f"page={page_number}:xref={xref}:index={index}",
                        " ".join(b.text for b in blocks if b.page_number == page_number),
                        page_number,
                    )
                    if warning:
                        warnings.append(warning)
                    if asset and ref:
                        assets.append(asset)
                        evidence.append(ref)
                        page_assets.append(asset.id)
                requires_ocr = not page_blocks
                if requires_ocr or len(page.get_drawings()) >= 5:
                    pixmap = page.get_pixmap(dpi=200, alpha=False)
                    asset, ref, warning = _asset(
                        self.writer,
                        document_id,
                        pixmap.tobytes("png"),
                        "image/png",
                        "pdf_page_render",
                        f"page={page_number}",
                        " ".join(b.text for b in blocks if b.page_number == page_number),
                        page_number,
                        requires_ocr,
                    )
                    if warning:
                        warnings.append(warning)
                    if asset and ref:
                        assets.append(asset)
                        evidence.append(ref)
                        page_assets.append(asset.id)
                if requires_ocr:
                    warnings.append(f"ocr_required:page={page_number}")
                pages.append(
                    DocumentPage(
                        id=stable_id("page", document_id, page_number),
                        page_number=page_number,
                        width=page.rect.width,
                        height=page.rect.height,
                        requires_ocr=requires_ocr,
                        text_block_ids=page_blocks,
                        media_asset_ids=page_assets,
                    )
                )
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type="application/pdf",
            pages=pages,
            text_blocks=blocks,
            media_assets=assets,
            evidence=evidence,
            warnings=warnings,
        )


class ImageParser:
    def __init__(self, asset_dir: Path | None = None) -> None:
        self.writer = AssetWriter(asset_dir)

    def supports(self, media_type: str) -> bool:
        return media_type in IMAGE_TYPES

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        document_id = stable_id("doc", source_hash)
        media_type = detect_media_type(path, source.media_type)
        asset, ref, warning = _asset(
            self.writer,
            document_id,
            path.read_bytes(),
            media_type,
            "source_image",
            str(path),
            requires_ocr=True,
        )
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_hash=source_hash,
            media_type=media_type,
            media_assets=[asset] if asset else [],
            evidence=[ref] if ref else [],
            warnings=[warning] if warning else [],
        )
