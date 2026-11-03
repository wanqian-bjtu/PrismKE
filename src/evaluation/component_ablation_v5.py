"""V5 paired visual contribution experiment built from immutable V4 predictions."""

from __future__ import annotations

import asyncio
import os
import shutil
from collections import Counter
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Any, Literal

from src.core.ids import canonical_hash
from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.evaluation import component_ablation as v1
from src.evaluation import component_ablation_v4 as v4
from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter

DatasetName = Literal["twitter2017", "mnre-v2"]
StageName = Literal["holdout", "main"]
VariantName = Literal["vanilla", "schema", "multimodal", "full"]

EXPERIMENT_VERSION = "component-ablation-v5"
SCORING_VERSION = v4.SCORING_VERSION
DATASETS: tuple[DatasetName, ...] = ("twitter2017", "mnre-v2")
VARIANTS: tuple[VariantName, ...] = ("vanilla", "schema", "multimodal", "full")
REUSED_VARIANTS: tuple[Literal["vanilla", "schema", "full"], ...] = (
    "vanilla",
    "schema",
    "full",
)
VARIANT_LABELS: dict[VariantName, str] = {
    "vanilla": "Vanilla",
    "schema": "+ Schema Guidance",
    "multimodal": "+ Paired Multimodal V5",
    "full": "Full PrismKE V4 (reused)",
}
EXPECTED: dict[tuple[DatasetName, StageName], int] = {
    ("twitter2017", "holdout"): 623,
    ("twitter2017", "main"): 723,
    ("mnre-v2", "holdout"): 1423,
    ("mnre-v2", "main"): 1614,
}


class V5BudgetLedger(v1.AblationBudgetLedger):
    """Independent V5 ledger with 7/9 CNY progress milestones."""

    def record(self, operation_id: str, record: ProviderCallRecord) -> list[float]:
        before = self.cost
        crossed = super().record(operation_id, record)
        for milestone in (7.0, 9.0):
            if before < milestone <= self.cost and milestone not in self.payload["milestones"]:
                self.payload["milestones"].append(milestone)
                crossed.append(milestone)
        self.persist()
        return sorted(crossed)


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_name(case_id: str) -> str:
    return case_id.replace(":", "-") + ".json"


def _copied_prediction_dir(
    output: Path, stage: StageName, dataset: DatasetName, variant: str
) -> Path:
    return output / "reused" / stage / dataset / variant / "predictions"


def _paired_prediction_dir(output: Path, stage: StageName, dataset: DatasetName) -> Path:
    return output / stage / dataset / "multimodal" / "predictions"


def _source_prediction_dir(
    source_v4: Path, stage: StageName, dataset: DatasetName, variant: str
) -> Path:
    return source_v4 / stage / dataset / variant / "predictions"


def _copy_verified(source: Path, target: Path) -> str:
    source_hash = _file_sha256(source)
    if target.exists():
        if _file_sha256(target) != source_hash:
            raise RuntimeError(f"existing V5 copy differs from V4 source: {target}")
        return source_hash
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        shutil.copy2(source, temporary)
        if _file_sha256(temporary) != source_hash:
            raise RuntimeError(f"copied prediction hash mismatch: {source}")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return source_hash


def _source_inventory(source_v4: Path) -> list[tuple[StageName, DatasetName, str, int]]:
    return [
        ("holdout", "twitter2017", "schema", 623),
        ("holdout", "mnre-v2", "schema", 1423),
        ("main", "twitter2017", "vanilla", 723),
        ("main", "twitter2017", "schema", 723),
        ("main", "twitter2017", "full", 723),
        ("main", "mnre-v2", "vanilla", 1614),
        ("main", "mnre-v2", "schema", 1614),
        ("main", "mnre-v2", "full", 1614),
    ]


def prepare_experiment(output: Path, source_v4: Path, settings: Settings) -> dict[str, Any]:
    """Import immutable V4 predictions and freeze the paired V5 protocol."""
    source_v4 = source_v4.resolve()
    v4_manifest = dict(v1.load_json(source_v4 / "manifest.json"))
    v4_frozen = dict(v1.load_json(source_v4 / "frozen-config.json"))
    if v4_manifest.get("experiment_version") != v4.EXPERIMENT_VERSION:
        raise RuntimeError("source experiment is not component-ablation-v4")
    if not (source_v4 / "results.json").is_file():
        raise RuntimeError("V4 source does not contain exported results")
    expected_settings = dict(v4_manifest["settings"])
    if settings.llm_model != expected_settings["llm_model"]:
        raise RuntimeError("configured LLM differs from frozen V4")
    if settings.vlm_model != expected_settings["vlm_model"]:
        raise RuntimeError("configured VLM differs from frozen V4")

    provenance: list[dict[str, Any]] = []
    for stage, dataset, variant, expected in _source_inventory(source_v4):
        source_dir = _source_prediction_dir(source_v4, stage, dataset, variant)
        paths = sorted(source_dir.glob("*.json"))
        if len(paths) != expected:
            raise RuntimeError(
                f"V4 source count mismatch for {stage}/{dataset}/{variant}: {len(paths)}"
            )
        target_dir = _copied_prediction_dir(output, stage, dataset, variant)
        for source in paths:
            target = target_dir / source.name
            provenance.append(
                {
                    "stage": stage,
                    "dataset": dataset,
                    "variant": variant,
                    "filename": source.name,
                    "sha256": _copy_verified(source, target),
                }
            )

    manifest = {
        "experiment_version": EXPERIMENT_VERSION,
        "code_commit": v1._git_commit(),
        "source_experiment": v4.EXPERIMENT_VERSION,
        "source_v4_path": source_v4.as_posix(),
        "source_v4_commit": v4_manifest["code_commit"],
        "source_v4_manifest_hash": canonical_hash(v4_manifest),
        "source_v4_frozen_hash": canonical_hash(v4_frozen),
        "source_v4_results_hash": _file_sha256(source_v4 / "results.json"),
        "settings": expected_settings,
        "settings_hash": v4_manifest["settings_hash"],
        "schemas": v4_manifest["schemas"],
        "counts": v4_manifest["counts"],
        "bootstrap_samples": v4.BOOTSTRAP_SAMPLES,
        "seed": v4.SEED,
        "budget_limit_cny": 10.0,
        "paid_stability_repetitions": 0,
        "paired_baseline": "immutable V4 schema prediction",
        "gold_fields_forwarded_to_model": False,
        "reused_variants": list(REUSED_VARIANTS),
    }
    output.mkdir(parents=True, exist_ok=True)
    v1.atomic_json(output / "source-provenance.json", {"files": provenance})
    v1.atomic_json(output / "manifest.json", manifest)
    frozen = {
        "experiment_version": EXPERIMENT_VERSION,
        "manifest_hash": canonical_hash(manifest),
        "source_provenance_hash": canonical_hash({"files": provenance}),
        "visual_prompt_policy_hash": canonical_hash(
            {
                "twitter": v4.twitter_visual_prompt.__doc__,
                "mnre": v4.mnre_visual_prompt.__doc__,
                "mnre_fusion": v4.mnre_fusion_prompt.__doc__,
                "eligible_relations": sorted(v4.VISUALLY_ELIGIBLE_RELATIONS),
                "baseline": "schema-prediction-v4",
            }
        ),
    }
    v1.atomic_json(output / "frozen-config.json", frozen)
    return manifest


def _require_frozen(output: Path) -> dict[str, Any]:
    manifest = dict(v1.load_json(output / "manifest.json"))
    frozen = dict(v1.load_json(output / "frozen-config.json"))
    if frozen["manifest_hash"] != canonical_hash(manifest):
        raise RuntimeError("V5 manifest changed after freeze")
    provenance = v1.load_json(output / "source-provenance.json")
    if frozen["source_provenance_hash"] != canonical_hash(provenance):
        raise RuntimeError("V5 source provenance changed after freeze")
    return manifest


def _load_schema(manifest: dict[str, Any], dataset: DatasetName) -> dict[str, Any]:
    path = Path(str(manifest["schemas"][dataset]["path"]))
    return twitter.load_schema(path) if dataset == "twitter2017" else mnre.load_schema(path)


def _baseline_payload(
    output: Path, stage: StageName, dataset: DatasetName, case_id: str
) -> dict[str, Any]:
    path = _copied_prediction_dir(output, stage, dataset, "schema") / _artifact_name(case_id)
    payload = dict(v1.load_json(path))
    if payload.get("id") != case_id or payload.get("variant") != "schema":
        raise RuntimeError(f"invalid imported Schema prediction: {path}")
    return payload


def _old_multimodal_payload(
    manifest: dict[str, Any], stage: StageName, dataset: DatasetName, case_id: str
) -> dict[str, Any] | None:
    path = (
        Path(str(manifest["source_v4_path"]))
        / stage
        / dataset
        / "multimodal"
        / "predictions"
        / _artifact_name(case_id)
    )
    return dict(v1.load_json(path)) if path.is_file() else None


def _visual_input_hash(
    prompt: str, image_sha256: str | None, schema_hash: str, model: str
) -> str:
    return canonical_hash(
        {
            "prompt": prompt,
            "image_sha256": image_sha256,
            "schema_hash": schema_hash,
            "model": model,
        }
    )


def _cache_usable(old: dict[str, Any] | None, baseline: Any, raw_field: str) -> bool:
    if not old or old.get("text_predicted") != baseline:
        return False
    if old.get("visual_errors"):
        return False
    return bool(old.get(raw_field))


def _twitter_changed_ids(
    baseline: list[twitter.PredictedEntity], final: list[twitter.PredictedEntity]
) -> list[int]:
    if v4._span_signature(baseline) != v4._span_signature(final):
        raise RuntimeError("paired MNER visual stage changed an entity span")
    return [
        index
        for index, (left, right) in enumerate(zip(baseline, final, strict=True))
        if left.type != right.type
    ]


def _assert_twitter_identity(
    baseline: list[twitter.PredictedEntity],
    final: list[twitter.PredictedEntity],
    accepted: int,
) -> list[int]:
    changed = _twitter_changed_ids(baseline, final)
    if not accepted and changed:
        raise RuntimeError("MNER output changed without an accepted visual edit")
    if len(changed) > accepted:
        raise RuntimeError("MNER changed more candidates than the visual gate accepted")
    return changed


def _assert_mnre_identity(baseline: str, final: str, fusion_accepted: bool) -> None:
    if baseline != final and not fusion_accepted:
        raise RuntimeError("MRE output changed without an accepted visual fusion")


async def _run_twitter_one(
    output: Path,
    manifest: dict[str, Any],
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    stage: StageName,
    settings: Settings,
    ledger: V5BudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    baseline_payload = _baseline_payload(output, stage, "twitter2017", case.id)
    baseline_raw = list(baseline_payload["predicted"])
    baseline = [twitter.PredictedEntity.model_validate(item) for item in baseline_raw]
    final = list(baseline)
    errors: list[str] = []
    visual_errors: list[str] = []
    raw_visual = ""
    visual_origin = "not_applicable"
    gate_triggered = bool(baseline and case.image_valid)
    accepted = 0
    rejected = 0
    input_hash: str | None = None
    if gate_triggered:
        prompt = v4.twitter_visual_prompt(schema, case, baseline)
        input_hash = _visual_input_hash(
            prompt,
            case.image_sha256,
            str(manifest["schemas"]["twitter2017"]["hash"]),
            str(settings.vlm_model or settings.llm_model),
        )
        old = _old_multimodal_payload(manifest, stage, "twitter2017", case.id)
        if _cache_usable(old, baseline_raw, "raw_visual"):
            assert old is not None
            raw_visual = str(old["raw_visual"])
            provider_errors: list[str] = []
            visual_origin = "v4_exact_input_cache"
        else:
            operation_id = f"ablation-v5:twitter2017:{stage}:{case.id}:visual"
            raw_visual, provider_errors = await v4._provider_vlm_json(
                settings,
                ledger,
                prompt,
                Path(case.image_path),
                operation_id,
                "ablation-v5-twitter-paired-type-evidence",
            )
            visual_origin = "v5_provider_call"
        evidence, visual_errors = v4._parse_twitter_visual(
            raw_visual, provider_errors, len(baseline)
        )
        final, accepted, rejected = v4.apply_twitter_visual_gate(baseline, evidence)
        errors.extend(visual_errors)
    changed_ids = _assert_twitter_identity(baseline, final, accepted)
    result = {
        "id": case.id,
        "dataset": "twitter2017",
        "variant": "multimodal",
        "stage": stage,
        "source_experiment": v4.EXPERIMENT_VERSION,
        "schema_baseline_hash": canonical_hash(baseline_raw),
        "schema_predicted": baseline_raw,
        "predicted": [item.model_dump(mode="json") for item in final],
        "gold": [item.model_dump(mode="json") for item in case.entities],
        "metrics": twitter._result_metrics(case, final),
        "errors": errors,
        "visual_errors": visual_errors,
        "visual_gate_triggered": gate_triggered,
        "visual_origin": visual_origin,
        "visual_input_hash": input_hash,
        "visual_changes_accepted": accepted,
        "visual_changes_rejected": rejected,
        "changed_candidate_ids": changed_ids,
        "changed_by_visual": bool(changed_ids),
        "span_mutations": 0,
        "image_valid": case.image_valid,
        "raw_visual": raw_visual,
        "scoring_version": SCORING_VERSION,
    }
    v1.atomic_json(target, result)
    return result


async def _run_mnre_one(
    output: Path,
    manifest: dict[str, Any],
    schema: dict[str, Any],
    case: mnre.MNRECase,
    stage: StageName,
    settings: Settings,
    ledger: V5BudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    baseline_payload = _baseline_payload(output, stage, "mnre-v2", case.id)
    baseline = str(baseline_payload["predicted"])
    final = baseline
    errors: list[str] = []
    visual_errors: list[str] = []
    raw_visual = ""
    raw_fusion = ""
    evidence: dict[str, str] | None = None
    gate_triggered = baseline in v4.VISUALLY_ELIGIBLE_RELATIONS
    fusion_triggered = False
    fusion_accepted = False
    visual_origin = "not_applicable"
    fusion_origin = "not_applicable"
    input_hash: str | None = None
    old = _old_multimodal_payload(manifest, stage, "mnre-v2", case.id)
    if gate_triggered:
        prompt = v4.mnre_visual_prompt(schema, case, baseline)
        input_hash = _visual_input_hash(
            prompt,
            case.image_sha256,
            str(manifest["schemas"]["mnre-v2"]["hash"]),
            str(settings.vlm_model or settings.llm_model),
        )
        if _cache_usable(old, baseline, "raw_visual"):
            assert old is not None
            raw_visual = str(old["raw_visual"])
            provider_errors: list[str] = []
            visual_origin = "v4_exact_input_cache"
        else:
            operation_id = f"ablation-v5:mnre-v2:{stage}:{case.id}:visual"
            raw_visual, provider_errors = await v4._provider_vlm_json(
                settings,
                ledger,
                prompt,
                Path(case.image_path),
                operation_id,
                "ablation-v5-mnre-paired-visual-evidence",
            )
            visual_origin = "v5_provider_call"
        evidence, visual_errors = v4._parse_mnre_visual(raw_visual, provider_errors)
        errors.extend(visual_errors)
        if (
            evidence
            and evidence["head_visible"] == "yes"
            and evidence["tail_visible"] == "yes"
            and evidence["visual_support"] == "contradicts"
            and evidence["confidence"] == "high"
        ):
            fusion_triggered = True
            fusion_prompt = v4.mnre_fusion_prompt(schema, case, baseline, evidence)
            if (
                old
                and old.get("text_predicted") == baseline
                and old.get("visual_evidence") == evidence
                and not old.get("visual_errors")
                and old.get("raw_fusion")
            ):
                raw_fusion = str(old["raw_fusion"])
                fusion_provider_errors: list[str] = []
                fusion_origin = "v4_exact_input_cache"
            else:
                operation_id = f"ablation-v5:mnre-v2:{stage}:{case.id}:fusion"
                raw_fusion, fusion_provider_errors = await v1._provider_json(
                    settings,
                    ledger,
                    fusion_prompt,
                    operation_id,
                    "ablation-v5-mnre-paired-fusion",
                )
                fusion_origin = "v5_provider_call"
            fused, fusion_errors = v1._parse_mnre_prediction(
                raw_fusion, fusion_provider_errors
            )
            if not fusion_errors:
                final = fused
                fusion_accepted = True
            else:
                errors.extend(fusion_errors)
                errors.append("fusion_rejected")
    _assert_mnre_identity(baseline, final, fusion_accepted)
    result = {
        "id": case.id,
        "dataset": "mnre-v2",
        "variant": "multimodal",
        "stage": stage,
        "source_experiment": v4.EXPERIMENT_VERSION,
        "schema_baseline_hash": canonical_hash(baseline),
        "schema_predicted": baseline,
        "predicted": final,
        "gold": case.relation,
        "gold_dataset_label": case.dataset_label,
        "metrics": mnre._result_metrics(case, final),
        "errors": errors,
        "visual_errors": visual_errors,
        "visual_gate_triggered": gate_triggered,
        "visual_origin": visual_origin,
        "visual_input_hash": input_hash,
        "visual_evidence": evidence,
        "fusion_triggered": fusion_triggered,
        "fusion_accepted": fusion_accepted,
        "fusion_origin": fusion_origin,
        "changed_by_visual": baseline != final,
        "endpoint_swaps": 0,
        "raw_visual": raw_visual,
        "raw_fusion": raw_fusion,
        "scoring_version": SCORING_VERSION,
    }
    v1.atomic_json(target, result)
    return result


def _usage_for(ledger: V5BudgetLedger, dataset: DatasetName, stage: StageName) -> dict[str, Any]:
    prefix = f"ablation-v5:{dataset}:{stage}:"
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


async def run_paired_dataset(
    output: Path,
    dataset: DatasetName,
    stage: StageName,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 10.0,
) -> dict[str, Any]:
    """Run only the paired visual stage from immutable V4 Schema predictions."""
    if concurrency not in {1, 2}:
        raise ValueError("prediction concurrency must be 1 or 2")
    manifest = _require_frozen(output)
    source_v4 = Path(str(manifest["source_v4_path"]))
    source_manifest = dict(v1.load_json(source_v4 / "manifest.json"))
    source = Path(
        str(
            source_manifest["twitter_source"]
            if dataset == "twitter2017"
            else source_manifest["mnre_source"]
        )
    )
    cases = v4._stage_cases(source_v4, source, dataset, stage)
    expected = EXPECTED[(dataset, stage)]
    if len(cases) != expected:
        raise RuntimeError(f"unexpected {dataset} {stage} case count: {len(cases)}")
    schema = _load_schema(manifest, dataset)
    ledger = V5BudgetLedger(output / "budget.json", budget_limit_cny)
    directory = _paired_prediction_dir(output, stage, dataset)
    results: list[dict[str, Any]] = []
    next_index = 0
    first_error: BaseException | None = None

    async def worker() -> None:
        nonlocal next_index, first_error
        while first_error is None and next_index < len(cases):
            case = cases[next_index]
            next_index += 1
            target = directory / _artifact_name(case.id)
            try:
                if dataset == "twitter2017":
                    assert isinstance(case, twitter.TwitterCase)
                    result = await _run_twitter_one(
                        output, manifest, schema, case, stage, settings, ledger, target
                    )
                else:
                    assert isinstance(case, mnre.MNRECase)
                    result = await _run_mnre_one(
                        output, manifest, schema, case, stage, settings, ledger, target
                    )
                results.append(result)
            except BaseException as exc:
                first_error = exc
                return

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    if first_error is not None:
        raise first_error
    results.sort(key=lambda item: str(item["id"]))
    metrics = (
        v1.aggregate_twitter(results)
        if dataset == "twitter2017"
        else v1.aggregate_mnre(results)
    )
    changed = [item for item in results if item["changed_by_visual"]]
    accepted = (
        sum(int(item["visual_changes_accepted"]) for item in results)
        if dataset == "twitter2017"
        else sum(bool(item["fusion_accepted"]) for item in results)
    )
    if not accepted and changed:
        raise RuntimeError("paired visual output changed without an accepted modification")
    report = {
        "experiment_version": EXPERIMENT_VERSION,
        "dataset": dataset,
        "variant": "multimodal",
        "variant_label": VARIANT_LABELS["multimodal"],
        "stage": stage,
        "metrics": metrics,
        "usage": _usage_for(ledger, dataset, stage),
        "visual_gate": {
            "triggered": sum(bool(item["visual_gate_triggered"]) for item in results),
            "provider_calls": sum(item["visual_origin"] == "v5_provider_call" for item in results),
            "v4_cache_hits": sum(
                item["visual_origin"] == "v4_exact_input_cache" for item in results
            ),
            "modifications_accepted": accepted,
            "changed_samples": len(changed),
        },
        "span_mutations": sum(int(item.get("span_mutations", 0)) for item in results),
        "endpoint_swaps": sum(int(item.get("endpoint_swaps", 0)) for item in results),
    }
    if dataset == "twitter2017" and report["span_mutations"]:
        raise RuntimeError("paired MNER stage mutated a span")
    if dataset == "mnre-v2" and report["endpoint_swaps"]:
        raise RuntimeError("paired MRE stage swapped endpoints")
    v1.atomic_json(output / stage / dataset / "multimodal" / "report.json", report)
    return report


async def run_validation(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 10.0,
) -> dict[str, Any]:
    """Run the already-frozen V4 holdouts once without tuning."""
    reports = []
    for dataset in DATASETS:
        reports.append(
            await run_paired_dataset(
                output,
                dataset,
                "holdout",
                settings,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    payload = {"passed": True, "reports": reports}
    v1.atomic_json(output / "validation-summary.json", payload)
    return payload


async def run_multimodal(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 10.0,
) -> dict[str, Any]:
    """Run complete MNER then MRE paired visual test cells."""
    validation = dict(v1.load_json(output / "validation-summary.json"))
    if not validation.get("passed"):
        raise RuntimeError("V5 holdout validation has not passed")
    reports = []
    for dataset in DATASETS:
        reports.append(
            await run_paired_dataset(
                output,
                dataset,
                "main",
                settings,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    payload = {"reports": reports}
    v1.atomic_json(output / "main-summary.json", payload)
    return payload


def _records(
    output: Path, dataset: DatasetName, variant: VariantName
) -> list[dict[str, Any]]:
    directory = (
        _paired_prediction_dir(output, "main", dataset)
        if variant == "multimodal"
        else _copied_prediction_dir(output, "main", dataset, variant)
    )
    return sorted(
        [dict(v1.load_json(path)) for path in directory.glob("*.json")],
        key=lambda item: str(item["id"]),
    )


def _contribution(records: list[dict[str, Any]], dataset: DatasetName) -> dict[str, Any]:
    changed = [item for item in records if item["changed_by_visual"]]
    improved = 0
    worsened = 0
    unchanged_score = 0
    for item in changed:
        if dataset == "mnre-v2":
            before = item["schema_predicted"] == item["gold"]
            after = item["predicted"] == item["gold"]
            improved += int(not before and after)
            worsened += int(before and not after)
            unchanged_score += int(before == after)
        else:
            baseline_entities = [
                twitter.PredictedEntity.model_validate(value)
                for value in item["schema_predicted"]
            ]
            case_metrics = dict(item["metrics"])
            gold = [twitter.GoldEntity.model_validate(value) for value in item["gold"]]
            synthetic = twitter.TwitterCase(
                id=str(item["id"]),
                split="test",
                tokens=[],
                text="",
                text_sha256="",
                image_path="",
                image_sha256=None,
                image_valid=True,
                invalid_image_reason=None,
                entities=gold,
            )
            before_metrics = twitter._result_metrics(synthetic, baseline_entities)
            before_score = (before_metrics["tp"], -before_metrics["fp"], -before_metrics["fn"])
            after_score = (case_metrics["tp"], -case_metrics["fp"], -case_metrics["fn"])
            improved += int(after_score > before_score)
            worsened += int(after_score < before_score)
            unchanged_score += int(after_score == before_score)
    return {
        "changed_samples": len(changed),
        "improved_samples": improved,
        "worsened_samples": worsened,
        "changed_but_score_unchanged": unchanged_score,
        "net_improved_minus_worsened": improved - worsened,
    }


def export_results(output: Path) -> dict[str, Any]:
    """Assemble reused V4 rows with the paired V5 multimodal row."""
    _require_frozen(output)
    rows: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    contribution: dict[str, Any] = {}
    source_v4 = Path(str(v1.load_json(output / "manifest.json")["source_v4_path"]))
    for dataset in DATASETS:
        expected = EXPECTED[(dataset, "main")]
        records_by_variant = {variant: _records(output, dataset, variant) for variant in VARIANTS}
        if any(len(records) != expected for records in records_by_variant.values()):
            raise RuntimeError(f"{dataset} V5 results are incomplete")
        schema_ids = [str(item["id"]) for item in records_by_variant["schema"]]
        for variant, records in records_by_variant.items():
            if [str(item["id"]) for item in records] != schema_ids:
                raise RuntimeError(f"{dataset}/{variant} sample IDs do not match Schema")
            metrics = (
                v1.aggregate_twitter(records)
                if dataset == "twitter2017"
                else v1.aggregate_mnre(records)
            )
            if variant == "multimodal":
                report = dict(
                    v1.load_json(output / "main" / dataset / variant / "report.json")
                )
                usage = report["usage"]
                origin = EXPERIMENT_VERSION
            else:
                source_report = dict(
                    v1.load_json(source_v4 / "main" / dataset / variant / "report.json")
                )
                usage = source_report["usage"]
                origin = v4.EXPERIMENT_VERSION
                report = {
                    "dataset": dataset,
                    "variant": variant,
                    "variant_label": VARIANT_LABELS[variant],
                    "stage": "main",
                    "execution_origin": origin,
                    "metrics": metrics,
                    "usage": usage,
                }
                v1.atomic_json(output / "main" / dataset / variant / "report.json", report)
            rows.append(
                {
                    "dataset": "Twitter-2017" if dataset == "twitter2017" else "MNRE-V2",
                    "dataset_id": dataset,
                    "variant": variant,
                    "variant_label": VARIANT_LABELS[variant],
                    "execution_origin": origin,
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["micro_f1"],
                    "macro_f1": metrics["macro_f1"],
                    "f1_ci_lower": metrics["f1_95_ci"]["lower"],
                    "f1_ci_upper": metrics["f1_95_ci"]["upper"],
                    "cost_cny": usage["estimated_cost_cny"],
                    "average_latency_ms": usage["average_latency_ms"],
                    "errors": metrics["errors"],
                }
            )
        for left, right in zip(VARIANTS[:-1], VARIANTS[1:], strict=True):
            paired.append(
                {
                    "dataset": dataset,
                    "left": left,
                    "right": right,
                    **v1._paired_bootstrap_delta(
                        records_by_variant[left], records_by_variant[right]
                    ),
                }
            )
        contribution[dataset] = _contribution(records_by_variant["multimodal"], dataset)
        if not contribution[dataset]["changed_samples"]:
            schema_metrics = next(
                row for row in rows if row["dataset_id"] == dataset and row["variant"] == "schema"
            )
            multimodal_metrics = next(
                row
                for row in rows
                if row["dataset_id"] == dataset and row["variant"] == "multimodal"
            )
            for field in (
                "precision",
                "recall",
                "f1",
                "macro_f1",
                "f1_ci_lower",
                "f1_ci_upper",
            ):
                if schema_metrics[field] != multimodal_metrics[field]:
                    raise RuntimeError(
                        f"{dataset} unchanged visual output does not reproduce Schema {field}"
                    )
    payload = {
        "experiment_version": EXPERIMENT_VERSION,
        "rows": rows,
        "paired_bootstrap": paired,
        "visual_contribution": contribution,
        "paid_stability_repetitions": 0,
        "manifest": v1.load_json(output / "manifest.json"),
    }
    v1.atomic_json(output / "results.json", payload)
    v1.atomic_json(output / "visual-contribution.json", contribution)
    headers = [
        "dataset",
        "variant",
        "execution_origin",
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


def evaluation_status(output: Path) -> dict[str, Any]:
    """Return resumable V5 progress, provenance, budget, and gate status."""
    def optional(path: Path) -> Any:
        return v1.load_json(path) if path.exists() else None

    cells = []
    for stage in ("holdout", "main"):
        for dataset in DATASETS:
            cells.append(
                {
                    "stage": stage,
                    "dataset": dataset,
                    "schema_reused": sum(
                        1
                        for _ in _copied_prediction_dir(
                            output, stage, dataset, "schema"
                        ).glob("*.json")
                    ),
                    "multimodal_predictions": sum(
                        1 for _ in _paired_prediction_dir(output, stage, dataset).glob("*.json")
                    ),
                }
            )
    return {
        "manifest": optional(output / "manifest.json"),
        "frozen": optional(output / "frozen-config.json"),
        "cells": cells,
        "validation": optional(output / "validation-summary.json"),
        "main": optional(output / "main-summary.json"),
        "budget": optional(output / "budget.json"),
        "results": optional(output / "results.json"),
        "error_counts": dict(
            Counter(
                str(error)
                for path in output.glob("**/multimodal/predictions/*.json")
                for error in dict(v1.load_json(path)).get("errors", [])
            )
        ),
    }

