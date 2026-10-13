"""MinerU V1 client and strict MiddleJson-to-DocumentIR conversion."""

from __future__ import annotations

import asyncio
import mimetypes
import os
import re
import zipfile
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

import httpx
import orjson
import pymupdf

from src.core.errors import MinerUEvidenceError, MinerUParseError, MinerUUnavailableError
from src.core.execution_control import current_execution
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
    PDFParseDecision,
    SourceDocument,
    TextBlock,
)


@dataclass(frozen=True)
class MinerUArtifacts:
    job_id: str
    status: str
    directory: Path
    middle_json: Path
    structured_content: Path | None
    markdown: Path | None
    manifest_path: Path
    manifest_hash: str


def _same_origin(left: str, right: str) -> bool:
    def origin(value: str) -> tuple[str, str, int]:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("invalid HTTP URL")
        return (
            parsed.scheme.lower(),
            parsed.hostname.lower(),
            parsed.port or (443 if parsed.scheme == "https" else 80),
        )

    return origin(left) == origin(right)


class MinerUV1Client:
    def __init__(
        self,
        base_url: str,
        output_root: Path,
        *,
        version: str = "4.0.12",
        tier: str = "standard",
        request_timeout: float = 60.0,
        transfer_timeout: float = 300.0,
        poll_interval: float = 2.0,
        max_polls: int = 300,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.output_root = output_root
        self.version = version
        self.tier = tier
        self.request_timeout = request_timeout
        self.transfer_timeout = transfer_timeout
        self.poll_interval = poll_interval
        self.max_polls = max_polls
        self.api_key = api_key
        self.transport = transport

    def fingerprint(self) -> str:
        return canonical_hash(
            {
                "provider": "mineru-v1",
                "version": self.version,
                "tier": self.tier,
                "base_url": self.base_url,
            }
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    @staticmethod
    async def _file_chunks(path: Path, size: int = 1024 * 1024) -> AsyncIterator[bytes]:
        stream = path.open("rb")
        try:
            while chunk := await asyncio.to_thread(stream.read, size):
                yield chunk
        finally:
            stream.close()

    async def status(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                transport=self.transport, timeout=self.request_timeout
            ) as client:
                response = await client.get(f"{self.base_url}/v1/health", headers=self._headers())
                response.raise_for_status()
                payload = cast(dict[str, Any], response.json())
            return {"available": True, "version": self.version, "tier": self.tier, **payload}
        except (httpx.HTTPError, ValueError, TypeError):
            return {"available": False, "version": self.version, "tier": self.tier}

    async def parse(self, source: SourceDocument) -> MinerUArtifacts:
        path = source.path.resolve()
        source_hash = file_sha256(path)
        request_key = stable_id("mineru-request", source_hash, self.fingerprint())
        output_dir = self.output_root / source_hash / request_key.replace(":", "_")
        output_dir.mkdir(parents=True, exist_ok=True)
        control = current_execution.get()
        existing = control.result(request_key) if control else None
        try:
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=httpx.Timeout(self.request_timeout, read=self.transfer_timeout),
                follow_redirects=True,
            ) as client:
                if existing and existing.get("job_id"):
                    job_id = str(existing["job_id"])
                else:
                    if control:
                        reused = control.begin_request(
                            request_key,
                            {
                                "provider": "mineru",
                                "source_hash": source_hash,
                                "mineru_version": self.version,
                                "tier": self.tier,
                                "config_fingerprint": self.fingerprint(),
                            },
                        )
                        if reused and reused.get("job_id"):
                            job_id = str(reused["job_id"])
                        else:
                            job_id = await self._submit(client, path, source_hash)
                    else:
                        job_id = await self._submit(client, path, source_hash)
                    if control:
                        control.put_result(request_key, {"job_id": job_id})
                job = await self._poll(client, job_id)
                artifacts = await self._download(client, job, output_dir)
            if control:
                control.finish_request(
                    request_key,
                    "completed",
                    {"job_id": job_id, "manifest_hash": artifacts.manifest_hash},
                    True,
                )
            return artifacts
        except (MinerUParseError, MinerUEvidenceError):
            if control:
                control.finish_request(request_key, "failed", None, True)
            raise
        except (httpx.HTTPError, OSError, ValueError, KeyError, TypeError) as exc:
            if control:
                control.finish_request(request_key, "unknown", None, False)
            raise MinerUUnavailableError(str(exc)) from exc

    async def _submit(self, client: httpx.AsyncClient, path: Path, source_hash: str) -> str:
        create = await client.post(
            f"{self.base_url}/v1/uploads",
            headers=self._headers(),
            json={
                "filename": path.name,
                "bytes": path.stat().st_size,
                "mime_type": "application/pdf",
                "purpose": "parse",
                "sha256sum": source_hash,
            },
        )
        create.raise_for_status()
        upload = cast(dict[str, Any], create.json())
        status = upload.get("status")
        if status not in {"pending", "completed"} or not isinstance(upload.get("id"), str):
            raise MinerUParseError("invalid MinerU upload response")
        if status == "pending":
            target = urljoin(f"{self.base_url}/", str(upload.get("upload_url", "")))
            if not target:
                raise MinerUParseError("MinerU upload URL is missing")
            headers = {
                str(key): str(value)
                for key, value in cast(dict[str, Any], upload.get("upload_headers") or {}).items()
            }
            if _same_origin(self.base_url, target):
                headers.update(self._headers())
            sent = await client.put(
                target,
                headers=headers,
                content=self._file_chunks(path),
            )
            sent.raise_for_status()
            completed = await client.post(
                f"{self.base_url}/v1/uploads/{upload['id']}/complete",
                headers=self._headers(),
            )
            completed.raise_for_status()
            upload = cast(dict[str, Any], completed.json())
        file_id = cast(dict[str, Any], upload.get("file") or {}).get("id")
        if not isinstance(file_id, str) or not file_id:
            raise MinerUParseError("MinerU file id is missing")
        response = await client.post(
            f"{self.base_url}/v1/parse/jobs",
            headers=self._headers(),
            json={
                "files": [{"source": {"type": "file_id", "file_id": file_id}}],
                "tier": self.tier,
                "output_formats": ["middle_json", "structured_content", "markdown", "zip"],
            },
        )
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())
        job_id = payload.get("job_id")
        if not isinstance(job_id, str) or not job_id:
            raise MinerUParseError("MinerU job id is missing")
        return job_id

    async def _poll(self, client: httpx.AsyncClient, job_id: str) -> dict[str, Any]:
        for _ in range(self.max_polls + 1):
            control = current_execution.get()
            if control:
                control.check()
            response = await client.get(
                f"{self.base_url}/v1/parse/jobs/{job_id}", headers=self._headers()
            )
            response.raise_for_status()
            payload = cast(dict[str, Any], response.json())
            status = payload.get("status")
            if status == "completed":
                payload.setdefault("job_id", job_id)
                return payload
            if status in {"partial", "failed", "canceled"}:
                raise MinerUParseError(f"MinerU job ended with {status}")
            if status not in {"queued", "running"}:
                raise MinerUParseError("invalid MinerU job status")
            await asyncio.sleep(self.poll_interval)
        raise MinerUParseError("MinerU polling budget exhausted")

    async def _download(
        self, client: httpx.AsyncClient, job: dict[str, Any], output_dir: Path
    ) -> MinerUArtifacts:
        control = current_execution.get()
        if control:
            control.check()
        job_id = str(job["job_id"])
        files = job.get("files")
        if not isinstance(files, list) or len(files) != 1:
            raise MinerUParseError("MinerU job must contain one file")
        output_files = cast(dict[str, Any], cast(dict[str, Any], files[0]).get("output_files"))
        saved: dict[str, Path] = {}
        for output_format in ("middle_json", "structured_content", "markdown", "zip"):
            descriptor = output_files.get(output_format)
            file_id = descriptor.get("file_id") if isinstance(descriptor, dict) else None
            if not isinstance(file_id, str):
                if output_format in {"structured_content", "markdown"}:
                    continue
                raise MinerUParseError(f"MinerU output missing: {output_format}")
            response = await client.get(
                f"{self.base_url}/v1/files/{file_id}/content", headers=self._headers()
            )
            response.raise_for_status()
            suffix = {
                "middle_json": ".json",
                "structured_content": ".json",
                "markdown": ".md",
                "zip": ".zip",
            }[output_format]
            target = output_dir / f"{output_format}{suffix}"
            self._atomic_write(target, response.content)
            saved[output_format] = target
        self._extract_zip(saved["zip"], output_dir / "package")
        middle = saved["middle_json"]
        try:
            payload = cast(dict[str, Any], orjson.loads(middle.read_bytes()))
        except (orjson.JSONDecodeError, TypeError) as exc:
            raise MinerUEvidenceError("MiddleJson is not valid JSON") from exc
        if payload.get("schema") != "docvortex.middle" or payload.get("schema_version") != "2.0":
            raise MinerUEvidenceError("unsupported MiddleJson schema")
        hashes = {
            str(path.relative_to(output_dir)).replace("\\", "/"): file_sha256(path)
            for path in sorted(output_dir.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        }
        manifest = output_dir / "manifest.json"
        self._atomic_write(
            manifest,
            orjson.dumps(
                {"job_id": job_id, "mineru_version": self.version, "files": hashes},
                option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2,
            ),
        )
        return MinerUArtifacts(
            job_id=job_id,
            status="completed",
            directory=output_dir,
            middle_json=middle,
            structured_content=saved.get("structured_content"),
            markdown=saved.get("markdown"),
            manifest_path=manifest,
            manifest_hash=file_sha256(manifest),
        )

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".tmp-{uuid4().hex[:8]}")
        try:
            with temporary.open("wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _extract_zip(path: Path, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            total = sum(item.file_size for item in archive.infolist())
            if total > 1024 * 1024 * 1024:
                raise MinerUEvidenceError("MinerU package exceeds safety limit")
            for item in archive.infolist():
                destination = (target / item.filename).resolve()
                if target.resolve() not in destination.parents and destination != target.resolve():
                    raise MinerUEvidenceError("unsafe MinerU archive path")
            archive.extractall(target)


def _block_text(block: dict[str, Any]) -> str:
    content = block.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            text for item in content if isinstance(item, dict) and (text := _block_text(item))
        ).strip()
    latex = block.get("latex")
    return latex.strip() if isinstance(latex, str) else ""


def _asset_references(value: object) -> list[str]:
    references: list[str] = []
    if isinstance(value, dict):
        for key in ("src", "path", "image", "image_path"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                references.append(candidate)
        for child in value.values():
            references.extend(_asset_references(child))
    elif isinstance(value, list):
        for child in value:
            references.extend(_asset_references(child))
    elif isinstance(value, str) and "<img" in value.lower():
        references.extend(
            match.group(1)
            for match in re.finditer(
                r"<img\b[^>]*\bsrc\s*=\s*['\"]([^'\"]+)['\"]",
                value,
                flags=re.IGNORECASE,
            )
        )
    return list(dict.fromkeys(references))


def _resolve_asset(package: Path, reference: str) -> Path:
    if reference.startswith(("http://", "https://", "data:")):
        raise MinerUEvidenceError("external or inline MinerU asset is not admissible evidence")
    candidate = (package / reference).resolve()
    package_root = package.resolve()
    if package_root in candidate.parents and candidate.is_file():
        return candidate
    matches = list(package.rglob(Path(reference).name))
    if len(matches) != 1:
        raise MinerUEvidenceError(f"MinerU asset cannot be resolved uniquely: {reference}")
    return matches[0]


def _bbox(
    block: dict[str, Any], canvas_width: float, canvas_height: float
) -> tuple[BBox | None, str | None]:
    value = block.get("bbox")
    if isinstance(value, dict):
        values = [value.get(key) for key in ("x0", "y0", "x1", "y1")]
    elif isinstance(value, list) and len(value) == 4:
        values = value
    else:
        return None, None
    if any(item is None for item in values):
        raise MinerUEvidenceError("invalid MiddleJson bbox")
    numeric_values = cast(list[Any], values)
    try:
        coordinates = tuple(float(item) for item in numeric_values)
        if all(0.0 <= item <= 1.0 for item in coordinates):
            return (
                BBox(
                    x0=coordinates[0] * canvas_width,
                    y0=coordinates[1] * canvas_height,
                    x1=coordinates[2] * canvas_width,
                    y1=coordinates[3] * canvas_height,
                ),
                "normalized",
            )
        return BBox(
            x0=coordinates[0],
            y0=coordinates[1],
            x1=coordinates[2],
            y1=coordinates[3],
        ), "pdf_points"
    except (TypeError, ValueError) as exc:
        raise MinerUEvidenceError("invalid MiddleJson bbox") from exc


def _block_asset_references(
    package: Path,
    block: dict[str, Any],
    *,
    page_idx: int,
    block_position: int,
    block_type: str,
) -> list[str]:
    references = _asset_references(block)
    if references:
        return references
    if block_type not in {"table", "chart", "image", "figure", "equation", "formula"}:
        return []
    raw_index = block.get("index", block_position)
    if not isinstance(raw_index, int) or raw_index < 0:
        raise MinerUEvidenceError("invalid MinerU block index for derived asset")
    images = package / "images"
    matches = sorted(images.glob(f"page_{page_idx}_{block_type}_{raw_index}.*"))
    if len(matches) > 1:
        raise MinerUEvidenceError("MinerU block has ambiguous derived assets")
    if not matches:
        return []
    return [str(matches[0].relative_to(package)).replace("\\", "/")]


def _layout_sizes(payload: dict[str, Any]) -> dict[int, tuple[float, float]]:
    extensions = cast(dict[str, Any], payload.get("extensions") or {})
    layout = cast(dict[str, Any], extensions.get("docvortex_layout") or {})
    sizes: dict[int, tuple[float, float]] = {}
    for page in cast(list[dict[str, Any]], layout.get("pages") or []):
        try:
            sizes[int(page["page_idx"])] = (float(page["width_pt"]), float(page["height_pt"]))
        except (KeyError, TypeError, ValueError):
            continue
    return sizes


def convert_mineru_document(
    source: SourceDocument,
    artifacts: MinerUArtifacts,
    decision: PDFParseDecision,
) -> DocumentIR:
    path = source.path.resolve()
    source_hash = file_sha256(path)
    document_id = stable_id("doc", source_hash)
    payload = cast(dict[str, Any], orjson.loads(artifacts.middle_json.read_bytes()))
    if payload.get("schema") != "docvortex.middle" or payload.get("schema_version") != "2.0":
        raise MinerUEvidenceError("unsupported MiddleJson schema")
    metadata = cast(dict[str, Any], payload.get("metadata") or {})
    producer = cast(dict[str, Any], metadata.get("producer") or {})
    if producer.get("name") != "mineru":
        raise MinerUEvidenceError("MiddleJson producer is not MinerU")
    if producer.get("version") != decision.parser_version:
        raise MinerUEvidenceError("MiddleJson MinerU version does not match the parser decision")
    extensions = cast(dict[str, Any], payload.get("extensions") or {})
    mineru_extension = cast(dict[str, Any], extensions.get("mineru") or {})
    if mineru_extension.get("tier") != "standard":
        raise MinerUEvidenceError("MiddleJson was not produced by MinerU Standard")
    pages_payload = payload.get("pages")
    if not isinstance(pages_payload, list) or not pages_payload:
        raise MinerUEvidenceError("MiddleJson pages are missing")
    if payload.get("is_full_document") is not True:
        raise MinerUEvidenceError("MiddleJson does not represent the complete PDF")
    with pymupdf.open(path) as pdf:  # type: ignore[no-untyped-call]
        source_page_sizes = {
            index: (float(page.rect.width), float(page.rect.height))
            for index, page in enumerate(pdf)
        }
    if len(pages_payload) != len(source_page_sizes):
        raise MinerUEvidenceError("MiddleJson page count does not match the source PDF")
    sizes = _layout_sizes(payload)
    blocks: list[TextBlock] = []
    evidence: list[EvidenceRef] = []
    pages: list[DocumentPage] = []
    assets: list[MediaAsset] = []
    derivation_id = stable_id("derivation", source_hash, artifacts.manifest_hash)
    seen_pages: set[int] = set()
    for page_position, page_payload in enumerate(pages_payload):
        if not isinstance(page_payload, dict):
            raise MinerUEvidenceError("MiddleJson page is invalid")
        page_idx = int(page_payload.get("page_idx", page_position))
        if page_idx in seen_pages or page_idx not in source_page_sizes:
            raise MinerUEvidenceError("MiddleJson page index is invalid or duplicated")
        seen_pages.add(page_idx)
        width, height = sizes.get(page_idx, (0.0, 0.0))
        if width <= 0 or height <= 0:
            raise MinerUEvidenceError("MiddleJson PDF page geometry is missing")
        source_width, source_height = source_page_sizes[page_idx]
        if abs(width - source_width) > 0.5 or abs(height - source_height) > 0.5:
            raise MinerUEvidenceError("MiddleJson page geometry does not match the source PDF")
        page_block_ids: list[str] = []
        page_asset_ids: list[str] = []
        raw_blocks = page_payload.get("blocks")
        if not isinstance(raw_blocks, list):
            raise MinerUEvidenceError("MiddleJson blocks are missing")
        for block_position, raw_block in enumerate(raw_blocks):
            if not isinstance(raw_block, dict):
                continue
            block_type = str(raw_block.get("type", "text")).lower()
            text = _block_text(raw_block)
            bbox, bbox_encoding = _bbox(raw_block, width, height)
            if bbox and (bbox.x1 > width or bbox.y1 > height):
                raise MinerUEvidenceError("MiddleJson bbox exceeds page canvas")
            locator = {
                "schema": "docvortex.middle",
                "schema_version": "2.0",
                "derived_hash": file_sha256(artifacts.middle_json),
                "page_idx": page_idx,
                "block_index": block_position,
                "block_type": block_type,
                "block_hash": canonical_hash(raw_block),
                "bbox_encoding": bbox_encoding,
            }
            if "table" in block_type:
                modality = Modality.TABLE
                kind = EvidenceKind.TABLE_REGION
            elif "chart" in block_type:
                modality = Modality.CHART
                kind = EvidenceKind.CHART_REGION
            elif block_type in {"image", "figure"}:
                modality = Modality.IMAGE
                kind = EvidenceKind.VISUAL_REGION
            elif block_type in {"equation", "formula"}:
                modality = Modality.FORMULA
                kind = EvidenceKind.FORMULA_REGION
            else:
                modality = Modality.TEXT
                kind = EvidenceKind.PDF_BBOX
            if text:
                if bbox is None:
                    raise MinerUEvidenceError("MiddleJson content block has no source bbox")
                evidence_id = stable_id("ev", document_id, page_idx, block_position, text)
                block_id = stable_id("block", document_id, page_idx, block_position, text)
                blocks.append(
                    TextBlock(
                        id=block_id,
                        text=text,
                        page_number=page_idx + 1,
                        bbox=bbox,
                        evidence_id=evidence_id,
                        modality=modality,
                    )
                )
                evidence.append(
                    EvidenceRef(
                        id=evidence_id,
                        kind=kind,
                        document_id=document_id,
                        source_hash=source_hash,
                        modality=modality,
                        page_number=page_idx + 1,
                        bbox=bbox,
                        coordinate_space=CoordinateSpace.PDF_POINTS,
                        canvas_width=width,
                        canvas_height=height,
                        localization_level=LocalizationLevel.REGION,
                        derivation_id=derivation_id,
                        source_locator=locator,
                    )
                )
                page_block_ids.append(block_id)
            references = _block_asset_references(
                artifacts.directory / "package",
                raw_block,
                page_idx=page_idx,
                block_position=block_position,
                block_type=block_type,
            )
            for reference in references:
                if bbox is None:
                    raise MinerUEvidenceError("MinerU visual asset has no source bbox")
                asset_path = _resolve_asset(artifacts.directory / "package", reference)
                asset_hash = file_sha256(asset_path)
                media_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
                asset_id = stable_id("asset", document_id, page_idx, block_position, asset_hash)
                asset_evidence_id = stable_id("ev", asset_id)
                if modality == Modality.TABLE:
                    origin = "mineru_table"
                elif modality == Modality.FORMULA:
                    origin = "mineru_formula"
                elif modality == Modality.CHART:
                    origin = "mineru_chart"
                else:
                    origin = "mineru_image"
                assets.append(
                    MediaAsset(
                        id=asset_id,
                        path=str(asset_path),
                        media_type=media_type,
                        page_number=page_idx + 1,
                        evidence_id=asset_evidence_id,
                        blob_hash=asset_hash,
                        origin=origin,
                        source_ref=reference,
                        context_text=text,
                    )
                )
                evidence.append(
                    EvidenceRef(
                        id=asset_evidence_id,
                        kind=EvidenceKind.IMAGE,
                        document_id=document_id,
                        source_hash=source_hash,
                        modality=Modality.IMAGE,
                        page_number=page_idx + 1,
                        bbox=bbox,
                        media_asset_id=asset_id,
                        coordinate_space=CoordinateSpace.PDF_POINTS,
                        canvas_width=width,
                        canvas_height=height,
                        localization_level=LocalizationLevel.REGION,
                        derivation_id=derivation_id,
                        source_locator={
                            **locator,
                            "asset_hash": asset_hash,
                            "asset_ref": reference,
                        },
                    )
                )
                page_asset_ids.append(asset_id)
        pages.append(
            DocumentPage(
                id=stable_id("page", document_id, page_idx + 1),
                page_number=page_idx + 1,
                width=width,
                height=height,
                requires_ocr=False,
                text_block_ids=page_block_ids,
                media_asset_ids=page_asset_ids,
            )
        )
    artifact_hashes = {
        str(item.relative_to(artifacts.directory)).replace("\\", "/"): file_sha256(item)
        for item in artifacts.directory.rglob("*")
        if item.is_file()
    }
    return DocumentIR(
        id=document_id,
        source_path=str(path),
        source_hash=source_hash,
        media_type="application/pdf",
        pages=pages,
        text_blocks=blocks,
        media_assets=assets,
        evidence=evidence,
        derivations=[
            DocumentDerivation(
                id=derivation_id,
                tool="mineru",
                tool_version=decision.parser_version,
                parser_fingerprint=decision.parser_fingerprint,
                source_hash=source_hash,
                derived_hash=file_sha256(artifacts.middle_json),
                derived_media_type="application/vnd.mineru.middle+json",
                derived_path=str(artifacts.middle_json),
                artifact_manifest_hash=artifacts.manifest_hash,
                artifact_hashes=artifact_hashes,
            )
        ],
        warnings=["mineru_markdown_preview_only"],
        pdf_parse_decision=decision,
    )
