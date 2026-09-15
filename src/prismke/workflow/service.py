"""Application service shared by CLI and future API/UI adapters."""

from __future__ import annotations

from pathlib import Path

from prismke.core.errors import LegacyCheckpointError, ProviderConfigurationError
from prismke.core.ids import canonical_hash, file_sha256, stable_id
from prismke.core.settings import Settings
from prismke.domain import ClaimStatus, ReviewDecision, WorkflowState, load_schema, utc_now
from prismke.persistence import FileEvidenceStore, JSONGraphStore, RunRepository
from prismke.providers import MockLLMProvider, OpenAICompatibleLLMProvider
from prismke.providers.base import LLMProvider
from prismke.workflow.graph import PrismKEWorkflow

PIPELINE_VERSION = "0.1.1"


class PrismKEService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.runs = RunRepository(self.settings.runs_dir)
        self.graph_store = JSONGraphStore(self.settings.graph_dir)
        self.evidence_store = FileEvidenceStore(self.settings.evidence_dir)

    def provider(self, name: str) -> LLMProvider:
        if name == "mock":
            return MockLLMProvider()
        if name != "openai-compatible":
            raise ProviderConfigurationError(f"unknown provider: {name}")
        if not self.settings.llm_api_key:
            raise ProviderConfigurationError(
                "openai-compatible requires PRISMKE_LLM_API_KEY"
            )
        if not self.settings.llm_model:
            raise ProviderConfigurationError(
                "openai-compatible requires PRISMKE_LLM_MODEL"
            )
        return OpenAICompatibleLLMProvider(
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            model=self.settings.llm_model,
            timeout=self.settings.request_timeout,
        )

    def _workflow(self, provider: LLMProvider) -> PrismKEWorkflow:
        return PrismKEWorkflow(
            provider,
            self.graph_store,
            self.evidence_store,
            self.settings.checkpoint_path,
            self.runs,
        )

    async def run(
        self, input_path: Path, schema_path: Path, provider_name: str
    ) -> WorkflowState:
        input_path = input_path.resolve()
        schema_path = schema_path.resolve()
        provider = self.provider(provider_name)
        schema = load_schema(schema_path)
        schema_fingerprint = canonical_hash(schema.model_dump(mode="json"))
        run_id = stable_id(
            "run",
            file_sha256(input_path),
            schema_fingerprint,
            schema.version,
            provider.fingerprint(),
            PIPELINE_VERSION,
        )
        if self.runs.exists(run_id):
            return self.runs.load(run_id)
        state = WorkflowState(
            run_id=run_id,
            input_path=str(input_path),
            schema_path=str(schema_path),
            provider_name=provider_name,
            provider_fingerprint=provider.fingerprint(),
            pipeline_version=PIPELINE_VERSION,
        )
        self.runs.save(state)
        return await self._workflow(provider).invoke(state)

    def show_run(self, run_id: str) -> WorkflowState:
        return self.runs.load(run_id)

    async def review(
        self, run_id: str, claim_id: str, decision: ReviewDecision
    ) -> WorkflowState:
        state = self.runs.load(run_id)
        claim = next((item for item in state.claims if item.id == claim_id), None)
        if claim is None:
            raise KeyError(f"claim not found: {claim_id}")
        task = next((item for item in state.review_tasks if item.claim_id == claim_id), None)
        if task is None:
            raise KeyError(f"review task not found for claim: {claim_id}")
        task.status = "resolved"
        task.decision = decision
        task.resolved_at = utc_now()
        claim.status = (
            ClaimStatus.APPROVED if decision == ReviewDecision.APPROVE else ClaimStatus.REJECTED
        )
        state.status = (
            "awaiting_review"
            if any(item.status == "pending" for item in state.review_tasks)
            else "running"
        )
        provider = self.provider(state.provider_name)
        if state.provider_fingerprint not in ("legacy", provider.fingerprint()):
            raise ProviderConfigurationError("provider configuration changed since run creation")
        if not await self._workflow(provider).record_review(state):
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        return state

    async def resume(self, run_id: str) -> WorkflowState:
        state = self.runs.load(run_id)
        provider = self.provider(state.provider_name)
        if state.provider_fingerprint == "legacy":
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        if state.provider_fingerprint != provider.fingerprint():
            raise ProviderConfigurationError("provider configuration changed since run creation")
        state.status = "running"
        result = await self._workflow(provider).resume(run_id)
        if result is None:
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        return result
