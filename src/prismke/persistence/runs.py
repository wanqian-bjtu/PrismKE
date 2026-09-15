"""User-facing serialized workflow summaries."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import orjson

from prismke.domain import WorkflowState


class RunRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def exists(self, run_id: str) -> bool:
        return (self.directory / f"{run_id}.json").is_file()

    def save(self, state: WorkflowState) -> Path:
        target = self.directory / f"{state.run_id}.json"
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
        return WorkflowState.model_validate(
            orjson.loads((self.directory / f"{run_id}.json").read_bytes())
        )
