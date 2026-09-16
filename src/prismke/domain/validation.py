"""Portable validation reports, exclusion audit and commit provenance."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from prismke.domain.schema import OutputSchema

VALIDATION_POLICY_VERSION = "validation-v1"


class ValidationIssue(BaseModel):
    id: str
    code: str
    stage: Literal["structure", "schema", "reference", "evidence", "commit"]
    target_type: Literal["candidate", "observation", "claim", "document", "conflict"]
    target_id: str
    field_path: str
    severity: Literal["warning", "blocking"] = "blocking"
    message: str
    evidence_ids: list[str] = Field(default_factory=list)
    allowed_actions: list[Literal["exclude"]] = Field(default=["exclude"])
    candidate_summary: dict[str, Any] = Field(default_factory=dict)
    status: Literal["open", "excluded"] = "open"


class ValidationReviewDecision(BaseModel):
    issue_id: str
    action: Literal["exclude"] = "exclude"
    reviewer: str = Field(min_length=1)
    comment: str = ""
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationResult(BaseModel):
    policy_version: str = VALIDATION_POLICY_VERSION
    input_fingerprint: str = ""
    issues: list[ValidationIssue] = Field(default_factory=list)
    passed_count: int = 0
    blocking_count: int = 0


class CommitValidationContext(BaseModel):
    policy_version: str = VALIDATION_POLICY_VERSION
    schemas: dict[str, OutputSchema] = Field(default_factory=dict)
    claim_schema_ids: dict[str, str] = Field(default_factory=dict)
    document_asset_ids: dict[str, list[str]] = Field(default_factory=dict)
