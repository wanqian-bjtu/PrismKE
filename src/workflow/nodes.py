"""Workflow node implementations."""

from __future__ import annotations

from pathlib import Path

from src.agents.entity_governance_agent import EntityGovernanceAgent
from src.agents.fusion_review_agent import FusionReviewAgent
from src.agents.multimodal_extraction_agent import MultimodalExtractionAgent
from src.core.errors import EvidenceIntegrityError, GraphIntegrityError
from src.core.execution_control import current_execution
from src.core.ids import canonical_hash, stable_id
from src.domain import (
    ClaimStatus,
    CommitValidationContext,
    EntityEmbedding,
    GraphChange,
    GraphCommit,
    GraphDocument,
    GraphRevision,
    SourceDocument,
    WorkflowState,
    load_schema,
)
from src.governance import entity_embedding_text
from src.governance.validation import ValidationService
from src.parsing import ParserRegistry
from src.persistence.base import EvidenceStore, GraphStore
from src.persistence.reviews import ReviewRepository
from src.providers.base import (
    EmbeddingProvider,
    LLMProvider,
    OCRProvider,
    SemanticAdvisor,
    VLMProvider,
)
from src.providers.embedding import DisabledEmbeddingProvider
from src.providers.semantic import DisabledSemanticAdvisor
from src.workflow.reflection import BoundedReflectionService


class WorkflowNodes:
    review_repository: ReviewRepository | None = None

    def __init__(
        self,
        provider: LLMProvider,
        ocr_provider: OCRProvider,
        vlm_provider: VLMProvider,
        graph_store: GraphStore,
        evidence_store: EvidenceStore,
        parsers: ParserRegistry,
        *,
        embedding_provider: EmbeddingProvider | None = None,
        entity_top_k: int = 10,
        entity_auto_link_threshold: float = 0.88,
        entity_review_threshold: float = 0.65,
        entity_min_margin: float = 0.08,
        reflection_service: BoundedReflectionService | None = None,
        semantic_advisor: SemanticAdvisor | None = None,
    ) -> None:
        self.provider = provider
        self.ocr_provider = ocr_provider
        self.vlm_provider = vlm_provider
        self.embedding_provider = embedding_provider or DisabledEmbeddingProvider()
        self.graph_store = graph_store
        self.evidence_store = evidence_store
        self.parsers = parsers
        self.entity_top_k = entity_top_k
        self.entity_auto_link_threshold = entity_auto_link_threshold
        self.entity_review_threshold = entity_review_threshold
        self.entity_min_margin = entity_min_margin
        self.reflection_service = reflection_service
        advisor = semantic_advisor or DisabledSemanticAdvisor()
        self.extraction_agent = MultimodalExtractionAgent(
            provider, ocr_provider, vlm_provider, evidence_store
        )
        self.governance_agent = EntityGovernanceAgent(
            graph_store,
            evidence_store,
            self.embedding_provider,
            advisor,
            top_k=entity_top_k,
            auto_link_threshold=entity_auto_link_threshold,
            review_threshold=entity_review_threshold,
            min_margin=entity_min_margin,
        )
        self.fusion_agent = FusionReviewAgent(graph_store, advisor, reflection_service)

    async def ingest(self, state: WorkflowState) -> WorkflowState:
        if not SourceDocument(path=state.input_path).path.is_file():
            raise FileNotFoundError(state.input_path)
        return state

    async def parse_document(self, state: WorkflowState) -> WorkflowState:
        state.document = await self.parsers.parse(SourceDocument(path=state.input_path))
        state.warnings.extend(state.document.warnings)
        return state

    async def materialize_visual_assets(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None
        missing = [
            asset.id for asset in state.document.media_assets if not Path(asset.path).is_file()
        ]
        if missing:
            raise EvidenceIntegrityError(f"materialized assets missing: {missing}")
        return state

    async def run_ocr(self, state: WorkflowState) -> WorkflowState:
        return await self.extraction_agent.recognize(state)

    async def persist_evidence(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None
        await self.evidence_store.put_document(state.document)
        return state

    async def load_schema(self, state: WorkflowState) -> WorkflowState:
        state.output_schema = load_schema(SourceDocument(path=state.schema_path).path)
        return state

    async def extract_text_claims(self, state: WorkflowState) -> WorkflowState:
        return await self.extraction_agent.extract_text(state)

    async def extract_visual_claims(self, state: WorkflowState) -> WorkflowState:
        return await self.extraction_agent.extract_visual(state)

    async def align_modalities(self, state: WorkflowState) -> WorkflowState:
        return await self.extraction_agent.align(state)

    async def reflect_candidates(self, state: WorkflowState) -> WorkflowState:
        return await self.fusion_agent.triage_candidates(state)

    async def resolve_entities(self, state: WorkflowState) -> WorkflowState:
        return await self.governance_agent.resolve(state)

    async def normalize_claims(self, state: WorkflowState) -> WorkflowState:
        return await self.governance_agent.normalize(state)

    async def detect_conflicts(self, state: WorkflowState) -> WorkflowState:
        return await self.fusion_agent.detect_conflicts(state)

    async def route_by_risk(self, state: WorkflowState) -> WorkflowState:
        self.fusion_agent.review_repository = self.review_repository
        return await self.fusion_agent.route_by_risk(state)

    async def prepare_graph_commit(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None
        if state.validation.blocking_count:
            raise GraphIntegrityError(
                f"VALIDATION_BLOCKED: {state.validation.blocking_count} 个问题未排除"
            )
        assert state.output_schema is not None
        accepted = [
            claim
            for claim in state.claims
            if claim.status in {ClaimStatus.AUTO_APPROVED, ClaimStatus.APPROVED}
        ]
        for claim in accepted:
            claim.source_run_ids = sorted(set([*claim.source_run_ids, state.run_id]))
        existing_claims = {claim.id: claim for claim in await self.graph_store.list_claims()}
        existing_entities = {entity.id: entity for entity in await self.graph_store.list_entities()}
        existing_claim_ids = set(existing_claims)
        persisted_claim_ids = existing_claim_ids | {claim.id for claim in accepted}
        conflicts = [item for item in state.conflicts if set(item.claim_ids) <= persisted_claim_ids]
        parent = await self.graph_store.latest_revision()
        entity_ids = {
            entity_id
            for claim in accepted
            for entity_id in (claim.subject_id, claim.object_entity_id)
            if entity_id
        }
        entities = [
            entity.model_copy(update={"active": True})
            for entity in state.entities
            if entity.id in entity_ids
        ]
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
            for entity in entities
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
            for claim in accepted
        )
        changes.extend(
            GraphChange(
                resource_type="conflict",
                resource_id=conflict.id,
                action="create",
                after=conflict.model_dump(mode="json"),
            )
            for conflict in conflicts
        )
        revision = GraphRevision(
            id=stable_id(
                "revision",
                state.run_id,
                parent.id if parent else "root",
                *sorted(claim.id for claim in accepted),
            ),
            run_id=state.run_id,
            parent_id=parent.id if parent else None,
            entity_ids=sorted(entity_ids),
            claim_ids=sorted(claim.id for claim in accepted),
            conflict_ids=sorted(conflict.id for conflict in conflicts),
            changes=changes,
        )
        state.revision = revision
        schema_id = canonical_hash(state.output_schema.model_dump(mode="json"))
        context = CommitValidationContext(
            schemas={schema_id: state.output_schema},
            claim_schema_ids={claim.id: schema_id for claim in accepted},
            document_asset_ids={state.document.id: [a.id for a in state.document.media_assets]},
        )
        revision.validation_context = context
        state.graph_commit = GraphCommit(
            documents=[
                GraphDocument(
                    id=state.document.id,
                    filename=(
                        state.document.source_filename or Path(state.document.source_path).name
                    ),
                    content_hash=state.document.source_hash,
                    media_type=state.document.media_type,
                )
            ],
            evidence=[
                evidence
                for evidence in state.document.evidence
                if evidence.id
                in {evidence_id for claim in accepted for evidence_id in claim.evidence_ids}
            ],
            entities=entities,
            claims=accepted,
            conflicts=conflicts,
            revision=revision,
            validation_context=context,
        )
        if state.pending_correction_id and self.review_repository is not None:
            from src.workflow.corrections import compensation_commit

            state.graph_commit = compensation_commit(
                state,
                state.graph_commit,
                self.review_repository.correction(state.pending_correction_id),
                existing_claims,
                existing_entities,
            )
            state.revision = state.graph_commit.revision
        await ValidationService().commit(
            state.graph_commit,
            {**existing_entities, **{e.id: e for e in entities}},
            {e.id: e for e in state.document.evidence},
            {state.document.id},
            self.evidence_store,
        )
        return state

    async def commit_graph(self, state: WorkflowState) -> WorkflowState:
        assert state.graph_commit is not None
        for claim in state.graph_commit.claims:
            for evidence_id in claim.evidence_ids:
                if not await self.evidence_store.verify(evidence_id):
                    raise EvidenceIntegrityError(
                        f"claim {claim.id} references invalid evidence {evidence_id}"
                    )
        control = current_execution.get()
        if control:
            control.commit_started(state.graph_commit.revision.id)
        await self.graph_store.commit(state.graph_commit)
        if control:
            control.commit_finished()
        if (
            self.embedding_provider.fingerprint() != "embedding:disabled"
            and state.graph_commit.entities
        ):
            active_entities = [item for item in state.graph_commit.entities if item.active]
            texts = [entity_embedding_text(item) for item in active_entities]
            vectors = await self.embedding_provider.encode(texts)
            await self.graph_store.upsert_entity_embeddings(
                [
                    EntityEmbedding(
                        entity_id=entity.id,
                        model_fingerprint=self.embedding_provider.fingerprint(),
                        text_hash=canonical_hash(text),
                        dimension=len(vector),
                        vector=vector,
                    )
                    for entity, text, vector in zip(active_entities, texts, vectors, strict=True)
                ]
            )
        state.status = "completed"
        return state
