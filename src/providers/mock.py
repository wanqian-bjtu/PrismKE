"""Deterministic providers for tests and offline demonstrations."""

from src.core.ids import stable_id
from src.domain import (
    EntityMention,
    ExtractionRequest,
    ExtractionResult,
    TaskMode,
    VisualExtractionRequest,
)
from src.providers.common import candidate_from_payload


class MockLLMProvider:
    """Parse pipe-delimited facts embedded in documents."""

    def fingerprint(self) -> str:
        return stable_id("provider", "mock", "v1")

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        candidates = []
        warnings: list[str] = []
        for block in request.document.text_blocks:
            parts = [part.strip() for part in block.text.split("|")]
            if len(parts) != 6:
                continue
            subject, relation, obj, subject_type, object_type, confidence = parts
            try:
                payload = {
                    "subject": subject,
                    "relation": relation,
                    "object": obj,
                    "subject_type": subject_type,
                    "object_type": object_type or None,
                    "confidence": float(confidence),
                }
                candidates.append(candidate_from_payload(payload, block.evidence_id, block.text))
            except (ValueError, KeyError) as exc:
                warnings.append(f"mock_parse_failed:block={block.id}:{exc}")
        entities: list[EntityMention] = []
        known: set[str] = set()
        for candidate in candidates:
            for mention in (candidate.subject, candidate.object):
                if isinstance(mention, EntityMention) and mention.id not in known:
                    entities.append(mention)
                    known.add(mention.id)
        if request.task_mode == TaskMode.ENTITY_EXTRACTION:
            candidates = []
        return ExtractionResult(candidates=candidates, entities=entities, warnings=warnings)


class MockVLMProvider:
    def fingerprint(self) -> str:
        return stable_id("provider", "mock-vlm", "v1")

    async def extract(self, request: VisualExtractionRequest) -> ExtractionResult:
        del request
        return ExtractionResult(warnings=["mock_vlm_returned_no_visual_claims"])
