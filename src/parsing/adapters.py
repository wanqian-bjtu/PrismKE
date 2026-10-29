"""Built-in document parsers with multimodal asset provenance."""

from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import os
import re
import shutil
import stat
import tempfile
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse
from zipfile import BadZipFile, ZipFile

import httpx
import pymupdf
from bs4 import BeautifulSoup, Tag
from docx import Document
from PIL import Image

from src.core.errors import DocumentConversionError
from src.core.ids import canonical_hash, file_sha256, stable_id
from src.domain import (
    BBox,
    CoordinateSpace,
    DocumentDerivation,
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
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/tiff", "image/bmp"}
MARKDOWN_TYPES = {"text/markdown"}
HTML_TYPES = {"text/html"}
HTML_PACKAGE_TYPES = {"application/zip"}
JSON_TYPES = {"application/json", "application/prismke.document-ir+json"}
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOC_TYPE = "application/msword"
MIN_ASSET_EDGE = 64
MAX_HTML_CONTEXT_CHARS = 500
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
        ".zip": "application/zip",
        ".docx": DOCX_TYPE,
        ".doc": DOC_TYPE,
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".bmp": "image/bmp",
    }
    return suffix_map.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or ""


def _uploaded_filename(path: Path) -> str:
    prefix, separator, original = path.name.partition("--")
    if (
        separator
        and len(prefix) == 32
        and all(character in "0123456789abcdef" for character in prefix)
    ):
        return original
    return path.name


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
    source_locator: dict[str, Any] | None = None,
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
        source_locator=source_locator,
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
    source: str,
    base: Path,
    allow_remote: bool = False,
    asset_root: Path | None = None,
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
    root = (asset_root or base).resolve()
    candidate = (base / unquote(parsed.path)).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate.read_bytes(), detect_media_type(candidate), relative.as_posix()


def _html_image_context(image: Tag) -> str:
    """Keep image context local and label it as auxiliary evidence."""

    parts: list[tuple[str, str]] = []
    for attribute in ("alt", "title"):
        value = " ".join(str(image.get(attribute, "")).split())
        if value:
            parts.append((attribute, value))

    figure = image.find_parent("figure")
    if isinstance(figure, Tag):
        caption = figure.find("figcaption")
        if isinstance(caption, Tag):
            text = " ".join(caption.get_text(" ", strip=True).split())
            if text:
                parts.append(("figcaption", text))

    container = figure if isinstance(figure, Tag) else image
    for sibling in (container.find_previous_sibling(), container.find_next_sibling()):
        if not isinstance(sibling, Tag) or sibling.name not in {
            "p",
            "li",
            "h1",
            "h2",
            "h3",
            "figcaption",
        }:
            continue
        text = " ".join(sibling.get_text(" ", strip=True).split())
        if text:
            parts.append(("nearby", text))

    unique: list[str] = []
    seen: set[str] = set()
    for label, value in parts:
        normalized = value.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(f"{label}: {value}")
    return "\n".join(unique)[:MAX_HTML_CONTEXT_CHARS]


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
                asset, asset_ref, warning = _asset(
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
                if asset and asset_ref:
                    assets.append(asset)
                    evidence.append(asset_ref)
            cursor += len(raw_line)
        for ordinal, image in enumerate(BeautifulSoup(content, "html.parser").find_all("img")):
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
            asset, asset_ref, warning = _asset(
                self.writer,
                document_id,
                data,
                media_type,
                "markdown_embedded",
                f"html:{ordinal}:{ref_name}",
                _html_image_context(image),
            )
            if warning:
                warnings.append(warning)
            if asset and asset_ref:
                assets.append(asset)
                evidence.append(asset_ref)
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


def _json_path_child(path: str, key: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        return f"{path}.{key}"
    return f"{path}[{json.dumps(key, ensure_ascii=False)}]"


def _json_scalars(value: object, path: str = "$") -> list[tuple[str, object]]:
    if isinstance(value, dict):
        output: list[tuple[str, object]] = []
        for key, item in value.items():
            output.extend(_json_scalars(item, _json_path_child(path, str(key))))
        return output
    if isinstance(value, list):
        output = []
        for index, item in enumerate(value):
            output.extend(_json_scalars(item, f"{path}[{index}]"))
        return output
    return [(path, value)]


class JSONParser:
    def supports(self, media_type: str) -> bool:
        return media_type in JSON_TYPES

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        document_id = stable_id("doc", source_hash)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid JSON document: {path.name}") from exc
        document_ir = isinstance(payload, dict) and {
            "id",
            "text_blocks",
            "evidence",
        }.issubset(payload)
        scalars = _json_scalars(payload)
        if document_ir:
            scalars = [
                (f"$.text_blocks[{index}].text", block.get("text"))
                for index, block in enumerate(payload.get("text_blocks", []))
                if isinstance(block, dict) and block.get("text") is not None
            ]
        blocks: list[TextBlock] = []
        evidence: list[EvidenceRef] = []
        for json_path, value in scalars:
            serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            display = value if isinstance(value, str) else serialized
            value_hash = canonical_hash(value)
            evidence_id = stable_id("ev", document_id, "json", json_path, value_hash)
            blocks.append(
                TextBlock(
                    id=stable_id("block", document_id, json_path, value_hash),
                    text=f"{json_path}: {display}",
                    evidence_id=evidence_id,
                )
            )
            evidence.append(
                EvidenceRef(
                    id=evidence_id,
                    kind=EvidenceKind.JSON_VALUE,
                    document_id=document_id,
                    source_hash=source_hash,
                    modality=Modality.TEXT,
                    localization_level=LocalizationLevel.TEXT_SPAN,
                    json_path=json_path,
                    json_value_hash=value_hash,
                )
            )
        return DocumentIR(
            id=document_id,
            source_path=str(path),
            source_filename=path.name,
            source_hash=source_hash,
            media_type=(
                "application/prismke.document-ir+json" if document_ir else "application/json"
            ),
            text_blocks=blocks,
            evidence=evidence,
        )


class LegacyDOCParser:
    def __init__(
        self,
        asset_dir: Path | None = None,
        derived_dir: Path | None = None,
        libreoffice_bin: Path | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        self.docx = DOCXParser(asset_dir)
        self.derived_dir = derived_dir or Path("runtime/derived-documents")
        self.libreoffice_bin = libreoffice_bin
        self.timeout_seconds = timeout_seconds

    def supports(self, media_type: str) -> bool:
        return media_type == DOC_TYPE

    def _executable(self) -> Path:
        configured = self.libreoffice_bin
        if configured and configured.is_file():
            return configured.resolve()
        found = shutil.which("soffice") or shutil.which("libreoffice")
        if found:
            return Path(found).resolve()
        raise DocumentConversionError(
            "LIBREOFFICE_NOT_FOUND: configure PRISMKE_LIBREOFFICE_BIN or install LibreOffice"
        )

    async def _version(self, executable: Path) -> str:
        process = await asyncio.create_subprocess_exec(
            str(executable),
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=15)
        return stdout.decode("utf-8", errors="replace").strip() or "unknown"

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        executable = self._executable()
        target_dir = self.derived_dir / source_hash[:2] / source_hash
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{path.stem}.docx"
        with tempfile.TemporaryDirectory(prefix="prismke-lo-") as profile:
            command = [
                str(executable),
                "--headless",
                f"-env:UserInstallation={Path(profile).resolve().as_uri()}",
                "--convert-to",
                "docx",
                "--outdir",
                str(target_dir),
                str(path),
            ]
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout_seconds
                )
            except TimeoutError as exc:
                process.kill()
                await process.wait()
                raise DocumentConversionError("LIBREOFFICE_TIMEOUT") from exc
        if process.returncode or not target.is_file():
            detail = (stderr or stdout).decode("utf-8", errors="replace").strip()
            raise DocumentConversionError(
                f"LIBREOFFICE_CONVERSION_FAILED: {detail[:300] or 'no output'}"
            )
        derived_hash = file_sha256(target)
        parsed = await self.docx.parse(SourceDocument(path=target, media_type=DOCX_TYPE))
        parsed.source_path = str(path)
        parsed.source_filename = path.name
        parsed.source_hash = source_hash
        parsed.media_type = DOC_TYPE
        parsed.derivations.append(
            DocumentDerivation(
                tool="libreoffice",
                tool_version=await self._version(executable),
                source_hash=source_hash,
                derived_hash=derived_hash,
                derived_media_type=DOCX_TYPE,
                derived_path=str(target.resolve()),
            )
        )
        return parsed


class HTMLParser:
    def __init__(self, asset_dir: Path | None = None, allow_remote: bool = False) -> None:
        self.writer = AssetWriter(asset_dir)
        self.allow_remote = allow_remote

    def supports(self, media_type: str) -> bool:
        return media_type in HTML_TYPES

    async def parse(self, source: SourceDocument) -> DocumentIR:
        path = source.path.resolve()
        source_hash = source.content_hash or file_sha256(path)
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
                tag = element.name or "element"
                same_tag_index = len(element.find_all_previous(tag)) + 1
                locator = {
                    "document_kind": "continuous_html",
                    "tag": tag,
                    "ordinal": ordinal + 1,
                    "selector": f"{tag}:nth-of-type({same_tag_index})",
                    "character_range": [0, len(text)],
                }
                block, ref = _text_block(
                    document_id,
                    source_hash,
                    text,
                    ordinal,
                    char_start=0,
                    char_end=len(text),
                    source_locator=locator,
                )
                blocks.append(block)
                evidence.append(ref)
        for ordinal, image in enumerate(soup.find_all("img")):
            src = str(image.get("src", ""))
            resolved = await _resolve_image(
                src,
                path.parent,
                self.allow_remote,
                source.asset_root,
            )
            if resolved is None:
                kind = (
                    "remote_asset_blocked"
                    if src.startswith(("http://", "https://"))
                    else "image_unavailable"
                )
                warnings.append(f"{kind}:{src}")
                continue
            data, media_type, ref_name = resolved
            context = _html_image_context(image)
            asset, asset_ref, warning = _asset(
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
            if asset and asset_ref:
                assets.append(asset)
                evidence.append(asset_ref)
        return DocumentIR(
            id=document_id,
            source_path=str((source.persisted_source_path or path).resolve()),
            source_filename=source.source_filename,
            source_package_filename=source.source_package_filename,
            source_entry_path=source.source_entry_path,
            source_hash=source_hash,
            media_type="text/html",
            text_blocks=blocks,
            media_assets=assets,
            evidence=evidence,
            warnings=warnings,
        )


class HTMLPackageParser:
    """Safely extract a single-HTML ZIP package and preserve relative assets."""

    def __init__(
        self,
        asset_dir: Path | None = None,
        allow_remote: bool = False,
        package_dir: Path | None = None,
        *,
        max_entries: int = 1000,
        max_entry_bytes: int = 200 * 1024 * 1024,
        max_total_bytes: int = 500 * 1024 * 1024,
        max_compression_ratio: float = 200.0,
    ) -> None:
        self.html = HTMLParser(asset_dir, allow_remote)
        self.package_dir = package_dir or Path("runtime/derived-documents/html-packages")
        self.max_entries = max_entries
        self.max_entry_bytes = max_entry_bytes
        self.max_total_bytes = max_total_bytes
        self.max_compression_ratio = max_compression_ratio

    def supports(self, media_type: str) -> bool:
        return media_type in HTML_PACKAGE_TYPES

    @staticmethod
    def _relative_path(name: str) -> PurePosixPath:
        if not name or "\\" in name or "\x00" in name:
            raise ValueError("HTML_PACKAGE_UNSAFE_PATH")
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or any(part in {"", ".", ".."} for part in path.parts)
            or (path.parts and re.match(r"^[A-Za-z]:", path.parts[0]))
        ):
            raise ValueError("HTML_PACKAGE_UNSAFE_PATH")
        return path

    def _members(self, archive: ZipFile) -> tuple[list[tuple[Any, PurePosixPath]], str]:
        members: list[tuple[Any, PurePosixPath]] = []
        html_entries: list[str] = []
        total = 0
        archive_entries = archive.infolist()
        if len(archive_entries) > self.max_entries:
            raise ValueError("HTML_PACKAGE_TOO_MANY_ENTRIES")
        for info in archive_entries:
            if info.is_dir() or info.filename.startswith("__MACOSX/"):
                continue
            relative = self._relative_path(info.filename)
            if info.flag_bits & 0x1:
                raise ValueError("HTML_PACKAGE_ENCRYPTED_ENTRY")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError("HTML_PACKAGE_SYMLINK_ENTRY")
            if info.file_size > self.max_entry_bytes:
                raise ValueError("HTML_PACKAGE_ENTRY_TOO_LARGE")
            total += info.file_size
            if total > self.max_total_bytes:
                raise ValueError("HTML_PACKAGE_TOO_LARGE")
            if (
                info.file_size >= 1024 * 1024
                and info.file_size / max(info.compress_size, 1)
                > self.max_compression_ratio
            ):
                raise ValueError("HTML_PACKAGE_COMPRESSION_RATIO_EXCEEDED")
            members.append((info, relative))
            if relative.suffix.lower() in {".html", ".htm"}:
                html_entries.append(relative.as_posix())
        if not html_entries:
            raise ValueError("HTML_PACKAGE_HTML_MISSING")
        if len(html_entries) != 1:
            raise ValueError("HTML_PACKAGE_HTML_AMBIGUOUS")
        return members, html_entries[0]

    def _extract(self, path: Path, digest: str) -> tuple[Path, str]:
        self.package_dir.mkdir(parents=True, exist_ok=True)
        target_root = (self.package_dir / digest).resolve()
        try:
            with ZipFile(path) as archive:
                members, html_entry = self._members(archive)
                target_html = target_root / PurePosixPath(html_entry)
                if target_html.is_file():
                    return target_root, html_entry
                temporary_root = Path(
                    tempfile.mkdtemp(prefix=f".{digest}.", dir=self.package_dir)
                ).resolve()
                try:
                    actual_total = 0
                    for info, relative in members:
                        destination = (temporary_root / relative).resolve()
                        try:
                            destination.relative_to(temporary_root)
                        except ValueError as exc:
                            raise ValueError("HTML_PACKAGE_UNSAFE_PATH") from exc
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(info) as source_stream, destination.open(
                            "wb"
                        ) as destination_stream:
                            while chunk := source_stream.read(1024 * 1024):
                                actual_total += len(chunk)
                                if actual_total > self.max_total_bytes:
                                    raise ValueError("HTML_PACKAGE_TOO_LARGE")
                                destination_stream.write(chunk)
                        if destination.stat().st_size != info.file_size:
                            raise ValueError("HTML_PACKAGE_SIZE_MISMATCH")
                    if target_root.exists():
                        shutil.rmtree(temporary_root)
                    else:
                        os.replace(temporary_root, target_root)
                finally:
                    if temporary_root.exists():
                        shutil.rmtree(temporary_root)
                if not target_html.is_file():
                    raise ValueError("HTML_PACKAGE_HTML_MISSING")
                return target_root, html_entry
        except BadZipFile as exc:
            raise ValueError("HTML_PACKAGE_INVALID_ZIP") from exc

    async def parse(self, source: SourceDocument) -> DocumentIR:
        package_path = source.path.resolve()
        digest = file_sha256(package_path)
        root, html_entry = self._extract(package_path, digest)
        package_filename = _uploaded_filename(package_path)
        return await self.html.parse(
            SourceDocument(
                path=root / PurePosixPath(html_entry),
                media_type="text/html",
                asset_root=root,
                content_hash=digest,
                persisted_source_path=package_path,
                source_filename=PurePosixPath(html_entry).name,
                source_package_filename=package_filename,
                source_entry_path=html_entry,
            )
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
        document = Document(str(path))
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
                asset, asset_ref, warning = _asset(
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
                if asset and asset_ref:
                    assets.append(asset)
                    evidence.append(asset_ref)
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
                    asset, asset_ref, warning = _asset(
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
                    if asset and asset_ref:
                        assets.append(asset)
                        evidence.append(asset_ref)
                        page_assets.append(asset.id)
                requires_ocr = not page_blocks
                if requires_ocr or len(page.get_drawings()) >= 5:
                    pixmap = page.get_pixmap(dpi=200, alpha=False)
                    asset, asset_ref, warning = _asset(
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
                    if asset and asset_ref:
                        assets.append(asset)
                        evidence.append(asset_ref)
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
