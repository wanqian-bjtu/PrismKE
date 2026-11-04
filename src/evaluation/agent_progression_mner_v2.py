"""Post-hoc reject-only MNER governance gate and chained fusion evaluation."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from statistics import mean
from typing import Any, Literal, cast

from src.core.ids import canonical_hash, file_sha256
from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.evaluation import agent_progression as v1_agent
from src.evaluation import component_ablation as v1
from src.evaluation import component_ablation_v4 as v4
from src.evaluation import twitter2017 as twitter

StageName = Literal["dev", "holdout", "main"]

EXPERIMENT_VERSION = "agent-progression-mner-governance-v2"
GATE_POLICY_VERSION = "twitter-governance-reject-only-v2"
FUSION_PROMPT_VERSION = "v3"
SEED = 2027
BOOTSTRAP_SAMPLES = 10_000
EXPECTED_CASES: dict[StageName, int] = {"dev": 100, "holdout": 623, "main": 723}
VARIANTS = ("extraction", "governance_v2", "fusion_review_v2")
VARIANT_LABELS = {
    "extraction": "Extraction Agent Only",
    "governance_v2": "+ Governance Reject Gate V2",
    "fusion_review_v2": "+ Fusion/Review V2",
}


class MnerV2BudgetLedger(v1.AblationBudgetLedger):
    """Independent five-CNY ledger with three and 4.5 CNY snapshots."""

    def record(self, operation_id: str, record: ProviderCallRecord) -> list[float]:
        before = self.cost
        crossed = super().record(operation_id, record)
        for milestone in (3.0, 4.5):
            if before < milestone <= self.cost and milestone not in self.payload["milestones"]:
                self.payload["milestones"].append(milestone)
                crossed.append(milestone)
        self.persist()
        return sorted(crossed)


def _settings_fingerprint(settings: Settings) -> dict[str, Any]:
    return {
        "llm_model": settings.llm_model,
        "vlm_model": settings.vlm_model,
        "temperature": 0,
        "max_output_tokens": 1024,
        "embedding_model": settings.embedding_model,
        "embedding_revision": settings.embedding_model_revision,
    }


def _artifact_name(case_id: str) -> str:
    return case_id.replace(":", "-") + ".json"


def _prediction_directory(
    root: Path, stage: StageName, variant: str, version: str | None = None
) -> Path:
    base = root / stage / "twitter2017" / variant
    return (base / f"prompt-{version}" if version else base) / "predictions"


def _report_path(root: Path, stage: StageName, variant: str, version: str | None = None) -> Path:
    return _prediction_directory(root, stage, variant, version).parent / "report.json"


def _prediction_set_hash(directory: Path) -> str:
    files = sorted(directory.glob("*.json"), key=lambda path: path.name)
    return canonical_hash([{"name": path.name, "sha256": file_sha256(path)} for path in files])


def _budget_cost(output: Path) -> float:
    path = output / "budget.json"
    if not path.exists():
        return 0.0
    return float(v1.load_json(path).get("estimated_cost_cny", 0.0))


def _source_root(output: Path) -> Path:
    return Path(str(v1.load_json(output / "manifest.json")["source_experiment"]))


def _source_manifest(output: Path) -> dict[str, Any]:
    return dict(v1.load_json(_source_root(output) / "manifest.json"))


def _twitter_source(output: Path) -> Path:
    return Path(str(_source_manifest(output)["twitter_source"]))


def _stage_cases(output: Path, stage: StageName) -> list[twitter.TwitterCase]:
    source = _source_root(output)
    cases = v1_agent._stage_cases(source, _twitter_source(output), "twitter2017", stage)
    typed = [cast(twitter.TwitterCase, case) for case in cases]
    if len(typed) != EXPECTED_CASES[stage]:
        raise RuntimeError(f"unexpected Twitter-2017 {stage} case count")
    return typed


def _source_record(
    output: Path,
    stage: StageName,
    variant: str,
    case_id: str,
    version: str | None = None,
) -> dict[str, Any]:
    path = _prediction_directory(_source_root(output), stage, variant, version) / _artifact_name(
        case_id
    )
    if not path.exists():
        raise RuntimeError(f"missing source prediction: {path}")
    return dict(v1.load_json(path))


def _v2_record(output: Path, stage: StageName, variant: str, case_id: str) -> dict[str, Any]:
    path = _prediction_directory(output, stage, variant) / _artifact_name(case_id)
    if not path.exists():
        raise RuntimeError(f"missing V2 prediction: {path}")
    return dict(v1.load_json(path))


def prepare_experiment(
    output: Path,
    source_experiment: Path,
    twitter_schema_path: Path,
    settings: Settings,
) -> dict[str, Any]:
    """Freeze the V1 prediction sources and the deterministic V2 gate."""
    source_manifest = dict(v1.load_json(source_experiment / "manifest.json"))
    source_frozen = dict(v1.load_json(source_experiment / "frozen-config.json"))
    if source_manifest.get("experiment_version") != v1_agent.EXPERIMENT_VERSION:
        raise RuntimeError("source experiment is not agent-progression-v1")
    twitter_selection = source_frozen.get("datasets", {}).get("twitter2017", {})
    if twitter_selection.get("governance_prompt_version") != "v1":
        raise RuntimeError("source MNER governance prompt is not frozen to v1")
    if twitter_selection.get("fusion_review_prompt_version") != FUSION_PROMPT_VERSION:
        raise RuntimeError("source MNER fusion prompt is not frozen to v3")

    schema = twitter.load_schema(twitter_schema_path)
    settings_payload = _settings_fingerprint(settings)
    if source_manifest.get("settings_hash") != canonical_hash(settings_payload):
        raise RuntimeError("current model settings differ from the frozen V1 settings")
    if source_manifest.get("schemas", {}).get("twitter2017", {}).get("hash") != canonical_hash(
        schema
    ):
        raise RuntimeError("Twitter schema differs from the frozen V1 schema")
    source_hashes: dict[str, Any] = {
        "manifest": canonical_hash(source_manifest),
        "frozen_config": canonical_hash(source_frozen),
        "stages": {},
    }
    for stage, expected in EXPECTED_CASES.items():
        stage_hashes: dict[str, Any] = {}
        reference_ids: set[str] | None = None
        for variant, version in (
            ("extraction", None),
            ("governance", "v1"),
            ("fusion_review", FUSION_PROMPT_VERSION),
        ):
            directory = _prediction_directory(source_experiment, stage, variant, version)
            count = sum(1 for _ in directory.glob("*.json"))
            if count != expected:
                raise RuntimeError(
                    f"source {stage}/{variant} has {count} predictions, expected {expected}"
                )
            record_ids = [
                str(v1.load_json(path).get("id"))
                for path in sorted(directory.glob("*.json"), key=lambda item: item.name)
            ]
            if len(set(record_ids)) != expected:
                raise RuntimeError(f"source {stage}/{variant} has duplicate sample IDs")
            if reference_ids is None:
                reference_ids = set(record_ids)
            elif set(record_ids) != reference_ids:
                raise RuntimeError(f"source {stage}/{variant} sample IDs do not match Extraction")
            stage_hashes[variant] = {
                "count": count,
                "prediction_set_hash": _prediction_set_hash(directory),
                "sample_ids_hash": canonical_hash(sorted(record_ids)),
            }
        source_hashes["stages"][stage] = stage_hashes

    payload = {
        "experiment_version": EXPERIMENT_VERSION,
        "post_hoc_protocol_refinement": True,
        "code_commit": v1._git_commit(),
        "source_experiment": source_experiment.resolve().as_posix(),
        "source_experiment_version": v1_agent.EXPERIMENT_VERSION,
        "source_hashes": source_hashes,
        "twitter_source": source_manifest["twitter_source"],
        "component_v4_output": source_manifest["component_v4_output"],
        "schema": {
            "path": twitter_schema_path.resolve().as_posix(),
            "hash": canonical_hash(schema),
        },
        "settings": settings_payload,
        "settings_hash": canonical_hash(settings_payload),
        "gate_policy_version": GATE_POLICY_VERSION,
        "gate_policy": {
            "accept": "action=reject and confidence=high",
            "block": ["all change_type", "medium/low reject"],
            "deduplicate_exact_entities": True,
            "allow_new_entities": False,
            "allow_span_changes": False,
        },
        "fusion_prompt_version": FUSION_PROMPT_VERSION,
        "retrieval_top_k": 3,
        "counts": EXPECTED_CASES,
        "seed": SEED,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "budget_limit_cny": 5.0,
        "test_gold_used_by_gate": False,
    }
    path = output / "manifest.json"
    if path.exists() and canonical_hash(v1.load_json(path)) != canonical_hash(payload):
        raise RuntimeError("existing V2 manifest differs from the requested frozen protocol")
    output.mkdir(parents=True, exist_ok=True)
    v1.atomic_json(path, payload)
    frozen_path = output / "frozen-config.json"
    frozen = (
        dict(v1.load_json(frozen_path))
        if frozen_path.exists()
        else {
            "experiment_version": EXPERIMENT_VERSION,
            "manifest_hash": canonical_hash(payload),
            "gate_policy_version": GATE_POLICY_VERSION,
            "fusion_prompt_version": FUSION_PROMPT_VERSION,
            "validation_gate_passed": False,
        }
    )
    if frozen.get("manifest_hash") != canonical_hash(payload):
        raise RuntimeError("existing V2 frozen config refers to a different manifest")
    v1.atomic_json(frozen_path, frozen)
    return payload


def apply_reject_only_gate(
    candidates: list[twitter.PredictedEntity], decisions: dict[int, dict[str, Any]]
) -> tuple[list[twitter.PredictedEntity], dict[str, Any]]:
    """Accept only high-confidence rejects and preserve all retained entities exactly."""
    output: list[twitter.PredictedEntity] = []
    decision_audit: list[dict[str, Any]] = []
    accepted_high_rejects = 0
    blocked_type_changes = 0
    blocked_low_confidence_rejects = 0
    for index, candidate in enumerate(candidates):
        decision = decisions.get(index)
        accepted = bool(
            decision and decision.get("action") == "reject" and decision.get("confidence") == "high"
        )
        if decision:
            action = str(decision.get("action"))
            confidence = str(decision.get("confidence"))
            if action == "change_type":
                blocked_type_changes += 1
                reason = "blocked_type_change"
            elif action == "reject" and confidence != "high":
                blocked_low_confidence_rejects += 1
                reason = "blocked_low_confidence_reject"
            elif accepted:
                reason = "accepted_high_confidence_reject"
            else:
                reason = "kept"
            decision_audit.append(
                {
                    "candidate_id": index,
                    "action": action,
                    "confidence": confidence,
                    "suggested_type": decision.get("type"),
                    "accepted": accepted,
                    "gate_reason": reason,
                    "source_reason_code": decision.get("reason_code"),
                }
            )
        if accepted:
            accepted_high_rejects += 1
            continue
        output.append(candidate)

    unique: list[twitter.PredictedEntity] = []
    seen: set[tuple[str, int, int, str]] = set()
    deduplications = 0
    for item in output:
        key = (item.text, item.start, item.end, item.type)
        if key in seen:
            deduplications += 1
            continue
        seen.add(key)
        unique.append(item)
    return unique, {
        "accepted_high_rejects": accepted_high_rejects,
        "blocked_type_changes": blocked_type_changes,
        "blocked_low_confidence_rejects": blocked_low_confidence_rejects,
        "governance_deduplications": deduplications,
        "decision_audit": decision_audit,
    }


def _rejection_quality(
    case: twitter.TwitterCase,
    source: list[twitter.PredictedEntity],
    decisions: dict[int, dict[str, Any]],
) -> tuple[int, int]:
    gold = {(item.start, item.end, item.type) for item in case.entities}
    correct = incorrect = 0
    for index, decision in decisions.items():
        if (
            decision.get("action") != "reject"
            or decision.get("confidence") != "high"
            or index >= len(source)
        ):
            continue
        candidate = source[index]
        if (candidate.start, candidate.end, candidate.type) in gold:
            incorrect += 1
        else:
            correct += 1
    return correct, incorrect


def reaggregate_governance(output: Path, stage: StageName) -> dict[str, Any]:
    """Reapply the frozen gate without provider calls or budget changes."""
    manifest = dict(v1.load_json(output / "manifest.json"))
    if manifest.get("gate_policy_version") != GATE_POLICY_VERSION:
        raise RuntimeError("gate policy is not frozen to reject-only V2")
    budget_before = _budget_cost(output)
    records: list[dict[str, Any]] = []
    changed_samples = correct_rejections = incorrect_rejections = 0
    for case in _stage_cases(output, stage):
        extraction = _source_record(output, stage, "extraction", case.id)
        source_governance = _source_record(output, stage, "governance", case.id, "v1")
        source_entities = [
            twitter.PredictedEntity.model_validate(item) for item in extraction["predicted"]
        ]
        decisions, parse_errors = v1_agent._parse_twitter_governance(
            str(source_governance.get("raw") or ""), [], len(source_entities)
        )
        final, audit = apply_reject_only_gate(source_entities, decisions)
        correct, incorrect = _rejection_quality(case, source_entities, decisions)
        correct_rejections += correct
        incorrect_rejections += incorrect
        changed_samples += int(
            [item.model_dump(mode="json") for item in final] != extraction["predicted"]
        )
        record = v1_agent._record_twitter(
            case,
            "governance",
            stage,
            final,
            [f"source_governance:{error}" for error in parse_errors],
            experiment_version=EXPERIMENT_VERSION,
            gate_policy_version=GATE_POLICY_VERSION,
            source_experiment=v1_agent.EXPERIMENT_VERSION,
            source_extraction_prediction_hash=canonical_hash(extraction["predicted"]),
            source_governance_response_hash=canonical_hash(
                {
                    "raw": source_governance.get("raw"),
                    "prompt_hash": source_governance.get("prompt_hash"),
                }
            ),
            input_variant="extraction",
            input_prediction_hash=canonical_hash(extraction["predicted"]),
            modifications_accepted=audit["accepted_high_rejects"]
            + audit["governance_deduplications"],
            modifications_rejected=audit["blocked_type_changes"]
            + audit["blocked_low_confidence_rejects"],
            retained_span_mutations=0,
            span_mutations=0,
            accepted_high_rejects=audit["accepted_high_rejects"],
            blocked_type_changes=audit["blocked_type_changes"],
            blocked_low_confidence_rejects=audit["blocked_low_confidence_rejects"],
            governance_rejections=audit["accepted_high_rejects"],
            governance_deduplications=audit["governance_deduplications"],
            original_decisions=audit["decision_audit"],
            raw=source_governance.get("raw", ""),
            source_text=case.text,
        )
        record["variant"] = "governance_v2"
        v1.atomic_json(
            _prediction_directory(output, stage, "governance_v2") / _artifact_name(case.id),
            record,
        )
        records.append(record)

    records.sort(key=lambda item: str(item["id"]))
    metrics = v1.aggregate_twitter(records)
    case_by_id = {case.id: case for case in _stage_cases(output, stage)}
    final_invalid = sum(
        v1_agent._twitter_final_output_invalid(case_by_id[str(record["id"])], record["predicted"])
        for record in records
    )
    accepted = sum(int(item["accepted_high_rejects"]) for item in records)
    blocked_types = sum(int(item["blocked_type_changes"]) for item in records)
    blocked_low = sum(int(item["blocked_low_confidence_rejects"]) for item in records)
    deduplications = sum(int(item["governance_deduplications"]) for item in records)
    budget_after = _budget_cost(output)
    report = {
        "experiment_version": EXPERIMENT_VERSION,
        "dataset": "twitter2017",
        "stage": stage,
        "variant": "governance_v2",
        "variant_label": VARIANT_LABELS["governance_v2"],
        "gate_policy_version": GATE_POLICY_VERSION,
        "metrics": metrics,
        "secondary_metrics": v1_agent._secondary_metrics("twitter2017", records),
        "usage": {
            "calls": 0,
            "estimated_cost_cny": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "average_latency_ms": None,
        },
        "accepted_high_rejects": accepted,
        "blocked_type_changes": blocked_types,
        "blocked_low_confidence_rejects": blocked_low,
        "governance_deduplications": deduplications,
        "changed_samples": changed_samples,
        "correct_rejections": correct_rejections,
        "incorrect_rejections": incorrect_rejections,
        "rejection_accuracy": round(correct_rejections / accepted, 6) if accepted else None,
        "net_rejection_benefit": correct_rejections - incorrect_rejections,
        "retained_span_mutations": 0,
        "span_mutations": 0,
        "input_hashes_present": len(records),
        "input_hash_mismatches": 0,
        "final_output_invalid_count": final_invalid,
        "budget_cost_before_cny": budget_before,
        "budget_cost_after_cny": budget_after,
        "no_paid_calls_during_reaggregation": budget_before == budget_after,
        "prediction_set_hash": _prediction_set_hash(
            _prediction_directory(output, stage, "governance_v2")
        ),
    }
    if not report["no_paid_calls_during_reaggregation"]:
        raise RuntimeError("offline governance reaggregation changed the budget")
    v1.atomic_json(_report_path(output, stage, "governance_v2"), report)
    return report


def _usage_for_fusion(ledger: MnerV2BudgetLedger, stage: StageName) -> dict[str, Any]:
    prefix = f"agent-progression-mner-v2:twitter2017:{stage}:fusion_review:v3:"
    calls = [
        item
        for item in ledger.payload.get("calls", [])
        if str(item.get("operation_id", "")).startswith(prefix)
    ]
    latencies = [float(item["latency_ms"]) for item in calls if item.get("latency_ms")]
    return {
        "calls": len(calls),
        "input_tokens": sum(int(item.get("input_tokens") or 0) for item in calls),
        "output_tokens": sum(int(item.get("output_tokens") or 0) for item in calls),
        "estimated_cost_cny": round(
            sum(float(item.get("estimated_cost_cny") or 0) for item in calls), 8
        ),
        "average_latency_ms": round(mean(latencies), 3) if latencies else None,
    }


def _can_reuse_v1_fusion(
    input_record: dict[str, Any],
    old_governance: dict[str, Any],
    old_fusion: dict[str, Any],
    prompt_hash: str,
    retrieved_ids: list[str],
) -> bool:
    """Require the complete deterministic request fingerprint to match V1."""
    return bool(
        input_record.get("predicted") == old_governance.get("predicted")
        and old_fusion.get("prompt_hash") == prompt_hash
        and old_fusion.get("input_prediction_hash") == canonical_hash(input_record.get("predicted"))
        and old_fusion.get("retrieved_case_ids") == retrieved_ids
    )


async def _fusion_one(
    output: Path,
    case: twitter.TwitterCase,
    stage: StageName,
    input_record: dict[str, Any],
    settings: Settings,
    ledger: MnerV2BudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    manifest = dict(v1.load_json(output / "manifest.json"))
    source = Path(str(manifest["twitter_source"]))
    schema = twitter.load_schema(Path(str(manifest["schema"]["path"])))
    entities = [twitter.PredictedEntity.model_validate(item) for item in input_record["predicted"]]
    retrieved_ids, examples = v1_agent._twitter_examples(output, source, case, stage)
    prompt = v1_agent.twitter_fusion_prompt("v3", schema, case, entities, examples)
    prompt_hash = canonical_hash(prompt)
    old_governance = _source_record(output, stage, "governance", case.id, "v1")
    old_fusion = _source_record(output, stage, "fusion_review", case.id, FUSION_PROMPT_VERSION)
    can_reuse = _can_reuse_v1_fusion(
        input_record,
        old_governance,
        old_fusion,
        prompt_hash,
        retrieved_ids,
    )
    if can_reuse:
        record = {
            **old_fusion,
            "variant": "fusion_review_v2",
            "experiment_version": EXPERIMENT_VERSION,
            "gate_policy_version": GATE_POLICY_VERSION,
            "source_experiment": v1_agent.EXPERIMENT_VERSION,
            "source_prediction_hash": canonical_hash(old_fusion),
            "cache_reused_from_v1": True,
            "fusion_request_fingerprint": canonical_hash(
                {
                    "prompt_hash": prompt_hash,
                    "settings_hash": manifest["settings_hash"],
                    "input_prediction_hash": canonical_hash(input_record["predicted"]),
                    "retrieved_case_ids": retrieved_ids,
                }
            ),
        }
        v1.atomic_json(target, record)
        return record

    prefix = f"agent-progression-mner-v2:twitter2017:{stage}:fusion_review:v3:{case.id}"
    raw, provider_errors = await v1._provider_json(
        settings,
        ledger,
        prompt,
        f"{prefix}:review",
        "agent-progression-mner-v2-fusion-v3",
    )
    reviewed, errors = v4._parse_twitter_prediction_v4(case, raw, provider_errors)
    accepted = not errors
    final = reviewed if accepted else entities
    if not accepted:
        errors.append("fusion_review_rejected")
    record = v1_agent._record_twitter(
        case,
        "fusion_review",
        stage,
        final,
        errors,
        experiment_version=EXPERIMENT_VERSION,
        gate_policy_version=GATE_POLICY_VERSION,
        source_experiment=v1_agent.EXPERIMENT_VERSION,
        prompt_version=FUSION_PROMPT_VERSION,
        input_variant="governance_v2",
        input_prediction_hash=canonical_hash(input_record["predicted"]),
        retrieved_case_ids=retrieved_ids,
        review_accepted=accepted
        and [item.model_dump(mode="json") for item in final] != input_record["predicted"],
        prompt_hash=prompt_hash,
        raw=raw,
        cache_reused_from_v1=False,
        fusion_request_fingerprint=canonical_hash(
            {
                "prompt_hash": prompt_hash,
                "settings_hash": manifest["settings_hash"],
                "input_prediction_hash": canonical_hash(input_record["predicted"]),
                "retrieved_case_ids": retrieved_ids,
            }
        ),
        source_text=case.text,
    )
    record["variant"] = "fusion_review_v2"
    v1.atomic_json(target, record)
    return record


async def run_fusion_stage(
    output: Path,
    stage: StageName,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 5.0,
) -> dict[str, Any]:
    if concurrency not in {1, 2}:
        raise ValueError("prediction concurrency must be 1 or 2")
    governance_report = _report_path(output, stage, "governance_v2")
    if not governance_report.exists():
        raise RuntimeError("Governance V2 must be reaggregated before Fusion V2")
    cases = _stage_cases(output, stage)
    ledger = MnerV2BudgetLedger(output / "budget.json", budget_limit_cny)
    results: list[dict[str, Any]] = []
    next_index = 0
    first_error: BaseException | None = None

    async def worker() -> None:
        nonlocal next_index, first_error
        while first_error is None and next_index < len(cases):
            case = cases[next_index]
            next_index += 1
            try:
                record = await _fusion_one(
                    output,
                    case,
                    stage,
                    _v2_record(output, stage, "governance_v2", case.id),
                    settings,
                    ledger,
                    _prediction_directory(output, stage, "fusion_review_v2")
                    / _artifact_name(case.id),
                )
                results.append(record)
            except BaseException as exc:
                first_error = exc
                return

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    if first_error is not None:
        raise first_error
    results.sort(key=lambda item: str(item["id"]))
    input_mismatches = sum(
        item.get("input_prediction_hash")
        != canonical_hash(_v2_record(output, stage, "governance_v2", str(item["id"]))["predicted"])
        for item in results
    )
    case_by_id = {case.id: case for case in cases}
    report = {
        "experiment_version": EXPERIMENT_VERSION,
        "dataset": "twitter2017",
        "stage": stage,
        "variant": "fusion_review_v2",
        "variant_label": VARIANT_LABELS["fusion_review_v2"],
        "prompt_version": FUSION_PROMPT_VERSION,
        "gate_policy_version": GATE_POLICY_VERSION,
        "metrics": v1.aggregate_twitter(results),
        "secondary_metrics": v1_agent._secondary_metrics("twitter2017", results),
        "usage": _usage_for_fusion(ledger, stage),
        "cache_reused_count": sum(bool(item.get("cache_reused_from_v1")) for item in results),
        "rerun_count": sum(not bool(item.get("cache_reused_from_v1")) for item in results),
        "input_hashes_present": sum("input_prediction_hash" in item for item in results),
        "input_hash_mismatches": input_mismatches,
        "final_output_invalid_count": sum(
            v1_agent._twitter_final_output_invalid(case_by_id[str(item["id"])], item["predicted"])
            for item in results
        ),
        "prediction_set_hash": _prediction_set_hash(
            _prediction_directory(output, stage, "fusion_review_v2")
        ),
    }
    v1.atomic_json(_report_path(output, stage, "fusion_review_v2"), report)
    return report


def _source_extraction_report(output: Path, stage: StageName) -> dict[str, Any]:
    return dict(v1.load_json(_report_path(_source_root(output), stage, "extraction")))


def _structure_gate(report: dict[str, Any], stage: StageName) -> None:
    expected = EXPECTED_CASES[stage]
    if int(report["metrics"]["cases"]) != expected:
        raise RuntimeError("stage report has an unexpected sample count")
    if int(report.get("final_output_invalid_count", 0)):
        raise RuntimeError("stage has invalid final outputs")
    if int(report.get("input_hash_mismatches", 0)):
        raise RuntimeError("stage input hashes do not match upstream outputs")
    if report["variant"] == "governance_v2" and int(report.get("retained_span_mutations", 0)):
        raise RuntimeError("Governance V2 mutated a retained entity")


async def run_validation(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 5.0,
) -> dict[str, Any]:
    dev_governance = reaggregate_governance(output, "dev")
    _structure_gate(dev_governance, "dev")
    dev_fusion = await run_fusion_stage(
        output,
        "dev",
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    _structure_gate(dev_fusion, "dev")
    holdout_governance = reaggregate_governance(output, "holdout")
    _structure_gate(holdout_governance, "holdout")
    holdout_fusion = await run_fusion_stage(
        output,
        "holdout",
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    _structure_gate(holdout_fusion, "holdout")
    extraction = _source_extraction_report(output, "holdout")
    extraction_f1 = float(extraction["metrics"]["micro_f1"])
    governance_f1 = float(holdout_governance["metrics"]["micro_f1"])
    fusion_f1 = float(holdout_fusion["metrics"]["micro_f1"])
    passed = extraction_f1 < governance_f1 < fusion_f1
    summary = {
        "experiment_version": EXPERIMENT_VERSION,
        "passed": passed,
        "required_order": "extraction < governance_v2 < fusion_review_v2",
        "dev": {
            "extraction": _source_extraction_report(output, "dev"),
            "governance_v2": dev_governance,
            "fusion_review_v2": dev_fusion,
        },
        "holdout": {
            "extraction": extraction,
            "governance_v2": holdout_governance,
            "fusion_review_v2": holdout_fusion,
        },
    }
    v1.atomic_json(output / "validation-summary.json", summary)
    frozen = dict(v1.load_json(output / "frozen-config.json"))
    frozen.update(
        {
            "validation_gate_passed": passed,
            "validation_summary_hash": canonical_hash(summary),
            "runtime_code_commit": v1._git_commit(),
        }
    )
    v1.atomic_json(output / "frozen-config.json", frozen)
    if not passed:
        raise RuntimeError("frozen holdout did not satisfy Extraction < Governance V2 < Fusion V2")
    return summary


async def run_test(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 5.0,
) -> dict[str, Any]:
    validation = dict(v1.load_json(output / "validation-summary.json"))
    if not validation.get("passed"):
        raise RuntimeError("validation gate has not passed")
    governance = reaggregate_governance(output, "main")
    _structure_gate(governance, "main")
    fusion = await run_fusion_stage(
        output,
        "main",
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    _structure_gate(fusion, "main")
    extraction = _source_extraction_report(output, "main")
    summary = {
        "experiment_version": EXPERIMENT_VERSION,
        "test_run_once": True,
        "configuration_changed_after_test": False,
        "observed_order": {
            "extraction": extraction["metrics"]["micro_f1"],
            "governance_v2": governance["metrics"]["micro_f1"],
            "fusion_review_v2": fusion["metrics"]["micro_f1"],
        },
        "target_order_observed": float(extraction["metrics"]["micro_f1"])
        < float(governance["metrics"]["micro_f1"])
        < float(fusion["metrics"]["micro_f1"]),
        "extraction": extraction,
        "governance_v2": governance,
        "fusion_review_v2": fusion,
    }
    v1.atomic_json(output / "test-summary.json", summary)
    return summary


def _main_records(output: Path, variant: str) -> list[dict[str, Any]]:
    if variant == "extraction":
        directory = _prediction_directory(_source_root(output), "main", "extraction")
    else:
        directory = _prediction_directory(output, "main", variant)
    records = [dict(v1.load_json(path)) for path in directory.glob("*.json")]
    return sorted(records, key=lambda item: str(item["id"]))


def _main_report(output: Path, variant: str) -> dict[str, Any]:
    if variant == "extraction":
        return _source_extraction_report(output, "main")
    return dict(v1.load_json(_report_path(output, "main", variant)))


def export_results(output: Path) -> dict[str, Any]:
    if not (output / "test-summary.json").exists():
        raise RuntimeError("test results are unavailable")
    records = {variant: _main_records(output, variant) for variant in VARIANTS}
    rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        report = _main_report(output, variant)
        metrics = report["metrics"]
        rows.append(
            {
                "dataset": "Twitter-2017",
                "variant": variant,
                "variant_label": VARIANT_LABELS[variant],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["micro_f1"],
                "macro_f1": metrics["macro_f1"],
                "f1_ci_lower": metrics["f1_95_ci"]["lower"],
                "f1_ci_upper": metrics["f1_95_ci"]["upper"],
                "cost_cny": report.get("usage", {}).get("estimated_cost_cny", 0.0),
                "average_latency_ms": report.get("usage", {}).get("average_latency_ms"),
            }
        )
    pairs = (("extraction", "governance_v2"), ("governance_v2", "fusion_review_v2"))
    paired = [
        {
            "left": left,
            "right": right,
            **v1._paired_bootstrap_delta(records[left], records[right]),
        }
        for left, right in pairs
    ]
    transitions = [
        {
            "left": left,
            "right": right,
            **v1_agent._transition_stats(records[left], records[right]),
        }
        for left, right in pairs
    ]
    payload = {
        "experiment_version": EXPERIMENT_VERSION,
        "post_hoc_protocol_refinement": True,
        "rows": rows,
        "paired_bootstrap": paired,
        "transitions": transitions,
        "governance_audit": _main_report(output, "governance_v2"),
        "fusion_audit": _main_report(output, "fusion_review_v2"),
        "manifest": v1.load_json(output / "manifest.json"),
        "frozen_config": v1.load_json(output / "frozen-config.json"),
    }
    v1.atomic_json(output / "results.json", payload)
    headers = [
        "dataset",
        "variant",
        "precision",
        "recall",
        "f1",
        "macro_f1",
        "f1_ci_lower",
        "f1_ci_upper",
        "cost_cny",
        "average_latency_ms",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(header, "")) for header in headers))
    csv_path = output / "results.csv"
    temporary = csv_path.with_name(f".{csv_path.name}.{os.getpid()}.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temporary, csv_path)
    return payload


async def run_all(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 5.0,
) -> dict[str, Any]:
    validation = await run_validation(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    test = await run_test(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    results = export_results(output)
    summary = {"validation": validation, "test": test, "results": results}
    v1.atomic_json(output / "run-all-summary.json", summary)
    return summary


def evaluation_status(output: Path) -> dict[str, Any]:
    def optional(path: Path) -> Any:
        return v1.load_json(path) if path.exists() else None

    cells = []
    for stage in EXPECTED_CASES:
        for variant in ("governance_v2", "fusion_review_v2"):
            cells.append(
                {
                    "stage": stage,
                    "variant": variant,
                    "predictions": sum(
                        1 for _ in _prediction_directory(output, stage, variant).glob("*.json")
                    ),
                    "report": optional(_report_path(output, stage, variant)),
                }
            )
    return {
        "manifest": optional(output / "manifest.json"),
        "frozen_config": optional(output / "frozen-config.json"),
        "validation": optional(output / "validation-summary.json"),
        "test": optional(output / "test-summary.json"),
        "budget": optional(output / "budget.json"),
        "cells": cells,
        "results": optional(output / "results.json"),
    }
