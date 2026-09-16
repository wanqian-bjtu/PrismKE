"""Workflow node implementations."""

from __future__ import annotations

from pathlib import Path

from prismke.core.errors import EvidenceIntegrityError, GraphIntegrityError
from prismke.core.ids import canonical_hash, stable_id
from prismke.domain import (
    ClaimStatus,
    CommitValidationContext,
    EntityEmbedding,
    ExtractionRequest,
    GraphChange,
    GraphCommit,
    GraphDocument,
    GraphRevision,
    LocalizationLevel,
    OCRRequest,
    SchemaIndex,
    SourceDocument,
    VisualExtractionRequest,
    WorkflowState,
    load_schema,
)
from prismke.governance import (
    MultimodalAlignmentService,
    SemanticEntityResolver,
    collect_mentions,
    detect_conflicts,
    entity_embedding_text,
    normalize_claims,
    route_by_risk,
)
from prismke.governance.validation import ValidationService
from prismke.parsing import ParserRegistry, select_analysis_assets
from prismke.persistence.base import EvidenceStore, GraphStore
from prismke.persistence.reviews import ReviewRepository
from prismke.providers.base import EmbeddingProvider, LLMProvider, OCRProvider, VLMProvider
from prismke.providers.embedding import DisabledEmbeddingProvider


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
        assert state.document is not None
        result = await self.ocr_provider.recognize(OCRRequest(document=state.document))
        existing = {block.id for block in state.document.text_blocks}
        state.document.text_blocks.extend(
            block for block in result.text_blocks if block.id not in existing
        )
        known_evidence = {item.id for item in state.document.evidence}
        state.document.evidence.extend(
            item for item in result.evidence if item.id not in known_evidence
        )
        state.warnings.extend(result.warnings)
        return state

    async def persist_evidence(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None
        await self.evidence_store.put_document(state.document)
        return state

    async def load_schema(self, state: WorkflowState) -> WorkflowState:
        state.output_schema = load_schema(SourceDocument(path=state.schema_path).path)
        return state

    async def extract_text_claims(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None and state.output_schema is not None
        if not state.document.text_blocks:
            state.text_candidates = []
            state.warnings.append("text_extraction_skipped:no_text_blocks")
            return state
        result = await self.provider.extract(
            ExtractionRequest(document=state.document, output_schema=state.output_schema)
        )
        state.text_candidates = result.candidates
        state.warnings.extend(result.warnings)
        state.provider_calls.extend(result.call_records)
        state.validation = ValidationService.merge(state.validation, result.validation.issues)
        return state

    async def extract_visual_claims(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None and state.output_schema is not None
        state.visual_candidates = []
        for asset in select_analysis_assets(state.document):
            ocr_blocks = [
                block
                for block in state.document.text_blocks
                if block.source_media_asset_id == asset.id
            ]
            result = await self.vlm_provider.extract(
                VisualExtractionRequest(
                    document=state.document,
                    output_schema=state.output_schema,
                    asset=asset,
                    ocr_blocks=ocr_blocks,
                )
            )
            for candidate in result.candidates:
                evidence_by_id = {
                    item.id: item for item in [*state.document.evidence, *result.evidence]
                }
                if any(
                    evidence_by_id[item].localization_level == LocalizationLevel.ASSET
                    for item in candidate.evidence_ids
                    if item in evidence_by_id
                ):
                    candidate.coarse_visual_evidence = True
            state.visual_candidates.extend(result.candidates)
            state.document.visual_observations.extend(result.observations)
            for evidence in result.evidence:
                await self.evidence_store.put_ref(evidence)
                state.document.evidence.append(evidence)
            state.warnings.extend(result.warnings)
            state.provider_calls.extend(result.call_records)
            state.validation = ValidationService.merge(state.validation, result.validation.issues)
        return state

    async def align_modalities(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        state.candidates, state.alignment_records = MultimodalAlignmentService().align(
            state.text_candidates, state.visual_candidates, SchemaIndex(state.output_schema)
        )
        return state

    async def resolve_entities(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        assert state.document is not None
        issues = await ValidationService().candidates(
            state.candidates, SchemaIndex(state.output_schema), state.document, self.evidence_store
        )
        state.validation = ValidationService.merge(state.validation, issues)
        excluded = ValidationService.blocked_candidate_ids(state.candidates, state.validation)
        resolver = SemanticEntityResolver(
            SchemaIndex(state.output_schema),
            self.graph_store,
            self.embedding_provider,
            run_id=state.run_id,
            top_k=self.entity_top_k,
            auto_link_threshold=self.entity_auto_link_threshold,
            review_threshold=self.entity_review_threshold,
            min_margin=self.entity_min_margin,
        )
        resolution = await resolver.resolve(
            collect_mentions([c for c in state.candidates if c.id not in excluded])
        )
        state.entities = resolution.entities
        state.mention_to_entity = resolution.mention_to_entity
        state.entity_resolution_decisions = resolution.decisions or []
        resolved = {
            item.mention_id: item
            for item in state.entity_review_tasks
            if item.status == "resolved" and item.mention_id is not None
        }
        state.entity_review_tasks = [
            resolved.get(item.mention_id, item) if item.mention_id is not None else item
            for item in (resolution.review_tasks or [])
        ]
        state.warnings.extend(
            f"review_required:{mention_id}:{','.join(reasons)}"
            for mention_id, reasons in resolution.review_reasons.items()
        )
        state.status = (
            "awaiting_review"
            if any(item.status == "pending" for item in state.entity_review_tasks)
            or state.validation.blocking_count
            else "running"
        )
        return state

    async def normalize_claims(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        assert state.document is not None
        entities = {item.id: item for item in state.entities}
        blocked = ValidationService.blocked_candidate_ids(state.candidates, state.validation)
        eligible = [c for c in state.candidates if c.id not in blocked]
        issues = await ValidationService().candidates(
            eligible,
            SchemaIndex(state.output_schema),
            state.document,
            self.evidence_store,
            entities,
            state.mention_to_entity,
        )
        state.validation = ValidationService.merge(
            state.validation,
            issues,
            canonical_hash([c.model_dump(mode="json") for c in state.candidates]),
        )
        blocked.update(i.target_id for i in issues)
        state.claims = normalize_claims(
            [c for c in eligible if c.id not in blocked],
            SchemaIndex(state.output_schema),
            entities,
            state.mention_to_entity,
        )
        state.validation.passed_count = len(state.claims)
        return state

    async def detect_conflicts(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        state.conflicts = detect_conflicts(
            state.claims, await self.graph_store.list_claims(), SchemaIndex(state.output_schema)
        )
        return state

    async def route_by_risk(self, state: WorkflowState) -> WorkflowState:
        state.claims, new_reviews = route_by_risk(state.run_id, state.claims, state.conflicts)
        if state.pending_correction_id and self.review_repository is not None:
            proposal = self.review_repository.correction(state.pending_correction_id)
            if proposal.kind == "entity":
                affected = set(proposal.preview["candidate_ids"])
                from prismke.domain import ReviewTask

                for claim in state.claims:
                    if (
                        set(claim.source_candidate_ids) & affected
                        and claim.status != ClaimStatus.REJECTED
                    ):
                        claim.status = ClaimStatus.REVIEW_REQUIRED
                        if claim.id not in {t.claim_id for t in new_reviews}:
                            new_reviews.append(
                                ReviewTask(
                                    id=stable_id("review", state.run_id, claim.id),
                                    run_id=state.run_id,
                                    claim_id=claim.id,
                                    reasons=["identity_correction_requires_review"],
                                )
                            )
        resolved = {item.claim_id: item for item in state.review_tasks if item.status == "resolved"}
        state.review_tasks = [resolved.get(item.claim_id, item) for item in new_reviews]
        repository = getattr(self, "review_repository", None)
        if repository is not None:
            for task in state.review_tasks:
                task.version = repository.version(state.run_id, task.id)
        for task in state.review_tasks:
            if task.status != "resolved":
                continue
            claim = next(item for item in state.claims if item.id == task.claim_id)
            claim.status = (
                ClaimStatus.APPROVED
                if task.decision and task.decision.value == "approve"
                else ClaimStatus.REJECTED
            )
        state.status = (
            "awaiting_review"
            if any(item.status == "pending" for item in state.review_tasks)
            or state.validation.blocking_count
            else "running"
        )
        return state

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
            from prismke.workflow.corrections import compensation_commit

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
        await self.graph_store.commit(state.graph_commit)
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
