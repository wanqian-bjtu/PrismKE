"""Immutable review-case store and rebuildable dense embeddings."""

from __future__ import annotations

import builtins
import sqlite3
from contextlib import closing
from pathlib import Path

from src.core.ids import canonical_hash
from src.domain import CaseEmbedding, CaseRecord, CaseStatusEvent


class CaseRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection, connection:
            connection.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS cases(
                    id TEXT PRIMARY KEY,
                    source_event_id TEXT NOT NULL UNIQUE,
                    payload BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS status_events(
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    payload BLOB NOT NULL,
                    FOREIGN KEY(case_id) REFERENCES cases(id)
                );
                CREATE TABLE IF NOT EXISTS projected_events(
                    event_id TEXT PRIMARY KEY,
                    case_id TEXT
                );
                CREATE TABLE IF NOT EXISTS embeddings(
                    case_id TEXT PRIMARY KEY,
                    model_fingerprint TEXT NOT NULL,
                    text_hash TEXT NOT NULL,
                    dimension INTEGER NOT NULL,
                    payload BLOB NOT NULL,
                    FOREIGN KEY(case_id) REFERENCES cases(id)
                );
                CREATE TRIGGER IF NOT EXISTS immutable_cases_update BEFORE UPDATE ON cases
                    BEGIN SELECT RAISE(ABORT,'cases are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_cases_delete BEFORE DELETE ON cases
                    BEGIN SELECT RAISE(ABORT,'cases are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_case_status_update
                    BEFORE UPDATE ON status_events
                    BEGIN SELECT RAISE(ABORT,'case status events are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_case_status_delete
                    BEFORE DELETE ON status_events
                    BEGIN SELECT RAISE(ABORT,'case status events are immutable'); END;
            """)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def add(self, record: CaseRecord) -> CaseRecord:
        payload = record.model_dump_json()
        with closing(self.connect()) as connection, connection:
            row = connection.execute(
                "SELECT payload FROM cases WHERE id=?", (record.id,)
            ).fetchone()
            if row is not None:
                existing = CaseRecord.model_validate_json(row[0])
                if canonical_hash(existing.model_dump(mode="json")) != canonical_hash(
                    record.model_dump(mode="json")
                ):
                    raise ValueError("immutable case id reused with different content")
                return existing
            connection.execute(
                "INSERT INTO cases(id,source_event_id,payload) VALUES (?,?,?)",
                (record.id, record.source_review_event_id, payload),
            )
        return record

    def get(self, case_id: str) -> CaseRecord:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT payload FROM cases WHERE id=?", (case_id,)).fetchone()
        if row is None:
            raise KeyError("case not found")
        return CaseRecord.model_validate_json(row[0])

    def by_source_event(self, event_id: str) -> CaseRecord | None:
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT payload FROM cases WHERE source_event_id=?", (event_id,)
            ).fetchone()
        return CaseRecord.model_validate_json(row[0]) if row else None

    def list(
        self,
        *,
        case_type: str | None = None,
        task_type: str | None = None,
        schema_fingerprint: str | None = None,
        language: str | None = None,
        active_only: bool = False,
        limit: int = 100,
    ) -> builtins.list[CaseRecord]:
        clauses: list[str] = []
        values: list[object] = []
        for expression, value in (
            ("json_extract(payload,'$.case_type')=?", case_type),
            ("json_extract(payload,'$.task_type')=?", task_type),
            ("json_extract(payload,'$.schema_fingerprint')=?", schema_fingerprint),
            ("json_extract(payload,'$.language')=?", language),
        ):
            if value is not None:
                clauses.append(expression)
                values.append(value)
        if active_only:
            clauses.append(
                "NOT EXISTS (SELECT 1 FROM status_events s WHERE s.case_id=cases.id "
                "AND json_extract(s.payload,'$.action')='disable')"
            )
        sql = "SELECT payload FROM cases"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY rowid DESC LIMIT ?"
        values.append(max(1, min(limit, 10000)))
        with closing(self.connect()) as connection:
            rows = connection.execute(sql, values).fetchall()
        return [CaseRecord.model_validate_json(row[0]) for row in rows]

    def status_events(self, case_id: str) -> builtins.list[CaseStatusEvent]:
        with closing(self.connect()) as connection:
            rows = connection.execute(
                "SELECT payload FROM status_events WHERE case_id=? ORDER BY rowid", (case_id,)
            ).fetchall()
        return [CaseStatusEvent.model_validate_json(row[0]) for row in rows]

    def disable(self, event: CaseStatusEvent) -> CaseStatusEvent:
        self.get(event.case_id)
        with closing(self.connect()) as connection, connection:
            row = connection.execute(
                "SELECT payload FROM status_events WHERE id=?", (event.id,)
            ).fetchone()
            if row is not None:
                existing = CaseStatusEvent.model_validate_json(row[0])
                if existing != event:
                    raise ValueError("case status request id reused with different content")
                return existing
            connection.execute(
                "INSERT INTO status_events(id,case_id,payload) VALUES (?,?,?)",
                (event.id, event.case_id, event.model_dump_json()),
            )
        return event

    def is_active(self, case_id: str) -> bool:
        self.get(case_id)
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT 1 FROM status_events WHERE case_id=? "
                "AND json_extract(payload,'$.action')='disable' LIMIT 1",
                (case_id,),
            ).fetchone()
        return row is None

    def projected(self, event_id: str) -> bool:
        with closing(self.connect()) as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM projected_events WHERE event_id=?", (event_id,)
                ).fetchone()
                is not None
            )

    def mark_projected(self, event_id: str, case_id: str | None) -> None:
        with closing(self.connect()) as connection, connection:
            connection.execute(
                "INSERT OR IGNORE INTO projected_events(event_id,case_id) VALUES (?,?)",
                (event_id, case_id),
            )

    def embedding(self, case_id: str) -> CaseEmbedding | None:
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT payload FROM embeddings WHERE case_id=?", (case_id,)
            ).fetchone()
        return CaseEmbedding.model_validate_json(row[0]) if row else None

    def save_embedding(self, embedding: CaseEmbedding) -> None:
        with closing(self.connect()) as connection, connection:
            connection.execute(
                "INSERT INTO embeddings VALUES (?,?,?,?,?) "
                "ON CONFLICT(case_id) DO UPDATE SET model_fingerprint=excluded.model_fingerprint,"
                "text_hash=excluded.text_hash,dimension=excluded.dimension,payload=excluded.payload",
                (
                    embedding.case_id,
                    embedding.model_fingerprint,
                    embedding.text_hash,
                    embedding.dimension,
                    embedding.model_dump_json(),
                ),
            )

    def index_status(self, model_fingerprint: str) -> dict[str, int]:
        active = self.list(active_only=True, limit=10000)
        current = 0
        for record in active:
            embedding = self.embedding(record.id)
            if embedding and embedding.model_fingerprint == model_fingerprint:
                current += 1
        return {
            "active_cases": len(active),
            "indexed_cases": current,
            "stale_cases": len(active) - current,
        }
