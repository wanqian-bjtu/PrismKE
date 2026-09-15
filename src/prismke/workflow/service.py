"""Application service shared by CLI and future API/UI adapters."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from prismke.core.errors import LegacyCheckpointError, ProviderConfigurationError
from prismke.core.ids import canonical_hash, file_sha256, stable_id
from prismke.core.settings import Settings
from prismke.domain import ClaimStatus, ReviewDecision, WorkflowState, load_schema, utc_now
from prismke.parsing import ParserRegistry
from prismke.persistence import FileEvidenceStore, JSONGraphStore, Neo4jGraphStore, RunRepository
from prismke.persistence.base import GraphStore
from prismke.providers import (
    DisabledOCRProvider,
    DisabledVLMProvider,
    MockLLMProvider,
    MockOCRProvider,
    MockVLMProvider,
    OpenAICompatibleLLMProvider,
    OpenAICompatibleVLMProvider,
    PaddleOCRProvider,
)
from prismke.providers.base import LLMProvider, OCRProvider, VLMProvider
from prismke.workflow.graph import PrismKEWorkflow

PIPELINE_VERSION = "0.3.0"
ASSET_POLICY_VERSION = "assets-v2"
ALIGNMENT_POLICY_VERSION = "alignment-v1"


class PrismKEService:
    def __init__(
        self, settings: Settings | None = None, graph_store: GraphStore | None = None
    ) -> None:
        self.settings = settings or Settings()
        self.runs = RunRepository(self.settings.runs_dir)
        self.graph_store = graph_store or self._create_graph_store()
        self.evidence_store = FileEvidenceStore(self.settings.evidence_dir)
        self._ocr_providers: dict[str, OCRProvider] = {}

    def _create_graph_store(self) -> GraphStore:
        if self.settings.graph_store == "json":
            return JSONGraphStore(self.settings.graph_dir)
        if self.settings.graph_store != "neo4j":
            raise ValueError(f"unknown graph store: {self.settings.graph_store}")
        if not self.settings.neo4j_password:
            raise ProviderConfigurationError("neo4j graph store requires PRISMKE_NEO4J_PASSWORD")
        return Neo4jGraphStore(
            uri=self.settings.neo4j_uri,
            user=self.settings.neo4j_user,
            password=self.settings.neo4j_password,
            database=self.settings.neo4j_database,
        )

    async def close(self) -> None:
        await self.graph_store.close()

    @staticmethod
    def _validate_endpoint(value: str, variable: str) -> None:
        parsed = urlparse(value.strip())
        if (
            not value.strip()
            or "<" in value
            or ">" in value
            or parsed.scheme not in {"http", "https"}
            or not parsed.netloc
        ):
            raise ProviderConfigurationError(f"openai-compatible requires a valid {variable}")

    def provider(self, name: str) -> LLMProvider:
        if name == "mock":
            return MockLLMProvider()
        if name != "openai-compatible":
            raise ProviderConfigurationError(f"unknown provider: {name}")
        if not self.settings.llm_api_key:
            raise ProviderConfigurationError("openai-compatible requires PRISMKE_LLM_API_KEY")
        if not self.settings.llm_model:
            raise ProviderConfigurationError("openai-compatible requires PRISMKE_LLM_MODEL")
        self._validate_endpoint(self.settings.llm_base_url, "PRISMKE_LLM_BASE_URL")
        return OpenAICompatibleLLMProvider(
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            model=self.settings.llm_model,
            timeout=self.settings.request_timeout,
        )

    def ocr_provider(self, name: str) -> OCRProvider:
        cached = self._ocr_providers.get(name)
        if cached is not None:
            return cached
        if name == "disabled":
            provider: OCRProvider = DisabledOCRProvider()
        elif name == "mock":
            provider = MockOCRProvider()
        elif name == "paddle":
            provider = PaddleOCRProvider(
                device=self.settings.ocr_device,
                lang=self.settings.ocr_lang,
                model=self.settings.ocr_model,
            )
        else:
            raise ProviderConfigurationError(f"unknown OCR provider: {name}")
        self._ocr_providers[name] = provider
        return provider

    def vlm_provider(self, name: str) -> VLMProvider:
        if name == "disabled":
            return DisabledVLMProvider()
        if name == "mock":
            return MockVLMProvider()
        if name != "openai-compatible":
            raise ProviderConfigurationError(f"unknown VLM provider: {name}")
        if not self.settings.vlm_api_key:
            raise ProviderConfigurationError("openai-compatible VLM requires PRISMKE_VLM_API_KEY")
        if not self.settings.vlm_model:
            raise ProviderConfigurationError("openai-compatible VLM requires PRISMKE_VLM_MODEL")
        self._validate_endpoint(self.settings.vlm_base_url, "PRISMKE_VLM_BASE_URL")
        return OpenAICompatibleVLMProvider(
            base_url=self.settings.vlm_base_url,
            api_key=self.settings.vlm_api_key,
            model=self.settings.vlm_model,
            timeout=self.settings.vlm_timeout,
            max_image_edge=self.settings.vlm_max_image_edge,
        )

    def _workflow(
        self,
        provider: LLMProvider,
        ocr_provider: OCRProvider,
        vlm_provider: VLMProvider,
        allow_remote_assets: bool = False,
    ) -> PrismKEWorkflow:
        return PrismKEWorkflow(
            provider,
            ocr_provider,
            vlm_provider,
            self.graph_store,
            self.evidence_store,
            self.settings.checkpoint_path,
            self.runs,
            ParserRegistry(
                asset_dir=self.settings.assets_dir,
                allow_remote_assets=allow_remote_assets,
            ),
        )

    async def run(
        self,
        input_path: Path,
        schema_path: Path,
        provider_name: str,
        ocr_provider_name: str = "disabled",
        vlm_provider_name: str = "disabled",
        allow_remote_assets: bool = False,
    ) -> WorkflowState:
        input_path = input_path.resolve()
        schema_path = schema_path.resolve()
        provider = self.provider(provider_name)
        ocr_provider = self.ocr_provider(ocr_provider_name)
        vlm_provider = self.vlm_provider(vlm_provider_name)
        schema = load_schema(schema_path)
        schema_fingerprint = canonical_hash(schema.model_dump(mode="json"))
        run_id = stable_id(
            "run",
            file_sha256(input_path),
            schema_fingerprint,
            schema.version,
            provider.fingerprint(),
            ocr_provider.fingerprint(),
            vlm_provider.fingerprint(),
            ASSET_POLICY_VERSION,
            ALIGNMENT_POLICY_VERSION,
            allow_remote_assets,
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
            ocr_provider_name=ocr_provider_name,
            ocr_provider_fingerprint=ocr_provider.fingerprint(),
            vlm_provider_name=vlm_provider_name,
            vlm_provider_fingerprint=vlm_provider.fingerprint(),
            allow_remote_assets=allow_remote_assets,
            pipeline_version=PIPELINE_VERSION,
        )
        self.runs.save(state)
        return await self._workflow(
            provider, ocr_provider, vlm_provider, allow_remote_assets
        ).invoke(state)

    def show_run(self, run_id: str) -> WorkflowState:
        return self.runs.load(run_id)

    async def review(self, run_id: str, claim_id: str, decision: ReviewDecision) -> WorkflowState:
        state = self.runs.load(run_id)
        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError(
                "this run was created by an older pipeline and cannot be resumed with v0.3"
            )
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
        ocr_provider = self.ocr_provider(state.ocr_provider_name)
        vlm_provider = self.vlm_provider(state.vlm_provider_name)
        if state.provider_fingerprint not in ("legacy", provider.fingerprint()):
            raise ProviderConfigurationError("provider configuration changed since run creation")
        if state.ocr_provider_fingerprint != ocr_provider.fingerprint():
            raise ProviderConfigurationError(
                "OCR provider configuration changed since run creation"
            )
        if state.vlm_provider_fingerprint != vlm_provider.fingerprint():
            raise ProviderConfigurationError(
                "VLM provider configuration changed since run creation"
            )
        if not await self._workflow(
            provider, ocr_provider, vlm_provider, state.allow_remote_assets
        ).record_review(state):
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        return state

    async def resume(self, run_id: str) -> WorkflowState:
        state = self.runs.load(run_id)
        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError(
                "this run was created by an older pipeline and cannot be resumed with v0.3"
            )
        provider = self.provider(state.provider_name)
        ocr_provider = self.ocr_provider(state.ocr_provider_name)
        vlm_provider = self.vlm_provider(state.vlm_provider_name)
        if state.provider_fingerprint == "legacy":
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        if state.provider_fingerprint != provider.fingerprint():
            raise ProviderConfigurationError("provider configuration changed since run creation")
        if state.ocr_provider_fingerprint != ocr_provider.fingerprint():
            raise ProviderConfigurationError(
                "OCR provider configuration changed since run creation"
            )
        if state.vlm_provider_fingerprint != vlm_provider.fingerprint():
            raise ProviderConfigurationError(
                "VLM provider configuration changed since run creation"
            )
        state.status = "running"
        result = await self._workflow(
            provider, ocr_provider, vlm_provider, state.allow_remote_assets
        ).resume(run_id)
        if result is None:
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        return result
