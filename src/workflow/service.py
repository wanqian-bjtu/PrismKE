"""Application service shared by CLI and future API/UI adapters."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from src.agents import AGENT_POLICY_VERSION
from src.core.errors import (
    GraphIntegrityError,
    LegacyCheckpointError,
    ProviderConfigurationError,
)
from src.core.ids import canonical_hash, file_sha256, stable_id
from src.core.settings import Settings
from src.domain import (
    BatchItem,
    BatchItemStatus,
    BatchResult,
    BatchRun,
    BatchStatus,
    CandidateClaim,
    CanonicalEntity,
    ClaimStatus,
    CommitValidationContext,
    EntityCandidate,
    EntityReviewTask,
    EntitySourceMode,
    ExtractionReviewEvent,
    GraphChange,
    GraphCommit,
    GraphDocument,
    GraphRevision,
    PDFComplexityThresholds,
    PDFParseMode,
    PDFParserFallbackEvent,
    PDFParserName,
    ProvidedEntity,
    ReviewDecision,
    SchemaIndex,
    TaskExtractionResult,
    TaskMode,
    ValidationAction,
    ValidationCorrectionEvent,
    ValidationResult,
    ValidationReviewDecision,
    WorkflowState,
    load_schema,
)
from src.governance import (
    EntityGovernanceService,
    detect_conflicts,
    merge_supporting_claims,
)
from src.governance.entity_resolution import ENTITY_RESOLUTION_POLICY_VERSION
from src.governance.validation import ValidationService
from src.governance.validation.actions import APPROVAL_REQUIRED, candidate_actions
from src.parsing import ParserRegistry
from src.parsing.mineru import MinerUV1Client
from src.persistence import (
    AuditLog,
    BatchRepository,
    CaseRepository,
    EntityGovernanceRepository,
    FileEvidenceStore,
    JSONGraphStore,
    Neo4jGraphStore,
    RunRepository,
    RuntimeConfigRepository,
)
from src.persistence.base import GraphStore
from src.providers import (
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
    resolve_ocr_device,
    resolve_ocr_language,
)
from src.providers.base import (
    EmbeddingProvider,
    LLMProvider,
    OCRProvider,
    ReflectionProvider,
    SemanticAdvisor,
    VLMProvider,
)
from src.providers.semantic import (
    DisabledSemanticAdvisor,
    MockSemanticAdvisor,
    OpenAICompatibleSemanticAdvisor,
)
from src.workflow.cases import (
    CASE_RETRIEVAL_VERSION,
    CaseRetriever,
    CaseService,
)
from src.workflow.graph import PrismKEWorkflow
from src.workflow.reflection import REFLECTION_POLICY_VERSION, BoundedReflectionService
from src.workflow.review_workspace import validate_workspace_run, workspace_metadata
from src.workflow.validation_corrections import corrected_candidate, replace_candidate

PIPELINE_VERSION = "0.13.0"
ASSET_POLICY_VERSION = "assets-v3"
ALIGNMENT_POLICY_VERSION = "alignment-v1"


@dataclass(frozen=True, repr=False)
class TransientProviderCredentials:
    """Per-browser credentials kept in process memory and never serialized."""

    llm_api_key: str | None = None
    vlm_api_key: str | None = None


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
        self.batches = BatchRepository(self.settings.batches_dir)
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
        self._run_credentials: dict[str, TransientProviderCredentials] = {}
        from src.workflow.reviews import ReviewService

        self.reviews = ReviewService(self)
        from src.workflow.corrections import CorrectionService

        self.corrections = CorrectionService(self)
        from src.workflow.execution import ExecutionManager

        self.executions = ExecutionManager(self)

    def settings_view(self) -> dict[str, Any]:
        view = self.runtime_config.public_view(self.settings)
        view["ocr_device_resolved"] = resolve_ocr_device(self.settings.ocr_device)
        return view

    def update_settings(
        self,
        values: dict[str, Any],
        clear_secrets: list[str],
        operator: str,
    ) -> dict[str, Any]:
        from src.persistence.runtime_config import EDITABLE_FIELDS, RESTART_FIELDS, SECRET_FIELDS

        if not operator.strip():
            raise ValueError("operator is required")
        invalid_values = set(values) - EDITABLE_FIELDS
        if invalid_values:
            raise ValueError("unsupported runtime settings: " + ", ".join(sorted(invalid_values)))
        invalid_clear = set(clear_secrets) - SECRET_FIELDS
        if invalid_clear:
            raise ValueError("only secret fields can be cleared")
        conflicting_secrets = {
            field
            for field in clear_secrets
            if field in values and values[field] is not None and str(values[field]).strip()
        }
        if conflicting_secrets:
            raise ValueError(
                "cannot set and clear secret fields together: "
                + ", ".join(sorted(conflicting_secrets))
            )
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
        if "ocr_device" in clean:
            resolve_ocr_device(str(clean["ocr_device"]))
        if "ocr_lang" in clean:
            resolve_ocr_language(str(clean["ocr_lang"]))
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
            pending_reviews += sum(t.status == "pending" for t in state.visual_review_tasks)
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
        from src.domain import SchemaIndex

        excluded = {
            item.target_id
            for item in state.validation.issues
            if item.target_type == "candidate" and item.status == "excluded"
        }
        issues = await ValidationService().candidates(
            [c for c in state.candidates if c.id not in excluded],
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
        report = ValidationService.merge(
            state.validation,
            issues,
            canonical_hash(state.document.model_dump(mode="json")),
            len(state.claims),
        )
        for candidate in state.candidates:
            current = [
                item for item in report.issues
                if item.target_id == candidate.id and item.status in {"open", "deferred"}
            ]
            for item in current:
                item.allowed_actions = candidate_actions(candidate, current)
        return report

    def _validation_target(
        self, state: WorkflowState, issue_ids: list[str]
    ) -> tuple[CandidateClaim, list[Any]]:
        if not issue_ids:
            raise ValueError("at least one validation issue is required")
        issues = [item for item in state.validation.issues if item.id in set(issue_ids)]
        if len(issues) != len(set(issue_ids)) or any(
            item.status not in {"open", "deferred"} for item in issues
        ):
            raise ValueError("validation issue already handled or unavailable")
        target_ids = {item.target_id for item in issues}
        if len(target_ids) != 1:
            raise ValueError("validation issues must belong to one candidate")
        target_id = next(iter(target_ids))
        candidate = next((item for item in state.candidates if item.id == target_id), None)
        if candidate is None:
            raise ValueError("validation candidate is unavailable")
        return candidate, issues

    async def preview_validation_correction(
        self,
        run_id: str,
        issue_ids: list[str],
        action: ValidationAction,
        replacement: dict[str, Any] | None = None,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        state = self.show_run(run_id)
        if state.pipeline_version != PIPELINE_VERSION or state.status != "awaiting_review":
            raise ValueError("validation decision is stale or incompatible")
        if expected_version is not None and state.validation_version != expected_version:
            raise ValueError("stale validation candidate version")
        candidate, issues = self._validation_target(state, issue_ids)

        all_issues = [
            item for item in state.validation.issues
            if item.target_id == candidate.id and item.status in {"open", "deferred"}
        ]
        if action not in candidate_actions(candidate, all_issues):
            raise ValueError("validation action is not allowed for this issue")
        patch = dict(replacement or {})
        if action == "approve" and patch:
            raise ValueError("approval cannot change the candidate")
        if (
            action in {"replace_entity_type", "replace_entity_link"}
            and patch.get("endpoint") == "object"
            and not isinstance(candidate.object, type(candidate.subject))
        ):
            raise ValueError("literal object has no entity type or entity link")
        projected = corrected_candidate(candidate, action, patch)
        link_override: dict[str, str | None] = {}
        if action == "replace_relation" and state.output_schema is not None:
            relation = SchemaIndex(state.output_schema).relation(str(patch.get("relation") or ""))
            if relation is None:
                raise ValueError("replacement relation is not in the run schema")
            patch["relation"] = relation.id
            projected = corrected_candidate(candidate, action, patch)
        elif action == "replace_entity_type" and state.output_schema is not None:
            entity_type = SchemaIndex(state.output_schema).entity_type(
                str(patch.get("entity_type") or "")
            )
            if entity_type is None:
                raise ValueError("replacement entity type is not in the run schema")
            patch["entity_type"] = entity_type
            projected = corrected_candidate(candidate, action, patch)
        elif action == "replace_entity_link":
            endpoint = str(patch.get("endpoint") or "")
            if endpoint not in {"subject", "object"}:
                raise ValueError("replacement endpoint must be subject or object")
            mention = candidate.subject if endpoint == "subject" else candidate.object
            if not isinstance(mention, type(candidate.subject)):
                raise ValueError("literal object cannot be linked to an entity")
            entity_id = str(patch.get("entity_id") or "").strip() or None
            if entity_id is None:
                link_override[mention.id] = None
            else:
                entity = next((item for item in state.entities if item.id == entity_id), None)
                if entity is None:
                    entity = await self.graph_store.get_entity(entity_id)
                if entity is None or not entity.active:
                    raise ValueError("replacement canonical entity is unavailable")
                patch["entity_id"] = entity.id
                patch["entity_type"] = entity.entity_type
                projected = corrected_candidate(
                    candidate,
                    "replace_entity_type",
                    {"endpoint": endpoint, "entity_type": entity.entity_type},
                )
                link_override[mention.id] = entity.id
        remaining: list[Any] = []
        if projected is not None:
            if state.output_schema is None or state.document is None:
                raise ValueError("run has no schema or document")
            remaining = await ValidationService().candidates(
                [projected],
                SchemaIndex(state.output_schema),
                state.document,
                self.evidence_store,
                ({e.id: e for e in state.entities} if state.entities else None)
                if action == "approve" else None,
                (state.mention_to_entity if state.entities else None)
                if action == "approve" else None,
            )
        return {
            "run_id": run_id,
            "target_id": candidate.id,
            "issue_ids": [item.id for item in all_issues],
            "action": action,
            "replacement": patch,
            "before": candidate.model_dump(mode="json"),
            "after": projected.model_dump(mode="json") if projected is not None else None,
            "remaining_issues": [item.model_dump(mode="json") for item in remaining],
            "remaining_issue_count": len(remaining),
            "can_apply": action in {"exclude", "defer"} or not any(
                item.severity == "blocking" for item in remaining
            ),
            "validation_version": state.validation_version,
            "link_override": link_override,
        }

    async def apply_validation_correction(
        self,
        run_id: str,
        issue_ids: list[str],
        action: ValidationAction,
        replacement: dict[str, Any],
        reviewer: str,
        reason: str,
        request_id: str,
        expected_version: int,
    ) -> WorkflowState:
        person, note, rid = reviewer.strip(), reason.strip(), request_id.strip()
        if not person or not note or not rid:
            raise ValueError("reviewer, reason and request_id are required")
        with self.runs.mutation_lock(run_id):
            await self.reviews.recover(run_id)
            state = self.show_run(run_id)
            previous = next(
                (item for item in state.validation_corrections if item.request_id == rid), None
            )
            if previous is not None:
                if (
                    previous.action != action
                    or set(previous.issue_ids) != set(issue_ids)
                    or previous.replacement != replacement
                    or previous.reviewer != person
                    or previous.reason != note
                ):
                    raise ValueError("request id reused with a different correction")
                return state
            preview = await self.preview_validation_correction(
                run_id, issue_ids, action, replacement, expected_version
            )
            if not preview["can_apply"]:
                raise ValueError("corrected candidate still violates validation constraints")
            candidate, issues = self._validation_target(state, issue_ids)
            issues = [
                item for item in state.validation.issues
                if item.target_id == candidate.id and item.status in {"open", "deferred"}
            ]
            event_id = stable_id("validation-correction", run_id, rid)
            projected = (
                CandidateClaim.model_validate(preview["after"])
                if preview["after"] is not None
                else None
            )
            if action == "approve":
                for item in issues:
                    item.status = "approved"
            elif action == "exclude":
                for item in state.validation.issues:
                    if item.target_id == candidate.id and item.status in {"open", "deferred"}:
                        item.status = "excluded"
            elif action == "defer":
                for item in state.validation.issues:
                    if item.target_id == candidate.id and item.status == "open":
                        item.status = "deferred"
            else:
                assert projected is not None
                state.candidates = replace_candidate(state.candidates, candidate.id, projected)
                state.text_candidates = replace_candidate(
                    state.text_candidates, candidate.id, projected
                )
                state.visual_candidates = replace_candidate(
                    state.visual_candidates, candidate.id, projected
                )
                if state.extraction_result is not None:
                    state.extraction_result.relations = replace_candidate(
                        state.extraction_result.relations, candidate.id, projected
                    )
                for item in state.validation.issues:
                    if item.target_id == candidate.id and item.status in {"open", "deferred"}:
                        item.status = "repaired"
                state.validation_entity_overrides.update(preview["link_override"])
                assert state.output_schema is not None and state.document is not None
                active = {
                    item.target_id
                    for item in state.validation.issues
                    if item.status == "excluded" and item.target_type == "candidate"
                }
                fresh = await ValidationService().candidates(
                    [item for item in state.candidates if item.id not in active],
                    SchemaIndex(state.output_schema),
                    state.document,
                    self.evidence_store,
                )
                state.validation = ValidationService.merge(state.validation, fresh)
                pending = ValidationService.issue(
                    APPROVAL_REQUIRED, "schema", "candidate", projected.id,
                    "approval", "待确认通过：请核对修正结果后选择审核通过。",
                    projected.evidence_ids,
                    {
                        "subject": projected.subject.model_dump(mode="json"),
                        "relation": projected.relation,
                        "object": (
                            projected.object.model_dump(mode="json")
                            if isinstance(projected.object, type(projected.subject))
                            else {"literal": projected.object}
                        ),
                    },
                    allowed_actions=["approve", "exclude", "defer"],
                    candidate_version=state.validation_version + 1,
                )
                state.validation = ValidationService.merge(state.validation, [pending])
                state.entities = []
                state.mention_to_entity = {}
                state.entity_resolution_decisions = []
                state.entity_review_tasks = []
                state.claims = []
                state.conflicts = []
                state.review_tasks = []
            state.validation_version += 1
            event = ValidationCorrectionEvent(
                id=event_id,
                run_id=run_id,
                target_id=candidate.id,
                issue_ids=list(issue_ids),
                action=action,
                replacement=preview["replacement"],
                before=preview["before"],
                after=preview["after"],
                reviewer=person,
                reason=note,
                request_id=rid,
                expected_version=expected_version,
                applied_version=state.validation_version,
            )
            state.validation_corrections.append(event)
            state.validation_decisions.extend(
                ValidationReviewDecision(
                    issue_id=item.id,
                    target_id=candidate.id,
                    action=action,
                    reviewer=person,
                    comment=note,
                    request_id=rid,
                    expected_version=expected_version,
                    replacement=preview["replacement"],
                )
                for item in issues
            )
            state.validation = ValidationService.merge(state.validation, [])
            self.reviews.update_status(state)
            workflow = self.review_workflow(state)
            updated = await workflow.record_validation_correction(state)
            if not updated:
                raise LegacyCheckpointError("checkpoint unavailable")
            self.audit.record("validation_correction", event_id, event.model_dump(mode="json"))
            return state

    async def exclude_validation_issue(
        self, run_id: str, issue_id: str, reviewer: str, comment: str = ""
    ) -> WorkflowState:
        state = self.show_run(run_id)
        issue = next((item for item in state.validation.issues if item.id == issue_id), None)
        if issue is None or issue.status != "open":
            raise ValueError("validation issue already handled or unavailable")
        return await self.apply_validation_correction(
            run_id,
            [issue_id],
            "exclude",
            {},
            reviewer,
            comment or "excluded by reviewer",
            stable_id("legacy-validation-request", run_id, issue_id, reviewer, comment),
            state.validation_version,
        )

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
        return self._llm_provider(
            name,
            base_url=self.settings.llm_base_url,
            model=self.settings.llm_model,
            api_key=self.settings.llm_api_key,
        )

    def _llm_provider(
        self,
        name: str,
        *,
        base_url: str,
        model: str | None,
        api_key: str | None,
    ) -> LLMProvider:
        if name == "mock":
            return MockLLMProvider()
        if name != "openai-compatible":
            raise ProviderConfigurationError(f"unknown provider: {name}")
        if not api_key:
            raise ProviderConfigurationError("openai-compatible requires PRISMKE_LLM_API_KEY")
        if not model:
            raise ProviderConfigurationError("openai-compatible requires PRISMKE_LLM_MODEL")
        self._validate_endpoint(base_url, "PRISMKE_LLM_BASE_URL")
        return OpenAICompatibleLLMProvider(
            base_url=base_url,
            api_key=api_key,
            model=model,
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
        return self._vlm_provider(
            name,
            base_url=self.settings.vlm_base_url,
            model=self.settings.vlm_model,
            api_key=self.settings.vlm_api_key,
        )

    def _vlm_provider(
        self,
        name: str,
        *,
        base_url: str,
        model: str | None,
        api_key: str | None,
    ) -> VLMProvider:
        if name == "disabled":
            return DisabledVLMProvider()
        if name == "mock":
            return MockVLMProvider()
        if name != "openai-compatible":
            raise ProviderConfigurationError(f"unknown VLM provider: {name}")
        if not api_key:
            raise ProviderConfigurationError("openai-compatible VLM requires PRISMKE_VLM_API_KEY")
        if not model:
            raise ProviderConfigurationError("openai-compatible VLM requires PRISMKE_VLM_MODEL")
        self._validate_endpoint(base_url, "PRISMKE_VLM_BASE_URL")
        return OpenAICompatibleVLMProvider(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout=self.settings.vlm_timeout,
            max_image_edge=self.settings.vlm_max_image_edge,
        )

    def _credentials(self, run_id: str) -> TransientProviderCredentials:
        return self._run_credentials.get(run_id, TransientProviderCredentials())

    def release_run_credentials(self, run_id: str) -> None:
        """Forget browser-supplied credentials after one execution attempt."""

        self._run_credentials.pop(run_id, None)

    def provider_for_state(self, state: WorkflowState) -> LLMProvider:
        credentials = self._credentials(state.run_id)
        if (
            credentials.llm_api_key is None
            and state.llm_base_url in {None, self.settings.llm_base_url}
            and state.llm_model in {None, self.settings.llm_model}
        ):
            return self.provider(state.provider_name)
        return self._llm_provider(
            state.provider_name,
            base_url=state.llm_base_url or self.settings.llm_base_url,
            model=state.llm_model or self.settings.llm_model,
            api_key=credentials.llm_api_key or self.settings.llm_api_key,
        )

    def vlm_provider_for_state(self, state: WorkflowState) -> VLMProvider:
        credentials = self._credentials(state.run_id)
        if (
            credentials.vlm_api_key is None
            and state.vlm_base_url in {None, self.settings.vlm_base_url}
            and state.vlm_model in {None, self.settings.vlm_model}
        ):
            return self.vlm_provider(state.vlm_provider_name)
        return self._vlm_provider(
            state.vlm_provider_name,
            base_url=state.vlm_base_url or self.settings.vlm_base_url,
            model=state.vlm_model or self.settings.vlm_model,
            api_key=credentials.vlm_api_key or self.settings.vlm_api_key,
        )

    def missing_run_credentials(self, state: WorkflowState) -> bool:
        credentials = self._credentials(state.run_id)
        needs_llm = (
            state.provider_name == "openai-compatible"
            or (state.reflection_enabled and state.reflection_provider_name == "openai-compatible")
            or state.semantic_advisor_name == "openai-compatible"
        )
        needs_vlm = state.vlm_provider_name == "openai-compatible"
        return bool(
            (needs_llm and not (credentials.llm_api_key or self.settings.llm_api_key))
            or (needs_vlm and not (credentials.vlm_api_key or self.settings.vlm_api_key))
        )

    def attach_run_credentials(
        self,
        run_id: str,
        *,
        llm_api_key: str | None = None,
        vlm_api_key: str | None = None,
    ) -> None:
        state = self.show_run(run_id)
        previous = self._credentials(run_id)
        credentials = TransientProviderCredentials(
            llm_api_key=(llm_api_key or "").strip() or previous.llm_api_key,
            vlm_api_key=(vlm_api_key or "").strip() or previous.vlm_api_key,
        )
        self._run_credentials[run_id] = credentials
        if self.provider_for_state(state).fingerprint() != state.provider_fingerprint:
            self._run_credentials.pop(run_id, None)
            raise ProviderConfigurationError("provider configuration changed since run creation")
        if self.vlm_provider_for_state(state).fingerprint() != state.vlm_provider_fingerprint:
            self._run_credentials.pop(run_id, None)
            raise ProviderConfigurationError("VLM configuration changed since run creation")
        if (
            self.reflection_provider_for_state(state).fingerprint()
            != state.reflection_provider_fingerprint
        ):
            self._run_credentials.pop(run_id, None)
            raise ProviderConfigurationError("Reflection configuration changed since run creation")
        if (
            self.semantic_advisor_for_state(state).fingerprint()
            != state.semantic_advisor_fingerprint
        ):
            self._run_credentials.pop(run_id, None)
            raise ProviderConfigurationError(
                "semantic advisor configuration changed since run creation"
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
        return self._reflection_provider(
            name,
            base_url=self.settings.llm_base_url,
            model=self.settings.llm_model,
            api_key=self.settings.llm_api_key,
        )

    def _reflection_provider(
        self,
        name: str,
        *,
        base_url: str,
        model: str | None,
        api_key: str | None,
    ) -> ReflectionProvider:
        if name == "disabled":
            return DisabledReflectionProvider()
        if name == "mock":
            return MockReflectionProvider()
        if name != "openai-compatible":
            raise ProviderConfigurationError(f"unknown Reflection provider: {name}")
        if not api_key:
            raise ProviderConfigurationError(
                "openai-compatible Reflection requires PRISMKE_LLM_API_KEY"
            )
        if not model:
            raise ProviderConfigurationError(
                "openai-compatible Reflection requires PRISMKE_LLM_MODEL"
            )
        self._validate_endpoint(base_url, "PRISMKE_LLM_BASE_URL")
        return OpenAICompatibleReflectionProvider(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout=self.settings.request_timeout,
        )

    def semantic_advisor(self, name: str) -> SemanticAdvisor:
        return self._semantic_advisor(
            name,
            base_url=self.settings.llm_base_url,
            model=self.settings.llm_model,
            api_key=self.settings.llm_api_key,
        )

    def _semantic_advisor(
        self,
        name: str,
        *,
        base_url: str,
        model: str | None,
        api_key: str | None,
    ) -> SemanticAdvisor:
        if name == "disabled":
            return DisabledSemanticAdvisor()
        if name == "mock":
            return MockSemanticAdvisor()
        if name != "openai-compatible":
            raise ProviderConfigurationError(f"unknown semantic advisor: {name}")
        if not api_key:
            raise ProviderConfigurationError("semantic advisor requires PRISMKE_LLM_API_KEY")
        if not model:
            raise ProviderConfigurationError("semantic advisor requires PRISMKE_LLM_MODEL")
        self._validate_endpoint(base_url, "PRISMKE_LLM_BASE_URL")
        return OpenAICompatibleSemanticAdvisor(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout=self.settings.request_timeout,
        )

    def reflection_provider_for_state(self, state: WorkflowState) -> ReflectionProvider:
        credentials = self._credentials(state.run_id)
        return self._reflection_provider(
            state.reflection_provider_name,
            base_url=state.llm_base_url or self.settings.llm_base_url,
            model=state.llm_model or self.settings.llm_model,
            api_key=credentials.llm_api_key or self.settings.llm_api_key,
        )

    def semantic_advisor_for_state(self, state: WorkflowState) -> SemanticAdvisor:
        credentials = self._credentials(state.run_id)
        return self._semantic_advisor(
            state.semantic_advisor_name,
            base_url=state.llm_base_url or self.settings.llm_base_url,
            model=state.llm_model or self.settings.llm_model,
            api_key=credentials.llm_api_key or self.settings.llm_api_key,
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
        from src.domain import CaseStatusEvent

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
                self.reflection_provider_for_state(state),
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
                derived_dir=self.settings.derived_documents_dir,
                libreoffice_bin=self.settings.libreoffice_bin,
                conversion_timeout_seconds=self.settings.document_conversion_timeout_seconds,
                pdf_parse_mode=(
                    state.pdf_parse_mode
                    if state is not None
                    else PDFParseMode(self.settings.pdf_parse_mode)
                ),
                pdf_thresholds=PDFComplexityThresholds(
                    no_text_ratio=self.settings.pdf_no_text_ratio,
                    short_text_chars=self.settings.pdf_short_text_chars,
                    short_text_ratio=self.settings.pdf_short_text_ratio,
                    table_ratio=self.settings.pdf_table_ratio,
                    drawing_count=self.settings.pdf_drawing_count,
                    drawing_ratio=self.settings.pdf_drawing_ratio,
                    multicolumn_ratio=self.settings.pdf_multicolumn_ratio,
                ),
                mineru_client=MinerUV1Client(
                    self.settings.mineru_base_url,
                    self.settings.derived_documents_dir,
                    version=self.settings.mineru_version,
                    tier=self.settings.mineru_tier,
                    request_timeout=self.settings.mineru_request_timeout,
                    transfer_timeout=self.settings.mineru_transfer_timeout,
                    poll_interval=self.settings.mineru_poll_interval,
                    max_polls=self.settings.mineru_max_polls,
                ),
                pdf_fallback_approved=(state.pdf_parser_fallback_approved if state else False),
                archive_max_entries=self.settings.max_archive_entries,
                archive_max_entry_bytes=self.settings.max_file_bytes,
                archive_max_total_bytes=self.settings.max_batch_bytes,
                archive_max_compression_ratio=self.settings.max_archive_compression_ratio,
            ),
            embedding_provider=self.embedding_provider(),
            entity_top_k=self.settings.entity_top_k,
            entity_auto_link_threshold=self.settings.entity_auto_link_threshold,
            entity_review_threshold=self.settings.entity_review_threshold,
            entity_min_margin=self.settings.entity_min_margin,
            reflection_service=reflection_service,
            semantic_advisor=(
                self.semantic_advisor_for_state(state)
                if state is not None
                else self.semantic_advisor("disabled")
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
        case_mode: Literal["none", "good", "good_bad"] = "none",
        reflection_enabled: bool = False,
        reflection_provider_name: str = "disabled",
        reflection_max_attempts: int | None = None,
        reflection_token_budget: int | None = None,
        reflection_time_budget_seconds: int | None = None,
        semantic_advisor_name: str = "disabled",
        agent_token_budget: int | None = None,
        llm_base_url: str | None = None,
        llm_model: str | None = None,
        vlm_base_url: str | None = None,
        vlm_model: str | None = None,
        credentials: TransientProviderCredentials | None = None,
        task_mode: TaskMode = TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION,
        entity_source_mode: EntitySourceMode = EntitySourceMode.AUTO,
        provided_entities: list[ProvidedEntity] | None = None,
        batch_id: str | None = None,
        pdf_parse_mode: PDFParseMode | str | None = None,
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
            semantic_advisor_name,
            agent_token_budget,
            llm_base_url,
            llm_model,
            vlm_base_url,
            vlm_model,
            credentials,
            task_mode,
            entity_source_mode,
            provided_entities,
            batch_id,
            pdf_parse_mode,
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
        semantic_advisor_name: str = "disabled",
        agent_token_budget: int | None = None,
        llm_base_url: str | None = None,
        llm_model: str | None = None,
        vlm_base_url: str | None = None,
        vlm_model: str | None = None,
        credentials: TransientProviderCredentials | None = None,
        task_mode: TaskMode = TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION,
        entity_source_mode: EntitySourceMode = EntitySourceMode.AUTO,
        provided_entities: list[ProvidedEntity] | None = None,
        batch_id: str | None = None,
        pdf_parse_mode: PDFParseMode | str | None = None,
    ) -> tuple[WorkflowState, bool]:
        """Validate a request and persist its initial state without executing it."""
        self.executions.ensure_accepting()
        if self.review_metadata:
            raise ValueError("isolated review workspace does not allow new extraction runs")
        input_path = input_path.resolve()
        schema_path = schema_path.resolve()
        runtime_credentials = credentials or TransientProviderCredentials()
        provided_entities = provided_entities or []
        resolved_pdf_mode = PDFParseMode(pdf_parse_mode or self.settings.pdf_parse_mode)
        if task_mode != TaskMode.RELATION_EXTRACTION:
            entity_source_mode = EntitySourceMode.AUTO
            provided_entities = []
        elif entity_source_mode == EntitySourceMode.PROVIDED and not provided_entities:
            raise ValueError("provided relation extraction requires an entity list")
        resolved_llm_base = (llm_base_url or self.settings.llm_base_url).strip()
        resolved_llm_model = (llm_model or self.settings.llm_model or "").strip() or None
        resolved_vlm_base = (vlm_base_url or self.settings.vlm_base_url).strip()
        resolved_vlm_model = (vlm_model or self.settings.vlm_model or "").strip() or None
        custom_llm = bool(
            llm_base_url is not None or llm_model is not None or runtime_credentials.llm_api_key
        )
        provider = (
            self._llm_provider(
                provider_name,
                base_url=resolved_llm_base,
                model=resolved_llm_model,
                api_key=runtime_credentials.llm_api_key or self.settings.llm_api_key,
            )
            if custom_llm
            else self.provider(provider_name)
        )
        ocr_provider = self.ocr_provider(ocr_provider_name)
        custom_vlm = bool(
            vlm_base_url is not None or vlm_model is not None or runtime_credentials.vlm_api_key
        )
        vlm_provider = (
            self._vlm_provider(
                vlm_provider_name,
                base_url=resolved_vlm_base,
                model=resolved_vlm_model,
                api_key=runtime_credentials.vlm_api_key or self.settings.vlm_api_key,
            )
            if custom_vlm
            else self.vlm_provider(vlm_provider_name)
        )
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
        reflection = self._reflection_provider(
            reflection_provider_name if reflection_enabled else "disabled",
            base_url=resolved_llm_base,
            model=resolved_llm_model,
            api_key=runtime_credentials.llm_api_key or self.settings.llm_api_key,
        )
        if reflection_enabled and reflection.fingerprint() == "reflection:disabled":
            raise ProviderConfigurationError(
                "Reflection requires mock or openai-compatible provider"
            )
        advisor = self._semantic_advisor(
            semantic_advisor_name,
            base_url=resolved_llm_base,
            model=resolved_llm_model,
            api_key=runtime_credentials.llm_api_key or self.settings.llm_api_key,
        )
        advice_budget = (
            self.settings.agent_token_budget if agent_token_budget is None else agent_token_budget
        )
        if advice_budget <= 0:
            raise ValueError("agent_token_budget must be positive")
        retriever = self.case_retriever() if case_mode != "none" else None
        case_snapshot_ids = retriever.snapshot_ids() if retriever else []
        case_snapshot = retriever.fingerprint_for(case_snapshot_ids) if retriever else "cases:none"
        schema = load_schema(schema_path)
        schema_fingerprint = canonical_hash(schema.model_dump(mode="json"))
        pdf_parser_config_fingerprint = canonical_hash(
            {
                "mode": resolved_pdf_mode,
                "thresholds": {
                    "no_text_ratio": self.settings.pdf_no_text_ratio,
                    "short_text_chars": self.settings.pdf_short_text_chars,
                    "short_text_ratio": self.settings.pdf_short_text_ratio,
                    "table_ratio": self.settings.pdf_table_ratio,
                    "drawing_count": self.settings.pdf_drawing_count,
                    "drawing_ratio": self.settings.pdf_drawing_ratio,
                    "multicolumn_ratio": self.settings.pdf_multicolumn_ratio,
                },
                "mineru": MinerUV1Client(
                    self.settings.mineru_base_url,
                    self.settings.derived_documents_dir,
                    version=self.settings.mineru_version,
                    tier=self.settings.mineru_tier,
                ).fingerprint(),
            }
        )
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
            advisor.fingerprint(),
            AGENT_POLICY_VERSION,
            advice_budget,
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
            task_mode,
            entity_source_mode,
            *(item.model_dump_json() for item in provided_entities),
            batch_id or "single",
            resolved_pdf_mode,
            pdf_parser_config_fingerprint,
            self.settings.pdf_no_text_ratio,
            self.settings.pdf_short_text_chars,
            self.settings.pdf_short_text_ratio,
            self.settings.pdf_table_ratio,
            self.settings.pdf_drawing_count,
            self.settings.pdf_drawing_ratio,
            self.settings.pdf_multicolumn_ratio,
            self.settings.mineru_version,
            self.settings.mineru_tier,
            PIPELINE_VERSION,
        )
        if self.runs.exists(run_id):
            existing = self.runs.load(run_id)
            if runtime_credentials.llm_api_key or runtime_credentials.vlm_api_key:
                self._run_credentials[run_id] = runtime_credentials
            return existing, False
        state = WorkflowState(
            run_id=run_id,
            batch_id=batch_id,
            pdf_parse_mode=resolved_pdf_mode,
            input_path=str(input_path),
            schema_path=str(schema_path),
            task_mode=task_mode,
            entity_source_mode=entity_source_mode,
            provided_entities=provided_entities,
            provider_name=provider_name,
            provider_fingerprint=provider.fingerprint(),
            llm_base_url=resolved_llm_base,
            llm_model=resolved_llm_model,
            ocr_provider_name=ocr_provider_name,
            ocr_provider_fingerprint=ocr_provider.fingerprint(),
            vlm_provider_name=vlm_provider_name,
            vlm_provider_fingerprint=vlm_provider.fingerprint(),
            vlm_base_url=resolved_vlm_base,
            vlm_model=resolved_vlm_model,
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
            semantic_advisor_name=semantic_advisor_name,
            semantic_advisor_fingerprint=advisor.fingerprint(),
            agent_policy_version=AGENT_POLICY_VERSION,
            agent_token_budget=advice_budget,
            allow_remote_assets=allow_remote_assets,
            pipeline_version=PIPELINE_VERSION,
            entity_resolution_policy_version=ENTITY_RESOLUTION_POLICY_VERSION,
        )
        with self.runs.creation_lock(run_id):
            if self.runs.exists(run_id):
                return self.runs.load(run_id), False
            if runtime_credentials.llm_api_key or runtime_credentials.vlm_api_key:
                self._run_credentials[run_id] = runtime_credentials
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
        provider = self.provider_for_state(state)
        ocr_provider = self.ocr_provider(state.ocr_provider_name)
        vlm_provider = self.vlm_provider_for_state(state)
        self._validate_reflection_policy(state)
        self._validate_agent_policy(state)
        return await self._workflow(
            provider,
            ocr_provider,
            vlm_provider,
            state.allow_remote_assets,
            state,
        ).invoke(state)

    def show_run(self, run_id: str) -> WorkflowState:
        return self.runs.load(run_id)

    async def pdf_parser_status(self) -> dict[str, Any]:
        client = MinerUV1Client(
            self.settings.mineru_base_url,
            self.settings.derived_documents_dir,
            version=self.settings.mineru_version,
            tier=self.settings.mineru_tier,
            request_timeout=self.settings.mineru_request_timeout,
        )
        mineru = await client.status()
        return {
            "default_mode": self.settings.pdf_parse_mode,
            "pymupdf": {"available": True},
            "mineru": mineru,
        }

    def pdf_parse_view(self, run_id: str) -> dict[str, Any]:
        state = self.show_run(run_id)
        return {
            "run_id": run_id,
            "mode": state.pdf_parse_mode,
            "decision": state.pdf_parse_decision,
            "fallback_approved": state.pdf_parser_fallback_approved,
            "fallback_events": self.executions.repository.pdf_fallbacks(run_id),
            "execution": self.executions.view(run_id),
        }

    def approve_pdf_parser_fallback(
        self,
        run_id: str,
        operator: str,
        reason: str,
        request_id: str,
        expected_execution_version: int,
    ) -> dict[str, Any]:
        normalized_operator = operator.strip()
        normalized_reason = reason.strip()
        normalized_request_id = request_id.strip()
        if not normalized_operator or not normalized_reason or not normalized_request_id:
            raise ValueError("PDF_FALLBACK_IDENTITY_REQUIRED")
        previous = next(
            (
                event
                for event in self.executions.repository.pdf_fallbacks(run_id)
                if event.request_id == normalized_request_id
            ),
            None,
        )
        if previous is not None:
            if (
                previous.operator != normalized_operator
                or previous.reason != normalized_reason
                or previous.expected_execution_version != expected_execution_version
            ):
                raise ValueError("REQUEST_ID_REUSED")
            task = self.executions.repository.get(run_id)
            if task is None:
                raise ValueError("EXECUTION_NOT_REGISTERED")
            return {
                "event": previous.model_dump(mode="json"),
                "execution": self.executions.view(run_id),
                "version": task.version,
            }
        state = self.show_run(run_id)
        if state.pdf_parse_mode != PDFParseMode.AUTO:
            raise ValueError("PDF_FALLBACK_FORCED_MINERU_FORBIDDEN")
        if (
            state.status != "parser_blocked"
            or state.pdf_parse_decision is None
            or state.pdf_parse_decision.actual_parser != PDFParserName.MINERU
        ):
            raise ValueError("PDF_FALLBACK_NOT_AVAILABLE")
        event, task = self.executions.repository.record_pdf_fallback(
            PDFParserFallbackEvent(
                run_id=run_id,
                operator=normalized_operator,
                reason=normalized_reason,
                request_id=normalized_request_id,
                expected_execution_version=expected_execution_version,
            )
        )
        if not state.pdf_parser_fallback_approved:
            state.pdf_parser_fallback_approved = True
            state.pdf_parser_fallback_event_id = stable_id("pdf-fallback", run_id, event.request_id)
            state.status = "running"
            state.failed_node = None
            self.runs.save(state)
            task = self.executions.enqueue(run_id, "resume", expected_version=task.version)
        self.audit.record(
            "pdf_parser_fallback",
            run_id,
            {
                "event_id": state.pdf_parser_fallback_event_id,
                "operator": event.operator,
                "reason": event.reason,
                "from_parser": event.from_parser,
                "to_parser": event.to_parser,
            },
        )
        return {
            "event": event.model_dump(mode="json"),
            "execution": self.executions.view(run_id),
            "version": task.version,
        }

    def run_result(self, run_id: str) -> TaskExtractionResult:
        state = self.show_run(run_id)
        if state.extraction_result is None:
            raise ValueError("RUN_RESULT_NOT_READY")
        return state.extraction_result

    def review_extraction_result(
        self,
        run_id: str,
        target_type: str,
        target_id: str,
        decision: str,
        reviewer: str,
        reason: str,
        request_id: str,
        expected_version: int,
    ) -> TaskExtractionResult:
        if decision not in {"approve", "reject", "defer"}:
            raise ValueError("INVALID_EXTRACTION_REVIEW_DECISION")
        if not reviewer.strip() or not request_id.strip():
            raise ValueError("EXTRACTION_REVIEW_IDENTITY_REQUIRED")
        if decision in {"reject", "defer"} and not reason.strip():
            raise ValueError("EXTRACTION_REVIEW_REASON_REQUIRED")
        with self.runs.mutation_lock(run_id):
            state = self.show_run(run_id)
            result = state.extraction_result
            if result is None:
                raise ValueError("RUN_RESULT_NOT_READY")
            previous = next(
                (event for event in result.review_events if event.request_id == request_id),
                None,
            )
            if previous:
                if (
                    previous.target_type != target_type
                    or previous.target_id != target_id
                    or previous.decision != decision
                ):
                    raise ValueError("REQUEST_ID_REUSED")
                return result
            if result.version != expected_version:
                raise ValueError("STALE_RESULT_VERSION")
            collections: dict[str, list[Any]] = {
                "entity": list(result.entities),
                "relation": list(result.relations),
                "attribute": list(result.attributes),
                "event": list(result.events),
            }
            if target_type not in collections or target_id not in {
                item.id for item in collections[target_type]
            }:
                raise KeyError(target_id)
            result.review_events.append(
                ExtractionReviewEvent(
                    id=stable_id(
                        "extraction-review",
                        run_id,
                        target_type,
                        target_id,
                        request_id,
                    ),
                    request_id=request_id,
                    target_type=target_type,
                    target_id=target_id,
                    decision=decision,
                    reviewer=reviewer.strip(),
                    reason=reason.strip(),
                )
            )
            result.version += 1
            state.extraction_result = result
            latest_decisions = {event.target_id: event.decision for event in result.review_events}
            pending_review_ids = {
                target_id
                for target_id in result.review_required_ids
                if latest_decisions.get(target_id) not in {"approve", "reject"}
            }
            if not pending_review_ids and state.status == "awaiting_review":
                state.status = "completed"
            self.runs.save(state)
            if not pending_review_ids and state.status == "completed":
                with suppress(KeyError):
                    self.executions.set_status(run_id, "completed")
            self.audit.record(
                "review_extraction_result",
                target_id,
                {
                    "event_id": result.review_events[-1].id,
                    "run_id": run_id,
                    "target_type": target_type,
                    "decision": decision,
                    "reviewer": reviewer.strip(),
                },
            )
            return result

    def create_batch(
        self,
        documents: list[Path],
        schema_path: Path,
        *,
        task_mode: TaskMode = TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION,
        entity_source_mode: EntitySourceMode = EntitySourceMode.AUTO,
        provided_entities: list[ProvidedEntity] | None = None,
        provider_name: str = "mock",
        ocr_provider_name: str = "disabled",
        vlm_provider_name: str = "disabled",
        allow_remote_assets: bool = False,
        case_mode: Literal["none", "good", "good_bad"] = "none",
        reflection_enabled: bool = False,
        reflection_provider_name: str = "disabled",
        reflection_max_attempts: int | None = None,
        reflection_token_budget: int | None = None,
        reflection_time_budget_seconds: int | None = None,
        semantic_advisor_name: str = "disabled",
        agent_token_budget: int | None = None,
        operator: str | None = None,
        llm_base_url: str | None = None,
        llm_model: str | None = None,
        vlm_base_url: str | None = None,
        vlm_model: str | None = None,
        credentials: TransientProviderCredentials | None = None,
        pdf_parse_mode: PDFParseMode | str | None = None,
    ) -> tuple[BatchRun, bool]:
        if not documents:
            raise ValueError("BATCH_EMPTY")
        if len(documents) > self.settings.max_batch_files:
            raise ValueError("BATCH_FILE_LIMIT_EXCEEDED")
        paths = [path.resolve() for path in documents]
        sizes = [path.stat().st_size for path in paths]
        if any(size > self.settings.max_file_bytes for size in sizes):
            raise ValueError("BATCH_FILE_SIZE_EXCEEDED")
        if sum(sizes) > self.settings.max_batch_bytes:
            raise ValueError("BATCH_TOTAL_SIZE_EXCEEDED")
        hashes = [file_sha256(path) for path in paths]
        filenames = []
        for path in paths:
            prefix, separator, extracted_name = path.name.partition("--")
            filenames.append(
                extracted_name
                if separator
                and len(prefix) == 32
                and all(character in "0123456789abcdef" for character in prefix)
                else path.name
            )
        batch_id = stable_id(
            "batch",
            file_sha256(schema_path.resolve()),
            task_mode,
            entity_source_mode,
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
            semantic_advisor_name,
            agent_token_budget,
            llm_base_url,
            llm_model,
            vlm_base_url,
            vlm_model,
            PDFParseMode(pdf_parse_mode or self.settings.pdf_parse_mode),
            *(item.model_dump_json() for item in provided_entities or []),
            *[f"{name}:{digest}" for name, digest in zip(filenames, hashes, strict=True)],
        )
        if self.batches.exists(batch_id):
            return self.refresh_batch(batch_id), False
        batch = BatchRun(
            id=batch_id,
            task_mode=task_mode,
            entity_source_mode=entity_source_mode,
            schema_path=str(schema_path.resolve()),
            operator=operator,
            pdf_parse_mode=PDFParseMode(pdf_parse_mode or self.settings.pdf_parse_mode),
        )
        first_by_hash: dict[str, BatchItem] = {}
        for index, (path, filename, digest, size) in enumerate(
            zip(paths, filenames, hashes, sizes, strict=True)
        ):
            item = BatchItem(
                id=stable_id("batch-item", batch_id, index, filename, digest),
                filename=filename,
                source_path=str(path),
                content_hash=digest,
                size_bytes=size,
            )
            reused_item = first_by_hash.get(digest)
            if reused_item is not None:
                item.status = BatchItemStatus.REUSED
                item.reused_from_item_id = reused_item.id
                item.run_id = reused_item.run_id
                batch.items.append(item)
                continue
            state, created = self.create_run(
                path,
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
                semantic_advisor_name,
                agent_token_budget,
                llm_base_url,
                llm_model,
                vlm_base_url,
                vlm_model,
                credentials,
                task_mode=task_mode,
                entity_source_mode=entity_source_mode,
                provided_entities=provided_entities,
                batch_id=batch_id,
                pdf_parse_mode=pdf_parse_mode,
            )
            item.run_id = state.run_id
            item.status = BatchItemStatus.QUEUED if created else BatchItemStatus.REUSED
            batch.items.append(item)
            first_by_hash[digest] = item
            if created:
                self.executions.enqueue(state.run_id, "execute")
        batch.status = BatchStatus.RUNNING
        self.batches.save(batch)
        return batch, True

    def refresh_batch(self, batch_id: str) -> BatchRun:
        batch = self.batches.load(batch_id)
        statuses: list[BatchItemStatus] = []
        for item in batch.items:
            if item.status == BatchItemStatus.EXCLUDED or not item.run_id:
                statuses.append(item.status)
                continue
            state = self.show_run(item.run_id)
            execution = self.executions.view(item.run_id)
            if state.status in {"failed", "parser_blocked"} or execution["status"] in {
                "failed",
                "parser_blocked",
            }:
                item.status = BatchItemStatus.FAILED
                item.failure_code = execution.get("error_code") or state.failed_node
                item.failure_reason = state.errors[-1] if state.errors else None
            elif state.status == "awaiting_review":
                item.status = BatchItemStatus.AWAITING_REVIEW
            elif state.status == "completed":
                if item.reused_from_item_id:
                    item.status = BatchItemStatus.REUSED
                else:
                    item.status = BatchItemStatus.COMPLETED
                item.token_usage = sum(call.total_tokens or 0 for call in state.provider_calls)
            else:
                item.status = BatchItemStatus.RUNNING
            statuses.append(item.status)
        active_statuses = [status for status in statuses if status != BatchItemStatus.EXCLUDED]
        cross_document_blocked = any(
            error.startswith("cross_document_conflict:") for error in batch.errors
        )
        if cross_document_blocked or BatchItemStatus.FAILED in active_statuses:
            batch.status = BatchStatus.BLOCKED
        elif BatchItemStatus.AWAITING_REVIEW in active_statuses:
            batch.status = BatchStatus.AWAITING_REVIEW
        elif any(
            status in {BatchItemStatus.QUEUED, BatchItemStatus.RUNNING}
            for status in active_statuses
        ):
            batch.status = BatchStatus.RUNNING
        elif batch.task_mode.permits_graph_commit and batch.revision_id is None:
            batch.status = BatchStatus.AWAITING_COMMIT
        else:
            batch.status = BatchStatus.COMPLETED
        from src.domain.knowledge import utc_now

        batch.updated_at = utc_now()
        self.batches.save(batch)
        return batch

    def batch_results(self, batch_id: str) -> list[BatchResult]:
        batch = self.refresh_batch(batch_id)
        results = []
        for item in batch.items:
            result = None
            error = item.failure_reason
            if item.run_id and item.status not in {
                BatchItemStatus.FAILED,
                BatchItemStatus.EXCLUDED,
            }:
                state = self.show_run(item.run_id)
                result = state.extraction_result
            results.append(
                BatchResult(
                    batch_id=batch.id,
                    item_id=item.id,
                    run_id=item.run_id,
                    status=item.status,
                    result=result,
                    error=error,
                )
            )
        return results

    def retry_batch_item(self, batch_id: str, item_id: str) -> BatchRun:
        batch = self.refresh_batch(batch_id)
        item = next((item for item in batch.items if item.id == item_id), None)
        if item is None:
            raise KeyError(item_id)
        if item.status != BatchItemStatus.FAILED or not item.run_id:
            raise ValueError("BATCH_ITEM_NOT_RETRYABLE")
        self.executions.enqueue(item.run_id, "resume")
        item.status = BatchItemStatus.QUEUED
        item.failure_code = None
        item.failure_reason = None
        batch.status = BatchStatus.RUNNING
        self.batches.save(batch)
        return batch

    def exclude_batch_item(
        self, batch_id: str, item_id: str, operator: str, reason: str
    ) -> BatchRun:
        if not operator.strip() or not reason.strip():
            raise ValueError("BATCH_EXCLUSION_REQUIRES_OPERATOR_REASON")
        batch = self.refresh_batch(batch_id)
        item = next((item for item in batch.items if item.id == item_id), None)
        if item is None:
            raise KeyError(item_id)
        conflict_blocked = batch.status == BatchStatus.BLOCKED and any(
            error.startswith("cross_document_conflict:") for error in batch.errors
        )
        if item.status not in {BatchItemStatus.FAILED, BatchItemStatus.QUEUED} and not (
            conflict_blocked and item.status in {BatchItemStatus.COMPLETED, BatchItemStatus.REUSED}
        ):
            raise ValueError("BATCH_ITEM_NOT_EXCLUDABLE")
        item.status = BatchItemStatus.EXCLUDED
        item.excluded_by = operator.strip()
        item.exclusion_reason = reason.strip()
        batch.errors = []
        self.batches.save(batch)
        return self.refresh_batch(batch_id)

    async def confirm_batch_commit(self, batch_id: str, reviewer: str) -> BatchRun:
        if not reviewer.strip():
            raise ValueError("BATCH_COMMIT_REVIEWER_REQUIRED")
        batch = self.refresh_batch(batch_id)
        if batch.task_mode != TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION:
            from src.core.errors import TaskModeCommitError

            raise TaskModeCommitError(TaskModeCommitError.code)
        if batch.status != BatchStatus.AWAITING_COMMIT or batch.revision_id:
            raise ValueError("BATCH_NOT_READY_FOR_COMMIT")
        states = {
            item.run_id: self.show_run(item.run_id)
            for item in batch.items
            if item.status != BatchItemStatus.EXCLUDED and item.run_id
        }
        if not states:
            raise ValueError("BATCH_HAS_NO_ACTIVE_ITEMS")
        if any(
            state.validation.blocking_count
            or any(task.status == "pending" for task in state.entity_review_tasks)
            or any(task.status == "pending" for task in state.review_tasks)
            for state in states.values()
        ):
            raise ValueError("BATCH_REVIEW_PENDING")
        schemas = {
            state.output_schema.schema_id: state.output_schema
            for state in states.values()
            if state.output_schema is not None
        }
        if len(schemas) != 1:
            raise ValueError("BATCH_SCHEMA_CHANGED")
        schema = next(iter(schemas.values()))
        schema_id = canonical_hash(schema.model_dump(mode="json"))
        merged_claims = merge_supporting_claims(
            [
                claim.model_copy(
                    deep=True,
                    update={"source_run_ids": sorted(set([*claim.source_run_ids, state.run_id]))},
                )
                for state in states.values()
                for claim in state.claims
                if claim.status in {ClaimStatus.AUTO_APPROVED, ClaimStatus.APPROVED}
            ]
        )
        cross_document_conflicts = [
            conflict
            for conflict in detect_conflicts(
                merged_claims,
                await self.graph_store.list_claims(),
                SchemaIndex(schema),
            )
            if len(set(conflict.claim_ids) & {claim.id for claim in merged_claims}) > 1
        ]
        if cross_document_conflicts:
            batch.status = BatchStatus.BLOCKED
            batch.errors = [
                f"cross_document_conflict:{conflict.id}" for conflict in cross_document_conflicts
            ]
            self.batches.save(batch)
            raise ValueError("BATCH_CROSS_DOCUMENT_CONFLICT")
        claims = {claim.id: claim for claim in merged_claims}
        if not claims:
            raise ValueError("BATCH_NO_APPROVED_CLAIMS")
        referenced_entities = {
            entity_id
            for claim in claims.values()
            for entity_id in (claim.subject_id, claim.object_entity_id)
            if entity_id
        }
        entities = {
            entity.id: entity.model_copy(update={"active": True})
            for state in states.values()
            for entity in state.entities
            if entity.id in referenced_entities
        }
        conflicts = {
            conflict.id: conflict
            for state in states.values()
            for conflict in state.conflicts
            if set(conflict.claim_ids) <= set(claims)
        }
        documents = {
            state.document.id: GraphDocument(
                id=state.document.id,
                filename=state.document.source_filename or Path(state.document.source_path).name,
                content_hash=state.document.source_hash,
                media_type=state.document.media_type,
            )
            for state in states.values()
            if state.document is not None
        }
        evidence_ids = {
            evidence_id for claim in claims.values() for evidence_id in claim.evidence_ids
        }
        evidence = {
            item.id: item
            for state in states.values()
            if state.document is not None
            for item in state.document.evidence
            if item.id in evidence_ids
        }
        existing_claims = {claim.id: claim for claim in await self.graph_store.list_claims()}
        existing_entities = {entity.id: entity for entity in await self.graph_store.list_entities()}
        parent = await self.graph_store.latest_revision()
        changes = [
            GraphChange(
                resource_type="entity",
                resource_id=entity.id,
                action="update" if entity.id in existing_entities else "create",
                before=(
                    existing_entities[entity.id].model_dump(mode="json")
                    if entity.id in existing_entities
                    else None
                ),
                after=entity.model_dump(mode="json"),
            )
            for entity in entities.values()
        ]
        changes.extend(
            GraphChange(
                resource_type="claim",
                resource_id=claim.id,
                action="update" if claim.id in existing_claims else "create",
                before=(
                    existing_claims[claim.id].model_dump(mode="json")
                    if claim.id in existing_claims
                    else None
                ),
                after=claim.model_dump(mode="json"),
            )
            for claim in claims.values()
        )
        changes.extend(
            GraphChange(
                resource_type="conflict",
                resource_id=conflict.id,
                action="create",
                after=conflict.model_dump(mode="json"),
            )
            for conflict in conflicts.values()
        )
        revision = GraphRevision(
            id=stable_id(
                "batch-revision",
                batch.id,
                parent.id if parent else "root",
                *sorted(claims),
            ),
            run_id=batch.id,
            parent_id=parent.id if parent else None,
            entity_ids=sorted(entities),
            claim_ids=sorted(claims),
            conflict_ids=sorted(conflicts),
            changes=changes,
        )
        context = CommitValidationContext(
            schemas={schema_id: schema},
            claim_schema_ids={claim_id: schema_id for claim_id in claims},
            document_asset_ids={
                state.document.id: [asset.id for asset in state.document.media_assets]
                for state in states.values()
                if state.document is not None
            },
        )
        revision.validation_context = context
        commit = GraphCommit(
            documents=list(documents.values()),
            evidence=list(evidence.values()),
            entities=list(entities.values()),
            claims=list(claims.values()),
            conflicts=list(conflicts.values()),
            revision=revision,
            validation_context=context,
        )
        await ValidationService().commit(
            commit,
            {**existing_entities, **entities},
            evidence,
            set(documents),
            self.evidence_store,
        )
        await self.graph_store.commit(commit)
        batch.revision_id = revision.id
        batch.status = BatchStatus.COMPLETED
        self.batches.save(batch)
        self.audit.record(
            "confirm_batch_commit",
            batch.id,
            {"reviewer": reviewer.strip(), "revision_id": revision.id},
        )
        return batch

    async def entity_review_detail(self, run_id: str, task_id: str) -> dict[str, Any]:
        from src.workflow.review_details import entity_task_base

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
        from src.workflow.review_details import claim_task_detail

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
        visual_pending = sum(item.status == "pending" for item in state.visual_review_tasks)
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
            "visual_pending": visual_pending,
            "validation_pending": state.validation.blocking_count,
            "isolated": state.review_workspace,
            "review_sync_pending": sync_pending,
            "can_resume": not execution["active"]
            and not execution["blocked"]
            and not sync_pending
            and not entity_pending
            and not claim_pending
            and not visual_pending
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
            and not visual_pending
            and not state.validation.blocking_count
            and (not state.submission_confirmed or retry_commit),
            "submission": {
                "entities": len(state.graph_commit.entities),
                "claims": len(state.graph_commit.claims),
                "conflicts": len(state.graph_commit.conflicts),
                "media_occurrences": len(state.graph_commit.media_occurrences),
                "media_relations": len(state.graph_commit.media_relations),
                "visual_assertions": len(state.graph_commit.visual_assertions),
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
        provider = self.provider_for_state(state)
        ocr_provider = self.ocr_provider(state.ocr_provider_name)
        vlm_provider = self.vlm_provider_for_state(state)
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
        self._validate_agent_policy(state)
        return provider, ocr_provider, vlm_provider

    def _validate_agent_policy(self, state: WorkflowState) -> None:
        if state.agent_policy_version != AGENT_POLICY_VERSION:
            raise LegacyCheckpointError(
                "agent policy changed; old runs are read-only, rerun the input"
            )
        advisor = self.semantic_advisor_for_state(state)
        if advisor.fingerprint() != state.semantic_advisor_fingerprint:
            raise ProviderConfigurationError(
                "semantic advisor configuration changed since run creation"
            )

    def _validate_reflection_policy(self, state: WorkflowState) -> None:
        if state.case_retrieval_policy_version != CASE_RETRIEVAL_VERSION:
            raise LegacyCheckpointError(
                "case retrieval policy changed; old runs are read-only, rerun the input"
            )
        if state.reflection_policy_version != REFLECTION_POLICY_VERSION:
            raise LegacyCheckpointError(
                "Reflection policy changed; old runs are read-only, rerun the input"
            )
        reflection = self.reflection_provider_for_state(state)
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

    async def review_visual(
        self,
        run_id: str,
        task_id: str,
        decision: Literal["approve", "reject", "defer"],
        reviewer: str,
        reason: str,
        request_id: str,
        expected_version: int,
    ) -> WorkflowState:
        from src.domain import (
            GraphMediaRelation,
            VisualAssertion,
            VisualReviewEvent,
            utc_now,
        )

        if not reviewer.strip() or not reason.strip() or not request_id.strip():
            raise ValueError("VISUAL_REVIEW_REQUIRES_IDENTITY_REASON_REQUEST")
        with self.runs.mutation_lock(run_id):
            state = self.show_run(run_id)
            prior = next(
                (item for item in state.visual_review_events if item.request_id == request_id),
                None,
            )
            if prior is not None:
                if prior.task_id != task_id or prior.decision != decision:
                    raise ValueError("VISUAL_REVIEW_REQUEST_CONFLICT")
                return state
            task = next((item for item in state.visual_review_tasks if item.id == task_id), None)
            if task is None:
                raise KeyError("visual review task not found")
            if task.version != expected_version:
                raise ValueError("VISUAL_REVIEW_VERSION_CONFLICT")
            if task.status == "resolved":
                raise ValueError("VISUAL_REVIEW_ALREADY_RESOLVED")
            event_id = stable_id("visual-review-event", run_id, task_id, request_id)
            event = VisualReviewEvent(
                id=event_id,
                request_id=request_id,
                run_id=run_id,
                task_id=task_id,
                target_type=task.target_type,
                target_id=task.target_id,
                decision=decision,
                reviewer=reviewer.strip(),
                reason=reason.strip(),
                expected_version=expected_version,
                resulting_version=expected_version + 1,
            )
            if decision == "approve" and task.target_type == "media_relation":
                relation_candidate = next(
                    item for item in state.candidate_media_relations if item.id == task.target_id
                )
                if relation_candidate.target_entity_id is None:
                    raise ValueError("VISUAL_REVIEW_TARGET_ENTITY_UNRESOLVED")
                relation = GraphMediaRelation(
                    id=stable_id(
                        "media-relation",
                        relation_candidate.occurrence_id,
                        relation_candidate.relation_type,
                        relation_candidate.target_entity_id,
                        *sorted(relation_candidate.evidence_ids),
                    ),
                    occurrence_id=relation_candidate.occurrence_id,
                    relation_type=relation_candidate.relation_type,
                    target_entity_id=relation_candidate.target_entity_id,
                    evidence_ids=relation_candidate.evidence_ids,
                    source_candidate_id=relation_candidate.id,
                    approved_review_event_id=event.id,
                )
                state.media_relations = [
                    *[item for item in state.media_relations if item.id != relation.id],
                    relation,
                ]
            elif decision == "approve":
                assertion_candidate = next(
                    item for item in state.candidate_visual_assertions if item.id == task.target_id
                )
                if assertion_candidate.subject_entity_id is None:
                    raise ValueError("VISUAL_REVIEW_SUBJECT_UNRESOLVED")
                assertion = VisualAssertion(
                    id=stable_id(
                        "visual-assertion",
                        assertion_candidate.subject_entity_id,
                        assertion_candidate.predicate,
                        canonical_hash(assertion_candidate.normalized_value),
                        assertion_candidate.occurrence_id,
                        *sorted(assertion_candidate.evidence_ids),
                    ),
                    occurrence_id=assertion_candidate.occurrence_id,
                    subject_entity_id=assertion_candidate.subject_entity_id,
                    predicate=assertion_candidate.predicate,
                    normalized_value=assertion_candidate.normalized_value,
                    value_type=assertion_candidate.value_type,
                    assertion_kind=assertion_candidate.assertion_kind,
                    evidence_ids=assertion_candidate.evidence_ids,
                    source_candidate_id=assertion_candidate.id,
                    approved_review_event_id=event.id,
                )
                state.visual_assertions = [
                    *[item for item in state.visual_assertions if item.id != assertion.id],
                    assertion,
                ]
            task.version += 1
            task.last_event_id = event.id
            task.decision = decision
            task.reviewer = reviewer.strip()
            task.reason = reason.strip()
            if decision != "defer":
                task.status = "resolved"
                task.resolved_at = utc_now()
            state.visual_review_events.append(event)
            pending = [
                item.target_id for item in state.visual_review_tasks if item.status == "pending"
            ]
            if state.extraction_result is not None:
                state.extraction_result.visual_review_required_ids = pending
            if (
                not pending
                and not any(item.status == "pending" for item in state.entity_review_tasks)
                and not any(item.status == "pending" for item in state.review_tasks)
            ):
                state.status = "running" if state.task_mode.permits_graph_commit else "completed"
            if state.task_mode.permits_graph_commit:
                recorded = await self.review_workflow(state).record_review(state)
                if not recorded:
                    self.runs.save(state)
            else:
                self.runs.save(state)
            self.audit.record(
                "review_visual",
                run_id,
                {
                    "task_id": task_id,
                    "decision": decision,
                    "reviewer": reviewer.strip(),
                    "event_id": event.id,
                },
            )
            return state

    async def resume(self, run_id: str) -> WorkflowState:
        return await self.executions.run_wait(run_id, "resume")

    async def _resume(self, run_id: str) -> WorkflowState:
        await self.reviews.recover(run_id)
        state = self.runs.load(run_id)
        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError(
                f"旧流程不能由 v{PIPELINE_VERSION} 恢复；请使用对应发布版本接续"
            )
        if (
            state.validation.blocking_count
            or any(task.status == "pending" for task in state.entity_review_tasks)
            or any(task.status == "pending" for task in state.review_tasks)
            or any(task.status == "pending" for task in state.visual_review_tasks)
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
            or any(task.status == "pending" for task in state.visual_review_tasks)
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
