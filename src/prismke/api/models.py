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


class RollbackRequest(BaseModel):
    confirm: Literal[True]


class EntityReviewRequest(BaseModel):
    action: Literal["link", "create", "approve", "reject"]
    run_id: str | None = None
    selected_entity_id: str | None = None
    reviewer: str | None = None


class MergeProposalRequest(BaseModel):
    source_entity_ids: list[str]
    target_entity_id: str
    reasons: list[str] = Field(default_factory=list)


class SplitProposalRequest(BaseModel):
    target_entities: list[CanonicalEntity]
    claim_assignments: dict[str, str]
    reasons: list[str] = Field(default_factory=list)
