"""Run a small, budgeted, isolated live smoke test for the v0.10 agents."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from prismke.core.ids import file_sha256
from prismke.core.settings import Settings
from prismke.domain import (
    CanonicalEntity,
    EntityAdviceRequest,
    EntityCandidate,
    EntityMention,
)
from prismke.evaluation.request_budget import (
    BudgetedTransport,
    EvaluationBudgetStop,
    RequestBudget,
)
from prismke.persistence.json_graph import JSONGraphStore
from prismke.providers.base import VLMProvider
from prismke.providers.openai_compatible import OpenAICompatibleLLMProvider
from prismke.providers.semantic import OpenAICompatibleSemanticAdvisor
from prismke.providers.vlm import OpenAICompatibleVLMProvider
from prismke.workflow.service import PrismKEService

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = (
    ("alias-zh", ROOT / "examples/eval_v0_2/11_alias_zh.md", "disabled"),
    ("alias-en", ROOT / "examples/eval_v0_2/12_alias_en.html", "disabled"),
    ("conflict-zh", ROOT / "examples/eval_v0_2/03_conflict_zh.md", "openai-compatible"),
)
SCHEMA = ROOT / "examples/eval_v0_2/schema.yaml"


class BudgetedAgentService(PrismKEService):
    def __init__(self, settings: Settings, budget: RequestBudget) -> None:
        super().__init__(settings, graph_store=JSONGraphStore(settings.graph_dir))
        self.budget = budget

    def provider(self, name: str) -> OpenAICompatibleLLMProvider:
        original = super().provider(name)
        if not isinstance(original, OpenAICompatibleLLMProvider):
            raise ValueError("live smoke test requires the real text provider")
        return OpenAICompatibleLLMProvider(
            original.base_url,
            original.api_key,
            original.model,
            original.timeout,
            transport=BudgetedTransport(self.budget),
        )

    def vlm_provider(self, name: str) -> VLMProvider:
        original = super().vlm_provider(name)
        if name == "disabled":
            return original
        if not isinstance(original, OpenAICompatibleVLMProvider):
            raise ValueError("live smoke test requires the real visual provider")
        return OpenAICompatibleVLMProvider(
            original.base_url,
            original.api_key,
            original.model,
            original.timeout,
            original.max_image_edge,
            transport=BudgetedTransport(self.budget),
        )

    def semantic_advisor(self, name: str) -> OpenAICompatibleSemanticAdvisor:
        original = super().semantic_advisor(name)
        if not isinstance(original, OpenAICompatibleSemanticAdvisor):
            raise ValueError("live smoke test requires the real semantic advisor")
        return OpenAICompatibleSemanticAdvisor(
            original.base_url,
            original.api_key,
            original.model,
            original.timeout,
            transport=BudgetedTransport(self.budget),
        )


async def _run(output: Path, env_file: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError("choose a fresh, isolated output directory")
    if not env_file.is_file():
        raise ValueError("configuration file is missing")
    output.mkdir(parents=True)
    budget = RequestBudget(
        limit=30_000,
        stop_at=27_000,
        max_output_tokens=2_048,
        ledger_path=output / "request-ledger.json",
    )
    original = Settings(_env_file=env_file)
    settings = original.model_copy(
        update={
            "runtime_dir": output / "runtime",
            "graph_store": "json",
            "embedding_allow_download": False,
            "embedding_model_cache": original.embedding_model_cache_dir.resolve(),
        }
    )
    if settings.llm_model != "qwen3.7-flash" or settings.vlm_model != "qwen3.7-flash":
        raise ValueError("live smoke test expects qwen3.7-flash for text and visual calls")
    if settings.embedding_provider != "bge-m3":
        raise ValueError("live smoke test requires the prepared BGE-M3 embedding provider")
    service = BudgetedAgentService(settings, budget)
    report: dict[str, Any] = {
        "code_version": "0.10.0.dev0",
        "graph_backend": "isolated_json",
        "token_limit": budget.limit,
        "stop_at": budget.stop_at,
        "samples": [],
        "advisor_probe": None,
        "stopped_reason": None,
    }
    try:
        for case_id, path, visual_provider in SAMPLES:
            if budget.stopped_reason or budget.total_tokens >= budget.stop_at:
                break
            budget.case_id = case_id
            state = await service.run(
                path,
                SCHEMA,
                "openai-compatible",
                vlm_provider_name=visual_provider,
                semantic_advisor_name="openai-compatible",
                agent_token_budget=5_000,
            )
            evidence_ids = {
                evidence_id
                for candidate in state.candidates
                for evidence_id in candidate.evidence_ids
            }
            evidence_valid = all(
                [await service.evidence_store.verify(item) for item in evidence_ids]
            )
            report["samples"].append(
                {
                    "case_id": case_id,
                    "source_sha256": file_sha256(path),
                    "run_id": state.run_id,
                    "status": state.status,
                    "modality_status": state.modality_status,
                    "agents": sorted({item.agent for item in state.agent_traces}),
                    "candidate_count": len(state.candidates),
                    "claim_count": len(state.claims),
                    "entity_review_count": sum(
                        item.status == "pending" for item in state.entity_review_tasks
                    ),
                    "claim_review_count": sum(
                        item.status == "pending" for item in state.review_tasks
                    ),
                    "evidence_valid": evidence_valid,
                    "model_tokens": sum(
                        item.total_tokens or 0 for item in state.provider_calls
                    ),
                }
            )
            if state.status == "failed" or not evidence_valid:
                report["stopped_reason"] = "sample failed or evidence verification failed"
                break
        if not report["stopped_reason"] and len(report["samples"]) == len(SAMPLES):
            budget.case_id = "semantic-advisor-probe"
            mention = EntityMention(
                id="mention:probe",
                name="Northstar Laboratory",
                entity_type="Organization",
                context="Northstar Laboratory developed AuroraGraph.",
                evidence_ids=["probe:synthetic"],
            )
            entity = CanonicalEntity(
                id="entity:probe",
                name="Northstar Labs",
                entity_type="Organization",
            )
            advice, call = await service.semantic_advisor(
                "openai-compatible"
            ).advise_entity(
                EntityAdviceRequest(
                    mention=mention,
                    candidates=[
                        EntityCandidate(
                            entity_id=entity.id,
                            retrieval_score=0.75,
                            name_score=0.75,
                            context_score=0.75,
                            final_score=0.75,
                        )
                    ],
                    candidate_entities=[entity],
                )
            )
            report["advisor_probe"] = {
                "action": advice.action,
                "candidate_id_valid": advice.selected_entity_id in {None, entity.id},
                "tokens": call.total_tokens if call else None,
                "auto_link_applied": False,
            }
    except EvaluationBudgetStop as exc:
        report["stopped_reason"] = str(exc)
    except Exception as exc:
        report["stopped_reason"] = f"sample_or_advisor_error:{type(exc).__name__}"
    finally:
        await budget.settle()
        await service.close()
        report["total_tokens"] = budget.total_tokens
        report["accounting_complete"] = budget.accounting_complete
        report["stopped_reason"] = report["stopped_reason"] or budget.stopped_reason
        (output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    report = asyncio.run(_run(args.output.resolve(), args.env_file.resolve()))
    print(
        json.dumps(
            {
                "samples": len(report["samples"]),
                "tokens": report["total_tokens"],
                "stopped_reason": report["stopped_reason"],
                "report": str(args.output.resolve() / "report.json"),
            },
            ensure_ascii=False,
        )
    )
    if report["stopped_reason"] or len(report["samples"]) != len(SAMPLES):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
