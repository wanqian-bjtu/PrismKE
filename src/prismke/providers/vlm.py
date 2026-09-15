"""OpenAI-compatible multimodal extraction provider."""

from __future__ import annotations

import asyncio
import base64
import json
from io import BytesIO
from typing import Any

import httpx
from PIL import Image

from prismke.core.ids import stable_id
from prismke.domain import (
    BBox,
    CoordinateSpace,
    EvidenceKind,
    EvidenceRef,
    ExtractionResult,
    LocalizationLevel,
    Modality,
    VisualExtractionRequest,
    VisualObservation,
)
from prismke.providers.common import candidate_from_payload

PROMPT_VERSION = "visual-schema-claims-v1"
PROTOCOL_VERSION = "chat-completions-vision-v1"
PROVIDER_VERSION = "0.2.0"


class DisabledVLMProvider:
    def fingerprint(self) -> str:
        return "disabled"

    async def extract(self, request: VisualExtractionRequest) -> ExtractionResult:
        del request
        return ExtractionResult()


class OpenAICompatibleVLMProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 120.0,
        max_image_edge: int = 2048,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_image_edge = max_image_edge
        self.transport = transport

    def fingerprint(self) -> str:
        return stable_id(
            "provider",
            "openai-compatible-vlm",
            self.base_url.casefold(),
            self.model,
            PROMPT_VERSION,
            PROTOCOL_VERSION,
            PROVIDER_VERSION,
        )

    def _image_data_url(self, path: str) -> str:
        with Image.open(path) as image:
            image.load()
            if max(image.size) > self.max_image_edge:
                image.thumbnail((self.max_image_edge, self.max_image_edge))
            output = BytesIO()
            image.save(output, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(output.getvalue()).decode('ascii')}"

    async def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        delay = 0.5
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout, transport=self.transport
                ) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=body
                    )
                response.raise_for_status()
                return dict(response.json())
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError):
                if attempt == 2:
                    raise
                await asyncio.sleep(delay)
                delay *= 2
        raise RuntimeError("unreachable")

    async def extract(self, request: VisualExtractionRequest) -> ExtractionResult:
        asset = request.asset
        prompt = (
            "Analyze this image under the supplied knowledge schema. Return JSON arrays "
            "'observations' and 'claims'. Observation fields: label, description, confidence, "
            "optional bbox=[x0,y0,x1,y1] normalized to 0..1, attributes. Claim fields: "
            "subject, relation, object, subject_type, optional object_type, confidence, "
            "optional observation_index. Do not invent unsupported facts.\n"
            f"Schema: {request.output_schema.model_dump_json()}\nContext: {asset.context_text}\n"
            f"OCR: {[block.text for block in request.ocr_blocks]}"
        )
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": self._image_data_url(asset.path)},
                        },
                    ],
                }
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        response = await self._post(body)
        payload = json.loads(response["choices"][0]["message"]["content"])
        observations: list[VisualObservation] = []
        evidence: list[EvidenceRef] = []
        warnings: list[str] = []
        for index, item in enumerate(payload.get("observations", [])):
            raw_bbox = item.get("bbox")
            bbox = None
            if (
                raw_bbox is not None
                and len(raw_bbox) == 4
                and all(0 <= float(v) <= 1 for v in raw_bbox)
            ):
                bbox = BBox(
                    x0=float(raw_bbox[0]),
                    y0=float(raw_bbox[1]),
                    x1=float(raw_bbox[2]),
                    y1=float(raw_bbox[3]),
                )
            elif raw_bbox is not None:
                warnings.append(f"invalid_visual_bbox:asset={asset.id}:index={index}")
            evidence_id = (
                asset.evidence_id
                if bbox is None
                else stable_id("ev", request.document.id, asset.id, "vlm", index, *raw_bbox)
            )
            observation_id = stable_id(
                "observation",
                request.document.id,
                asset.id,
                index,
                item.get("label", ""),
                item.get("description", ""),
            )
            if bbox is not None:
                evidence.append(
                    EvidenceRef(
                        id=evidence_id,
                        kind=EvidenceKind.VISUAL_REGION,
                        document_id=request.document.id,
                        source_hash=asset.blob_hash or request.document.source_hash,
                        modality=Modality.IMAGE,
                        page_number=asset.page_number,
                        bbox=bbox,
                        media_asset_id=asset.id,
                        model_name=self.model,
                        prompt_version=PROMPT_VERSION,
                        coordinate_space=CoordinateSpace.NORMALIZED,
                        canvas_width=asset.width,
                        canvas_height=asset.height,
                        localization_level=LocalizationLevel.REGION,
                    )
                )
            observations.append(
                VisualObservation(
                    id=observation_id,
                    media_asset_id=asset.id,
                    label=str(item.get("label", "object")),
                    description=str(item.get("description", "")),
                    bbox=bbox,
                    confidence=float(item.get("confidence", 0.5)),
                    evidence_id=evidence_id,
                    attributes=dict(item.get("attributes", {})),
                )
            )
        candidates = []
        for item in payload.get("claims", []):
            oi = item.get("observation_index")
            observation = (
                observations[oi] if isinstance(oi, int) and 0 <= oi < len(observations) else None
            )
            try:
                candidates.append(
                    candidate_from_payload(
                        item,
                        observation.evidence_id if observation else asset.evidence_id,
                        asset.context_text,
                        modality=Modality.IMAGE,
                        source_tool="visual_extraction",
                        visual_observation_ids=[observation.id] if observation else [],
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                warnings.append(f"visual_claim_invalid:asset={asset.id}:{exc}")
        return ExtractionResult(
            candidates=candidates, observations=observations, evidence=evidence, warnings=warnings
        )
