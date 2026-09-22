"""Structured contracts exchanged by PrismKE's three semantic agents."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from prismke.domain.knowledge import (
    CandidateClaim,
    CanonicalEntity,
    EntityCandidate,
    EntityMention,
    utc_now,
)

AgentRole = Literal["extraction", "governance", "fusion_review"]


class AgentHandoff(BaseModel):
    id: str
    run_id: str
    agent: AgentRole
    input_ids: list[str] = Field(default_factory=list)
    output_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    issue_ids: list[str] = Field(default_factory=list)
    review_task_ids: list[str] = Field(default_factory=list)
    next_action: Literal["continue", "review", "stop"] = "continue"


class AgentTrace(BaseModel):
    id: str
    run_id: str
    agent: AgentRole
    step: str
    selected_tools: list[str] = Field(default_factory=list)
    decision: str
    reason_codes: list[str] = Field(default_factory=list)
    input_ids: list[str] = Field(default_factory=list)
    output_ids: list[str] = Field(default_factory=list)
    model_fingerprint: str | None = None
    token_usage: int | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)
    status: Literal["succeeded", "failed", "skipped"] = "succeeded"
    created_at: datetime = Field(default_factory=utc_now)


class EntityAdviceRequest(BaseModel):
    mention: EntityMention
    candidates: list[EntityCandidate]
    candidate_entities: list[CanonicalEntity]


class EntityAdvice(BaseModel):
    action: Literal["link", "review", "nil"]
    selected_entity_id: str | None = None
    reason_code: str


class FusionAdviceRequest(BaseModel):
    left: CandidateClaim
    right: CandidateClaim


class FusionAdvice(BaseModel):
    decision: Literal["support", "conflict", "related", "uncertain"]
    reason_code: str
