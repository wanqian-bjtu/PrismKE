"""Execution metadata is separate from knowledge and review state."""

from datetime import UTC, datetime
from typing import Any, Literal

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


class BranchProgress(BaseModel):
    branch: Literal["text", "visual", "ocr", "commit"]
    status: Literal["disabled", "pending", "running", "completed", "failed"]
    completed: int = Field(ge=0)
    total: int | None = Field(default=None, ge=0)
    current_asset: str | None = None
    updated_at: datetime


class WorkspaceSummary(BaseModel):
    run_counts: dict[str, int] = Field(default_factory=dict)
    pending_reviews: int = Field(ge=0)
    blocking_issues: int = Field(ge=0)
    worker_status: str
    graph_health: dict[str, Any]


class RequestReconciliation(BaseModel):
    request_id: str
    outcome: Literal["confirmed_not_sent", "confirmed_not_billed", "possibly_billed"]
    operator: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    expected_execution_version: int = Field(ge=0)


class RequestReconciliationEvent(RequestReconciliation):
    sequence: int
    run_id: str
    created_at: datetime
