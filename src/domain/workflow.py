"""Provider request contracts and persisted workflow state."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.domain.agents import AgentHandoff, AgentTrace
from src.domain.cases import ReflectionAttempt, RetrievedCase
from src.domain.documents import (
    DocumentIR,
    EvidenceRef,
    MediaAsset,
    TextBlock,
    VisualObservation,
)
from src.domain.knowledge import (
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
from src.domain.schema import OutputSchema
from src.domain.validation import ValidationResult, ValidationReviewDecision


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
    provider: Literal["llm", "vlm", "governance", "fusion"]
    operation_id: str
    requested_model: str
    response_model: str | None = None
    request_id: str | None = None
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
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
    original_candidates: list[CandidateClaim] = Field(default_factory=list)
    superseded_review_tasks: list[ReviewTask] = Field(default_factory=list)
    review_sync_pending: bool = False
    pending_correction_id: str | None = None
    correction_tail_only: bool = False

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
    case_mode: Literal["none", "good", "good_bad"] = "none"
    case_snapshot_fingerprint: str = "cases:disabled"
    case_snapshot_ids: list[str] = Field(default_factory=list)
    case_retrieval_policy_version: str | None = None
    reflection_enabled: bool = False
    reflection_provider_name: str = "disabled"
    reflection_provider_fingerprint: str = "reflection:disabled"
    reflection_policy_version: str | None = None
    reflection_max_attempts: int = 0
    reflection_token_budget: int = 0
    reflection_time_budget_seconds: float = 0.0
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
    retrieved_cases: list[RetrievedCase] = Field(default_factory=list)
    reflection_attempts: list[ReflectionAttempt] = Field(default_factory=list)
    repaired_issue_ids: list[str] = Field(default_factory=list)
    reflection_token_usage: int = 0
    reflection_elapsed_ms: float = 0.0
    semantic_advisor_name: str = "disabled"
    semantic_advisor_fingerprint: str = "semantic:disabled"
    agent_policy_version: str | None = None
    agent_token_budget: int = 0
    agent_token_usage: int = 0
    agent_traces: list[AgentTrace] = Field(default_factory=list)
    agent_handoffs: list[AgentHandoff] = Field(default_factory=list)
    agent_review_claim_ids: list[str] = Field(default_factory=list)
    modality_status: dict[str, Literal["pending", "skipped", "succeeded", "failed"]] = Field(
        default_factory=dict
    )
    modality_errors: dict[str, str] = Field(default_factory=dict)
    review_workspace: bool = False
    submission_confirmed: bool = False
