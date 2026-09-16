"""Authoritative review events and transactional projection outbox."""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import orjson

from prismke.core.ids import canonical_hash
from prismke.domain.reviews import ReviewCorrection, ReviewEvent


class ReviewRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as c, c:
            c.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS archives(run_id TEXT PRIMARY KEY,payload BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS events(
                    id TEXT PRIMARY KEY,run_id TEXT NOT NULL,task_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,payload BLOB NOT NULL,state BLOB NOT NULL,
                    UNIQUE(run_id,request_id));
                CREATE TABLE IF NOT EXISTS versions(
                    run_id TEXT,task_id TEXT,version INTEGER NOT NULL,PRIMARY KEY(run_id,task_id));
                CREATE TABLE IF NOT EXISTS outbox(
                    event_id TEXT PRIMARY KEY,delivered INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS corrections(id TEXT PRIMARY KEY,payload BLOB NOT NULL);
                CREATE TRIGGER IF NOT EXISTS immutable_events_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT,'review events are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_events_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT,'review events are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_archive_update BEFORE UPDATE ON archives
                    BEGIN SELECT RAISE(ABORT,'candidate archives are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_archive_delete BEFORE DELETE ON archives
                    BEGIN SELECT RAISE(ABORT,'candidate archives are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_corrections_update
                    BEFORE UPDATE ON corrections
                    BEGIN SELECT RAISE(ABORT,'correction proposals are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_corrections_delete
                    BEFORE DELETE ON corrections
                    BEGIN SELECT RAISE(ABORT,'correction proposals are immutable'); END;
            """)

    def connect(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, timeout=10)
        c.execute("PRAGMA synchronous=FULL")
        return c

    def archive(self, run_id: str, candidates: list[dict[str, Any]]) -> None:
        payload = orjson.dumps(candidates, option=orjson.OPT_SORT_KEYS)
        with closing(self.connect()) as c, c:
            row = c.execute("SELECT payload FROM archives WHERE run_id=?", (run_id,)).fetchone()
            if row and row[0] != payload:
                raise ValueError("immutable candidate archive mismatch")
            c.execute("INSERT OR IGNORE INTO archives VALUES (?,?)", (run_id, payload))

    def original(self, run_id: str) -> list[dict[str, Any]]:
        with closing(self.connect()) as c:
            row = c.execute("SELECT payload FROM archives WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            raise ValueError(
                "original candidate archive unavailable; legacy runs cannot be corrected"
            )
        return orjson.loads(row[0])  # type: ignore[no-any-return]

    def events(self, run_id: str) -> list[ReviewEvent]:
        with closing(self.connect()) as c:
            rows = c.execute("SELECT payload FROM events WHERE run_id=? ORDER BY rowid", (run_id,))
            return [ReviewEvent.model_validate_json(r[0]) for r in rows]

    def request(self, run_id: str, request_id: str) -> ReviewEvent | None:
        with closing(self.connect()) as c:
            row = c.execute(
                "SELECT payload FROM events WHERE run_id=? AND request_id=?", (run_id, request_id)
            ).fetchone()
        return ReviewEvent.model_validate_json(row[0]) if row else None

    def event_state(self, event_id: str) -> dict[str, Any]:
        with closing(self.connect()) as c:
            row = c.execute("SELECT state FROM events WHERE id=?", (event_id,)).fetchone()
        if row is None:
            raise KeyError("review event not found")
        return orjson.loads(row[0])  # type: ignore[no-any-return]

    def version(self, run_id: str, task_id: str) -> int:
        with closing(self.connect()) as c:
            row = c.execute(
                "SELECT version FROM versions WHERE run_id=? AND task_id=?", (run_id, task_id)
            ).fetchone()
        return row[0] if row else 0

    def append(self, event: ReviewEvent, state: dict[str, Any], expected_version: int) -> None:
        with closing(self.connect()) as c, c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute(
                "SELECT 1 FROM outbox o JOIN events e ON e.id=o.event_id "
                "WHERE e.run_id=? AND o.delivered=0",
                (event.run_id,),
            ).fetchone():
                raise ValueError("review projection pending; recover before another decision")
            row = c.execute(
                "SELECT version FROM versions WHERE run_id=? AND task_id=?",
                (event.run_id, event.task_id),
            ).fetchone()
            actual = row[0] if row else 0
            if actual != expected_version or event.version != expected_version + 1:
                raise ValueError("stale review version")
            c.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?)",
                (
                    event.id,
                    event.run_id,
                    event.task_id,
                    event.request_id,
                    event.model_dump_json(),
                    orjson.dumps(state),
                ),
            )
            c.execute(
                "INSERT OR REPLACE INTO versions VALUES (?,?,?)",
                (event.run_id, event.task_id, event.version),
            )
            c.execute("INSERT INTO outbox(event_id) VALUES (?)", (event.id,))

    def pending(self, run_id: str | None = None) -> list[tuple[ReviewEvent, dict[str, Any]]]:
        with closing(self.connect()) as c:
            sql = "SELECT e.payload,e.state FROM events e JOIN outbox o ON o.event_id=e.id "
            sql += (
                "WHERE o.delivered=0" + (" AND e.run_id=?" if run_id else "") + " ORDER BY e.rowid"
            )
            rows = c.execute(sql, (run_id,) if run_id else ())
            return [(ReviewEvent.model_validate_json(r[0]), orjson.loads(r[1])) for r in rows]

    def delivered(self, event_id: str) -> None:
        with closing(self.connect()) as c, c:
            c.execute("UPDATE outbox SET delivered=1 WHERE event_id=?", (event_id,))

    def propose(self, proposal: ReviewCorrection) -> None:
        with closing(self.connect()) as c, c:
            row = c.execute("SELECT payload FROM corrections WHERE id=?", (proposal.id,)).fetchone()
            if row and canonical_hash(orjson.loads(row[0])) != canonical_hash(
                proposal.model_dump(mode="json")
            ):
                raise ValueError("correction request id reused with different proposal")
            c.execute(
                "INSERT OR IGNORE INTO corrections VALUES (?,?)",
                (proposal.id, proposal.model_dump_json()),
            )

    def correction(self, correction_id: str) -> ReviewCorrection:
        with closing(self.connect()) as c:
            row = c.execute(
                "SELECT payload FROM corrections WHERE id=?", (correction_id,)
            ).fetchone()
        if row is None:
            raise KeyError("correction not found")
        return ReviewCorrection.model_validate_json(row[0])
