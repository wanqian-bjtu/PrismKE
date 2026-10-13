"""Versioned media knowledge contracts kept separate from raw visual observations."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from src.domain.documents import BBox


def utc_now() -> datetime:
    return datetime.now(UTC)


def visual_value_matches(value: Any, value_type: str) -> bool:
    expected = value_type.casefold()
    if expected in {"string", "str", "text"}:
        return isinstance(value, str)
    if expected in {"integer", "int"}:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected in {"number", "float"}:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected in {"boolean", "bool"}:
        return isinstance(value, bool)
    if expected in {"object", "dict"}:
        return isinstance(value, dict)
    if expected in {"array", "list"}:
        return isinstance(value, list)
    return False


class MediaKnowledgeType(StrEnum):
    IMAGE = "image"
    CHART = "chart"
    TABLE = "table"
    FORMULA = "formula"
    PAGE_RENDER = "page_render"


class MediaRelationType(StrEnum):
    DEPICTS = "DEPICTS"
    SUPPORTS = "SUPPORTS"


class VisualAssertionKind(StrEnum):
    ATTRIBUTE = "attribute"
    COUNT = "count"
    SPATIAL_RELATION = "spatial_relation"


class GraphMediaContent(BaseModel):
    id: str
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    blob_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    media_type: str
    asset_type: MediaKnowledgeType
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    created_at: datetime = Field(default_factory=utc_now)


class GraphMediaOccurrence(BaseModel):
    id: str
    document_id: str
    media_content_id: str
    evidence_id: str
    page_number: int | None = Field(default=None, ge=1)
    bbox: BBox | None = None
    canvas_width: float | None = Field(default=None, gt=0)
    canvas_height: float | None = Field(default=None, gt=0)
    caption: str = ""
    source_type: str
    active: bool = True
    tx_from: datetime = Field(default_factory=utc_now)
    tx_to: datetime | None = None

    @model_validator(mode="after")
    def validate_coordinates(self) -> GraphMediaOccurrence:
        if self.bbox is not None:
            if self.canvas_width is None or self.canvas_height is None:
                raise ValueError("media occurrence bbox requires canvas dimensions")
            if self.bbox.x1 > self.canvas_width or self.bbox.y1 > self.canvas_height:
                raise ValueError("media occurrence bbox exceeds canvas")
        return self


class CandidateMediaRelation(BaseModel):
    id: str
    occurrence_id: str
    relation_type: MediaRelationType
    target_mention_id: str | None = None
    target_entity_id: str | None = None
    target_claim_id: str | None = None
    evidence_ids: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_target(self) -> CandidateMediaRelation:
        targets = [self.target_mention_id, self.target_entity_id, self.target_claim_id]
        if sum(item is not None for item in targets) != 1:
            raise ValueError("candidate media relation requires exactly one target")
        return self


class GraphMediaRelation(BaseModel):
    id: str
    occurrence_id: str
    relation_type: MediaRelationType
    target_entity_id: str | None = None
    target_claim_id: str | None = None
    evidence_ids: list[str] = Field(min_length=1)
    source_candidate_id: str | None = None
    approved_review_event_id: str | None = None
    active: bool = True
    tx_from: datetime = Field(default_factory=utc_now)
    tx_to: datetime | None = None

    @model_validator(mode="after")
    def validate_target(self) -> GraphMediaRelation:
        if (self.target_entity_id is None) == (self.target_claim_id is None):
            raise ValueError("media relation requires exactly one graph target")
        if self.relation_type is MediaRelationType.DEPICTS and self.target_entity_id is None:
            raise ValueError("DEPICTS requires an entity target")
        if self.relation_type is MediaRelationType.SUPPORTS and self.target_claim_id is None:
            raise ValueError("SUPPORTS requires a claim target")
        return self


class CandidateVisualAssertion(BaseModel):
    id: str
    occurrence_id: str
    subject_mention_id: str | None = None
    subject_entity_id: str | None = None
    predicate: str = Field(min_length=1)
    normalized_value: Any
    value_type: str = "string"
    assertion_kind: VisualAssertionKind = VisualAssertionKind.ATTRIBUTE
    evidence_ids: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_subject(self) -> CandidateVisualAssertion:
        if (self.subject_mention_id is None) == (self.subject_entity_id is None):
            raise ValueError("candidate visual assertion requires one subject")
        return self


class VisualAssertion(BaseModel):
    id: str
    occurrence_id: str
    subject_entity_id: str
    predicate: str = Field(min_length=1)
    normalized_value: Any
    value_type: str = "string"
    assertion_kind: VisualAssertionKind = VisualAssertionKind.ATTRIBUTE
    evidence_ids: list[str] = Field(min_length=1)
    source_candidate_id: str
    approved_review_event_id: str
    active: bool = True
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    tx_from: datetime = Field(default_factory=utc_now)
    tx_to: datetime | None = None


class VisualReviewTask(BaseModel):
    id: str
    run_id: str
    target_type: Literal["media_relation", "visual_assertion"]
    target_id: str
    reasons: list[str] = Field(min_length=1)
    status: Literal["pending", "resolved"] = "pending"
    decision: Literal["approve", "reject", "defer"] | None = None
    reviewer: str | None = None
    reason: str | None = None
    version: int = 0
    last_event_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None


class VisualReviewEvent(BaseModel):
    id: str
    request_id: str
    run_id: str
    task_id: str
    target_type: Literal["media_relation", "visual_assertion"]
    target_id: str
    decision: Literal["approve", "reject", "defer"]
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    expected_version: int = Field(ge=0)
    resulting_version: int = Field(ge=1)
    created_at: datetime = Field(default_factory=utc_now)
