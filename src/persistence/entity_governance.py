"""Durable review queue for entity governance proposals."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import orjson
from filelock import FileLock

from src.domain import EntityOperation, EntityReviewTask


class EntityGovernanceRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = FileLock(str(path.with_suffix(path.suffix + ".lock")))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"tasks": {}, "operations": {}})

    def _read(self) -> dict[str, Any]:
        payload = cast(dict[str, Any], orjson.loads(self.path.read_bytes()))
        payload.setdefault("tasks", {})
        payload.setdefault("operations", {})
        return payload

    def _write(self, payload: dict[str, Any]) -> None:
        temporary = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("wb") as stream:
                stream.write(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def save(self, task: EntityReviewTask, operation: EntityOperation) -> None:
        with self.lock:
            data = self._read()
            data["tasks"][task.id] = task.model_dump(mode="json")
            data["operations"][operation.id] = operation.model_dump(mode="json")
            self._write(data)

    def update(self, task: EntityReviewTask, operation: EntityOperation) -> None:
        self.save(task, operation)

    def get_task(self, task_id: str) -> EntityReviewTask | None:
        with self.lock:
            payload = self._read()["tasks"].get(task_id)
        return EntityReviewTask.model_validate(payload) if payload is not None else None

    def get_operation(self, operation_id: str) -> EntityOperation | None:
        with self.lock:
            payload = self._read()["operations"].get(operation_id)
        return EntityOperation.model_validate(payload) if payload is not None else None

    def list_tasks(self, status: str | None = None) -> list[EntityReviewTask]:
        with self.lock:
            payloads = list(self._read()["tasks"].values())
        tasks = [EntityReviewTask.model_validate(item) for item in payloads]
        if status is not None:
            tasks = [item for item in tasks if item.status == status]
        return sorted(tasks, key=lambda item: item.created_at, reverse=True)
