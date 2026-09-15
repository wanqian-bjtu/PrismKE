"""Small SQLite snapshot store used around LangGraph node execution."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import orjson

from prismke.models import WorkflowState


class SQLiteCheckpointStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    node TEXT NOT NULL,
                    state_json BLOB NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_run "
                "ON snapshots(run_id, sequence DESC)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save(self, state: WorkflowState) -> None:
        payload = orjson.dumps(state.model_dump(mode="json"))
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO snapshots(run_id, node, state_json) VALUES (?, ?, ?)",
                (state.run_id, state.current_node, payload),
            )

    def load_latest(self, run_id: str) -> WorkflowState | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM snapshots WHERE run_id = ? "
                "ORDER BY sequence DESC LIMIT 1",
                (run_id,),
            ).fetchone()
        return WorkflowState.model_validate(orjson.loads(row[0])) if row else None


class RunRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, state: WorkflowState) -> Path:
        target = self.directory / f"{state.run_id}.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_bytes(
            orjson.dumps(state.model_dump(mode="json"), option=orjson.OPT_INDENT_2)
        )
        temporary.replace(target)
        return target

    def load(self, run_id: str) -> WorkflowState:
        return WorkflowState.model_validate(
            orjson.loads((self.directory / f"{run_id}.json").read_bytes())
        )
