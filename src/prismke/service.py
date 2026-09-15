"""Application service shared by the CLI and future API/UI adapters."""

from __future__ import annotations

from pathlib import Path

from prismke.checkpoint import RunRepository, SQLiteCheckpointStore
from prismke.ids import stable_id
from prismke.interfaces import LLMProvider
from prismke.models import ClaimStatus, ReviewDecision, WorkflowState, utc_now
from prismke.providers import MockLLMProvider, OpenAICompatibleLLMProvider
from prismke.settings import Settings
from prismke.stores import JSONGraphStore
from prismke.workflow import PrismKEWorkflow


class PrismKEService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.checkpoints = SQLiteCheckpointStore(self.settings.checkpoint_path)
        self.runs = RunRepository(self.settings.runs_dir)
        self.graph_store = JSONGraphStore(self.settings.graph_dir)

    def provider(self, name: str) -> LLMProvider:
        if name == "mock":
            return MockLLMProvider()
        if name != "openai-compatible":
            raise ValueError(f"unknown provider: {name}")
        if not self.settings.llm_api_key or not self.settings.llm_model:
            return MockLLMProvider()
        return OpenAICompatibleLLMProvider(
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            model=self.settings.llm_model,
            timeout=self.settings.request_timeout,
        )

    async def run(self, input_path: Path, schema_path: Path, provider_name: str) -> WorkflowState:
        input_path = input_path.resolve()
        schema_path = schema_path.resolve()
        run_id = stable_id("run", input_path, schema_path, input_path.stat().st_mtime_ns)
        state = WorkflowState(
            run_id=run_id,
            input_path=str(input_path),
            schema_path=str(schema_path),
            provider_name=provider_name,
        )
        self.checkpoints.save(state)
        self.runs.save(state)
        workflow = PrismKEWorkflow(
            self.provider(provider_name), self.graph_store, self.checkpoints, self.runs
        )
        return await workflow.invoke(state)

    def show_run(self, run_id: str) -> WorkflowState:
        return self.runs.load(run_id)

    def review(self, run_id: str, claim_id: str, decision: ReviewDecision) -> WorkflowState:
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
        state.status = "running"
        state.current_node = "route_by_risk"
        self.checkpoints.save(state)
        self.runs.save(state)
        return state

    async def resume(self, run_id: str) -> WorkflowState:
        state = self.checkpoints.load_latest(run_id)
        if state is None:
            raise KeyError(f"run not found: {run_id}")
        state.status = "running"
        state.errors = []
        workflow = PrismKEWorkflow(
            self.provider(state.provider_name),
            self.graph_store,
            self.checkpoints,
            self.runs,
        )
        return await workflow.invoke(state)
