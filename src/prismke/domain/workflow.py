"""Provider request contracts and persisted workflow state."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from prismke.domain.documents import DocumentIR
from prismke.domain.knowledge import (
    CandidateClaim,
    CanonicalEntity,
    Claim,
    ConflictSet,
    GraphCommit,
    GraphRevision,
    ReviewTask,
)
from prismke.domain.schema import OutputSchema


class ExtractionRequest(BaseModel):
    document: DocumentIR
    output_schema: OutputSchema = Field(alias="schema")

    model_config = ConfigDict(populate_by_name=True)


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
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    run_id: str
    input_path: str
    schema_path: str
    provider_name: str = "mock"
    provider_fingerprint: str = "legacy"
    pipeline_version: str = "0.1.1"
    current_node: str = "ingest"
    failed_node: str | None = None
    status: Literal["running", "awaiting_review", "completed", "failed"] = "running"
    document: DocumentIR | None = None
    output_schema: OutputSchema | None = Field(default=None, alias="schema")
    candidates: list[CandidateClaim] = Field(default_factory=list)
    entities: list[CanonicalEntity] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    conflicts: list[ConflictSet] = Field(default_factory=list)
    review_tasks: list[ReviewTask] = Field(default_factory=list)
    graph_commit: GraphCommit | None = None
    revision: GraphRevision | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    retry_count: int = 0
