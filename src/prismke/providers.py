"""Extraction providers with deterministic mock and OpenAI-compatible implementations."""

from __future__ import annotations

import json
from typing import Any

import httpx

from prismke.ids import stable_id
from prismke.models import (
    CandidateClaim,
    EntityMention,
    ExtractionRequest,
    ExtractionResult,
    Modality,
    VisualExtractionRequest,
)


def _candidate_from_payload(item: dict[str, Any], evidence_id: str, context: str) -> CandidateClaim:
    subject_name = str(item["subject"]).strip()
    object_name = str(item["object"]).strip()
    subject_type = str(item.get("subject_type", "Unknown")).strip()
    object_type = item.get("object_type")
    subject = EntityMention(
        id=stable_id("mention", subject_name, subject_type, evidence_id),
        name=subject_name,
        entity_type=subject_type,
        context=context,
        modality=Modality.TEXT,
        evidence_ids=[evidence_id],
    )
    if object_type:
        obj: EntityMention | str = EntityMention(
            id=stable_id("mention", object_name, object_type, evidence_id),
            name=object_name,
            entity_type=str(object_type),
            context=context,
            modality=Modality.TEXT,
            evidence_ids=[evidence_id],
        )
    else:
        obj = object_name
    relation = str(item["relation"]).strip()
    return CandidateClaim(
        id=stable_id("candidate", subject.id, relation, object_name, evidence_id),
        subject=subject,
        relation=relation,
        object=obj,
        confidence=float(item.get("confidence", 0.5)),
        evidence_ids=[evidence_id],
        qualifiers=dict(item.get("qualifiers", {})),
    )


class MockLLMProvider:
    """Parse pipe-delimited facts embedded in documents for repeatable tests."""

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        candidates: list[CandidateClaim] = []
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
                candidates.append(
                    _candidate_from_payload(payload, block.evidence_id, block.text)
                )
            except (ValueError, KeyError) as exc:
                warnings.append(f"mock_parse_failed:block={block.id}:{exc}")
        if request.document.media_assets:
            warnings.append("mock_vlm_returned_no_visual_claims")
        return ExtractionResult(candidates=candidates, warnings=warnings)


class MockVLMProvider:
    async def extract(self, request: VisualExtractionRequest) -> ExtractionResult:
        del request
        return ExtractionResult(warnings=["mock_vlm_returned_no_visual_claims"])


class OpenAICompatibleLLMProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.transport = transport

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        blocks = [
            {"evidence_id": block.evidence_id, "text": block.text}
            for block in request.document.text_blocks
        ]
        prompt = (
            "Extract factual claims from the supplied blocks under the supplied schema. "
            "Return a JSON object with key 'claims'. Each claim must contain subject, "
            "relation, object, subject_type, optional object_type, confidence, and "
            "evidence_id. Never invent an evidence_id.\n"
            f"Schema: {request.schema.model_dump_json()}\n"
            f"Blocks: {json.dumps(blocks, ensure_ascii=False)}"
        )
        headers = {"Authorization": f"Bearer {self.api_key}"}
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(
            timeout=self.timeout, transport=self.transport
        ) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=body
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)
        evidence = {item.id: item for item in request.document.evidence}
        blocks_by_evidence = {item.evidence_id: item for item in request.document.text_blocks}
        candidates: list[CandidateClaim] = []
        warnings: list[str] = []
        for item in payload.get("claims", []):
            evidence_id = str(item.get("evidence_id", ""))
            if evidence_id not in evidence:
                warnings.append("provider_returned_unknown_evidence_id")
                continue
            context = blocks_by_evidence.get(evidence_id)
            candidates.append(
                _candidate_from_payload(
                    item, evidence_id, context.text if context is not None else ""
                )
            )
        return ExtractionResult(candidates=candidates, warnings=warnings)
