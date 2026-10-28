"""Portable validation reports, exclusion audit and commit provenance."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.domain.schema import OutputSchema

VALIDATION_POLICY_VERSION = "validation-v2"

ValidationAction = Literal[
    "swap_endpoints",
    "replace_relation",
    "replace_entity_type",
    "replace_entity_link",
    "exclude",
    "defer",
]


def default_validation_actions() -> list[ValidationAction]:
    return ["exclude"]


class ValidationIssue(BaseModel):
    id: str
    code: str
    stage: Literal["structure", "schema", "reference", "evidence", "commit"]
    target_type: Literal[
        "candidate",
        "entity",
        "attribute",
        "event",
        "observation",
        "claim",
        "document",
        "conflict",
    ]
    target_id: str
    field_path: str
    severity: Literal["warning", "blocking"] = "blocking"
    message: str
    evidence_ids: list[str] = Field(default_factory=list)
    message_key: str = ""
    message_args: dict[str, Any] = Field(default_factory=dict)
    expected_constraint: dict[str, Any] = Field(default_factory=dict)
    actual_value: dict[str, Any] = Field(default_factory=dict)
    candidate_version: int = Field(default=0, ge=0)
    allowed_actions: list[ValidationAction] = Field(default_factory=default_validation_actions)
    candidate_summary: dict[str, Any] = Field(default_factory=dict)
    status: Literal["open", "excluded", "repaired", "deferred"] = "open"


class ValidationReviewDecision(BaseModel):
    issue_id: str
    target_id: str = ""
    action: ValidationAction = "exclude"
    reviewer: str = Field(min_length=1)
    comment: str = ""
    request_id: str = ""
    expected_version: int = Field(default=0, ge=0)
    replacement: dict[str, Any] = Field(default_factory=dict)
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationCorrectionEvent(BaseModel):
    id: str
    run_id: str
    target_id: str
    issue_ids: list[str] = Field(min_length=1)
    action: ValidationAction
    replacement: dict[str, Any] = Field(default_factory=dict)
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] | None = None
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    expected_version: int = Field(ge=0)
    applied_version: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationResult(BaseModel):
    policy_version: str = VALIDATION_POLICY_VERSION
    input_fingerprint: str = ""
    issues: list[ValidationIssue] = Field(default_factory=list)
    passed_count: int = 0
    blocking_count: int = 0


class CommitValidationContext(BaseModel):
    # GraphCommit provenance is still validation-v1. Candidate correction is
    # validation-v2, but the workflow protocol and persisted graph contract do
    # not change in v0.14.
    policy_version: str = "validation-v1"
    schemas: dict[str, OutputSchema] = Field(default_factory=dict)
    claim_schema_ids: dict[str, str] = Field(default_factory=dict)
    document_asset_ids: dict[str, list[str]] = Field(default_factory=dict)
