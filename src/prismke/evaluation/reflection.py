"""Isolated nine-cell case retrieval and Reflection release evaluation."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from prismke.core.ids import canonical_hash, stable_id
from prismke.core.settings import Settings
from prismke.domain import (
    CandidateClaim,
    CaseRecord,
    DocumentIR,
    EvidenceKind,
    EvidenceRef,
    Modality,
    OutputSchema,
    WorkflowState,
)
from prismke.evaluation.request_budget import (
    BudgetedTransport,
    EvaluationBudgetStop,
    RequestBudget,
)
from prismke.persistence import CaseRepository, FileEvidenceStore
from prismke.providers import (
    MockEmbeddingProvider,
    MockReflectionProvider,
    OpenAICompatibleReflectionProvider,
)
from prismke.providers.base import EmbeddingProvider, ReflectionProvider
from prismke.workflow.cases import CaseRetriever
from prismke.workflow.reflection import BoundedReflectionService


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _candidate_content(candidate: CandidateClaim) -> dict[str, Any]:
    return candidate.model_dump(mode="json", exclude={"id"})


def _summary(candidate: CandidateClaim) -> str:
    target = candidate.object.name if hasattr(candidate.object, "name") else candidate.object
    return " | ".join(
        [
            candidate.subject.name,
            candidate.subject.entity_type,
            candidate.relation,
            str(target),
            candidate.subject.context,
        ]
    )


def _seed_cases(
    repository: CaseRepository,
    samples: list[dict[str, Any]],
    schema_fingerprint: str,
) -> dict[str, str]:
    relevant: dict[str, str] = {}
    for sample in samples:
        original = CandidateClaim.model_validate(sample["candidate"])
        corrected = CandidateClaim.model_validate(sample["expected_candidate"])
        key = str(sample["relevant_case_key"])
        good_id = f"case:{key}:good"
        relevant[key] = good_id
        for case_type, candidate, decision in (
            ("good", corrected, "approve"),
            ("bad", original, "reject"),
        ):
            case_id = f"case:{key}:{case_type}"
            repository.add(
                CaseRecord(
                    id=case_id,
                    run_id=f"eval-dev:{sample['id']}",
                    case_type=case_type,
                    task_type="claim",
                    schema_fingerprint=schema_fingerprint,
                    language=str(sample["language"]),
                    input_summary=_summary(candidate),
                    candidate_snapshot={"candidate": candidate.model_dump(mode="json")},
                    decision=decision,
                    reasons=[f"reviewed development example: {sample['category']}"],
                    evidence_ids=list(corrected.evidence_ids),
                    source_review_event_id=f"eval-event:{sample['id']}:{case_type}",
                )
            )
    return relevant


async def _document(sample: dict[str, Any], evidence_store: FileEvidenceStore) -> DocumentIR:
    text = str(sample["text"])
    source_hash = await evidence_store.put_blob(text.encode("utf-8"), "text/plain")
    evidence_id = f"evidence:{sample['id']}"
    reference = EvidenceRef(
        id=evidence_id,
        kind=EvidenceKind.TEXT_SPAN,
        document_id=f"document:{sample['id']}",
        source_hash=source_hash,
        modality=Modality.TEXT,
    )
    await evidence_store.put_ref(reference)
    return DocumentIR(
        id=reference.document_id,
        source_path=f"{sample['id']}.txt",
        source_filename=f"{sample['id']}.txt",
        source_hash=source_hash,
        media_type="text/plain",
        evidence=[reference],
    )


def _reflection_provider(
    settings: Settings,
    name: str,
    budget: RequestBudget,
) -> ReflectionProvider:
    if name == "mock":
        return MockReflectionProvider()
    if name != "openai-compatible":
        raise ValueError("reflection provider must be mock or openai-compatible")
    if not settings.llm_api_key or not settings.llm_model or not settings.llm_base_url:
        raise ValueError("real Reflection evaluation requires configured LLM endpoint")
    return OpenAICompatibleReflectionProvider(
        settings.llm_base_url,
        settings.llm_api_key,
        settings.llm_model,
        settings.request_timeout,
        BudgetedTransport(budget),
    )


def _embedding_provider(settings: Settings, name: str) -> EmbeddingProvider:
    if name == "mock":
        return MockEmbeddingProvider()
    if name != "bge-m3":
        raise ValueError("embedding provider must be mock or bge-m3")
    from prismke.providers import BGEM3EmbeddingProvider

    return BGEM3EmbeddingProvider(
        model_name=settings.embedding_model,
        model_revision=settings.embedding_model_revision,
        device=settings.embedding_device,
        use_fp16=settings.embedding_use_fp16,
        batch_size=settings.embedding_batch_size,
        max_tokens=settings.embedding_max_tokens,
        cache_dir=settings.embedding_cache_dir,
        model_cache_dir=settings.embedding_model_cache_dir,
        allow_download=settings.embedding_allow_download,
    )


def _configuration_name(case_mode: str, attempts: int) -> str:
    return f"cases={case_mode};reflection={attempts}"


async def evaluate_reflection_manifest(
    manifest_path: Path,
    output: Path,
    *,
    settings: Settings | None = None,
    reflection_provider_name: str = "mock",
    embedding_provider_name: str = "mock",
    token_limit: int = 200_000,
    stop_at: int = 180_000,
) -> dict[str, Any]:
    if not 0 < stop_at < token_limit:
        raise ValueError("budget must satisfy 0 < stop_at < token_limit")
    settings = settings or Settings()
    output.mkdir(parents=True, exist_ok=True)
    manifest = _load(manifest_path)
    base = manifest_path.parent
    schema = OutputSchema.model_validate(_load(base / manifest["schema"]))
    schema_fingerprint = canonical_hash(schema.model_dump(mode="json"))
    development = [_load(base / item) for item in manifest["development"]]
    final = [_load(base / item) for item in manifest["test"]]
    if len(development) != 6 or len(final) != 12:
        raise ValueError("v0.9 evaluation requires 6 development and 12 final samples")
    repository = CaseRepository(output / "cases.sqlite")
    relevant = _seed_cases(repository, development, schema_fingerprint)
    embeddings = _embedding_provider(settings, embedding_provider_name)
    retriever = CaseRetriever(repository, embeddings)
    await retriever.rebuild()
    budget = RequestBudget(
        limit=token_limit,
        stop_at=stop_at,
        ledger_path=output / "request-ledger.json",
    )
    provider = _reflection_provider(settings, reflection_provider_name, budget)
    evidence_store = FileEvidenceStore(output / "evidence")
    configurations = [
        (case_mode, attempts)
        for case_mode in ("none", "good", "good_bad")
        for attempts in (0, 1, 2)
    ]
    report: dict[str, Any] = {
        "version": str(manifest["version"]),
        "schema_fingerprint": schema_fingerprint,
        "reflection_provider": provider.fingerprint(),
        "embedding_provider": embeddings.fingerprint(),
        "token_limit": token_limit,
        "stop_at": stop_at,
        "development_samples": len(development),
        "test_samples": len(final),
        "configurations": [],
        "stopped_reason": None,
    }
    stop = False
    for case_mode, attempts in configurations:
        name = _configuration_name(case_mode, attempts)
        result: dict[str, Any] = {"name": name, "samples": []}
        for sample in final:
            budget.case_id = f"{name}:{sample['id']}"
            document = await _document(sample, evidence_store)
            original = CandidateClaim.model_validate(sample["candidate"])
            state = WorkflowState(
                run_id=stable_id("reflection-eval", name, sample["id"]),
                input_path=f"{sample['id']}.txt",
                schema_path=str(base / manifest["schema"]),
                pipeline_version="0.9.0",
                output_schema=schema,
                document=document,
                candidates=[original.model_copy(deep=True)],
                original_candidates=[original.model_copy(deep=True)],
                case_mode=case_mode,
                case_snapshot_ids=retriever.snapshot_ids(),
                reflection_enabled=attempts > 0,
                reflection_provider_name=reflection_provider_name,
                reflection_provider_fingerprint=provider.fingerprint(),
                reflection_policy_version="bounded-reflection-v1",
                reflection_max_attempts=attempts,
                reflection_token_budget=20_000,
                reflection_time_budget_seconds=180,
            )
            service = BoundedReflectionService(
                provider,
                retriever if case_mode != "none" else None,
                evidence_store,
            )
            try:
                state = await service.run(state)
            except EvaluationBudgetStop as exc:
                report["stopped_reason"] = str(exc)
                stop = True
                break
            output_candidate = state.candidates[0]
            expected_raw = sample.get("expected_candidate")
            expected = CandidateClaim.model_validate(expected_raw) if expected_raw else None
            original_content = _candidate_content(original)
            output_content = _candidate_content(output_candidate)
            expected_content = _candidate_content(expected) if expected else None
            retrieved_ids = [item.case_id for item in state.retrieved_cases]
            relevant_id = relevant.get(str(sample.get("relevant_case_key")))
            evidence_checks = [
                await evidence_store.exists(item)
                and await evidence_store.verify(item)
                for item in output_candidate.evidence_ids
            ]
            evidence_valid = all(evidence_checks)
            result["samples"].append(
                {
                    "id": sample["id"],
                    "category": sample["category"],
                    "repairable": bool(sample["repairable"]),
                    "fixed": expected_content is not None and output_content == expected_content,
                    "changed": output_content != original_content,
                    "wrong_rewrite": output_content != original_content
                    and output_content != expected_content,
                    "blocking_issues": state.validation.blocking_count,
                    "evidence_valid": evidence_valid,
                    "relevant_case_id": relevant_id,
                    "retrieved_case_ids": retrieved_ids,
                    "recall_at_5": relevant_id in retrieved_ids[:5] if relevant_id else None,
                    "attempts": [
                        item.model_dump(mode="json") for item in state.reflection_attempts
                    ],
                    "output_candidate": output_candidate.model_dump(mode="json"),
                }
            )
            _write_atomic(output / "report.json", report)
            if budget.stopped_reason or budget.total_tokens >= stop_at:
                report["stopped_reason"] = budget.stopped_reason or "token stop threshold reached"
                stop = True
                break
        report["configurations"].append(result)
        if stop:
            break
    await budget.settle()
    rows = [row for config in report["configurations"] for row in config["samples"]]
    attempts_rows = [attempt for row in rows for attempt in row["attempts"]]
    structured = [
        attempt
        for attempt in attempts_rows
        if not any(str(w).startswith("invalid_reflection_response") for w in attempt["warnings"])
    ]
    release_config: dict[str, Any] = next(
        (
            item
            for item in report["configurations"]
            if item["name"] == "cases=good_bad;reflection=2"
        ),
        {"samples": []},
    )
    release_rows = release_config["samples"]
    repairable = [row for row in release_rows if row["repairable"]]
    recall_rows = [row for row in release_rows if row["recall_at_5"] is not None]
    metrics = {
        "structured_json_success_rate": (
            len(structured) / len(attempts_rows) if attempts_rows else 1.0
        ),
        "case_recall_at_5": (
            sum(bool(row["recall_at_5"]) for row in recall_rows) / len(recall_rows)
            if recall_rows
            else 0.0
        ),
        "repair_rate": (
            sum(bool(row["fixed"]) for row in repairable) / len(repairable) if repairable else 0.0
        ),
        "wrong_rewrite_rate": (
            sum(bool(row["wrong_rewrite"]) for row in release_rows) / len(release_rows)
            if release_rows
            else 0.0
        ),
        "evidence_valid_rate": (
            sum(bool(row["evidence_valid"]) for row in release_rows) / len(release_rows)
            if release_rows
            else 0.0
        ),
        "illegal_schema_passes": sum(
            row["blocking_issues"] == 0 and row["category"] == "unrepairable"
            for row in release_rows
        ),
        "max_attempts_per_candidate": max((len(row["attempts"]) for row in rows), default=0),
        "token_usage": budget.total_tokens,
        "accounting_complete": budget.accounting_complete,
    }
    report["metrics"] = metrics
    report["request_ledger"] = budget.calls
    report["stopped_reason"] = report["stopped_reason"] or budget.stopped_reason
    report["publish_ready"] = bool(
        report["stopped_reason"] is None
        and metrics["structured_json_success_rate"] >= 0.95
        and metrics["case_recall_at_5"] >= 0.80
        and metrics["repair_rate"] >= 0.50
        and metrics["wrong_rewrite_rate"] <= 0.05
        and metrics["evidence_valid_rate"] == 1.0
        and metrics["illegal_schema_passes"] == 0
        and metrics["max_attempts_per_candidate"] <= 2
        and metrics["token_usage"] < token_limit
        and metrics["accounting_complete"]
        and len(report["configurations"]) == 9
        and all(len(item["samples"]) == 12 for item in report["configurations"])
    )
    _write_atomic(output / "report.json", report)
    return report
