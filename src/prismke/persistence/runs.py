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

    def list(self, limit: int = 100) -> list[WorkflowState]:
        paths = sorted(
            self.directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True
        )
        states: list[WorkflowState] = []
        for path in paths[: max(limit, 0)]:
            states.append(WorkflowState.model_validate(orjson.loads(path.read_bytes())))
        return states

    def find_review(self, task_id: str) -> tuple[WorkflowState, str]:
        for state in self.list():
            task = next((item for item in state.review_tasks if item.id == task_id), None)
            if task is not None:
                return state, task.claim_id
        raise KeyError(f"review task not found: {task_id}")
