"""Evaluation manifest and report models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GoldClaim(BaseModel):
    subject: str
    relation: str
    object: str


class EvaluationCase(BaseModel):
    id: str
    input: str
    language: str
    scenarios: list[str] = Field(default_factory=list)
    claims: list[GoldClaim] = Field(default_factory=list)
    expected_alignment_decisions: list[str] = Field(default_factory=list)
    expected_localization_levels: list[str] = Field(default_factory=list)


class EvaluationManifest(BaseModel):
    version: str
    schema_path: str
    cases: list[EvaluationCase] = Field(min_length=1)


class EvaluationCaseResult(BaseModel):
    id: str
    status: str
    error: str | None = None
    claim_true_positive: int = 0
    claim_false_positive: int = 0
    claim_false_negative: int = 0
    entity_true_positive: int = 0
    entity_false_positive: int = 0
    entity_false_negative: int = 0
    evidence_claims: int = 0
    total_claims: int = 0
    valid_bboxes: int = 0
    total_bboxes: int = 0
    alignment_passed: bool = False
    localization_passed: bool = False
    provider_calls: int = 0
    unknown_usage_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    estimated_cost_cny: float = 0.0


class EvaluationReport(BaseModel):
    manifest_version: str
    requested_model: str | None = None
    cases: list[EvaluationCaseResult]
    completed_cases: int
    failed_cases: int
    claim_precision: float
    claim_recall: float
    claim_f1: float
    entity_precision: float
    entity_recall: float
    entity_f1: float
    evidence_coverage: float
    bbox_validity: float
    scenario_pass_rate: float
    provider_calls: int
    unknown_usage_calls: int = 0
    input_tokens: int
    output_tokens: int
    latency_ms: float
    estimated_cost_cny: float
    pricing_note: str = "估算值，仅用于实验比较；实际费用以阿里云账单为准。"
