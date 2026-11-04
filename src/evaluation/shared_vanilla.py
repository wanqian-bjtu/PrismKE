"""One shared text-only Vanilla baseline for component and agent evaluations."""

from __future__ import annotations

import asyncio
import json
import os
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Literal

from src.core.ids import canonical_hash, file_sha256
from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.evaluation import component_ablation as v1
from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter

DatasetName = Literal["twitter2017", "mnre-v2"]
StageName = Literal["smoke", "main"]

EXPERIMENT_VERSION = "shared-vanilla-v1"
SCORING_VERSION = "component-ablation-scoring-v1"
SEED = 2027
BOOTSTRAP_SAMPLES = 10_000
BUDGET_LIMIT_CNY = 5.0
DATASETS: tuple[DatasetName, ...] = ("twitter2017", "mnre-v2")
TWITTER_LABELS: tuple[str, ...] = (
    "Person",
    "Organization",
    "Location",
    "Miscellaneous",
)
MNRE_LABELS: tuple[str, ...] = tuple(sorted(mnre.CANONICAL_TO_DATASET))

TWITTER_INSTRUCTION = (
    "Extract named entities from SOURCE text. Return JSON only as "
    '{"entities":[{"text":"...","start":0,"end":1,"type":"Person"}]}. '
    "Offsets use the Unicode half-open interval [start,end), and text must equal "
    "SOURCE[start:end]. Select types only from LABEL_IDS. If there are no entities, "
    'return {"entities":[]}.'
)
MNRE_INSTRUCTION = (
    "Classify the relation for the supplied ordered HEAD-TAIL pair in SOURCE. Select exactly "
    "one value from LABEL_IDS and return JSON only as "
    '{"relation":"MemberOf"}. Never exchange HEAD and TAIL.'
)


class SharedVanillaBudgetLedger(v1.AblationBudgetLedger):
    """Independent five-CNY ledger with 3/4.5 CNY progress milestones."""

    def record(self, operation_id: str, record: ProviderCallRecord) -> list[float]:
        before = self.cost
        crossed = super().record(operation_id, record)
        for milestone in (3.0, 4.5):
            if before < milestone <= self.cost and milestone not in self.payload["milestones"]:
                self.payload["milestones"].append(milestone)
                crossed.append(milestone)
        self.persist()
        return sorted(crossed)


def _artifact_name(case_id: str) -> str:
    return case_id.replace(":", "-") + ".json"


def _settings_fingerprint(settings: Settings) -> dict[str, Any]:
    return {
        "llm_model": settings.llm_model,
        "temperature": 0,
        "max_output_tokens": 1024,
        "enable_thinking": False,
        "response_format": {"type": "json_object"},
    }


def _twitter_cases(path: Path) -> list[twitter.TwitterCase]:
    return [twitter.TwitterCase.model_validate(item) for item in v1.load_json(path)]


def _mnre_cases(path: Path) -> list[mnre.MNRECase]:
    return [mnre.MNRECase.model_validate(item) for item in v1.load_json(path)]


def twitter_prompt(case: twitter.TwitterCase) -> str:
    """Build the canonical-label text-only MNER Vanilla prompt."""
    return (
        f"{TWITTER_INSTRUCTION}\n"
        f"LABEL_IDS: {json.dumps(TWITTER_LABELS, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(case.text, ensure_ascii=False)}"
    )


def mnre_prompt(case: mnre.MNRECase) -> str:
    """Build the canonical-label text-only ordered-pair MRE Vanilla prompt."""
    return (
        f"{MNRE_INSTRUCTION}\n"
        f"LABEL_IDS: {json.dumps(MNRE_LABELS, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(mnre.marked_text(case), ensure_ascii=False)}\n"
        f"HEAD: {json.dumps(case.head.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"TAIL: {json.dumps(case.tail.model_dump(mode='json'), ensure_ascii=False)}"
    )


def _write_frozen(path: Path, payload: Any) -> None:
    if path.exists():
        existing = v1.load_json(path)
        if existing != payload:
            raise RuntimeError(f"refusing to overwrite frozen artifact: {path}")
        return
    v1.atomic_json(path, payload)


def prepare_experiment(
    output: Path,
    twitter_source: Path,
    mnre_source: Path,
    twitter_dataset: Path,
    invalid_images_path: Path,
    settings: Settings,
) -> dict[str, Any]:
    """Freeze the shared prompt, test data, model settings, and input provenance."""
    invalid = twitter._invalid_images(invalid_images_path)
    twitter_cases = twitter.parse_annotation_split(
        twitter_dataset / "annotations" / "test.txt",
        twitter_dataset / "images",
        "test",
        invalid,
    )
    mnre_cases = _mnre_cases(mnre_source / "test_cases.json")
    if len(twitter_cases) != 723 or len(mnre_cases) != 1614:
        raise RuntimeError("accepted test split counts are unavailable")
    if sum(case.image_valid for case in twitter_cases) != 673:
        raise RuntimeError("Twitter-2017 valid-image count does not match the accepted split")

    output.mkdir(parents=True, exist_ok=True)
    twitter_path = output / "twitter2017" / "test_cases.json"
    mnre_path = output / "mnre-v2" / "test_cases.json"
    _write_frozen(
        twitter_path,
        [case.model_dump(mode="json") for case in twitter_cases],
    )
    _write_frozen(
        mnre_path,
        [case.model_dump(mode="json") for case in mnre_cases],
    )
    smoke = {
        "seed": SEED,
        "ids": {
            "twitter2017": v1._stratified_ids_twitter(twitter_cases, 20),
            "mnre-v2": v1._stratified_ids_mnre(mnre_cases, 20),
        },
    }
    _write_frozen(output / "smoke-split.json", smoke)

    prompt_protocol = {
        "twitter_instruction": TWITTER_INSTRUCTION,
        "twitter_labels": TWITTER_LABELS,
        "mnre_instruction": MNRE_INSTRUCTION,
        "mnre_labels": MNRE_LABELS,
        "forbidden_inputs": [
            "schema_definitions",
            "visual_descriptions",
            "retrieved_cases",
            "agent_prompts",
            "gold_labels",
        ],
    }
    manifest = {
        "experiment_version": EXPERIMENT_VERSION,
        "scoring_version": SCORING_VERSION,
        "code_commit": v1._git_commit(),
        "seed": SEED,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "budget_limit_cny": BUDGET_LIMIT_CNY,
        "settings": _settings_fingerprint(settings),
        "settings_hash": canonical_hash(_settings_fingerprint(settings)),
        "prompt_protocol": prompt_protocol,
        "prompt_protocol_hash": canonical_hash(prompt_protocol),
        "counts": {"twitter2017": 723, "mnre-v2": 1614},
        "test_cases": {
            "twitter2017": {
                "path": str(twitter_path.resolve()),
                "hash": canonical_hash(
                    [case.model_dump(mode="json") for case in twitter_cases]
                ),
            },
            "mnre-v2": {
                "path": str(mnre_path.resolve()),
                "hash": canonical_hash([case.model_dump(mode="json") for case in mnre_cases]),
            },
        },
        "source_provenance": {
            "twitter_source": str(twitter_source.resolve()),
            "twitter_test_annotations_sha256": file_sha256(
                twitter_dataset / "annotations" / "test.txt"
            ),
            "twitter_invalid_images_sha256": file_sha256(invalid_images_path),
            "mnre_source": str(mnre_source.resolve()),
            "mnre_test_cases_sha256": file_sha256(mnre_source / "test_cases.json"),
        },
        "shared_by": ["component-ablation-v4", "agent-progression-v1"],
    }
    _write_frozen(output / "manifest.json", manifest)
    frozen = {
        "experiment_version": EXPERIMENT_VERSION,
        "code_commit": manifest["code_commit"],
        "manifest_hash": canonical_hash(manifest),
        "prompt_protocol_hash": manifest["prompt_protocol_hash"],
        "settings_hash": manifest["settings_hash"],
        "model": settings.llm_model,
        "temperature": 0,
        "max_output_tokens": 1024,
        "budget_limit_cny": BUDGET_LIMIT_CNY,
    }
    _write_frozen(output / "frozen-config.json", frozen)
    SharedVanillaBudgetLedger(output / "budget.json", BUDGET_LIMIT_CNY)
    return manifest


def _cases_for(output: Path, dataset: DatasetName, stage: StageName) -> list[Any]:
    path = output / dataset / "test_cases.json"
    cases: list[Any] = _twitter_cases(path) if dataset == "twitter2017" else _mnre_cases(path)
    if stage == "smoke":
        ids = set(v1.load_json(output / "smoke-split.json")["ids"][dataset])
        cases = [case for case in cases if case.id in ids]
    return cases


def _usage(
    ledger: SharedVanillaBudgetLedger, dataset: DatasetName, stage: StageName
) -> dict[str, Any]:
    prefix = f"shared-vanilla-v1:{dataset}:{stage}:"
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


async def _run_one(
    output: Path,
    dataset: DatasetName,
    stage: StageName,
    case: twitter.TwitterCase | mnre.MNRECase,
    settings: Settings,
    ledger: SharedVanillaBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    prompt = twitter_prompt(case) if dataset == "twitter2017" else mnre_prompt(case)  # type: ignore[arg-type]
    prompt_hash = canonical_hash(prompt)
    operation_id = f"shared-vanilla-v1:{dataset}:{stage}:{case.id}"
    raw, provider_errors = await v1._provider_json(
        settings,
        ledger,
        prompt,
        operation_id,
        f"shared-vanilla-v1-{dataset}",
    )
    manifest = dict(v1.load_json(output / "manifest.json"))
    input_fingerprint = canonical_hash(
        {
            "dataset": dataset,
            "case_id": case.id,
            "source_sha256": case.text_sha256,
            "prompt_hash": prompt_hash,
            "settings_hash": manifest["settings_hash"],
        }
    )
    if dataset == "twitter2017":
        assert isinstance(case, twitter.TwitterCase)
        twitter_predicted, errors = v1._parse_twitter_prediction(
            case, raw, provider_errors
        )
        result = {
            "id": case.id,
            "dataset": dataset,
            "stage": stage,
            "source_text": case.text,
            "gold": [item.model_dump(mode="json") for item in case.entities],
            "predicted": [item.model_dump(mode="json") for item in twitter_predicted],
            "metrics": twitter._result_metrics(case, twitter_predicted),
            "image_valid": case.image_valid,
            "endpoint_swaps": 0,
        }
    else:
        assert isinstance(case, mnre.MNRECase)
        mnre_predicted, errors = v1._parse_mnre_prediction(raw, provider_errors)
        result = {
            "id": case.id,
            "dataset": dataset,
            "stage": stage,
            "source_text": case.text,
            "gold": case.relation,
            "gold_dataset_label": case.dataset_label,
            "predicted": mnre_predicted,
            "predicted_dataset_label": mnre.CANONICAL_TO_DATASET[mnre_predicted],
            "metrics": mnre._result_metrics(case, mnre_predicted),
            "endpoint_swaps": 0,
        }
    result.update(
        {
            "errors": errors,
            "raw_text": raw,
            "request_id": operation_id,
            "prompt_hash": prompt_hash,
            "input_fingerprint": input_fingerprint,
            "model": settings.llm_model,
            "temperature": 0,
            "max_output_tokens": 1024,
            "scoring_version": SCORING_VERSION,
        }
    )
    v1.atomic_json(target, result)
    return result


def _assert_report(report: dict[str, Any]) -> None:
    expected = 20 if report["stage"] == "smoke" else (
        723 if report["dataset"] == "twitter2017" else 1614
    )
    if int(report["metrics"]["cases"]) != expected:
        raise RuntimeError("shared Vanilla report has missing cases")
    if int(report.get("endpoint_swaps", 0)) != 0:
        raise RuntimeError("shared Vanilla changed ordered MNRE endpoints")


async def run_dataset(
    output: Path,
    dataset: DatasetName,
    stage: StageName,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = BUDGET_LIMIT_CNY,
) -> dict[str, Any]:
    """Run or resume one shared Vanilla dataset/stage."""
    if concurrency not in {1, 2}:
        raise ValueError("prediction concurrency must be 1 or 2")
    if budget_limit_cny != BUDGET_LIMIT_CNY:
        raise ValueError("Shared Vanilla v1 budget limit is frozen at 5 CNY")
    if not (output / "frozen-config.json").exists():
        raise RuntimeError("run prepare before predictions")
    if stage == "main":
        smoke_report = output / "smoke" / dataset / "report.json"
        if not smoke_report.exists():
            raise RuntimeError(f"complete and gate {dataset} smoke before main predictions")
        _assert_report(dict(v1.load_json(smoke_report)))
    if dataset == "mnre-v2" and stage == "main":
        twitter_report = output / "main" / "twitter2017" / "report.json"
        if not twitter_report.exists():
            raise RuntimeError("complete and gate MNER before starting MRE")
        _assert_report(dict(v1.load_json(twitter_report)))
    cases = _cases_for(output, dataset, stage)
    expected = 20 if stage == "smoke" else (723 if dataset == "twitter2017" else 1614)
    if len(cases) != expected:
        raise RuntimeError(f"unexpected {dataset} {stage} case count: {len(cases)}")
    ledger = SharedVanillaBudgetLedger(output / "budget.json", budget_limit_cny)
    directory = output / stage / dataset
    results: list[dict[str, Any]] = []
    next_index = 0
    first_error: BaseException | None = None

    async def worker() -> None:
        nonlocal next_index, first_error
        while first_error is None and next_index < len(cases):
            case = cases[next_index]
            next_index += 1
            try:
                results.append(
                    await _run_one(
                        output,
                        dataset,
                        stage,
                        case,
                        settings,
                        ledger,
                        directory / "predictions" / _artifact_name(case.id),
                    )
                )
            except BaseException as exc:
                first_error = exc
                return

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    if first_error is not None:
        raise first_error
    results.sort(key=lambda item: str(item["id"]))
    metrics = (
        v1.aggregate_twitter(results) if dataset == "twitter2017" else v1.aggregate_mnre(results)
    )
    report = {
        "experiment_version": EXPERIMENT_VERSION,
        "dataset": dataset,
        "stage": stage,
        "metrics": metrics,
        "usage": _usage(ledger, dataset, stage),
        "parse_error_count": sum(bool(item["errors"]) for item in results),
        "error_counts": dict(
            Counter(error for item in results for error in item.get("errors", []))
        ),
        "endpoint_swaps": sum(int(item.get("endpoint_swaps", 0)) for item in results),
        "prediction_set_hash": canonical_hash(results),
        "prompt_protocol_hash": v1.load_json(output / "manifest.json")[
            "prompt_protocol_hash"
        ],
    }
    _assert_report(report)
    v1.atomic_json(directory / "report.json", report)
    return report


async def run_smoke(
    output: Path, settings: Settings, *, concurrency: int = 2
) -> dict[str, Any]:
    reports: dict[str, Any] = {
        dataset: await run_dataset(
            output, dataset, "smoke", settings, concurrency=concurrency
        )
        for dataset in DATASETS
    }
    v1.atomic_json(output / "smoke-summary.json", reports)
    return reports


async def run_all(
    output: Path, settings: Settings, *, concurrency: int = 2
) -> dict[str, Any]:
    smoke = await run_smoke(output, settings, concurrency=concurrency)
    twitter_report = await run_dataset(
        output, "twitter2017", "main", settings, concurrency=concurrency
    )
    mnre_report = await run_dataset(
        output, "mnre-v2", "main", settings, concurrency=concurrency
    )
    summary = {"smoke": smoke, "twitter2017": twitter_report, "mnre-v2": mnre_report}
    v1.atomic_json(output / "run-all-summary.json", summary)
    return summary


def _prediction_records(output: Path, dataset: DatasetName) -> list[dict[str, Any]]:
    directory = output / "main" / dataset / "predictions"
    return sorted(
        [dict(v1.load_json(path)) for path in directory.glob("*.json")],
        key=lambda item: str(item["id"]),
    )


def _row(dataset: DatasetName, report: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(report["metrics"])
    return {
        "dataset": "Twitter-2017" if dataset == "twitter2017" else "MNRE-V2",
        "dataset_id": dataset,
        "variant": "vanilla",
        "variant_label": "Vanilla",
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["micro_f1"],
        "macro_f1": metrics["macro_f1"],
        "f1_ci_lower": metrics["f1_95_ci"]["lower"],
        "f1_ci_upper": metrics["f1_95_ci"]["upper"],
        "cost_cny": report["usage"]["estimated_cost_cny"],
        "average_latency_ms": report["usage"]["average_latency_ms"],
        "prediction_set_hash": report["prediction_set_hash"],
        "source_experiment": EXPERIMENT_VERSION,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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
        "prediction_set_hash",
    ]
    lines = [",".join(headers)]
    lines.extend(",".join(str(row.get(header, "")) for header in headers) for row in rows)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _source_manifest(output: Path) -> dict[str, Any]:
    datasets: dict[str, Any] = {}
    for dataset in DATASETS:
        paths = sorted((output / "main" / dataset / "predictions").glob("*.json"))
        records = _prediction_records(output, dataset)
        datasets[dataset] = {
            "count": len(paths),
            "ordered_sample_ids_hash": canonical_hash([item["id"] for item in records]),
            "prediction_set_hash": canonical_hash(records),
            "files": [
                {"name": path.name, "sha256": file_sha256(path)} for path in paths
            ],
        }
    return {
        "experiment_version": EXPERIMENT_VERSION,
        "manifest_hash": canonical_hash(v1.load_json(output / "manifest.json")),
        "frozen_config_hash": canonical_hash(v1.load_json(output / "frozen-config.json")),
        "datasets": datasets,
    }


def export_results(output: Path) -> dict[str, Any]:
    """Export the two shared rows and an immutable prediction provenance manifest."""
    rows: list[dict[str, Any]] = []
    for dataset in DATASETS:
        records = _prediction_records(output, dataset)
        expected = 723 if dataset == "twitter2017" else 1614
        if len(records) != expected:
            raise RuntimeError(f"{dataset} shared Vanilla predictions are incomplete")
        report = dict(v1.load_json(output / "main" / dataset / "report.json"))
        rows.append(_row(dataset, report))
    provenance = _source_manifest(output)
    payload = {
        "experiment_version": EXPERIMENT_VERSION,
        "rows": rows,
        "manifest": v1.load_json(output / "manifest.json"),
        "frozen_config": v1.load_json(output / "frozen-config.json"),
        "prediction_provenance": provenance,
    }
    v1.atomic_json(output / "prediction-source-manifest.json", provenance)
    v1.atomic_json(output / "results.json", payload)
    _write_csv(output / "results.csv", rows)
    return payload


def _write_integrated_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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
        "source_experiment",
        "prediction_set_hash",
    ]
    lines = [",".join(headers)]
    lines.extend(",".join(str(row.get(header, "")) for header in headers) for row in rows)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _integrated_component_results(
    output: Path, component_output: Path
) -> dict[str, Any]:
    from src.evaluation import component_ablation_v4 as component

    rows: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    for dataset in DATASETS:
        shared_records = _prediction_records(output, dataset)
        records_by_variant: dict[str, list[dict[str, Any]]] = {
            "vanilla": shared_records,
            **{
                variant: component._prediction_records(component_output, dataset, variant)
                for variant in component.VARIANTS
                if variant != "vanilla"
            },
        }
        expected = 723 if dataset == "twitter2017" else 1614
        if any(len(records) != expected for records in records_by_variant.values()):
            raise RuntimeError(f"{dataset} component integration is incomplete")
        shared_report = dict(v1.load_json(output / "main" / dataset / "report.json"))
        rows.append(_row(dataset, shared_report))
        for variant in component.VARIANTS[1:]:
            report = dict(
                v1.load_json(
                    component._report_directory(
                        component_output, "main", dataset, variant
                    )
                    / "report.json"
                )
            )
            metrics = (
                v1.aggregate_twitter(records_by_variant[variant])
                if dataset == "twitter2017"
                else v1.aggregate_mnre(records_by_variant[variant])
            )
            rows.append(
                {
                    "dataset": (
                        "Twitter-2017" if dataset == "twitter2017" else "MNRE-V2"
                    ),
                    "dataset_id": dataset,
                    "variant": variant,
                    "variant_label": component.VARIANT_LABELS[variant],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["micro_f1"],
                    "macro_f1": metrics["macro_f1"],
                    "f1_ci_lower": metrics["f1_95_ci"]["lower"],
                    "f1_ci_upper": metrics["f1_95_ci"]["upper"],
                    "cost_cny": report["usage"]["estimated_cost_cny"],
                    "average_latency_ms": report["usage"]["average_latency_ms"],
                    "source_experiment": component.EXPERIMENT_VERSION,
                    "prediction_set_hash": canonical_hash(records_by_variant[variant]),
                }
            )
        for left, right in zip(
            component.VARIANTS[:-1], component.VARIANTS[1:], strict=True
        ):
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
    payload = {
        "experiment_version": "component-ablation-v4-shared-vanilla-v1",
        "shared_vanilla_source": str(output.resolve()),
        "component_source": str(component_output.resolve()),
        "rows": rows,
        "paired_bootstrap": paired,
    }
    path = output / "component-ablation-v4-shared-vanilla-results.json"
    v1.atomic_json(path, payload)
    _write_integrated_csv(path.with_suffix(".csv"), rows)
    return payload


def _integrated_agent_results(output: Path, agent_output: Path) -> dict[str, Any]:
    from src.evaluation import agent_progression as agent

    rows: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    for dataset in DATASETS:
        shared_records = _prediction_records(output, dataset)
        records_by_variant: dict[str, list[dict[str, Any]]] = {
            "vanilla": shared_records,
            **{
                variant: agent._prediction_records(agent_output, dataset, variant)
                for variant in agent.VARIANTS
                if variant != "vanilla"
            },
        }
        expected = 723 if dataset == "twitter2017" else 1614
        if any(len(records) != expected for records in records_by_variant.values()):
            raise RuntimeError(f"{dataset} agent integration is incomplete")
        shared_report = dict(v1.load_json(output / "main" / dataset / "report.json"))
        vanilla_row = _row(dataset, shared_report)
        vanilla_row.update(agent._secondary_metrics(dataset, shared_records))
        vanilla_row["correction_accuracy"] = None
        rows.append(vanilla_row)
        previous = "vanilla"
        for variant in agent.VARIANTS[1:]:
            report = agent._main_report(agent_output, dataset, variant)
            metrics = (
                v1.aggregate_twitter(records_by_variant[variant])
                if dataset == "twitter2017"
                else v1.aggregate_mnre(records_by_variant[variant])
            )
            transition = agent._transition_stats(
                records_by_variant[previous], records_by_variant[variant]
            )
            transitions.append(
                {"dataset": dataset, "left": previous, "right": variant, **transition}
            )
            rows.append(
                {
                    "dataset": (
                        "Twitter-2017" if dataset == "twitter2017" else "MNRE-V2"
                    ),
                    "dataset_id": dataset,
                    "variant": variant,
                    "variant_label": agent.VARIANT_LABELS[variant],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["micro_f1"],
                    "macro_f1": metrics["macro_f1"],
                    "f1_ci_lower": metrics["f1_95_ci"]["lower"],
                    "f1_ci_upper": metrics["f1_95_ci"]["upper"],
                    **report["secondary_metrics"],
                    "correction_accuracy": transition["correction_accuracy"],
                    "cost_cny": report["usage"]["estimated_cost_cny"],
                    "average_latency_ms": report["usage"]["average_latency_ms"],
                    "source_experiment": agent.EXPERIMENT_VERSION,
                    "prediction_set_hash": canonical_hash(records_by_variant[variant]),
                }
            )
            previous = variant
        for left, right in zip(agent.VARIANTS[:-1], agent.VARIANTS[1:], strict=True):
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
    payload = {
        "experiment_version": "agent-progression-v1-shared-vanilla-v1",
        "shared_vanilla_source": str(output.resolve()),
        "agent_source": str(agent_output.resolve()),
        "rows": rows,
        "paired_bootstrap": paired,
        "transitions": transitions,
    }
    path = output / "agent-progression-v1-shared-vanilla-results.json"
    v1.atomic_json(path, payload)
    _write_integrated_csv(path.with_suffix(".csv"), rows)
    return payload


def export_integrated_results(
    output: Path,
    component_output: Path | None = None,
    agent_output: Path | None = None,
) -> dict[str, Any]:
    """Recompute both paper tables using the exact same Vanilla predictions."""
    shared = export_results(output)
    integrated: dict[str, Any] = {"shared": shared}
    if component_output is not None:
        integrated["component_ablation"] = _integrated_component_results(
            output, component_output
        )
    if agent_output is not None:
        integrated["agent_progression"] = _integrated_agent_results(output, agent_output)
    v1.atomic_json(output / "integrated-results.json", integrated)
    return integrated


def evaluation_status(output: Path) -> dict[str, Any]:
    def optional(path: Path) -> Any:
        return v1.load_json(path) if path.exists() else None

    cells = []
    for stage in ("smoke", "main"):
        for dataset in DATASETS:
            directory = output / stage / dataset
            cells.append(
                {
                    "stage": stage,
                    "dataset": dataset,
                    "predictions": sum(1 for _ in (directory / "predictions").glob("*.json")),
                    "report": optional(directory / "report.json"),
                }
            )
    return {
        "manifest": optional(output / "manifest.json"),
        "frozen_config": optional(output / "frozen-config.json"),
        "cells": cells,
        "budget": optional(output / "budget.json"),
        "results": optional(output / "results.json"),
    }
