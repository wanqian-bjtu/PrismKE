"""Live document validation against an isolated JSON graph, without gold-assisted review."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from prismke.core.ids import file_sha256, stable_id
from prismke.core.settings import Settings
from prismke.domain import (
    CandidateClaim,
    CanonicalEntity,
    DocumentIR,
    ExtractionRequest,
    ExtractionResult,
    GraphCommit,
    GraphRevision,
    OCRRequest,
    OCRResult,
    ProviderCallRecord,
    TextBlock,
)
from prismke.evaluation.request_budget import BudgetedTransport, EvaluationBudgetStop, RequestBudget
from prismke.governance.entity_index import rebuild_entity_index
from prismke.persistence.json_graph import JSONGraphStore
from prismke.providers.base import LLMProvider, OCRProvider, VLMProvider
from prismke.providers.openai_compatible import OpenAICompatibleLLMProvider
from prismke.providers.vlm import OpenAICompatibleVLMProvider
from prismke.workflow.service import PrismKEService


class _EvaluationLLM(OpenAICompatibleLLMProvider):
    cached_state: dict[str, Any] | None = None
    cache_dir: Path | None = None

    def fingerprint(self) -> str:
        return stable_id(
            "provider",
            super().fingerprint(),
            "evaluation-output-limit-v4",
            4096,
            12000,
            self.cached_state.get("run_id") if self.cached_state else None,
        )

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        combined = ExtractionResult()
        blocks = request.document.text_blocks
        if self.cached_state:
            cached = self.cached_state
            old_doc = cached["document"]
            expected_fingerprint = stable_id(
                "provider", super().fingerprint(), "evaluation-output-limit-v3", 4096, 12000
            )
            if cached.get("provider_fingerprint") != expected_fingerprint or cached.get(
                "status"
            ) not in {"completed", "awaiting_review"}:
                raise ValueError("cached text provider or completion provenance mismatch")
            if old_doc["source_hash"] != request.document.source_hash:
                raise ValueError("cached text source hash mismatch")
            if cached["output_schema"] != request.output_schema.model_dump(mode="json"):
                raise ValueError("cached text schema mismatch")
            old_blocks = [TextBlock.model_validate(row) for row in old_doc["text_blocks"]]
            ids = {block.id for block in old_blocks}
            if [block for block in blocks if block.id in ids] != old_blocks:
                raise ValueError("cached text blocks or evidence changed")
            llm_calls = [row for row in cached["provider_calls"] if row["provider"] == "llm"]
            if not llm_calls or any(
                row["requested_model"] != self.model
                or row["status"] != "succeeded"
                or row["prompt_version"] != "schema-claims-v1"
                for row in llm_calls
            ):
                raise ValueError("cached text model/protocol does not match real completed calls")
            combined.candidates = [
                CandidateClaim.model_validate(row) for row in cached["text_candidates"]
            ]
            current_refs = {ref.id for ref in request.document.evidence}
            if any(
                eid not in current_refs
                for candidate in combined.candidates
                for eid in candidate.evidence_ids
            ):
                raise ValueError("cached candidate evidence missing")
            combined.warnings.extend(w for w in cached["warnings"] if w.startswith("provider_"))
            combined.warnings.append(f"evaluation_reused_text_run:{cached['run_id']}")
            combined.warnings.append(f"evaluation_cached_text_blocks:{len(old_blocks)}")
            blocks = [block for block in blocks if block.id not in ids]
        batches = text_batches(blocks)
        for batch in batches:
            subset = request.document.model_copy(update={"text_blocks": batch})
            cache_path = None
            if self.cache_dir:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                key = stable_id(
                    "text-batch",
                    super().fingerprint(),
                    "batch-v1",
                    request.document.source_hash,
                    request.output_schema.model_dump(mode="json"),
                    [block.model_dump(mode="json") for block in batch],
                )
                cache_path = self.cache_dir / f"{key.replace(':', '-')}.json"
            if cache_path and cache_path.exists():
                result = ExtractionResult.model_validate_json(
                    cache_path.read_text(encoding="utf-8")
                )
                result.call_records = []
                result.warnings.append("evaluation_text_batch_cache_hit")
            else:
                result = await super().extract(request.model_copy(update={"document": subset}))
                if cache_path:
                    with tempfile.NamedTemporaryFile(
                        mode="w", encoding="utf-8", dir=cache_path.parent, delete=False
                    ) as stream:
                        temporary = Path(stream.name)
                        stream.write(result.model_dump_json())
                        stream.flush()
                        os.fsync(stream.fileno())
                    try:
                        os.replace(temporary, cache_path)
                    finally:
                        temporary.unlink(missing_ok=True)
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


class _ReusedOCR:
    def __init__(self, original: OCRProvider, state: dict[str, Any]) -> None:
        self.original, self.state = original, state

    def fingerprint(self) -> str:
        return stable_id(
            "provider",
            self.original.fingerprint(),
            "evaluation-reused-ocr-v1",
            self.state["run_id"],
        )

    async def recognize(self, request: OCRRequest) -> OCRResult:
        if self.state.get("ocr_provider_fingerprint") != self.original.fingerprint():
            raise ValueError("cached OCR provider fingerprint mismatch")
        downstream = {
            "load_schema",
            "extract_text_claims",
            "extract_visual_claims",
            "align_modalities",
            "resolve_entities",
            "normalize_claims",
        }
        if self.state.get("status") not in {"completed", "awaiting_review"} and (
            self.state.get("failed_node") not in downstream
        ):
            raise ValueError("cached OCR stage did not complete")
        cached = DocumentIR.model_validate(self.state["document"])
        if cached.source_hash != request.document.source_hash:
            raise ValueError("cached OCR source hash mismatch")

        def signature(document: DocumentIR) -> list[tuple[Any, ...]]:
            return [
                (a.id, a.blob_hash, a.width, a.height, a.page_number, a.origin)
                for a in document.media_assets
            ]

        if signature(cached) != signature(request.document):
            raise ValueError("cached OCR visual assets changed")
        for asset in request.document.media_assets:
            if not asset.blob_hash or file_sha256(Path(asset.path)) != asset.blob_hash:
                raise ValueError("cached OCR visual asset hash mismatch")
        warnings = [
            w
            for w in self.state.get("warnings", [])
            if w.startswith(("low_confidence_ocr:", "ocr_failed:"))
        ]
        if any(w.startswith("ocr_failed:") for w in warnings):
            raise ValueError("cached OCR contains failed assets")
        return OCRResult(
            text_blocks=[b for b in cached.text_blocks if b.modality == "ocr"],
            evidence=[e for e in cached.evidence if e.modality == "ocr"],
            warnings=[*warnings, f"evaluation_reused_ocr_run:{self.state['run_id']}"],
        )


class _EvaluationVLM(OpenAICompatibleVLMProvider):
    def fingerprint(self) -> str:
        return stable_id(
            "provider", super().fingerprint(), "evaluation-vision-output-limit-v3", 8192
        )

    async def _post(
        self, body: dict[str, Any], operation_id: str
    ) -> tuple[dict[str, Any], ProviderCallRecord]:
        return await super()._post({**body, "max_tokens": 8192}, operation_id)


class _EvaluationService(PrismKEService):
    cached_text_state: dict[str, Any] | None = None
    cached_ocr_state: dict[str, Any] | None = None

    def __init__(self, settings: Settings, store: JSONGraphStore, budget: RequestBudget) -> None:
        super().__init__(settings, graph_store=store)
        self.budget = budget

    def ocr_provider(self, name: str) -> OCRProvider:
        original = super().ocr_provider(name)
        return _ReusedOCR(original, self.cached_ocr_state) if self.cached_ocr_state else original

    def provider(self, name: str) -> LLMProvider:
        original = super().provider(name)
        if not isinstance(original, OpenAICompatibleLLMProvider):
            raise ValueError("live validation requires a real text provider")
        provider = _EvaluationLLM(
            original.base_url,
            original.api_key,
            original.model,
            original.timeout,
            transport=BudgetedTransport(self.budget),
        )
        provider.cached_state = self.cached_text_state
        cache_root = (
            self.budget.ledger_path.parent
            if self.budget.ledger_path is not None
            else self.settings.runtime_dir
        )
        provider.cache_dir = cache_root / "extraction-cache" / "text"
        return provider

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
    budget_ledger: Path | None = None,
    extend_budget: bool = False,
) -> dict[str, Any]:
    budget = RequestBudget(
        limit=token_limit,
        stop_at=stop_at,
        ledger_path=budget_ledger or output / "request-ledger.json",
        resume_ledger=budget_ledger is not None,
        extend_budget=extend_budget,
    )
    starting_tokens = budget.total_tokens
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
        "vision_max_output_tokens": 8192,
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
            cache = cases[index].get("reuse_text_run")
            service.cached_text_state = (
                json.loads((manifest_path.parent / cache).resolve().read_text(encoding="utf-8"))
                if cache
                else None
            )
            ocr_cache = cases[index].get("reuse_ocr_run")
            service.cached_ocr_state = (
                json.loads((manifest_path.parent / ocr_cache).resolve().read_text(encoding="utf-8"))
                if ocr_cache
                else None
            )
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
                        "status": "budget_stopped"
                        if isinstance(exc, EvaluationBudgetStop)
                        else "failed",
                        "error_type": type(exc).__name__,
                        "seconds": time.perf_counter() - started,
                    }
                )
                matching = [
                    saved
                    for saved in service.runs.list()
                    if saved.input_path == str(path) and saved.schema_path == str(schema)
                ]
                if matching:
                    report["cases"][-1]["run_id"] = matching[0].run_id
                    report["cases"][-1]["failed_node"] = matching[0].failed_node
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
                "starting_tokens": starting_tokens,
                "new_tokens": budget.total_tokens - starting_tokens,
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
