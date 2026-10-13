"""Persistent multi-document batch contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.domain.knowledge import utc_now
from src.domain.pdf import PDFParseMode
from src.domain.tasks import EntitySourceMode, TaskExtractionResult, TaskMode


class BatchStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    AWAITING_REVIEW = "awaiting_review"
    AWAITING_COMMIT = "awaiting_commit"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchItemStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    REUSED = "reused"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    EXCLUDED = "excluded"


class BatchItem(BaseModel):
    id: str
    filename: str
    source_path: str
    content_hash: str
    size_bytes: int = Field(ge=0)
    status: BatchItemStatus = BatchItemStatus.QUEUED
    run_id: str | None = None
    reused_from_item_id: str | None = None
    failure_code: str | None = None
    failure_reason: str | None = None
    token_usage: int | None = Field(default=None, ge=0)
    excluded_by: str | None = None
    exclusion_reason: str | None = None
    updated_at: datetime = Field(default_factory=utc_now)


class BatchRun(BaseModel):
    id: str
    task_mode: TaskMode = TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION
    entity_source_mode: EntitySourceMode = EntitySourceMode.AUTO
    pdf_parse_mode: PDFParseMode = PDFParseMode.AUTO
    schema_path: str
    status: BatchStatus = BatchStatus.QUEUED
    items: list[BatchItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    operator: str | None = None
    errors: list[str] = Field(default_factory=list)
    revision_id: str | None = None


class BatchResult(BaseModel):
    batch_id: str
    item_id: str
    run_id: str | None = None
    status: BatchItemStatus
    result: TaskExtractionResult | None = None
    error: str | None = None
