"""Task modes and portable extraction-only result contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from src.domain.documents import EvidenceRef
from src.domain.knowledge import CandidateClaim, CanonicalEntity, EntityMention, utc_now
from src.domain.validation import ValidationIssue


class TaskMode(StrEnum):
    ENTITY_EXTRACTION = "entity_extraction"
    RELATION_EXTRACTION = "relation_extraction"
    SCHEMA_INFORMATION_EXTRACTION = "schema_information_extraction"
    JOINT_ENTITY_RELATION_EXTRACTION = "joint_entity_relation_extraction"
    JOINT_ENTITY_RELATION_DISAMBIGUATION = "joint_entity_relation_disambiguation"
    KNOWLEDGE_GRAPH_CONSTRUCTION = "knowledge_graph_construction"

    @property
    def permits_graph_commit(self) -> bool:
        return self is TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION

    @property
    def resolves_entities(self) -> bool:
        return self in {
            TaskMode.JOINT_ENTITY_RELATION_DISAMBIGUATION,
            TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION,
        }


class EntitySourceMode(StrEnum):
    PROVIDED = "provided"
    AUTO = "auto"


class ProvidedEntity(BaseModel):
    name: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_span(self) -> ProvidedEntity:
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("provided entity ranges require both char_start and char_end")
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_start >= self.char_end
        ):
            raise ValueError("provided entity char_start must be less than char_end")
        return self


class CandidateAttribute(BaseModel):
    id: str
    subject: EntityMention
    field: str = Field(min_length=1)
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(min_length=1)


class CandidateEventArgument(BaseModel):
    role: str = Field(min_length=1)
    value: EntityMention | str
    evidence_ids: list[str] = Field(default_factory=list)


class CandidateEvent(BaseModel):
    id: str
    event_type: str = Field(min_length=1)
    trigger: str = Field(min_length=1)
    arguments: list[CandidateEventArgument] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(min_length=1)


class ExtractionReviewEvent(BaseModel):
    id: str
    request_id: str
    target_type: str
    target_id: str
    decision: str
    reviewer: str = Field(min_length=1)
    reason: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class TaskExtractionResult(BaseModel):
    task_mode: TaskMode
    entity_source_mode: EntitySourceMode = EntitySourceMode.AUTO
    entities: list[EntityMention] = Field(default_factory=list)
    canonical_entities: list[CanonicalEntity] = Field(default_factory=list)
    mention_to_entity: dict[str, str] = Field(default_factory=dict)
    relations: list[CandidateClaim] = Field(default_factory=list)
    attributes: list[CandidateAttribute] = Field(default_factory=list)
    events: list[CandidateEvent] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    review_required_ids: list[str] = Field(default_factory=list)
    review_events: list[ExtractionReviewEvent] = Field(default_factory=list)
    version: int = 0
