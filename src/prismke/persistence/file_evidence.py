"""Immutable content-addressed evidence storage."""

from __future__ import annotations

import os
import shutil
from hashlib import sha256
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import orjson

from prismke.core.errors import EvidenceIntegrityError
from prismke.core.ids import canonical_hash, file_sha256
from prismke.domain import DocumentIR, EvidenceRef


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
        for evidence in document.evidence:
            if evidence.document_id != document.id or evidence.source_hash != document.source_hash:
                raise EvidenceIntegrityError(
                    f"evidence {evidence.id} does not belong to document {document.id}"
                )
            path = self._ref_path(evidence.id)
            payload = self._serialize_ref(evidence)
            if path.exists():
                if path.read_bytes() != payload:
                    raise EvidenceIntegrityError(
                        f"immutable evidence already exists with different content: {evidence.id}"
                    )
                continue
            self._atomic_write(path, payload)

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
