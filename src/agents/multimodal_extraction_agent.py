"""MultimodalExtractionAgent with explicit tool choice and evidence handoff."""

from __future__ import annotations

import re
from time import perf_counter

from src.agents.trace import handoff, trace_step
from src.core.errors import ProviderResponseError
from src.core.execution_control import cached_operation, check_execution
from src.core.ids import stable_id
from src.domain import (
    EntityMention,
    EntitySourceMode,
    ExtractionRequest,
    ExtractionResult,
    LocalizationLevel,
    OCRRequest,
    OCRResult,
    SchemaIndex,
    TaskMode,
    VisualExtractionRequest,
    WorkflowState,
)
from src.governance import MultimodalAlignmentService
from src.parsing import select_analysis_assets
from src.persistence.base import EvidenceStore
from src.providers.base import LLMProvider, OCRProvider, VLMProvider


def _known_response_failure(
    state: WorkflowState, exc: ProviderResponseError, modality: str
) -> None:
    records = getattr(exc, "call_records", [])
    known = {item.id for item in state.provider_calls}
    state.provider_calls.extend(item for item in records if item.id not in known)
    state.modality_status[modality] = "failed"
    state.modality_errors[modality] = "provider_response_invalid"
    state.warnings.append(f"{modality}_extraction_failed:provider_response_invalid")


class MultimodalExtractionAgent:
    def __init__(
        self,
        provider: LLMProvider,
        ocr_provider: OCRProvider,
        vlm_provider: VLMProvider,
        evidence_store: EvidenceStore,
    ) -> None:
        self.provider = provider
        self.ocr_provider = ocr_provider
        self.vlm_provider = vlm_provider
        self.evidence_store = evidence_store

    @staticmethod
    def _ground_provided_entities(state: WorkflowState) -> list[EntityMention]:
        """Resolve user-provided entities to document evidence before model use."""
        assert state.document is not None
        grounded: list[EntityMention] = []
        for provided in state.provided_entities:
            matches: list[tuple[str, int, int, str]] = []
            for block in state.document.text_blocks:
                if provided.char_start is not None and provided.char_end is not None:
                    if block.char_start is None:
                        continue
                    local_start = provided.char_start - block.char_start
                    local_end = provided.char_end - block.char_start
                    if (
                        0 <= local_start < local_end <= len(block.text)
                        and block.text[local_start:local_end].casefold() == provided.name.casefold()
                    ):
                        matches.append(
                            (block.evidence_id, provided.char_start, provided.char_end, block.text)
                        )
                    continue
                for match in re.finditer(re.escape(provided.name), block.text, re.IGNORECASE):
                    base = block.char_start or 0
                    matches.append(
                        (
                            block.evidence_id,
                            base + match.start(),
                            base + match.end(),
                            block.text,
                        )
                    )
            if not matches:
                code = (
                    "PROVIDED_ENTITY_SPAN_INVALID"
                    if provided.char_start is not None
                    else "PROVIDED_ENTITY_NOT_FOUND"
                )
                raise ValueError(f"{code}:{provided.name}")
            evidence_ids = list(dict.fromkeys(item[0] for item in matches))
            mention_id = stable_id(
                "provided-entity",
                state.document.id,
                provided.name,
                provided.entity_type,
                *(f"{item[0]}:{item[1]}:{item[2]}" for item in matches),
            )
            is_ambiguous = len(matches) > 1
            if is_ambiguous:
                state.extraction_review_required_ids.append(mention_id)
                state.warnings.append(f"provided_entity_ambiguous:{mention_id}:{len(matches)}")
            grounded.append(
                EntityMention(
                    id=mention_id,
                    name=provided.name,
                    entity_type=provided.entity_type,
                    context=" | ".join(dict.fromkeys(item[3] for item in matches))[:1000],
                    evidence_ids=evidence_ids,
                    confidence=None if is_ambiguous else 1.0,
                    char_start=matches[0][1] if len(matches) == 1 else None,
                    char_end=matches[0][2] if len(matches) == 1 else None,
                )
            )
        return grounded

    async def recognize(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None
        started = perf_counter()
        if self.ocr_provider.fingerprint() == "disabled":
            state.modality_status["ocr"] = "skipped"
            trace_step(state, "extraction", "ocr", "disabled", status="skipped")
            return state
        request = OCRRequest(document=state.document)
        try:
            result = await cached_operation(
                stable_id("ocr-result", self.ocr_provider.fingerprint(), state.document.id),
                OCRResult,
                lambda: self.ocr_provider.recognize(request),
            )
        except ProviderResponseError as exc:
            _known_response_failure(state, exc, "ocr")
            trace_step(
                state,
                "extraction",
                "ocr",
                "invalid_provider_response",
                tools=("ocr",),
                input_ids=(state.document.id,),
                status="failed",
            )
            return state
        existing = {block.id for block in state.document.text_blocks}
        state.document.text_blocks.extend(
            block for block in result.text_blocks if block.id not in existing
        )
        known_evidence = {item.id for item in state.document.evidence}
        state.document.evidence.extend(
            item for item in result.evidence if item.id not in known_evidence
        )
        state.warnings.extend(result.warnings)
        state.modality_status["ocr"] = "succeeded"
        trace_step(
            state,
            "extraction",
            "ocr",
            "recognized",
            tools=("ocr",),
            input_ids=(state.document.id,),
            output_ids=tuple(block.id for block in result.text_blocks),
            model_fingerprint=self.ocr_provider.fingerprint(),
            latency_ms=(perf_counter() - started) * 1000,
        )
        return state

    async def extract_text(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None and state.output_schema is not None
        started = perf_counter()
        if not state.document.text_blocks:
            state.text_candidates = []
            state.modality_status["text"] = "skipped"
            state.warnings.append("text_extraction_skipped:no_text_blocks")
            trace_step(state, "extraction", "text", "no_text_blocks", status="skipped")
            return state
        provided_mentions: list[EntityMention] = []
        if (
            state.task_mode == TaskMode.RELATION_EXTRACTION
            and state.entity_source_mode == EntitySourceMode.PROVIDED
        ):
            provided_mentions = self._ground_provided_entities(state)
        request = ExtractionRequest(
            document=state.document,
            output_schema=state.output_schema,
            task_mode=state.task_mode,
            entity_source_mode=state.entity_source_mode,
            provided_entities=state.provided_entities,
        )
        try:
            result = await cached_operation(
                stable_id(
                    "text-result",
                    self.provider.fingerprint(),
                    state.document.id,
                    state.task_mode,
                    state.entity_source_mode,
                    *(item.model_dump_json() for item in state.provided_entities),
                ),
                ExtractionResult,
                lambda: self.provider.extract(request),
            )
        except ProviderResponseError as exc:
            _known_response_failure(state, exc, "text")
            trace_step(
                state,
                "extraction",
                "text",
                "invalid_provider_response",
                tools=("text_llm",),
                input_ids=(state.document.id,),
                status="failed",
            )
            return state
        if (
            state.task_mode == TaskMode.RELATION_EXTRACTION
            and state.entity_source_mode == EntitySourceMode.PROVIDED
        ):
            allowed = {
                (item.name.casefold(), item.entity_type.casefold())
                for item in state.provided_entities
            }

            def permitted(candidate: object) -> bool:
                if not hasattr(candidate, "subject") or not hasattr(candidate, "object"):
                    return False
                subject = candidate.subject
                obj = candidate.object
                if (subject.name.casefold(), subject.entity_type.casefold()) not in allowed:
                    return False
                return (
                    not isinstance(obj, EntityMention)
                    or (obj.name.casefold(), obj.entity_type.casefold()) in allowed
                )

            result.candidates = [item for item in result.candidates if permitted(item)]
        if state.task_mode == TaskMode.ENTITY_EXTRACTION:
            result.candidates = []
        state.text_candidates = result.candidates
        provided_keys = {
            (item.name.casefold(), item.entity_type.casefold()) for item in provided_mentions
        }
        state.extracted_entities = [
            *provided_mentions,
            *[
                item
                for item in result.entities
                if (item.name.casefold(), item.entity_type.casefold()) not in provided_keys
            ],
        ]
        state.candidate_attributes = result.attributes
        state.candidate_events = result.events
        state.warnings.extend(result.warnings)
        state.provider_calls.extend(result.call_records)
        from src.governance.validation import ValidationService

        state.validation = ValidationService.merge(state.validation, result.validation.issues)
        state.modality_status["text"] = "succeeded"
        trace_step(
            state,
            "extraction",
            "text",
            "candidates_extracted",
            tools=("text_llm",),
            input_ids=(state.document.id,),
            output_ids=tuple(item.id for item in result.candidates),
            model_fingerprint=self.provider.fingerprint(),
            token_usage=sum(item.total_tokens or 0 for item in result.call_records),
            latency_ms=(perf_counter() - started) * 1000,
        )
        return state

    async def extract_visual(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None and state.output_schema is not None
        started = perf_counter()
        state.visual_candidates = []
        assets = select_analysis_assets(state.document)
        if not assets or self.vlm_provider.fingerprint() == "disabled":
            state.modality_status["visual"] = "skipped"
            trace_step(state, "extraction", "visual", "no_visual_tool", status="skipped")
            return state
        failed_assets: list[str] = []
        call_records = []
        for asset in assets:
            check_execution()
            ocr_blocks = [
                block
                for block in state.document.text_blocks
                if block.source_media_asset_id == asset.id
            ]
            request = VisualExtractionRequest(
                document=state.document,
                output_schema=state.output_schema,
                asset=asset,
                ocr_blocks=ocr_blocks,
                task_mode=state.task_mode,
                entity_source_mode=state.entity_source_mode,
                provided_entities=state.provided_entities,
            )

            async def visual_call(req: VisualExtractionRequest = request) -> ExtractionResult:
                return await self.vlm_provider.extract(req)

            try:
                result = await cached_operation(
                    stable_id(
                        "visual-result",
                        self.vlm_provider.fingerprint(),
                        asset.id,
                        state.task_mode,
                        state.entity_source_mode,
                    ),
                    ExtractionResult,
                    visual_call,
                )
            except ProviderResponseError as exc:
                _known_response_failure(state, exc, "visual")
                failed_assets.append(asset.id)
                continue
            evidence_by_id = {
                item.id: item for item in [*state.document.evidence, *result.evidence]
            }
            for candidate in result.candidates:
                if any(
                    evidence_by_id[item].localization_level == LocalizationLevel.ASSET
                    for item in candidate.evidence_ids
                    if item in evidence_by_id
                ):
                    candidate.coarse_visual_evidence = True
            state.visual_candidates.extend(result.candidates)
            known_mentions = {item.id for item in state.extracted_entities}
            state.extracted_entities.extend(
                item for item in result.entities if item.id not in known_mentions
            )
            state.candidate_attributes.extend(result.attributes)
            state.candidate_events.extend(result.events)
            state.document.visual_observations.extend(result.observations)
            for evidence in result.evidence:
                await self.evidence_store.put_ref(evidence)
                state.document.evidence.append(evidence)
            state.warnings.extend(result.warnings)
            state.provider_calls.extend(result.call_records)
            call_records.extend(result.call_records)
            from src.governance.validation import ValidationService

            state.validation = ValidationService.merge(state.validation, result.validation.issues)
        if failed_assets:
            state.modality_status["visual"] = "failed"
            state.modality_errors["visual"] = f"invalid_response_assets:{len(failed_assets)}"
        else:
            state.modality_status["visual"] = "succeeded"
        trace_step(
            state,
            "extraction",
            "visual",
            "partial_failure" if failed_assets else "candidates_extracted",
            tools=("vision_vlm",),
            input_ids=tuple(asset.id for asset in assets),
            output_ids=tuple(item.id for item in state.visual_candidates),
            reasons=("invalid_provider_response",) if failed_assets else (),
            model_fingerprint=self.vlm_provider.fingerprint(),
            token_usage=sum(item.total_tokens or 0 for item in call_records),
            latency_ms=(perf_counter() - started) * 1000,
            status="failed" if failed_assets else "succeeded",
        )
        return state

    async def align(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        statuses = [state.modality_status.get(name) for name in ("ocr", "text", "visual")]
        if "failed" in statuses and "succeeded" not in statuses:
            raise ProviderResponseError("all available extraction modalities failed")
        state.candidates, state.alignment_records = MultimodalAlignmentService().align(
            state.text_candidates, state.visual_candidates, SchemaIndex(state.output_schema)
        )
        trace_step(
            state,
            "extraction",
            "align_modalities",
            "candidates_handed_off",
            tools=("modality_alignment",),
            input_ids=tuple(item.id for item in [*state.text_candidates, *state.visual_candidates]),
            output_ids=tuple(item.id for item in state.candidates),
        )
        handoff(
            state,
            "extraction",
            input_ids=(state.document.id,) if state.document else (),
            output_ids=tuple(item.id for item in state.candidates),
            evidence_ids=tuple(
                sorted({eid for item in state.candidates for eid in item.evidence_ids})
            ),
            issue_ids=tuple(issue.id for issue in state.validation.issues),
        )
        return state
