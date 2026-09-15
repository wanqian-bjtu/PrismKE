"""Workflow node implementations."""

from __future__ import annotations

from pathlib import Path

from prismke.core.errors import EvidenceIntegrityError
from prismke.core.ids import stable_id
from prismke.domain import (
    ClaimStatus,
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
    EntityResolver,
    MultimodalAlignmentService,
    collect_mentions,
    detect_conflicts,
    normalize_claims,
    route_by_risk,
)
from prismke.parsing import ParserRegistry, select_analysis_assets
from prismke.persistence.base import EvidenceStore, GraphStore
from prismke.providers.base import LLMProvider, OCRProvider, VLMProvider


class WorkflowNodes:
    def __init__(
        self,
        provider: LLMProvider,
        ocr_provider: OCRProvider,
        vlm_provider: VLMProvider,
        graph_store: GraphStore,
        evidence_store: EvidenceStore,
        parsers: ParserRegistry,
    ) -> None:
        self.provider = provider
        self.ocr_provider = ocr_provider
        self.vlm_provider = vlm_provider
        self.graph_store = graph_store
        self.evidence_store = evidence_store
        self.parsers = parsers

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
        return state

    async def align_modalities(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        state.candidates, state.alignment_records = MultimodalAlignmentService().align(
            state.text_candidates, state.visual_candidates, SchemaIndex(state.output_schema)
        )
        return state

    async def resolve_entities(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        resolver = EntityResolver(
            SchemaIndex(state.output_schema), await self.graph_store.list_entities()
        )
        resolution = resolver.resolve(collect_mentions(state.candidates))
        state.entities = resolution.entities
        state.warnings.extend(
            f"review_required:{mention_id}:{','.join(reasons)}"
            for mention_id, reasons in resolution.review_reasons.items()
        )
        return state

    async def normalize_claims(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        resolver = EntityResolver(SchemaIndex(state.output_schema), state.entities)
        resolution = resolver.resolve(collect_mentions(state.candidates))
        entities = {item.id: item for item in resolution.entities}
        state.entities = list(entities.values())
        state.claims = normalize_claims(
            state.candidates,
            SchemaIndex(state.output_schema),
            entities,
            resolution.mention_to_entity,
        )
        return state

    async def detect_conflicts(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        state.conflicts = detect_conflicts(
            state.claims, await self.graph_store.list_claims(), SchemaIndex(state.output_schema)
        )
        return state

    async def route_by_risk(self, state: WorkflowState) -> WorkflowState:
        state.claims, new_reviews = route_by_risk(state.run_id, state.claims, state.conflicts)
        resolved = {item.claim_id: item for item in state.review_tasks if item.status == "resolved"}
        state.review_tasks = [resolved.get(item.claim_id, item) for item in new_reviews]
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
            else "running"
        )
        return state

    async def prepare_graph_commit(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None
        accepted = [
            claim
            for claim in state.claims
            if claim.status in {ClaimStatus.AUTO_APPROVED, ClaimStatus.APPROVED}
        ]
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
        state.graph_commit = GraphCommit(
            documents=[
                GraphDocument(
                    id=state.document.id,
                    filename=Path(state.document.source_path).name,
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
        state.status = "completed"
        return state
