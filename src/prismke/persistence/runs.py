"""User-facing serialized workflow summaries."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import orjson

from prismke.domain import WorkflowState


class RunRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _target(self, run_id: str) -> Path:
        return self.directory / f"{quote(run_id, safe='')}.json"

    def _legacy_target(self, run_id: str) -> Path:
        return self.directory / f"{run_id}.json"

    def exists(self, run_id: str) -> bool:
        return self._target(run_id).is_file() or self._legacy_target(run_id).is_file()

    def save(self, state: WorkflowState) -> Path:
        target = self._target(state.run_id)
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("wb") as stream:
                stream.write(
                    orjson.dumps(state.model_dump(mode="json"), option=orjson.OPT_INDENT_2)
                )
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return target

    def load(self, run_id: str) -> WorkflowState:
        target = self._target(run_id)
        if not target.is_file() and self._legacy_target(run_id).is_file():
            target = self._legacy_target(run_id)
        return WorkflowState.model_validate(
            orjson.loads(target.read_bytes())
        )
