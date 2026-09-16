"""Provider request contracts and persisted workflow state."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from prismke.domain.documents import (
    DocumentIR,
    EvidenceRef,
    MediaAsset,
    TextBlock,
    VisualObservation,
)
from prismke.domain.knowledge import (
    AlignmentRecord,
    CandidateClaim,
    CanonicalEntity,
    Claim,
    ConflictSet,
    EntityResolutionDecision,
    EntityReviewTask,
    GraphCommit,
    GraphRevision,
    ReviewTask,
)
from prismke.domain.schema import OutputSchema
from prismke.domain.validation import ValidationResult, ValidationReviewDecision


class ExtractionRequest(BaseModel):
    document: DocumentIR
    output_schema: OutputSchema = Field(alias="schema")

    model_config = ConfigDict(populate_by_name=True)


class VisualExtractionRequest(ExtractionRequest):
    asset: MediaAsset
    ocr_blocks: list[TextBlock] = Field(default_factory=list)


class ProviderCallRecord(BaseModel):
    """Sanitized metadata for one external model request."""

    id: str
    provider: Literal["llm", "vlm"]
    operation_id: str
    requested_model: str
    response_model: str | None = None
    request_id: str | None = None
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    latency_ms: float = Field(ge=0.0)
    retry_count: int = Field(default=0, ge=0)
    status: Literal["succeeded", "failed"]
    error_code: str | None = None
    prompt_version: str
    estimated_cost_cny: float | None = Field(default=None, ge=0.0)
    pricing_snapshot: str | None = None


class ExtractionResult(BaseModel):
    candidates: list[CandidateClaim] = Field(default_factory=list)
    observations: list[VisualObservation] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    call_records: list[ProviderCallRecord] = Field(default_factory=list)
    validation: ValidationResult = Field(default_factory=ValidationResult)


class OCRRequest(BaseModel):
    document: DocumentIR


class OCRResult(BaseModel):
    text_blocks: list[TextBlock] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ResolutionDecision(BaseModel):
    mention_id: str
    entity: CanonicalEntity
    method: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool = False


class WorkflowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    run_id: str
    input_path: str
    schema_path: str
    provider_name: str = "mock"
    provider_fingerprint: str = "legacy"
    ocr_provider_name: str = "disabled"
    ocr_provider_fingerprint: str = "disabled"
    vlm_provider_name: str = "disabled"
    vlm_provider_fingerprint: str = "disabled"
    embedding_provider_name: str = "disabled"
    embedding_provider_fingerprint: str = "disabled"
    allow_remote_assets: bool = False
    pipeline_version: str = "0.4.0"
    entity_resolution_policy_version: str | None = None
    current_node: str = "ingest"
    failed_node: str | None = None
    status: Literal["running", "awaiting_review", "completed", "failed"] = "running"
    document: DocumentIR | None = None
    output_schema: OutputSchema | None = Field(default=None, alias="schema")
    candidates: list[CandidateClaim] = Field(default_factory=list)
    text_candidates: list[CandidateClaim] = Field(default_factory=list)
    visual_candidates: list[CandidateClaim] = Field(default_factory=list)
    alignment_records: list[AlignmentRecord] = Field(default_factory=list)
    entities: list[CanonicalEntity] = Field(default_factory=list)
    mention_to_entity: dict[str, str] = Field(default_factory=dict)
    entity_resolution_decisions: list[EntityResolutionDecision] = Field(default_factory=list)
    entity_review_tasks: list[EntityReviewTask] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    conflicts: list[ConflictSet] = Field(default_factory=list)
    review_tasks: list[ReviewTask] = Field(default_factory=list)
    normalization_issues: dict[str, str] = Field(default_factory=dict)
    validation: ValidationResult = Field(default_factory=ValidationResult)
    validation_decisions: list[ValidationReviewDecision] = Field(default_factory=list)
    graph_commit: GraphCommit | None = None
    revision: GraphRevision | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    retry_count: int = 0
    provider_calls: list[ProviderCallRecord] = Field(default_factory=list)
    review_workspace: bool = False
    submission_confirmed: bool = False
