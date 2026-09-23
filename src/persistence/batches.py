"""Atomic JSON persistence for multi-document batch summaries."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import orjson
from filelock import FileLock

from src.domain import BatchRun


class BatchRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, batch_id: str) -> Path:
        return self.directory / f"{quote(batch_id, safe='')}.json"

    def _lock(self, batch_id: str) -> FileLock:
        return FileLock(str(self._path(batch_id).with_suffix(".lock")), timeout=30)

    def save(self, batch: BatchRun) -> Path:
        target = self._path(batch.id)
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        with self._lock(batch.id):
            try:
                with temporary.open("wb") as stream:
                    stream.write(
                        orjson.dumps(batch.model_dump(mode="json"), option=orjson.OPT_INDENT_2)
                    )
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        return target

    def load(self, batch_id: str) -> BatchRun:
        return BatchRun.model_validate(orjson.loads(self._path(batch_id).read_bytes()))

    def exists(self, batch_id: str) -> bool:
        return self._path(batch_id).is_file()

    def list(self) -> list[BatchRun]:
        paths = sorted(
            self.directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True
        )
        return [BatchRun.model_validate(orjson.loads(path.read_bytes())) for path in paths]
