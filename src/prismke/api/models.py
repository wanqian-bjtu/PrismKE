"""Public HTTP request and response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from prismke.domain import CanonicalEntity, ReviewDecision


class RunAccepted(BaseModel):
    run_id: str
    status: str
    created: bool


class ReviewRequest(BaseModel):
    decision: ReviewDecision
    reviewer: str | None = None
    comment: str | None = None
    expected_version: int | None = Field(default=None, ge=0)
    request_id: str | None = None


class RollbackRequest(BaseModel):
    confirm: Literal[True]


class ValidationExcludeRequest(BaseModel):
    reviewer: str = Field(min_length=1)
    comment: str = ""


class EntityReviewRequest(BaseModel):
    action: Literal["link", "create", "approve", "reject", "defer"]
    run_id: str | None = None
    selected_entity_id: str | None = None
    reviewer: str | None = None
    comment: str | None = None
    expected_version: int | None = Field(default=None, ge=0)
    request_id: str | None = None


class CorrectionRequest(BaseModel):
    source_event_id: str
    action: Literal["link", "create", "approve", "reject"]
    selected_entity_id: str | None = None
    expected_version: int = Field(ge=1)
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    request_id: str = Field(min_length=1)


class MergeProposalRequest(BaseModel):
    source_entity_ids: list[str]
    target_entity_id: str
    reasons: list[str] = Field(default_factory=list)


class SplitProposalRequest(BaseModel):
    target_entities: list[CanonicalEntity]
    claim_assignments: dict[str, str]
    reasons: list[str] = Field(default_factory=list)
