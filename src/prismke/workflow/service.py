"""Application service shared by CLI and future API/UI adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from prismke.core.errors import (
    GraphIntegrityError,
    LegacyCheckpointError,
    ProviderConfigurationError,
)
from prismke.core.ids import canonical_hash, file_sha256, stable_id
from prismke.core.settings import Settings
from prismke.domain import (
    CanonicalEntity,
    CommitValidationContext,
    EntityCandidate,
    EntityReviewTask,
    GraphCommit,
    GraphRevision,
    ReviewDecision,
    ValidationResult,
    ValidationReviewDecision,
    WorkflowState,
    load_schema,
)
from prismke.governance import EntityGovernanceService
from prismke.governance.entity_resolution import ENTITY_RESOLUTION_POLICY_VERSION
from prismke.governance.validation import ValidationService
from prismke.parsing import ParserRegistry
from prismke.persistence import (
    AuditLog,
    CaseRepository,
    EntityGovernanceRepository,
    FileEvidenceStore,
    JSONGraphStore,
    Neo4jGraphStore,
    RunRepository,
    RuntimeConfigRepository,
)
from prismke.persistence.base import GraphStore
from prismke.providers import (
    BGEM3EmbeddingProvider,
    DisabledEmbeddingProvider,
    DisabledOCRProvider,
    DisabledReflectionProvider,
    DisabledVLMProvider,
    MockEmbeddingProvider,
    MockLLMProvider,
    MockOCRProvider,
    MockReflectionProvider,
    MockVLMProvider,
    OpenAICompatibleLLMProvider,
    OpenAICompatibleReflectionProvider,
    OpenAICompatibleVLMProvider,
    PaddleOCRProvider,
)
from prismke.providers.base import (
    EmbeddingProvider,
    LLMProvider,
    OCRProvider,
    ReflectionProvider,
    VLMProvider,
)
from prismke.workflow.cases import (
    CASE_RETRIEVAL_VERSION,
    CaseRetriever,
    CaseService,
)
from prismke.workflow.graph import PrismKEWorkflow
from prismke.workflow.reflection import REFLECTION_POLICY_VERSION, BoundedReflectionService
from prismke.workflow.review_workspace import validate_workspace_run, workspace_metadata

PIPELINE_VERSION = "0.9.0"
ASSET_POLICY_VERSION = "assets-v3"
ALIGNMENT_POLICY_VERSION = "alignment-v1"


class PrismKEService:
    def __init__(
        self, settings: Settings | None = None, graph_store: GraphStore | None = None
    ) -> None:
        self.settings = settings or Settings()
        self.runtime_config = RuntimeConfigRepository(
            self.settings.runtime_dir / "config" / "overrides.json"
        )
        self.runtime_config.apply(self.settings)
        self.review_metadata = workspace_metadata(self.settings.runtime_dir)
        if self.review_metadata and self.settings.graph_store != "json" and graph_store is None:
            raise ValueError("imported review workspace must use its isolated JSON graph")
        self.runs = RunRepository(self.settings.runs_dir)
        self.evidence_store = FileEvidenceStore(self.settings.evidence_dir)
        self.graph_store = graph_store or self._create_graph_store()
        if isinstance(self.graph_store, (JSONGraphStore, Neo4jGraphStore)):
            if isinstance(graph_store, (JSONGraphStore, Neo4jGraphStore)) and isinstance(
                graph_store.evidence_store, FileEvidenceStore
            ):
                self.evidence_store = graph_store.evidence_store
            self.graph_store.evidence_store = self.evidence_store
        self.audit = AuditLog(self.settings.audit_path)
        self.entity_governance_repository = EntityGovernanceRepository(
            self.settings.entity_governance_path
        )
        self.case_repository = CaseRepository(self.settings.cases_path)
        self.cases = CaseService(self.case_repository, self.evidence_store)
        self._ocr_providers: dict[str, OCRProvider] = {}
        self._embedding_provider: EmbeddingProvider | None = None
        from prismke.workflow.reviews import ReviewService

        self.reviews = ReviewService(self)
        from prismke.workflow.corrections import CorrectionService

        self.corrections = CorrectionService(self)
        from prismke.workflow.execution import ExecutionManager

        self.executions = ExecutionManager(self)

    def settings_view(self) -> dict[str, Any]:
        return self.runtime_config.public_view(self.settings)

    def update_settings(
        self,
        values: dict[str, Any],
        clear_secrets: list[str],
        operator: str,
    ) -> dict[str, Any]:
        from prismke.persistence.runtime_config import RESTART_FIELDS, SECRET_FIELDS

        if not operator.strip():
            raise ValueError("operator is required")
        invalid_clear = set(clear_secrets) - SECRET_FIELDS
        if invalid_clear:
            raise ValueError("only secret fields can be cleared")
        clean = {key: value for key, value in values.items() if value is not None}
        for field in SECRET_FIELDS:
            if field in clean and not str(clean[field]).strip():
                clean.pop(field)
        for field in clear_secrets:
            clean[field] = None
        for field in {"llm_base_url", "vlm_base_url"} & clean.keys():
            parsed = urlparse(str(clean[field]))
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError(f"{field} must not contain credentials, query or fragment")
            self._validate_endpoint(str(clean[field]), field)
        if "neo4j_uri" in clean:
            parsed = urlparse(str(clean["neo4j_uri"]))
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("neo4j_uri must not contain credentials, query or fragment")
            if parsed.scheme not in {"bolt", "neo4j", "bolt+s", "neo4j+s"} or not parsed.netloc:
                raise ValueError("invalid neo4j_uri")
        if clean.get("graph_store", self.settings.graph_store) not in {"json", "neo4j"}:
            raise ValueError("graph_store must be json or neo4j")
        if clean.get("embedding_provider", self.settings.embedding_provider) not in {
            "disabled",
            "mock",
            "bge-m3",
        }:
            raise ValueError("unsupported embedding_provider")
        candidate = Settings.model_validate({**self.settings.model_dump(), **clean})
        clean = {key: getattr(candidate, key) for key in clean}
        self.runtime_config.update(clean)
        for key, value in clean.items():
            setattr(self.settings, key, value)
        if {"ocr_device", "ocr_lang", "ocr_model"} & clean.keys():
            self._ocr_providers.clear()
        if any(key.startswith("embedding_") for key in clean):
            self._embedding_provider = None
        changed = sorted(clean)
        self.audit.record(
            "update_runtime_settings",
            "workspace",
            {
                "operator": operator.strip(),
                "changed_fields": changed,
                "cleared_secrets": sorted(clear_secrets),
            },
        )
        return {
            "settings": self.settings_view(),
            "changed_fields": changed,
            "restart_required": bool(RESTART_FIELDS & clean.keys()),
        }

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
        await self.executions.stop()
        await self.graph_store.close()

    async def workspace_summary(self) -> dict[str, Any]:
        states = self.runs.list(limit=1000)
        run_counts: dict[str, int] = {}
        pending_reviews = 0
        blocking_issues = 0
        for state in states:
            execution_status = self.executions.view(state.run_id)["status"]
            run_counts[execution_status] = run_counts.get(execution_status, 0) + 1
            pending_reviews += sum(t.status == "pending" for t in state.entity_review_tasks)
            pending_reviews += sum(t.status == "pending" for t in state.review_tasks)
            blocking_issues += state.validation.blocking_count
        return {
            "run_counts": run_counts,
            "pending_reviews": pending_reviews,
            "blocking_issues": blocking_issues,
            "worker_status": self.executions.health()["worker"],
            "graph_health": (await self.graph_store.healthcheck()).model_dump(mode="json"),
        }

    async def validate_run(self, run_id: str) -> ValidationResult:
        state = self.show_run(run_id)
        if state.document is None or state.output_schema is None:
            raise ValueError("run has no parsed document/schema to validate")
        from prismke.domain import SchemaIndex

        blocked = ValidationService.blocked_candidate_ids(state.candidates, state.validation)
        issues = await ValidationService().candidates(
            [c for c in state.candidates if c.id not in blocked],
            SchemaIndex(state.output_schema),
            state.document,
            self.evidence_store,
            {e.id: e for e in state.entities} if state.entities else None,
            state.mention_to_entity if state.entities else None,
        )
        sid = canonical_hash(state.output_schema.model_dump(mode="json"))
        context = (
            CommitValidationContext(
                schemas={sid: state.output_schema},
                claim_schema_ids={c.id: sid for c in state.claims},
                document_asset_ids={state.document.id: [a.id for a in state.document.media_assets]},
            )
            if state.pipeline_version == PIPELINE_VERSION
            else None
        )
        for claim in state.claims:
            try:
                await ValidationService().commit(
                    GraphCommit(
                        claims=[claim],
                        revision=GraphRevision(id="readonly-validation", run_id=state.run_id),
                        validation_context=context,
                    ),
                    {e.id: e for e in state.entities},
                    {e.id: e for e in state.document.evidence},
                    {state.document.id},
                    self.evidence_store,
                )
            except GraphIntegrityError as error:
                for code in str(error).split(":", 1)[0].split(","):
                    issue = ValidationService.issue(
                        code.strip(),
                        "commit",
                        "claim",
                        claim.id,
                        "claim",
                        "事实只读复核未通过，不能用排除候选绕过存储约束",
                        claim.evidence_ids,
                    )
                    issue.allowed_actions = []
                    issues.append(issue)
        claim_ids = {c.id for c in state.claims}
        # Conflict members are transient until normalization has materialized Claims.
        for conflict in state.conflicts if state.claims or state.status == "completed" else []:
            if not set(conflict.claim_ids) <= claim_ids:
                issue = ValidationService.issue(
                    "MISSING_CONFLICT_MEMBER",
                    "reference",
                    "conflict",
                    conflict.id,
                    "claim_ids",
                    "冲突集合引用未知事实",
                )
                issue.allowed_actions = []
                issues.append(issue)
        if state.status == "failed":
            issue = ValidationService.issue(
                "INCOMPLETE_PIPELINE",
                "commit",
                "document",
                state.document.id,
                "status",
                "运行失败，不能将不完整抽取解释为校验通过",
            )
            issue.allowed_actions = []
            issues.append(issue)
        return ValidationService.merge(
            state.validation,
            issues,
            canonical_hash(state.document.model_dump(mode="json")),
            len(state.claims),
        )

    async def exclude_validation_issue(
        self, run_id: str, issue_id: str, reviewer: str, comment: str = ""
    ) -> WorkflowState:
        if not reviewer.strip():
            raise ValueError("reviewer is required")
        with self.runs.mutation_lock(run_id):
            await self.reviews.recover(run_id)
            state = self.show_run(run_id)
            if state.pipeline_version != PIPELINE_VERSION or state.status != "awaiting_review":
                raise ValueError("validation decision is stale or incompatible")
            issue = next((i for i in state.validation.issues if i.id == issue_id), None)
            if issue is None or issue.status != "open" or "exclude" not in issue.allowed_actions:
                raise ValueError("validation issue already handled or unavailable")
            issue.status = "excluded"
            state.validation_decisions.append(
                ValidationReviewDecision(
                    issue_id=issue_id, reviewer=reviewer.strip(), comment=comment
                )
            )
            state.validation = ValidationService.merge(state.validation, [])
            state.status = (
                "awaiting_review"
                if (
                    state.validation.blocking_count
                    or any(t.status == "pending" for t in state.entity_review_tasks)
                    or any(t.status == "pending" for t in state.review_tasks)
                )
                else "running"
            )
            state.graph_commit = None
            workflow = self.review_workflow(state)
            if state.current_node == "resolve_entities":
                updated = await workflow.record_entity_review(state)
            else:
                updated = await workflow.record_review(state)
            if not updated:
                raise LegacyCheckpointError("checkpoint unavailable")
            self.audit.record(
                "exclude_validation_issue",
                run_id,
                state.validation_decisions[-1].model_dump(mode="json"),
            )
            return state

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
                model_revision=self.settings.embedding_model_revision,
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

    def reflection_provider(self, name: str) -> ReflectionProvider:
        if name == "disabled":
            return DisabledReflectionProvider()
        if name == "mock":
            return MockReflectionProvider()
        if name != "openai-compatible":
            raise ProviderConfigurationError(f"unknown Reflection provider: {name}")
        if not self.settings.llm_api_key:
            raise ProviderConfigurationError(
                "openai-compatible Reflection requires PRISMKE_LLM_API_KEY"
            )
        if not self.settings.llm_model:
            raise ProviderConfigurationError(
                "openai-compatible Reflection requires PRISMKE_LLM_MODEL"
            )
        self._validate_endpoint(self.settings.llm_base_url, "PRISMKE_LLM_BASE_URL")
        return OpenAICompatibleReflectionProvider(
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            model=self.settings.llm_model,
            timeout=self.settings.request_timeout,
        )

    def case_retriever(self) -> CaseRetriever:
        provider = self.embedding_provider()
        if provider.fingerprint() == "embedding:disabled":
            raise ProviderConfigurationError("case retrieval requires an embedding provider")
        return CaseRetriever(self.case_repository, provider)

    def list_cases(
        self,
        *,
        case_type: str | None = None,
        task_type: str | None = None,
        language: str | None = None,
        active_only: bool = True,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        records = self.case_repository.list(
            case_type=case_type,
            task_type=task_type,
            language=language,
            active_only=active_only,
            limit=limit,
        )
        return [
            {
                **record.model_dump(mode="json"),
                "active": self.case_repository.is_active(record.id),
            }
            for record in records
        ]

    def get_case(self, case_id: str) -> dict[str, Any]:
        record = self.case_repository.get(case_id)
        return {
            **record.model_dump(mode="json"),
            "active": self.case_repository.is_active(case_id),
            "status_events": [
                item.model_dump(mode="json") for item in self.case_repository.status_events(case_id)
            ],
        }

    def disable_case(
        self, case_id: str, *, operator: str, reason: str, request_id: str
    ) -> dict[str, Any]:
        from prismke.domain import CaseStatusEvent

        if not operator.strip() or not reason.strip() or not request_id.strip():
            raise ValueError("operator, reason and request_id are required")
        self.case_repository.get(case_id)
        event = CaseStatusEvent(
            id=stable_id("case-status", case_id, request_id),
            case_id=case_id,
            action="disable",
            operator=operator.strip(),
            reason=reason.strip(),
        )
        self.case_repository.disable(event)
        self.audit.record("disable_case", case_id, event.model_dump(mode="json"))
        return self.get_case(case_id)

    async def rebuild_case_index(self, *, dry_run: bool = False) -> dict[str, Any]:
        return await self.case_retriever().rebuild(dry_run=dry_run)

    async def replay_case_projections(self) -> int:
        count = 0
        for run in self.runs.list(limit=10_000):
            if run.pipeline_version != PIPELINE_VERSION:
                continue
            for event in self.reviews.repository.events(run.run_id):
                if self.case_repository.projected(event.id):
                    continue
                payload = self.reviews.repository.event_state(event.id)
                state = WorkflowState.model_validate(payload)
                await self.cases.project_review_event(event, state)
                count += 1
        return count

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
        matches = await self.graph_store.search_entities(
            vector, entity_type, limit, provider.fingerprint()
        )
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
        if not (reviewer or "").strip():
            raise ValueError("reviewer is required")
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
        state: WorkflowState | None = None,
    ) -> PrismKEWorkflow:
        reflection_service = None
        if state is not None and state.reflection_enabled:
            retriever = self.case_retriever() if state.case_mode != "none" else None
            reflection_service = BoundedReflectionService(
                self.reflection_provider(state.reflection_provider_name),
                retriever,
                self.evidence_store,
            )
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
            reflection_service=reflection_service,
        )

    async def run(
        self,
        input_path: Path,
        schema_path: Path,
        provider_name: str,
        ocr_provider_name: str = "disabled",
        vlm_provider_name: str = "disabled",
        allow_remote_assets: bool = False,
        case_mode: Literal["none", "good", "good_bad"] = "none",
        reflection_enabled: bool = False,
        reflection_provider_name: str = "disabled",
        reflection_max_attempts: int | None = None,
        reflection_token_budget: int | None = None,
        reflection_time_budget_seconds: int | None = None,
    ) -> WorkflowState:
        state, created = self.create_run(
            input_path,
            schema_path,
            provider_name,
            ocr_provider_name,
            vlm_provider_name,
            allow_remote_assets,
            case_mode,
            reflection_enabled,
            reflection_provider_name,
            reflection_max_attempts,
            reflection_token_budget,
            reflection_time_budget_seconds,
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
        case_mode: Literal["none", "good", "good_bad"] = "none",
        reflection_enabled: bool = False,
        reflection_provider_name: str = "disabled",
        reflection_max_attempts: int | None = None,
        reflection_token_budget: int | None = None,
        reflection_time_budget_seconds: int | None = None,
    ) -> tuple[WorkflowState, bool]:
        """Validate a request and persist its initial state without executing it."""
        self.executions.ensure_accepting()
        if self.review_metadata:
            raise ValueError("isolated review workspace does not allow new extraction runs")
        input_path = input_path.resolve()
        schema_path = schema_path.resolve()
        provider = self.provider(provider_name)
        ocr_provider = self.ocr_provider(ocr_provider_name)
        vlm_provider = self.vlm_provider(vlm_provider_name)
        embedding_provider = self.embedding_provider()
        if case_mode not in {"none", "good", "good_bad"}:
            raise ValueError("case_mode must be none, good or good_bad")
        if case_mode != "none" and embedding_provider.fingerprint() == "embedding:disabled":
            raise ProviderConfigurationError("case retrieval requires an embedding provider")
        max_attempts = (
            self.settings.reflection_max_attempts
            if reflection_max_attempts is None
            else reflection_max_attempts
        )
        token_budget = (
            self.settings.reflection_token_budget
            if reflection_token_budget is None
            else reflection_token_budget
        )
        time_budget = (
            self.settings.reflection_time_budget_seconds
            if reflection_time_budget_seconds is None
            else reflection_time_budget_seconds
        )
        if not 0 <= max_attempts <= 2:
            raise ValueError("reflection_max_attempts must be between 0 and 2")
        if token_budget <= 0 or time_budget <= 0:
            raise ValueError("Reflection token and time budgets must be positive")
        reflection = self.reflection_provider(
            reflection_provider_name if reflection_enabled else "disabled"
        )
        if reflection_enabled and reflection.fingerprint() == "reflection:disabled":
            raise ProviderConfigurationError(
                "Reflection requires mock or openai-compatible provider"
            )
        retriever = self.case_retriever() if case_mode != "none" else None
        case_snapshot_ids = retriever.snapshot_ids() if retriever else []
        case_snapshot = retriever.fingerprint_for(case_snapshot_ids) if retriever else "cases:none"
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
            case_snapshot,
            CASE_RETRIEVAL_VERSION,
            reflection.fingerprint(),
            REFLECTION_POLICY_VERSION,
            case_mode,
            reflection_enabled,
            max_attempts,
            token_budget,
            time_budget,
            ASSET_POLICY_VERSION,
            ALIGNMENT_POLICY_VERSION,
            ENTITY_RESOLUTION_POLICY_VERSION,
            "validation-v1",
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
            case_mode=case_mode,
            case_snapshot_fingerprint=case_snapshot,
            case_snapshot_ids=case_snapshot_ids,
            case_retrieval_policy_version=CASE_RETRIEVAL_VERSION,
            reflection_enabled=reflection_enabled,
            reflection_provider_name=(
                reflection_provider_name if reflection_enabled else "disabled"
            ),
            reflection_provider_fingerprint=reflection.fingerprint(),
            reflection_policy_version=REFLECTION_POLICY_VERSION,
            reflection_max_attempts=max_attempts,
            reflection_token_budget=token_budget,
            reflection_time_budget_seconds=time_budget,
            allow_remote_assets=allow_remote_assets,
            pipeline_version=PIPELINE_VERSION,
            entity_resolution_policy_version=ENTITY_RESOLUTION_POLICY_VERSION,
        )
        with self.runs.creation_lock(run_id):
            if self.runs.exists(run_id):
                return self.runs.load(run_id), False
            self.executions.register(state)
            self.runs.save(state)
            return state, True

    async def execute_run(self, run_id: str) -> WorkflowState:
        return await self.executions.run_wait(run_id, "execute")

    async def _execute_run(self, run_id: str) -> WorkflowState:
        if self.review_metadata:
            raise ValueError("isolated review workspace cannot execute extraction")
        state = self.runs.load(run_id)
        self._validate_entity_policy(state)
        provider = self.provider(state.provider_name)
        ocr_provider = self.ocr_provider(state.ocr_provider_name)
        vlm_provider = self.vlm_provider(state.vlm_provider_name)
        self._validate_reflection_policy(state)
        return await self._workflow(
            provider,
            ocr_provider,
            vlm_provider,
            state.allow_remote_assets,
            state,
        ).invoke(state)

    def show_run(self, run_id: str) -> WorkflowState:
        return self.runs.load(run_id)

    async def entity_review_detail(self, run_id: str, task_id: str) -> dict[str, Any]:
        from prismke.workflow.review_details import entity_task_base

        state = self.show_run(run_id)
        detail = entity_task_base(state, task_id)
        entities = {item.id: item for item in state.entities}
        candidates = []
        task = next(item for item in state.entity_review_tasks if item.id == task_id)
        for score in task.candidates:
            entity = entities.get(score.entity_id) or await self.graph_store.get_entity(
                score.entity_id
            )
            candidates.append(
                {
                    **score.model_dump(mode="json"),
                    "entity": entity.model_dump(mode="json") if entity else None,
                }
            )
        detail["candidates"] = candidates
        detail["margin"] = next(
            (
                item.margin
                for item in state.entity_resolution_decisions
                if item.mention_id == task.mention_id
            ),
            None,
        )
        return detail

    def claim_review_detail(self, run_id: str, task_id: str) -> dict[str, Any]:
        from prismke.workflow.review_details import claim_task_detail

        try:
            return claim_task_detail(self.show_run(run_id), task_id)
        except (KeyError, StopIteration):
            event = next(
                (
                    e
                    for e in reversed(self.reviews.repository.events(run_id))
                    if e.kind == "claim" and e.task_id == task_id
                ),
                None,
            )
            if event is None:
                raise KeyError("claim review task not found") from None
            historical = WorkflowState.model_validate(self.reviews.repository.event_state(event.id))
            detail = claim_task_detail(historical, task_id)
            detail["historical_only"] = True
            return detail

    def review_progress(self, run_id: str) -> dict[str, Any]:
        state = self.show_run(run_id)
        entity_pending = sum(item.status == "pending" for item in state.entity_review_tasks)
        claim_pending = sum(item.status == "pending" for item in state.review_tasks)
        retry_commit = state.status == "failed" and state.failed_node == "commit_graph"
        sync_pending = bool(self.reviews.repository.pending(run_id))
        execution = self.executions.view(run_id)
        return {
            "run_id": run_id,
            "status": state.status,
            "node": state.current_node,
            "execution": execution,
            "entity_pending": entity_pending,
            "claim_pending": claim_pending,
            "validation_pending": state.validation.blocking_count,
            "isolated": state.review_workspace,
            "review_sync_pending": sync_pending,
            "can_resume": not execution["active"]
            and not execution["blocked"]
            and not sync_pending
            and not entity_pending
            and not claim_pending
            and not state.validation.blocking_count
            and state.status != "completed"
            and state.current_node != "prepare_graph_commit"
            and not retry_commit,
            "can_commit": not execution["active"]
            and not execution["blocked"]
            and not sync_pending
            and (state.review_workspace or bool(state.pending_correction_id))
            and (state.current_node == "prepare_graph_commit" or retry_commit)
            and not entity_pending
            and not claim_pending
            and not state.validation.blocking_count
            and (not state.submission_confirmed or retry_commit),
            "submission": {
                "entities": len(state.graph_commit.entities),
                "claims": len(state.graph_commit.claims),
                "conflicts": len(state.graph_commit.conflicts),
                "evidence": len(state.graph_commit.evidence),
                "revision_id": state.graph_commit.revision.id,
                "parent_id": state.graph_commit.revision.parent_id,
                "changes": [c.model_dump(mode="json") for c in state.graph_commit.revision.changes]
                if state.pending_correction_id
                else [],
            }
            if state.graph_commit
            else None,
        }

    def review_workflow(self, state: WorkflowState) -> PrismKEWorkflow:
        if state.pipeline_version == PIPELINE_VERSION and state.current_node in {
            "resolve_entities",
            "normalize_claims",
            "detect_conflicts",
            "route_by_risk",
            "prepare_graph_commit",
            "commit_graph",
        }:
            return self.review_tail_workflow(
                state,
                use_embeddings=(not state.review_workspace and not state.correction_tail_only),
            )
        if self.review_metadata:
            validate_workspace_run(self.settings.runtime_dir, state)
        if not state.review_workspace:
            provider, ocr, vlm = self._validated_run_providers(state)
            self._validate_reflection_policy(state)
            return self._workflow(provider, ocr, vlm, state.allow_remote_assets, state)
        validate_workspace_run(self.settings.runtime_dir, state)
        self._validate_entity_policy(state)
        return PrismKEWorkflow(
            MockLLMProvider(),
            DisabledOCRProvider(),
            DisabledVLMProvider(),
            self.graph_store,
            self.evidence_store,
            self.settings.checkpoint_path,
            self.runs,
            embedding_provider=DisabledEmbeddingProvider(),
            review_only=True,
        )

    def review_tail_workflow(
        self, state: WorkflowState, *, use_embeddings: bool = False
    ) -> PrismKEWorkflow:
        self.reviews.compatible(state)
        if state.review_workspace:
            validate_workspace_run(self.settings.runtime_dir, state)
        embedding: EmbeddingProvider = DisabledEmbeddingProvider()
        if use_embeddings:
            embedding = self.embedding_provider()
            if embedding.fingerprint() != state.embedding_provider_fingerprint:
                raise ProviderConfigurationError(
                    "embedding configuration changed since run creation"
                )
        return PrismKEWorkflow(
            MockLLMProvider(),
            DisabledOCRProvider(),
            DisabledVLMProvider(),
            self.graph_store,
            self.evidence_store,
            self.settings.checkpoint_path,
            self.runs,
            embedding_provider=embedding,
            review_only=True,
        )

    def _validated_run_providers(
        self, state: WorkflowState
    ) -> tuple[LLMProvider, OCRProvider, VLMProvider]:
        self._validate_entity_policy(state)
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
        self._validate_reflection_policy(state)
        return provider, ocr_provider, vlm_provider

    def _validate_reflection_policy(self, state: WorkflowState) -> None:
        if state.case_retrieval_policy_version != CASE_RETRIEVAL_VERSION:
            raise LegacyCheckpointError(
                "case retrieval policy changed; old runs are read-only, rerun the input"
            )
        if state.reflection_policy_version != REFLECTION_POLICY_VERSION:
            raise LegacyCheckpointError(
                "Reflection policy changed; old runs are read-only, rerun the input"
            )
        reflection = self.reflection_provider(state.reflection_provider_name)
        if reflection.fingerprint() != state.reflection_provider_fingerprint:
            raise ProviderConfigurationError(
                "Reflection provider configuration changed since run creation"
            )
        if state.case_mode != "none":
            expected = self.case_retriever().fingerprint_for(state.case_snapshot_ids)
            if expected != state.case_snapshot_fingerprint:
                raise ProviderConfigurationError("case library snapshot is inconsistent")

    @staticmethod
    def _validate_entity_policy(state: WorkflowState) -> None:
        if state.entity_resolution_policy_version != ENTITY_RESOLUTION_POLICY_VERSION:
            raise LegacyCheckpointError(
                "entity resolution policy changed; old runs are read-only, rerun the input"
            )

    async def review(
        self,
        run_id: str,
        claim_id: str,
        decision: ReviewDecision,
        reviewer: str | None = None,
        comment: str | None = None,
        expected_version: int | None = None,
        request_id: str | None = None,
    ) -> WorkflowState:
        with self.runs.mutation_lock(run_id):
            state = self.show_run(run_id)
            task = next((t for t in state.review_tasks if t.claim_id == claim_id), None)
            if task is None:
                raise KeyError("claim review task not found")
            return await self.reviews.decide(
                run_id,
                task.id,
                "claim",
                decision.value,
                None,
                reviewer,
                comment,
                expected_version,
                request_id,
            )

    async def review_entity(
        self,
        run_id: str,
        task_id: str,
        decision: Literal["link", "create", "reject", "defer"],
        selected_entity_id: str | None = None,
        reviewer: str | None = None,
        comment: str | None = None,
        expected_version: int | None = None,
        request_id: str | None = None,
    ) -> WorkflowState:
        with self.runs.mutation_lock(run_id):
            return await self.reviews.decide(
                run_id,
                task_id,
                "entity",
                decision,
                selected_entity_id,
                reviewer,
                comment,
                expected_version,
                request_id,
            )

    async def resume(self, run_id: str) -> WorkflowState:
        return await self.executions.run_wait(run_id, "resume")

    async def _resume(self, run_id: str) -> WorkflowState:
        await self.reviews.recover(run_id)
        state = self.runs.load(run_id)
        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError("旧流程不能由 v0.8 恢复；请使用对应发布版本接续")
        if (
            state.validation.blocking_count
            or any(task.status == "pending" for task in state.entity_review_tasks)
            or any(task.status == "pending" for task in state.review_tasks)
        ):
            raise ValueError("pending reviews must be resolved before continuation")
        workflow = self.review_workflow(state)
        state.status = "running"
        result = await workflow.resume(run_id)
        if result is None:
            raise LegacyCheckpointError(
                "this run uses the v0.1 checkpoint format; rerun the input with v0.1.1"
            )
        return result

    async def confirm_review_commit(self, run_id: str, reviewer: str) -> WorkflowState:
        return await self.executions.run_wait(run_id, "confirm", reviewer)

    async def _confirm_review_commit(self, run_id: str, reviewer: str) -> WorkflowState:
        await self.reviews.recover(run_id)
        state = self.show_run(run_id)
        if not reviewer.strip():
            raise ValueError("reviewer is required")
        retry_commit = state.status == "failed" and state.failed_node == "commit_graph"
        if not (state.review_workspace or state.pending_correction_id) or (
            state.current_node != "prepare_graph_commit" and not retry_commit
        ):
            raise ValueError("run is not at an isolated submission preview")
        if (
            state.validation.blocking_count
            or any(task.status == "pending" for task in state.entity_review_tasks)
            or any(task.status == "pending" for task in state.review_tasks)
        ):
            raise ValueError("pending reviews prevent graph submission")
        if state.graph_commit is None or (state.submission_confirmed and not retry_commit):
            raise ValueError("missing preview or submission already confirmed")
        if state.pending_correction_id:
            return await self.corrections.confirm(state, reviewer)
        result = await self.review_workflow(state).confirm_submission(state)
        self.audit.record(
            "confirm_graph_commit",
            run_id,
            {
                "reviewer": reviewer,
                "revision_id": result.revision.id if result.revision else None,
            },
        )
        return result
