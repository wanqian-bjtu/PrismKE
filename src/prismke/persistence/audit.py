"""Append-only audit records for review and rollback operations."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson
from filelock import FileLock


class AuditLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(path.with_suffix(path.suffix + ".lock")))

    def record(self, action: str, target_id: str, details: dict[str, Any] | None = None) -> None:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "target_id": target_id,
            "details": details or {},
        }
        with self.lock, self.path.open("ab") as stream:
            event_id = (details or {}).get("event_id")
            if event_id:
                with self.path.open("rb") as existing:
                    if any(
                        orjson.loads(line).get("details", {}).get("event_id") == event_id
                        for line in existing
                        if line.strip()
                    ):
                        return
            stream.write(orjson.dumps(payload) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
