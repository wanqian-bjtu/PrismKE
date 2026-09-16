"""Execution metadata is separate from knowledge and review state."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

ExecutionStatus = Literal[
    "queued",
    "running",
    "cancelling",
    "cancelled",
    "interrupted",
    "failed",
    "awaiting_review",
    "awaiting_commit",
    "completed",
]


class ExecutionTask(BaseModel):
    run_id: str
    operation: Literal["execute", "resume", "confirm"] = "execute"
    status: ExecutionStatus = "queued"
    version: int = 0
    attempt: int = 0
    node: str = "ingest"
    input_hash: str
    schema_hash: str
    cancel_requested: bool = False
    operator: str | None = None
    reason: str | None = None
    error_code: str | None = None
    reviewer: str | None = None
    commit_revision_id: str | None = None
    commit_applied: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExecutionEvent(BaseModel):
    sequence: int
    run_id: str
    version: int
    status: ExecutionStatus
    node: str
    reason: str | None
    created_at: datetime
