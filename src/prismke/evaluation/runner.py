"""Run a public evaluation manifest through the application service."""

from __future__ import annotations

from pathlib import Path

import orjson

from prismke.domain import CoordinateSpace, SchemaIndex, WorkflowState, normalize_label
from prismke.evaluation.models import (
    EvaluationCase,
    EvaluationCaseResult,
    EvaluationManifest,
    EvaluationReport,
)
from prismke.workflow import PrismKEService


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _safe_error(exc: Exception, service: PrismKEService) -> str:
    message = f"{type(exc).__name__}:{exc}"
    secrets = (service.settings.llm_api_key, service.settings.vlm_api_key)
    for secret in secrets:
        if secret:
            message = message.replace(secret, "***")
    return message


def _canonical_entity_name(value: str, schema: SchemaIndex | None) -> str:
    if schema is None:
        return _normalize(value)
    normalized = normalize_label(value)
    matches = {
        item.name
        for item in schema.schema.entity_catalog
        if normalized in {normalize_label(name) for name in [item.name, *item.aliases]}
    }
    return _normalize(next(iter(matches))) if len(matches) == 1 else _normalize(value)


def _canonical_claim(
    subject: str,
    relation: str,
    obj: str,
    schema: SchemaIndex | None,
) -> tuple[str, str, str]:
    canonical_subject = _canonical_entity_name(subject, schema)
    canonical_object = _canonical_entity_name(obj, schema)
    if schema is None:
        return canonical_subject, _normalize(relation), canonical_object
    relation_def = schema.relation(relation)
    if relation_def is None:
        return canonical_subject, _normalize(relation), canonical_object
    relation_id = relation_def.id
    if relation_def.symmetric:
        canonical_subject, canonical_object = sorted((canonical_subject, canonical_object))
    elif relation_def.inverse_relation:
        canonical_relation = min(relation_id, relation_def.inverse_relation)
        if relation_id != canonical_relation:
            canonical_subject, canonical_object = canonical_object, canonical_subject
        relation_id = canonical_relation
    return canonical_subject, _normalize(relation_id), canonical_object


def _predicted_claims(
    state: WorkflowState, schema: SchemaIndex | None
) -> set[tuple[str, str, str]]:
    entities = {entity.id: entity.name for entity in state.entities}
    predicted: set[tuple[str, str, str]] = set()
    for claim in state.claims:
        subject = entities.get(claim.subject_id, claim.subject_id)
        obj = (
            entities.get(claim.object_entity_id, claim.object_entity_id)
            if claim.object_entity_id
            else claim.object_literal
        )
        if obj is not None:
            predicted.add(_canonical_claim(subject, claim.relation_id, obj, schema))
    return predicted


def _gold_claims(case: EvaluationCase, schema: SchemaIndex | None) -> set[tuple[str, str, str]]:
    return {
        _canonical_claim(item.subject, item.relation, item.object, schema) for item in case.claims
    }


def _entity_names(claims: set[tuple[str, str, str]]) -> set[str]:
    return {value for subject, _, obj in claims for value in (subject, obj)}


def _case_result(case: EvaluationCase, state: WorkflowState) -> EvaluationCaseResult:
    schema = SchemaIndex(state.output_schema) if state.output_schema else None
    predicted = _predicted_claims(state, schema)
    gold = _gold_claims(case, schema)
    predicted_entities = _entity_names(predicted)
    gold_entities = _entity_names(gold)
    evidence = state.document.evidence if state.document else []
    bboxes = [item for item in evidence if item.bbox is not None]
    valid_bboxes = 0
    for item in bboxes:
        assert item.bbox is not None
        if item.coordinate_space != CoordinateSpace.NORMALIZED or all(
            0 <= value <= 1 for value in (item.bbox.x0, item.bbox.y0, item.bbox.x1, item.bbox.y1)
        ):
            valid_bboxes += 1
    decisions = {item.decision for item in state.alignment_records}
    localization = {
        item.localization_level.value for item in evidence if item.localization_level is not None
    }
    calls = state.provider_calls
    return EvaluationCaseResult(
        id=case.id,
        status=state.status,
        claim_true_positive=len(predicted & gold),
        claim_false_positive=len(predicted - gold),
        claim_false_negative=len(gold - predicted),
        entity_true_positive=len(predicted_entities & gold_entities),
        entity_false_positive=len(predicted_entities - gold_entities),
        entity_false_negative=len(gold_entities - predicted_entities),
        evidence_claims=sum(bool(claim.evidence_ids) for claim in state.claims),
        total_claims=len(state.claims),
        valid_bboxes=valid_bboxes,
        total_bboxes=len(bboxes),
        alignment_passed=set(case.expected_alignment_decisions) <= decisions,
        localization_passed=set(case.expected_localization_levels) <= localization,
        provider_calls=len(calls),
        input_tokens=sum(item.input_tokens for item in calls if item.input_tokens is not None),
        output_tokens=sum(item.output_tokens for item in calls if item.output_tokens is not None),
        unknown_usage_calls=sum(item.total_tokens is None for item in calls),
        latency_ms=round(sum(item.latency_ms for item in calls), 3),
        estimated_cost_cny=round(sum(item.estimated_cost_cny or 0.0 for item in calls), 8),
    )


async def evaluate_manifest(
    manifest_path: Path,
    service: PrismKEService,
    *,
    provider_name: str,
    ocr_provider_name: str,
    vlm_provider_name: str,
) -> EvaluationReport:
    """Evaluate every case and keep failures isolated to their case."""

    manifest_path = manifest_path.resolve()
    root = manifest_path.parent
    manifest = EvaluationManifest.model_validate(orjson.loads(manifest_path.read_bytes()))
    schema_path = (root / manifest.schema_path).resolve()
    results: list[EvaluationCaseResult] = []
    for case in manifest.cases:
        try:
            state = await service.run(
                (root / case.input).resolve(),
                schema_path,
                provider_name,
                ocr_provider_name,
                vlm_provider_name,
            )
            results.append(_case_result(case, state))
        except Exception as exc:
            results.append(
                EvaluationCaseResult(
                    id=case.id,
                    status="failed",
                    error=_safe_error(exc, service),
                )
            )
    claim_tp = sum(item.claim_true_positive for item in results)
    claim_fp = sum(item.claim_false_positive for item in results)
    claim_fn = sum(item.claim_false_negative for item in results)
    entity_tp = sum(item.entity_true_positive for item in results)
    entity_fp = sum(item.entity_false_positive for item in results)
    entity_fn = sum(item.entity_false_negative for item in results)
    claim_precision = _safe_ratio(claim_tp, claim_tp + claim_fp)
    claim_recall = _safe_ratio(claim_tp, claim_tp + claim_fn)
    entity_precision = _safe_ratio(entity_tp, entity_tp + entity_fp)
    entity_recall = _safe_ratio(entity_tp, entity_tp + entity_fn)
    total_claims = sum(item.total_claims for item in results)
    total_bboxes = sum(item.total_bboxes for item in results)
    return EvaluationReport(
        manifest_version=manifest.version,
        requested_model=service.settings.vlm_model,
        cases=results,
        completed_cases=sum(item.status != "failed" for item in results),
        failed_cases=sum(item.status == "failed" for item in results),
        claim_precision=round(claim_precision, 6),
        claim_recall=round(claim_recall, 6),
        claim_f1=round(_f1(claim_precision, claim_recall), 6),
        entity_precision=round(entity_precision, 6),
        entity_recall=round(entity_recall, 6),
        entity_f1=round(_f1(entity_precision, entity_recall), 6),
        evidence_coverage=round(
            _safe_ratio(sum(item.evidence_claims for item in results), total_claims), 6
        ),
        bbox_validity=round(
            _safe_ratio(sum(item.valid_bboxes for item in results), total_bboxes), 6
        ),
        scenario_pass_rate=round(
            _safe_ratio(
                sum(item.alignment_passed and item.localization_passed for item in results),
                len(results),
            ),
            6,
        ),
        provider_calls=sum(item.provider_calls for item in results),
        input_tokens=sum(item.input_tokens for item in results),
        output_tokens=sum(item.output_tokens for item in results),
        unknown_usage_calls=sum(item.unknown_usage_calls for item in results),
        latency_ms=round(sum(item.latency_ms for item in results), 3),
        estimated_cost_cny=round(sum(item.estimated_cost_cny for item in results), 8),
    )
