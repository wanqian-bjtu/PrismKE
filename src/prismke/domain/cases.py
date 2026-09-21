"""Immutable review cases and bounded Reflection contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from prismke.domain.knowledge import CandidateClaim
from prismke.domain.schema import OutputSchema
from prismke.domain.validation import ValidationIssue


class CaseRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    run_id: str
    case_type: Literal["good", "bad"]
    task_type: Literal["entity", "claim"]
    schema_fingerprint: str
    language: str
    input_summary: str
    candidate_snapshot: dict[str, Any]
    decision: str
    reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    source_review_event_id: str
    supersedes_case_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CaseStatusEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    case_id: str
    action: Literal["disable"]
    operator: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    source_event_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CaseEmbedding(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str
    model_fingerprint: str
    text_hash: str
    dimension: int = Field(gt=0)
    vector: list[float]


class RetrievedCase(BaseModel):
    case_id: str
    case_type: Literal["good", "bad"]
    task_type: Literal["entity", "claim"]
    score: float = Field(ge=-1.0, le=1.0)
    decision: str
    input_summary: str
    reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    use_location: str


class ReflectionRequest(BaseModel):
    run_id: str
    candidate: CandidateClaim
    issues: list[ValidationIssue]
    retrieved_cases: list[RetrievedCase] = Field(default_factory=list)
    output_schema: OutputSchema
    allowed_evidence_ids: list[str]
    attempt: int = Field(ge=1, le=2)
    remaining_tokens: int = Field(ge=0)


class ReflectionResult(BaseModel):
    candidate: CandidateClaim | None = None
    raw_response_model: str | None = None
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    request_id: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ReflectionAttempt(BaseModel):
    id: str
    run_id: str
    candidate_id: str
    attempt: int = Field(ge=1, le=2)
    issue_ids: list[str]
    retrieved_case_ids: list[str]
    input_candidate: dict[str, Any]
    output_candidate: dict[str, Any] | None = None
    model_fingerprint: str
    prompt_version: str
    token_usage: int | None = Field(default=None, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    status: Literal[
        "succeeded",
        "failed",
        "rejected_by_validation",
        "budget_exhausted",
        "unknown_usage",
    ]
    error_code: str | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
