"""Stable public data contracts shared by every PrismKE component."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class Modality(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    OCR = "ocr"
    TABLE = "table"
    CHART = "chart"


class EvidenceKind(StrEnum):
    TEXT_SPAN = "text_span"
    PDF_BBOX = "pdf_bbox"
    IMAGE = "image"
    VISUAL_REGION = "visual_region"


class ClaimStatus(StrEnum):
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class BBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class SourceDocument(BaseModel):
    path: Path
    media_type: str | None = None


class TextBlock(BaseModel):
    id: str
    text: str
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    bbox: BBox | None = None
    evidence_id: str


class MediaAsset(BaseModel):
    id: str
    path: str
    media_type: str
    width: int | None = None
    height: int | None = None
    page_number: int | None = None
    evidence_id: str


class EvidenceRef(BaseModel):
    id: str
    kind: EvidenceKind
    document_id: str
    source_hash: str
    modality: Modality
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    bbox: BBox | None = None
    media_asset_id: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None


class DocumentIR(BaseModel):
    id: str
    source_path: str
    source_hash: str
    media_type: str
    text_blocks: list[TextBlock] = Field(default_factory=list)
    media_assets: list[MediaAsset] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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
    created_at: datetime = Field(default_factory=utc_now)


class CandidateClaim(BaseModel):
    id: str
    subject: EntityMention
    relation: str
    object: EntityMention | str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(min_length=1)
    qualifiers: dict[str, Any] = Field(default_factory=dict)


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
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    tx_from: datetime = Field(default_factory=utc_now)
    tx_to: datetime | None = None

    @model_validator(mode="after")
    def exactly_one_object(self) -> Claim:
        if (self.object_entity_id is None) == (self.object_literal is None):
            raise ValueError("exactly one claim object representation is required")
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


class GraphRevision(BaseModel):
    id: str
    run_id: str
    parent_id: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class EntityTypeDef(BaseModel):
    id: str
    aliases: list[str] = Field(default_factory=list)


class RelationDef(BaseModel):
    id: str
    aliases: list[str] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)
    range: list[str] = Field(default_factory=list)


class EntityCatalogItem(BaseModel):
    id: str
    name: str
    type: str
    aliases: list[str] = Field(default_factory=list)


class OutputSchema(BaseModel):
    schema_id: str
    version: str
    strict: bool = True
    entity_types: list[EntityTypeDef]
    relations: list[RelationDef]
    entity_catalog: list[EntityCatalogItem] = Field(default_factory=list)


class ExtractionRequest(BaseModel):
    document: DocumentIR
    schema: OutputSchema


class VisualExtractionRequest(ExtractionRequest):
    pass


class ExtractionResult(BaseModel):
    candidates: list[CandidateClaim] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ResolutionDecision(BaseModel):
    mention_id: str
    entity: CanonicalEntity
    method: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool = False


class WorkflowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    input_path: str
    schema_path: str
    provider_name: str = "mock"
    current_node: str = "ingest"
    status: Literal["running", "awaiting_review", "completed", "failed"] = "running"
    document: DocumentIR | None = None
    schema: OutputSchema | None = None
    candidates: list[CandidateClaim] = Field(default_factory=list)
    entities: list[CanonicalEntity] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    conflicts: list[ConflictSet] = Field(default_factory=list)
    review_tasks: list[ReviewTask] = Field(default_factory=list)
    revision: GraphRevision | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    retry_count: int = 0
