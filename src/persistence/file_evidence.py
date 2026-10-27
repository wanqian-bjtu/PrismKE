"""Immutable content-addressed evidence storage."""

from __future__ import annotations

import json
import os
import re
import shutil
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import orjson
import pymupdf
from PIL import Image

from src.core.errors import EvidenceIntegrityError
from src.core.ids import canonical_hash, file_sha256
from src.domain import CoordinateSpace, DocumentIR, EvidenceRef


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
        for derivation in document.derivations:
            derived = Path(derivation.derived_path)
            if not derived.is_file() or file_sha256(derived) != derivation.derived_hash:
                raise EvidenceIntegrityError("derived document hash mismatch")
            self._store_blob(derived, derivation.derived_hash)
            if derivation.artifact_manifest_hash:
                manifest = derived.parent / "manifest.json"
                if (
                    not manifest.is_file()
                    or file_sha256(manifest) != derivation.artifact_manifest_hash
                ):
                    raise EvidenceIntegrityError("derived artifact manifest mismatch")
                self._store_blob(manifest, derivation.artifact_manifest_hash)
            for relative_path, expected_hash in derivation.artifact_hashes.items():
                artifact = (derived.parent / relative_path).resolve()
                if derived.parent.resolve() not in artifact.parents:
                    raise EvidenceIntegrityError("derived artifact escapes its package")
                if not artifact.is_file() or file_sha256(artifact) != expected_hash:
                    raise EvidenceIntegrityError("derived artifact hash mismatch")
                self._store_blob(artifact, expected_hash)
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
        return self.verified_blob_path(blob_hash).read_bytes()

    def verified_blob_path(self, blob_hash: str) -> Path:
        """Return an internal blob path only after its content hash has been verified."""

        path = self._blob_path(blob_hash)
        if not path.is_file() or file_sha256(path) != blob_hash:
            raise EvidenceIntegrityError(f"evidence blob not found or corrupt: {blob_hash}")
        return path

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
                    matrix=pymupdf.Matrix(2, 2),  # type: ignore[no-untyped-call]
                    clip=pymupdf.Rect(  # type: ignore[no-untyped-call]
                        box.x0, box.y0, box.x1, box.y1
                    ),
                    alpha=False,
                )
                return bytes(pixmap.tobytes("png"))
        with Image.open(BytesIO(content)) as image:
            if evidence.coordinate_space == CoordinateSpace.NORMALIZED:
                coordinates = (
                    int(box.x0 * image.width),
                    int(box.y0 * image.height),
                    int(box.x1 * image.width),
                    int(box.y1 * image.height),
                )
            else:
                coordinates = (
                    int(box.x0),
                    int(box.y0),
                    int(box.x1),
                    int(box.y1),
                )
            cropped = image.crop(coordinates)
            if cropped.mode not in {"RGB", "RGBA", "L", "LA", "P", "1"}:
                cropped = cropped.convert("RGB")
            output = BytesIO()
            cropped.save(output, format="PNG")
            return output.getvalue()

    async def get(self, evidence_id: str) -> EvidenceRef:
        return self._load_ref(evidence_id)

    async def exists(self, evidence_id: str) -> bool:
        self._require_available()
        return self._ref_path(evidence_id).is_file()

    def _require_available(self) -> None:
        for directory in (self.refs_dir, self.blobs_dir):
            # Fail on unavailable stores, not as an excludable candidate problem.
            with os.scandir(directory) as entries:
                next(entries, None)

    async def verify(self, evidence_id: str) -> bool:
        self._require_available()
        try:
            evidence = self._load_ref(evidence_id)
            if evidence.json_path and evidence.json_value_hash:
                payload = json.loads((await self.get_blob(evidence.source_hash)).decode("utf-8"))
                value = _json_path_value(payload, evidence.json_path)
                if canonical_hash(value) != evidence.json_value_hash:
                    return False
            if evidence.coordinate_space == CoordinateSpace.PDF_POINTS:
                if evidence.page_number is None or evidence.bbox is None:
                    return False
                content = await self.get_blob(evidence.source_hash)
                with pymupdf.open(stream=content, filetype="pdf") as pdf:  # type: ignore[no-untyped-call]
                    if not 1 <= evidence.page_number <= len(pdf):
                        return False
                    page = pdf[evidence.page_number - 1]
                    if evidence.canvas_width and abs(page.rect.width - evidence.canvas_width) > 0.5:
                        return False
                    if (
                        evidence.canvas_height
                        and abs(page.rect.height - evidence.canvas_height) > 0.5
                    ):
                        return False
                    box = evidence.bbox
                    if (
                        box.x0 < 0
                        or box.y0 < 0
                        or box.x1 > page.rect.width
                        or box.y1 > page.rect.height
                    ):
                        return False
            if evidence.derivation_id:
                locator = evidence.source_locator
                if not isinstance(locator, dict) or locator.get("schema") != "docvortex.middle":
                    return False
                derived_hash = locator.get("derived_hash")
                if not isinstance(derived_hash, str):
                    return False
                derived = orjson.loads(await self.get_blob(derived_hash))
                if (
                    not isinstance(derived, dict)
                    or derived.get("schema") != "docvortex.middle"
                    or derived.get("schema_version") != "2.0"
                    or derived.get("is_full_document") is not True
                ):
                    return False
                metadata = derived.get("metadata")
                extensions = derived.get("extensions")
                if (
                    not isinstance(metadata, dict)
                    or not isinstance(metadata.get("producer"), dict)
                    or metadata["producer"].get("name") != "mineru"
                    or not isinstance(extensions, dict)
                    or not isinstance(extensions.get("mineru"), dict)
                    or extensions["mineru"].get("tier") != "standard"
                ):
                    return False
                page_idx = locator.get("page_idx")
                block_index = locator.get("block_index")
                if not isinstance(page_idx, int) or not isinstance(block_index, int):
                    return False
                if evidence.page_number != page_idx + 1:
                    return False
                pages = derived.get("pages")
                if not isinstance(pages, list):
                    return False
                page = next(
                    (
                        item
                        for item in pages
                        if isinstance(item, dict) and item.get("page_idx") == page_idx
                    ),
                    None,
                )
                if not isinstance(page, dict) or not isinstance(page.get("blocks"), list):
                    return False
                if not 0 <= block_index < len(page["blocks"]):
                    return False
                block = page["blocks"][block_index]
                if (
                    not isinstance(block, dict)
                    or locator.get("block_hash") != canonical_hash(block)
                    or locator.get("block_type") != str(block.get("type", "text")).lower()
                ):
                    return False
                block_bbox = block.get("bbox")
                if evidence.bbox is not None:
                    if not isinstance(block_bbox, list) or len(block_bbox) != 4:
                        return False
                    expected_bbox = tuple(float(value) for value in block_bbox)
                    encoding = locator.get("bbox_encoding")
                    if encoding == "normalized":
                        if (
                            evidence.canvas_width is None
                            or evidence.canvas_height is None
                            or any(value < 0 or value > 1 for value in expected_bbox)
                        ):
                            return False
                        expected_bbox = (
                            expected_bbox[0] * evidence.canvas_width,
                            expected_bbox[1] * evidence.canvas_height,
                            expected_bbox[2] * evidence.canvas_width,
                            expected_bbox[3] * evidence.canvas_height,
                        )
                    elif encoding != "pdf_points":
                        return False
                    if any(
                        abs(float(actual) - expected) > 0.001
                        for actual, expected in zip(
                            expected_bbox,
                            (
                                evidence.bbox.x0,
                                evidence.bbox.y0,
                                evidence.bbox.x1,
                                evidence.bbox.y1,
                            ),
                            strict=True,
                        )
                    ):
                        return False
                asset_hash = locator.get("asset_hash")
                if asset_hash is not None:
                    if not isinstance(asset_hash, str):
                        return False
                    await self.get_blob(asset_hash)
        except (
            EvidenceIntegrityError,
            FileNotFoundError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            return False
        return True


def _json_path_value(payload: object, path: str) -> object:
    """Resolve the restricted JSONPath emitted by JSONParser."""
    if not path.startswith("$"):
        raise EvidenceIntegrityError("invalid JSONPath evidence")
    value = payload
    for key, index, quoted in re.findall(
        r"\.([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]|\[(\"(?:[^\"\\]|\\.)*\")\]", path[1:]
    ):
        if key:
            if not isinstance(value, dict):
                raise EvidenceIntegrityError("JSONPath object segment mismatch")
            value = value[key]
        elif index:
            if not isinstance(value, list):
                raise EvidenceIntegrityError("JSONPath array segment mismatch")
            value = value[int(index)]
        else:
            if not isinstance(value, dict):
                raise EvidenceIntegrityError("JSONPath object segment mismatch")
            value = value[json.loads(quoted)]
    return value
