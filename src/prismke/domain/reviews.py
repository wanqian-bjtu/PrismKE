"""Immutable review history and optimistic correction contracts."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ReviewEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    request_id: str
    run_id: str
    task_id: str
    kind: Literal["entity", "claim"]
    action: Literal["link", "create", "approve", "reject", "defer", "commit_correction"]
    version: int = Field(ge=1)
    reviewer: str = Field(min_length=1)
    reason: str = ""
    before: dict[str, Any]
    after: dict[str, Any]
    supersedes_event_id: str | None = None
    correction_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CorrectionGuard(BaseModel):
    source_event_id: str
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    expected_resources: dict[str, str | None]


class ReviewCorrection(BaseModel):
    id: str
    run_id: str
    source_event_id: str
    task_id: str
    kind: Literal["entity", "claim"]
    action: Literal["link", "create", "approve", "reject"]
    selected_entity_id: str | None = None
    expected_version: int
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    parent_revision_id: str | None
    affected_claim_ids: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)
    preview: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
