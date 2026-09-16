"""Live document validation against an isolated JSON graph, without gold-assisted review."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from prismke.core.ids import file_sha256, stable_id
from prismke.core.settings import Settings
from prismke.domain import (
    CanonicalEntity,
    ExtractionRequest,
    ExtractionResult,
    GraphCommit,
    GraphRevision,
    TextBlock,
)
from prismke.evaluation.request_budget import BudgetedTransport, RequestBudget
from prismke.governance.entity_index import rebuild_entity_index
from prismke.persistence.json_graph import JSONGraphStore
from prismke.providers.base import LLMProvider, VLMProvider
from prismke.providers.openai_compatible import OpenAICompatibleLLMProvider
from prismke.providers.vlm import OpenAICompatibleVLMProvider
from prismke.workflow.service import PrismKEService


class _EvaluationLLM(OpenAICompatibleLLMProvider):
    def fingerprint(self) -> str:
        return stable_id(
            "provider", super().fingerprint(), "evaluation-output-limit-v3", 4096, 12000
        )

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        batches = text_batches(request.document.text_blocks)
        combined = ExtractionResult()
        for batch in batches:
            subset = request.document.model_copy(update={"text_blocks": batch})
            result = await super().extract(request.model_copy(update={"document": subset}))
            combined.candidates.extend(result.candidates)
            combined.warnings.extend(result.warnings)
            combined.call_records.extend(result.call_records)
        combined.warnings.append(f"evaluation_text_batches_completed:{len(batches)}")
        if any(len(block.text.encode("utf-8")) > 12000 for block in request.document.text_blocks):
            combined.warnings.append("evaluation_oversized_text_block_processed_alone")
        return combined


def text_batches(blocks: list[TextBlock], max_bytes: int = 12000) -> list[list[TextBlock]]:
    batches: list[list[TextBlock]] = []
    batch: list[TextBlock] = []
    size = 0
    for block in blocks:
        block_size = len(block.text.encode("utf-8"))
        if batch and size + block_size > max_bytes:
            batches.append(batch)
            batch, size = [], 0
        batch.append(block)
        size += block_size
    if batch:
        batches.append(batch)
    return batches


class _EvaluationVLM(OpenAICompatibleVLMProvider):
    def fingerprint(self) -> str:
        return stable_id("provider", super().fingerprint(), "evaluation-output-limit-v2", 4096)


class _EvaluationService(PrismKEService):
    def __init__(self, settings: Settings, store: JSONGraphStore, budget: RequestBudget) -> None:
        super().__init__(settings, graph_store=store)
        self.budget = budget

    def provider(self, name: str) -> LLMProvider:
        original = super().provider(name)
        if not isinstance(original, OpenAICompatibleLLMProvider):
            raise ValueError("live validation requires a real text provider")
        return _EvaluationLLM(
            original.base_url,
            original.api_key,
            original.model,
            original.timeout,
            transport=BudgetedTransport(self.budget),
        )

    def vlm_provider(self, name: str) -> VLMProvider:
        original = super().vlm_provider(name)
        if not isinstance(original, OpenAICompatibleVLMProvider):
            raise ValueError("live validation requires a real visual provider")
        return _EvaluationVLM(
            original.base_url,
            original.api_key,
            original.model,
            original.timeout,
            original.max_image_edge,
            transport=BudgetedTransport(self.budget),
        )


async def validate_documents(
    manifest_path: Path,
    settings: Settings,
    output: Path,
    *,
    token_limit: int = 100_000,
    stop_at: int = 90_000,
) -> dict[str, Any]:
    budget = RequestBudget(
        limit=token_limit, stop_at=stop_at, ledger_path=output / "request-ledger.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if output.exists():
        raise ValueError("choose a fresh validation output directory")
    cases = manifest["cases"]
    if len({item["id"] for item in cases}) != len(cases):
        raise ValueError("duplicate document case IDs")
    inputs = []
    for case in cases:
        path = (manifest_path.parent / case["input_path"]).resolve()
        schema = (manifest_path.parent / case["schema_path"]).resolve()
        if not path.is_file() or not schema.is_file():
            raise ValueError(f"missing input/schema for {case['id']}")
        if case.get("sha256") and file_sha256(path) != case["sha256"]:
            raise ValueError(f"document hash mismatch: {case['id']}")
        inputs.append((case["id"], path, schema))
    original_graph = settings.graph_dir / "graph.json"
    before = file_sha256(original_graph) if original_graph.exists() else None
    isolated = settings.model_copy(
        update={
            "runtime_dir": output,
            "graph_store": "json",
            "embedding_allow_download": False,
            "embedding_model_cache": settings.embedding_model_cache_dir.resolve(),
        }
    )
    store = JSONGraphStore(output / "graph")
    service = _EvaluationService(isolated, store, budget)
    report: dict[str, Any] = {
        "graph_backend": "isolated_json",
        "full_text_precision_f1": "not_evaluated",
        "manual_reviews_auto_approved": False,
        "manifest_sha256": file_sha256(manifest_path),
        "cases": [],
        "token_target": budget.limit,
        "token_stop_threshold": budget.stop_at,
        "max_output_tokens": budget.max_output_tokens,
        "bailian_qwen_enable_thinking": False,
        "text_batch_max_utf8_bytes": 12000,
    }
    try:
        service.provider("openai-compatible")
        service.vlm_provider("openai-compatible")
        if isolated.embedding_provider != "bge-m3":
            raise ValueError("live document validation requires prepared real BGE-M3")
        provider = service.embedding_provider()
        report["embedding_fingerprint"] = provider.fingerprint()
        if manifest.get("seed_kb"):
            seed_path = (manifest_path.parent / manifest["seed_kb"]).resolve()
            seed = json.loads(seed_path.read_text(encoding="utf-8"))
            entities = [CanonicalEntity.model_validate(item) for item in seed["entities"]]
            report["seed_entities"] = len(entities)
            report["seed_kb_sha256"] = file_sha256(seed_path)
            await store.commit(
                GraphCommit(
                    entities=entities,
                    revision=GraphRevision(
                        id="revision:document-validation-seed",
                        run_id="document-validation-seed",
                        entity_ids=[item.id for item in entities],
                    ),
                )
            )
            await rebuild_entity_index(
                store, provider, backend="json", batch_size=32, dry_run=False
            )
        for index, (case_id, path, schema) in enumerate(inputs):
            if budget.stopped_reason or budget.total_tokens >= budget.stop_at:
                break
            print(f"Validating {case_id}; used tokens={budget.total_tokens}", flush=True)
            budget.case_id = case_id
            started = time.perf_counter()
            try:
                state = await service.run(
                    path, schema, "openai-compatible", "paddle", "openai-compatible"
                )
            except Exception as exc:
                await budget.settle()
                report["cases"].append(
                    {
                        "id": case_id,
                        "status": "budget_stopped" if budget.stopped_reason else "failed",
                        "error_type": type(exc).__name__,
                        "seconds": time.perf_counter() - started,
                    }
                )
                if not budget.stopped_reason:
                    budget.stopped_reason = "document workflow failed; inspect saved run"
                break
            evidence_ids = {eid for candidate in state.candidates for eid in candidate.evidence_ids}
            verified = sum([await service.evidence_store.verify(eid) for eid in evidence_ids])
            row = {
                "id": case_id,
                "run_id": state.run_id,
                "status": state.status,
                "text_candidates": len(state.text_candidates),
                "visual_candidates": len(state.visual_candidates),
                "fused_candidates": len(state.candidates),
                "claims": len(state.claims),
                "entity_reviews": sum(
                    task.status == "pending" for task in state.entity_review_tasks
                ),
                "claim_reviews": sum(task.status == "pending" for task in state.review_tasks),
                "verified_evidence": verified,
                "referenced_evidence": len(evidence_ids),
                "warnings": state.warnings,
                "error_types": [error.split(":", 1)[0] for error in state.errors],
                "seconds": time.perf_counter() - started,
                "provider_calls": [call.model_dump(mode="json") for call in state.provider_calls],
                "observations": len(state.document.visual_observations) if state.document else 0,
            }
            report["cases"].append(row)
            print(
                json.dumps(
                    {k: v for k, v in row.items() if k not in {"warnings", "provider_calls"}}
                ),
                flush=True,
            )
            if budget.stopped_reason or index < 2 and state.status == "failed":
                break
    finally:
        await budget.settle()
        await service.close()
        after = file_sha256(original_graph) if original_graph.exists() else None
        report.update(
            {
                "production_json_unchanged": before == after,
                "production_json_before": before,
                "production_json_after": after,
                "total_tokens": budget.total_tokens,
                "token_accounting_complete": budget.accounting_complete,
                "request_ledger": budget.calls,
                "stop_reason": budget.stopped_reason,
                "unprocessed_case_ids": [item[0] for item in inputs[len(report["cases"]) :]],
                "token_estimation": (
                    "UTF-8 text bytes + 8192/image + output limit + 1024 overhead; "
                    "conservative estimate, not provider billing"
                ),
            }
        )
        try:
            report["code_commit"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            report["code_commit"] = "unknown"
        output.mkdir(parents=True, exist_ok=True)
        (output / "document-validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
        )
        if before != after:
            raise RuntimeError("production JSON graph changed during validation")
    return report
