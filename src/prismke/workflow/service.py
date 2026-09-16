"""Application service shared by CLI and future API/UI adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from prismke.core.errors import LegacyCheckpointError, ProviderConfigurationError
from prismke.core.ids import canonical_hash, file_sha256, stable_id
from prismke.core.settings import Settings
from prismke.domain import (
    CanonicalEntity,
    ClaimStatus,
    EntityCandidate,
    EntityMention,
    EntityReviewTask,
    GraphRevision,
    ReviewDecision,
    WorkflowState,
    load_schema,
    utc_now,
)
from prismke.governance import EntityGovernanceService
from prismke.parsing import ParserRegistry
from prismke.persistence import (
    AuditLog,
    EntityGovernanceRepository,
    FileEvidenceStore,
    JSONGraphStore,
    Neo4jGraphStore,
    RunRepository,
)
from prismke.persistence.base import GraphStore
from prismke.providers import (
    BGEM3EmbeddingProvider,
    DisabledEmbeddingProvider,
    DisabledOCRProvider,
    DisabledVLMProvider,
    MockEmbeddingProvider,
    MockLLMProvider,
    MockOCRProvider,
    MockVLMProvider,
    OpenAICompatibleLLMProvider,
    OpenAICompatibleVLMProvider,
    PaddleOCRProvider,
)
from prismke.providers.base import EmbeddingProvider, LLMProvider, OCRProvider, VLMProvider
from prismke.workflow.graph import PrismKEWorkflow

PIPELINE_VERSION = "0.4.0"
ASSET_POLICY_VERSION = "assets-v2"
ALIGNMENT_POLICY_VERSION = "alignment-v1"
ENTITY_RESOLUTION_POLICY_VERSION = "entity-resolution-v1"


class PrismKEService:
    def __init__(
        self, settings: Settings | None = None, graph_store: GraphStore | None = None
    ) -> None:
        self.settings = settings or Settings()
        self.runs = RunRepository(self.settings.runs_dir)
        self.graph_store = graph_store or self._create_graph_store()
        self.evidence_store = FileEvidenceStore(self.settings.evidence_dir)
        self.audit = AuditLog(self.settings.audit_path)
        self.entity_governance_repository = EntityGovernanceRepository(
            self.settings.entity_governance_path
        )
        self._ocr_providers: dict[str, OCRProvider] = {}
        self._embedding_provider: EmbeddingProvider | None = None

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

    def embedding_provider(self) -> EmbeddingProvider:
        if self._embedding_provider is not None:
            return self._embedding_provider
        name = self.settings.embedding_provider
        if name == "disabled":
            provider: EmbeddingProvider = DisabledEmbeddingProvider()
        elif name == "mock":
            provider = MockEmbeddingProvider()
        elif name == "bge-m3":
            provider = BGEM3EmbeddingProvider(
                model_name=self.settings.embedding_model,
                device=self.settings.embedding_device,
                use_fp16=self.settings.embedding_use_fp16,
                batch_size=self.settings.embedding_batch_size,
                max_tokens=self.settings.embedding_max_tokens,
                cache_dir=self.settings.embedding_cache_dir,
                model_cache_dir=self.settings.embedding_model_cache_dir,
                allow_download=self.settings.embedding_allow_download,
            )
        else:
            raise ProviderConfigurationError(f"unknown embedding provider: {name}")
        self._embedding_provider = provider
        return provider

    def entity_governance(self) -> EntityGovernanceService:
        return EntityGovernanceService(
            self.graph_store,
            self.entity_governance_repository,
            self.embedding_provider(),
        )

    async def search_entities(
        self, query: str, entity_type: str, limit: int = 10
    ) -> list[EntityCandidate]:
        provider = self.embedding_provider()
        if provider.fingerprint() == "embedding:disabled":
            normalized = query.casefold().strip()
            return [
                EntityCandidate(
                    entity_id=item.id,
                    retrieval_score=1.0,
                    name_score=1.0,
                    context_score=0.0,
                    final_score=1.0,
                    reasons=["exact_name_match"],
                )
                for item in await self.graph_store.list_entities()
                if item.active
                and item.entity_type == entity_type
                and normalized in {item.name.casefold(), *(a.casefold() for a in item.aliases)}
            ][:limit]
        vector = (await provider.encode([f"name: {query}\ntype: {entity_type}"]))[0]
        matches = await self.graph_store.search_entities(vector, entity_type, limit)
        return [
            EntityCandidate(
                entity_id=entity.id,
                retrieval_score=score,
                name_score=0.0,
                context_score=max(0.0, min(1.0, (score + 1.0) / 2.0)),
                final_score=max(0.0, min(1.0, (score + 1.0) / 2.0)),
                reasons=["dense_retrieval"],
            )
            for entity, score in matches
        ]

    def list_entity_reviews(self, status: str | None = None) -> list[EntityReviewTask]:
        workflow_tasks = [
            task
            for state in self.runs.list(limit=1000)
            for task in state.entity_review_tasks
            if status is None or task.status == status
        ]
        governance_tasks = self.entity_governance_repository.list_tasks(status)
        return sorted(
            [*workflow_tasks, *governance_tasks],
            key=lambda item: item.created_at,
            reverse=True,
        )

    async def propose_entity_merge(
        self, source_entity_ids: list[str], target_entity_id: str, reasons: list[str]
    ) -> EntityReviewTask:
        return await self.entity_governance().propose_merge(
            source_entity_ids, target_entity_id, reasons
        )

    async def propose_entity_split(
        self,
        source_entity_id: str,
        target_entities: list[CanonicalEntity],
        claim_assignments: dict[str, str],
        reasons: list[str],
    ) -> EntityReviewTask:
        return await self.entity_governance().propose_split(
            source_entity_id, target_entities, claim_assignments, reasons
        )

    async def review_entity_operation(
        self, task_id: str, approve: bool, reviewer: str | None = None
    ) -> GraphRevision | None:
        result = await self.entity_governance().resolve_operation(task_id, approve, reviewer)
        self.audit.record(
            "entity_operation_review",
            task_id,
            {
                "approved": approve,
                "reviewer": reviewer,
                "revision_id": result.id if result else None,
            },
        )
        return result

    async def entity_history(self, entity_id: str) -> list[GraphRevision]:
        revisions = await self.graph_store.list_revisions(limit=10_000)
        return [
            item
            for item in revisions
            if entity_id in item.entity_ids
            or any(
                change.resource_type == "entity" and change.resource_id == entity_id
                for change in item.changes
            )
        ]

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
            embedding_provider=self.embedding_provider(),
            entity_top_k=self.settings.entity_top_k,
            entity_auto_link_threshold=self.settings.entity_auto_link_threshold,
            entity_review_threshold=self.settings.entity_review_threshold,
            entity_min_margin=self.settings.entity_min_margin,
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
        state, created = self.create_run(
            input_path,
            schema_path,
            provider_name,
            ocr_provider_name,
            vlm_provider_name,
            allow_remote_assets,
        )
        if not created:
            return state
        return await self.execute_run(state.run_id)

    def create_run(
        self,
        input_path: Path,
        schema_path: Path,
        provider_name: str,
        ocr_provider_name: str = "disabled",
        vlm_provider_name: str = "disabled",
        allow_remote_assets: bool = False,
    ) -> tuple[WorkflowState, bool]:
        """Validate a request and persist its initial state without executing it."""
        input_path = input_path.resolve()
        schema_path = schema_path.resolve()
        provider = self.provider(provider_name)
        ocr_provider = self.ocr_provider(ocr_provider_name)
        vlm_provider = self.vlm_provider(vlm_provider_name)
        embedding_provider = self.embedding_provider()
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
            embedding_provider.fingerprint(),
            ASSET_POLICY_VERSION,
            ALIGNMENT_POLICY_VERSION,
            ENTITY_RESOLUTION_POLICY_VERSION,
            self.settings.entity_top_k,
            self.settings.entity_auto_link_threshold,
            self.settings.entity_review_threshold,
            self.settings.entity_min_margin,
            allow_remote_assets,
            PIPELINE_VERSION,
        )
        if self.runs.exists(run_id):
            return self.runs.load(run_id), False
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
            embedding_provider_name=self.settings.embedding_provider,
            embedding_provider_fingerprint=embedding_provider.fingerprint(),
            allow_remote_assets=allow_remote_assets,
            pipeline_version=PIPELINE_VERSION,
        )
        self.runs.save(state)
        return state, True

    async def execute_run(self, run_id: str) -> WorkflowState:
        state = self.runs.load(run_id)
        provider = self.provider(state.provider_name)
        ocr_provider = self.ocr_provider(state.ocr_provider_name)
        vlm_provider = self.vlm_provider(state.vlm_provider_name)
        return await self._workflow(
            provider, ocr_provider, vlm_provider, state.allow_remote_assets
        ).invoke(state)

    def show_run(self, run_id: str) -> WorkflowState:
        return self.runs.load(run_id)

    def _validated_run_providers(
        self, state: WorkflowState
    ) -> tuple[LLMProvider, OCRProvider, VLMProvider]:
        provider = self.provider(state.provider_name)
        ocr_provider = self.ocr_provider(state.ocr_provider_name)
        vlm_provider = self.vlm_provider(state.vlm_provider_name)
        embedding_provider = self.embedding_provider()
        if state.provider_fingerprint == "legacy":
            raise LegacyCheckpointError(
                "this run uses an unsupported checkpoint format; rerun the input with v0.4"
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
        if state.embedding_provider_fingerprint != embedding_provider.fingerprint():
            raise ProviderConfigurationError(
                "embedding provider configuration changed since run creation"
            )
        return provider, ocr_provider, vlm_provider

    async def review(self, run_id: str, claim_id: str, decision: ReviewDecision) -> WorkflowState:
        state = self.runs.load(run_id)
        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError(
                "this run was created by an older pipeline and cannot be resumed with v0.4"
            )
        provider, ocr_provider, vlm_provider = self._validated_run_providers(state)
        claim = next((item for item in state.claims if item.id == claim_id), None)
        if claim is None:
            raise KeyError(f"claim not found: {claim_id}")
        task = next((item for item in state.review_tasks if item.claim_id == claim_id), None)
        if task is None:
            raise KeyError(f"review task not found for claim: {claim_id}")
        task.status = "resolved"
        task.decision = decision
        task.resolved_at = utc_now()
        self.audit.record(
            "review",
            task.id,
            {"run_id": run_id, "claim_id": claim_id, "decision": decision.value},
        )
        claim.status = (
            ClaimStatus.APPROVED if decision == ReviewDecision.APPROVE else ClaimStatus.REJECTED
        )
        state.status = (
            "awaiting_review"
            if any(item.status == "pending" for item in state.review_tasks)
            else "running"
        )
        if not await self._workflow(
            provider, ocr_provider, vlm_provider, state.allow_remote_assets
        ).record_review(state):
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        return state

    async def review_entity(
        self,
        run_id: str,
        task_id: str,
        decision: Literal["link", "create", "reject"],
        selected_entity_id: str | None = None,
    ) -> WorkflowState:
        state = self.runs.load(run_id)
        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError(
                "this run was created by an older pipeline and cannot be resumed with v0.4"
            )
        provider, ocr_provider, vlm_provider = self._validated_run_providers(state)
        task = next((item for item in state.entity_review_tasks if item.id == task_id), None)
        if task is None or task.mention_id is None:
            raise KeyError(f"entity review task not found: {task_id}")
        if decision not in {"link", "create", "reject"}:
            raise ValueError(f"unsupported entity review decision: {decision}")
        target_id: str | None = None
        if decision == "link":
            allowed = {item.entity_id for item in task.candidates}
            if selected_entity_id not in allowed:
                raise ValueError("selected entity is not one of the review candidates")
            target_id = selected_entity_id
        elif decision == "create":
            target_id = task.proposed_entity_id
            if target_id is None:
                raise ValueError("review task does not contain a proposed entity")
        else:
            state.candidates = [
                candidate
                for candidate in state.candidates
                if candidate.subject.id != task.mention_id
                and not (
                    isinstance(candidate.object, EntityMention)
                    and candidate.object.id == task.mention_id
                )
            ]
        task.status = "resolved"
        task.decision = decision
        task.selected_entity_id = target_id
        task.resolved_at = utc_now()
        if target_id is not None:
            state.mention_to_entity[task.mention_id] = target_id
        state.status = (
            "awaiting_review"
            if any(item.status == "pending" for item in state.entity_review_tasks)
            else "running"
        )
        self.audit.record(
            "entity_review",
            task.id,
            {
                "run_id": run_id,
                "mention_id": task.mention_id,
                "decision": decision,
                "selected_entity_id": target_id,
            },
        )
        if not await self._workflow(
            provider,
            ocr_provider,
            vlm_provider,
            state.allow_remote_assets,
        ).record_entity_review(state):
            raise LegacyCheckpointError("entity review checkpoint is unavailable; rerun the input")
        return state

    async def resume(self, run_id: str) -> WorkflowState:
        state = self.runs.load(run_id)
        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError(
                "this run was created by an older pipeline and cannot be resumed with v0.4"
            )
        provider, ocr_provider, vlm_provider = self._validated_run_providers(state)
        state.status = "running"
        result = await self._workflow(
            provider, ocr_provider, vlm_provider, state.allow_remote_assets
        ).resume(run_id)
        if result is None:
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        return result
