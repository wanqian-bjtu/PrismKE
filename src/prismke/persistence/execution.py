"""Durable execution state, immutable transitions and private response journal."""

import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson

from prismke.domain.execution import ExecutionEvent, ExecutionTask


class ExecutionConflict(ValueError):
    pass


class ExecutionRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS tasks (run_id TEXT PRIMARY KEY, payload BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
                    payload BLOB NOT NULL);
                CREATE TRIGGER IF NOT EXISTS immutable_events_update
                    BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'immutable event'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_events_delete
                    BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'immutable event'); END;
                CREATE TABLE IF NOT EXISTS commands (
                    run_id TEXT NOT NULL, request_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    result BLOB NOT NULL, PRIMARY KEY(run_id,request_id));
                CREATE TABLE IF NOT EXISTS requests (
                    run_id TEXT NOT NULL, key TEXT NOT NULL, status TEXT NOT NULL,
                    metadata BLOB NOT NULL, response BLOB, usage_known INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(run_id,key));
                CREATE TABLE IF NOT EXISTS results (
                    run_id TEXT NOT NULL, key TEXT NOT NULL, payload BLOB NOT NULL,
                    PRIMARY KEY(run_id,key));
            """)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30)
        db.execute("PRAGMA synchronous=FULL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, run_id: str) -> ExecutionTask | None:
        with self.connect() as db:
            row = db.execute("SELECT payload FROM tasks WHERE run_id=?", (run_id,)).fetchone()
        return ExecutionTask.model_validate(orjson.loads(row[0])) if row else None

    def list_tasks(self) -> list[ExecutionTask]:
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM tasks ORDER BY rowid").fetchall()
        return [ExecutionTask.model_validate(orjson.loads(r[0])) for r in rows]

    @staticmethod
    def _write(db: sqlite3.Connection, task: ExecutionTask) -> None:
        task.updated_at = datetime.now(UTC)
        payload = orjson.dumps(task.model_dump(mode="json"))
        db.execute("INSERT OR REPLACE INTO tasks VALUES (?,?)", (task.run_id, payload))
        db.execute("INSERT INTO events(run_id,payload) VALUES (?,?)", (task.run_id, payload))

    def register(self, task: ExecutionTask) -> ExecutionTask:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM tasks WHERE run_id=?", (task.run_id,)).fetchone()
            if row:
                return ExecutionTask.model_validate(orjson.loads(row[0]))
            self._write(db, task)
        return task

    def change(
        self,
        run_id: str,
        action: Callable[[ExecutionTask], None],
        expected_version: int | None = None,
        command: tuple[str, str] | None = None,
    ) -> ExecutionTask:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if command:
                old = db.execute(
                    "SELECT fingerprint,result FROM commands WHERE run_id=? AND request_id=?",
                    (run_id, command[0]),
                ).fetchone()
                if old:
                    if old[0] != command[1]:
                        raise ExecutionConflict("REQUEST_ID_REUSED")
                    return ExecutionTask.model_validate(orjson.loads(old[1]))
            row = db.execute("SELECT payload FROM tasks WHERE run_id=?", (run_id,)).fetchone()
            if not row:
                raise ExecutionConflict("EXECUTION_NOT_REGISTERED")
            task = ExecutionTask.model_validate(orjson.loads(row[0]))
            if expected_version is not None and task.version != expected_version:
                raise ExecutionConflict("STALE_EXECUTION_VERSION")
            action(task)
            task.version += 1
            self._write(db, task)
            if command:
                db.execute(
                    "INSERT INTO commands VALUES (?,?,?,?)",
                    (
                        run_id,
                        *command,
                        orjson.dumps(task.model_dump(mode="json")),
                    ),
                )
        return task

    def events(self, run_id: str) -> list[ExecutionEvent]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT seq,payload FROM events WHERE run_id=? ORDER BY seq", (run_id,)
            ).fetchall()
        return [
            ExecutionEvent(
                sequence=seq,
                **{
                    k: v
                    for k, v in orjson.loads(payload).items()
                    if k in {"run_id", "version", "status", "node", "reason"}
                },
                created_at=orjson.loads(payload)["updated_at"],
            )
            for seq, payload in rows
        ]

    def begin_request(
        self, run_id: str, key: str, metadata: dict[str, Any]
    ) -> dict[str, Any] | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT status,response FROM requests WHERE run_id=? AND key=?", (run_id, key)
            ).fetchone()
            if old and old[0] == "completed":
                return dict(orjson.loads(old[1]))
            if old and old[0] in {"sent", "unknown"}:
                raise ExecutionConflict("UNKNOWN_PROVIDER_REQUEST")
            db.execute(
                "INSERT OR REPLACE INTO requests VALUES (?,?,?,?,NULL,0)",
                (
                    run_id,
                    key,
                    "sent",
                    orjson.dumps(
                        {
                            **metadata,
                            "dispatched_at": datetime.now(UTC).isoformat(),
                        }
                    ),
                ),
            )
        return None

    def finish_request(
        self,
        run_id: str,
        key: str,
        status: str,
        response: dict[str, Any] | None = None,
        usage_known: bool = False,
    ) -> None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT metadata FROM requests WHERE run_id=? AND key=?", (run_id, key)
            ).fetchone()
            if row is None:
                raise ExecutionConflict("REQUEST_JOURNAL_MISSING")
            metadata = dict(orjson.loads(row[0]))
            settled = datetime.now(UTC)
            metadata["settled_at"] = settled.isoformat()
            if metadata.get("dispatched_at"):
                metadata["latency_ms"] = round(
                    (settled - datetime.fromisoformat(metadata["dispatched_at"])).total_seconds()
                    * 1000,
                    3,
                )
            changed = db.execute(
                "UPDATE requests SET status=?,response=?,usage_known=?,metadata=? "
                "WHERE run_id=? AND key=?",
                (
                    status,
                    orjson.dumps(response) if response is not None else None,
                    int(usage_known),
                    orjson.dumps(metadata),
                    run_id,
                    key,
                ),
            ).rowcount
            if changed != 1:
                raise ExecutionConflict("REQUEST_JOURNAL_MISSING")

    def unknown(self, run_id: str, *, include_sent: bool = True) -> int:
        with self.connect() as db:
            return int(
                db.execute(
                    """SELECT count(*) FROM requests WHERE run_id=? AND
                (status='unknown' OR (status='sent' AND ?) OR
                 (status='completed' AND usage_known=0))""",
                    (run_id, int(include_sent)),
                ).fetchone()[0]
            )

    def result(self, run_id: str, key: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT payload FROM results WHERE run_id=? AND key=?", (run_id, key)
            ).fetchone()
        return dict(orjson.loads(row[0])) if row else None

    def put_result(self, run_id: str, key: str, payload: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO results VALUES (?,?,?)", (run_id, key, orjson.dumps(payload))
            )
