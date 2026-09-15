"""Immutable content-addressed evidence storage."""

from __future__ import annotations

import os
import shutil
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import orjson
import pymupdf
from PIL import Image

from prismke.core.errors import EvidenceIntegrityError
from prismke.core.ids import canonical_hash, file_sha256
from prismke.domain import CoordinateSpace, DocumentIR, EvidenceRef


class FileEvidenceStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.blobs_dir = directory / "blobs"
        self.refs_dir = directory / "refs"
        self.blobs_dir.mkdir(parents=True, exist_ok=True)
        self.refs_dir.mkdir(parents=True, exist_ok=True)

    def _blob_path(self, source_hash: str) -> Path:
        return self.blobs_dir / source_hash[:2] / source_hash

    def _ref_path(self, evidence_id: str) -> Path:
        safe_name = sha256(evidence_id.encode("utf-8")).hexdigest()
        return self.refs_dir / f"{safe_name}.json"

    def _atomic_write(self, path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def _store_blob(self, source: Path, source_hash: str) -> None:
        if file_sha256(source) != source_hash:
            raise EvidenceIntegrityError("source file no longer matches DocumentIR hash")
        target = self._blob_path(source_hash)
        if target.exists():
            if file_sha256(target) != source_hash:
                raise EvidenceIntegrityError(f"stored evidence blob is corrupt: {source_hash}")
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        try:
            shutil.copyfile(source, temporary)
            if file_sha256(temporary) != source_hash:
                raise EvidenceIntegrityError("copied evidence blob failed hash verification")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    def _store_blob_bytes(self, content: bytes) -> str:
        digest = sha256(content).hexdigest()
        target = self._blob_path(digest)
        if target.exists():
            if file_sha256(target) != digest:
                raise EvidenceIntegrityError(f"stored evidence blob is corrupt: {digest}")
            return digest
        self._atomic_write(target, content)
        return digest

    def _serialize_ref(self, evidence: EvidenceRef) -> bytes:
        record = evidence.model_dump(mode="json")
        wrapper = {"checksum": canonical_hash(record), "record": record}
        return orjson.dumps(wrapper, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2)

    def _load_ref(self, evidence_id: str) -> EvidenceRef:
        path = self._ref_path(evidence_id)
        if not path.exists():
            raise EvidenceIntegrityError(f"evidence not found: {evidence_id}")
        try:
            wrapper = cast(dict[str, Any], orjson.loads(path.read_bytes()))
            record = cast(dict[str, Any], wrapper["record"])
            if wrapper["checksum"] != canonical_hash(record):
                raise EvidenceIntegrityError(f"evidence metadata checksum failed: {evidence_id}")
            evidence = EvidenceRef.model_validate(record)
        except (KeyError, TypeError, ValueError, orjson.JSONDecodeError) as exc:
            if isinstance(exc, EvidenceIntegrityError):
                raise
            raise EvidenceIntegrityError(f"invalid evidence metadata: {evidence_id}") from exc
        if evidence.id != evidence_id:
            raise EvidenceIntegrityError(f"evidence id mismatch: {evidence_id}")
        if file_sha256(self._blob_path(evidence.source_hash)) != evidence.source_hash:
            raise EvidenceIntegrityError(f"evidence blob checksum failed: {evidence_id}")
        return evidence

    async def put_document(self, document: DocumentIR) -> None:
        source = Path(document.source_path)
        if not source.is_file():
            raise EvidenceIntegrityError(f"evidence source not found: {source}")
        self._store_blob(source, document.source_hash)
        for asset in document.media_assets:
            asset_path = Path(asset.path)
            if not asset_path.is_file():
                raise EvidenceIntegrityError(f"media asset source not found: {asset_path}")
            digest = file_sha256(asset_path)
            if asset.blob_hash and digest != asset.blob_hash:
                raise EvidenceIntegrityError(f"media asset hash mismatch: {asset.id}")
            self._store_blob(asset_path, digest)
        for evidence in document.evidence:
            if evidence.document_id != document.id:
                raise EvidenceIntegrityError(
                    f"evidence {evidence.id} does not belong to document {document.id}"
                )
            await self.put_ref(evidence)

    async def put_blob(self, content: bytes, media_type: str) -> str:
        del media_type
        return self._store_blob_bytes(content)

    async def put_ref(self, evidence: EvidenceRef) -> None:
        if not self._blob_path(evidence.source_hash).is_file():
            raise EvidenceIntegrityError(f"evidence blob not found: {evidence.source_hash}")
        path = self._ref_path(evidence.id)
        payload = self._serialize_ref(evidence)
        if path.exists():
            if path.read_bytes() != payload:
                raise EvidenceIntegrityError(
                    f"immutable evidence already exists with different content: {evidence.id}"
                )
            return
        self._atomic_write(path, payload)

    async def get_blob(self, blob_hash: str) -> bytes:
        path = self._blob_path(blob_hash)
        if not path.is_file() or file_sha256(path) != blob_hash:
            raise EvidenceIntegrityError(f"evidence blob not found or corrupt: {blob_hash}")
        return path.read_bytes()

    async def crop(self, evidence_id: str) -> bytes:
        evidence = self._load_ref(evidence_id)
        content = await self.get_blob(evidence.source_hash)
        if evidence.bbox is None:
            return content
        box = evidence.bbox
        if evidence.coordinate_space == CoordinateSpace.PDF_POINTS:
            with pymupdf.open(stream=content, filetype="pdf") as pdf:  # type: ignore[no-untyped-call]
                if evidence.page_number is None:
                    raise EvidenceIntegrityError("PDF evidence has no page number")
                page = pdf[evidence.page_number - 1]
                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2),
                    clip=pymupdf.Rect(box.x0, box.y0, box.x1, box.y1),
                    alpha=False,
                )
                return pixmap.tobytes("png")
        with Image.open(BytesIO(content)) as image:
            if evidence.coordinate_space == CoordinateSpace.NORMALIZED:
                coordinates = (
                    int(box.x0 * image.width),
                    int(box.y0 * image.height),
                    int(box.x1 * image.width),
                    int(box.y1 * image.height),
                )
            else:
                coordinates = tuple(map(int, (box.x0, box.y0, box.x1, box.y1)))
            cropped = image.crop(coordinates)
            output = BytesIO()
            cropped.save(output, format="PNG")
            return output.getvalue()

    async def get(self, evidence_id: str) -> EvidenceRef:
        return self._load_ref(evidence_id)

    async def exists(self, evidence_id: str) -> bool:
        return self._ref_path(evidence_id).is_file()

    async def verify(self, evidence_id: str) -> bool:
        try:
            self._load_ref(evidence_id)
        except (EvidenceIntegrityError, OSError):
            return False
        return True
