"""Entities, claims, reviews, conflicts, and graph transactions."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from prismke.domain.documents import EvidenceRef, Modality


def utc_now() -> datetime:
    return datetime.now(UTC)


class ClaimStatus(StrEnum):
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class EntityMention(BaseModel):
    id: str
    name: str
    entity_type: str
    context: str = ""
    modality: Modality = Modality.TEXT
    evidence_ids: list[str] = Field(min_length=1)


class CanonicalEntity(BaseModel):
    id: str
    name: str
    entity_type: str
    aliases: list[str] = Field(default_factory=list)
    active: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class CandidateClaim(BaseModel):
    id: str
    subject: EntityMention
    relation: str
    object: EntityMention | str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(min_length=1)
    qualifiers: dict[str, Any] = Field(default_factory=dict)
    modalities: list[Modality] = Field(default_factory=lambda: [Modality.TEXT])
    source_tool: str = "text_extraction"
    visual_observation_ids: list[str] = Field(default_factory=list)
    cross_modal_support: bool = False
    coarse_visual_evidence: bool = False
    context_only_visual_claim: bool = False


class AlignmentRecord(BaseModel):
    id: str
    candidate_ids: list[str] = Field(min_length=1)
    modalities: list[Modality] = Field(min_length=1)
    decision: Literal["support", "conflict", "related", "independent"]
    confidence_before: list[float] = Field(default_factory=list)
    confidence_after: float | None = Field(default=None, ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    id: str
    subject_id: str
    relation_id: str
    object_entity_id: str | None = None
    object_literal: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    status: ClaimStatus = ClaimStatus.PENDING
    evidence_ids: list[str] = Field(min_length=1)
    source_candidate_ids: list[str] = Field(default_factory=list)
    qualifiers: dict[str, Any] = Field(default_factory=dict)
    cross_modal_support: bool = False
    coarse_visual_evidence: bool = False
    context_only_visual_claim: bool = False
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    tx_from: datetime = Field(default_factory=utc_now)
    tx_to: datetime | None = None

    @model_validator(mode="after")
    def validate_claim(self) -> Claim:
        if (self.object_entity_id is None) == (self.object_literal is None):
            raise ValueError("exactly one claim object representation is required")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("valid_from must not be later than valid_to")
        return self


class ConflictSet(BaseModel):
    id: str
    claim_ids: list[str] = Field(min_length=2)
    reason: str
    status: Literal["open", "resolved"] = "open"


class ReviewTask(BaseModel):
    id: str
    run_id: str
    claim_id: str
    reasons: list[str] = Field(min_length=1)
    status: Literal["pending", "resolved"] = "pending"
    decision: ReviewDecision | None = None
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None


class GraphDocument(BaseModel):
    """Portable document metadata stored in a graph backend."""

    id: str
    filename: str
    content_hash: str
    media_type: str
    imported_at: datetime = Field(default_factory=utc_now)


class GraphChange(BaseModel):
    resource_type: Literal["entity", "claim", "conflict"]
    resource_id: str
    action: Literal["create", "update", "close", "restore"]
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None


class GraphRevision(BaseModel):
    id: str
    run_id: str
    parent_id: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
    changes: list[GraphChange] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class GraphCommit(BaseModel):
    documents: list[GraphDocument] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    entities: list[CanonicalEntity] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    conflicts: list[ConflictSet] = Field(default_factory=list)
    revision: GraphRevision


class GraphHealth(BaseModel):
    backend: Literal["json", "neo4j"]
    healthy: bool
    message: str = "ok"


class GraphNeighborhood(BaseModel):
    center_entity_id: str
    depth: int = Field(default=1, ge=1, le=3)
    entities: list[CanonicalEntity] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)


class RevisionDiff(BaseModel):
    from_revision_id: str
    to_revision_id: str
    changes: list[GraphChange] = Field(default_factory=list)
    legacy_id_only: bool = False
    entity_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
