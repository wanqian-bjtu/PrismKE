"""OpenAI-compatible multimodal extraction provider."""

from __future__ import annotations

import base64
import json
import math
from io import BytesIO
from typing import Any, cast

import httpx
from PIL import Image

from src.core.errors import ProviderResponseError
from src.core.ids import stable_id
from src.domain import (
    BBox,
    CandidateClaim,
    CoordinateSpace,
    EntityMention,
    EvidenceKind,
    EvidenceRef,
    ExtractionResult,
    LocalizationLevel,
    Modality,
    ProviderCallRecord,
    TaskMode,
    ValidationResult,
    VisualExtractionRequest,
    VisualObservation,
    normalize_label,
)
from src.governance.validation import ValidationService
from src.providers.common import candidate_from_payload, parse_json_object
from src.providers.http_client import post_chat_completion
from src.providers.validation import summarize, validate_item

PROMPT_VERSION = "visual-task-extraction-v5"
PROTOCOL_VERSION = "chat-completions-vision-v1"
PROVIDER_VERSION = "0.2.1"


def _visual_prompt(request: VisualExtractionRequest) -> str:
    ocr_text = [block.text for block in request.ocr_blocks]
    return (
        f"Task mode: {request.task_mode.value}. Extract knowledge that is directly supported "
        "by the supplied image. Return one JSON object containing arrays named "
        "'observations', 'entities' and 'claims'. For entity_extraction, claims must be empty.\n"
        "Evidence priority:\n"
        "1. PRIMARY evidence is the image pixels and IMAGE-DERIVED OCR below.\n"
        "2. AUXILIARY document context may help interpretation but may contradict the image. "
        "Never replace visible image content with auxiliary context.\n"
        "First transcribe or describe visible objects and text as observations. If the image "
        "contains body paragraphs, do not copy them or the full OCR transcript into observations. "
        "Use short labels and concise descriptions (at most 160 characters each), retaining "
        "only the visible details needed to support claims. "
        "If the image and auxiliary context disagree, output the fact visible in the image. "
        "Omit any visual claim that cannot be confirmed from image pixels or image-derived OCR.\n"
        "Confidence must be a JSON number between 0 and 1, never labels like high or low. "
        "Observation fields: label, description, confidence, optional "
        "bbox=[x0,y0,x1,y1] normalized to 0..1, attributes. Claim fields: subject, relation, "
        "object, subject_type, optional object_type, confidence, observation_index. A claim "
        "with region-level support must reference its supporting observation_index. Use source "
        "surface forms and obey the schema relation direction. Do not invent unsupported facts.\n"
        "Entity fields: name, type, confidence and optional observation_index.\n"
        "For every directly visible schema attribute, put the normalized value in the "
        "supporting observation's attributes object and use the exact schema attribute id "
        "as its key. Do not use display labels or invent non-schema attribute keys. If an "
        "image visibly shows a schema attribute, at least one observation must have a "
        "non-empty attributes object. Follow this shape: "
        '{"observations":[{"label":"...","description":"...","confidence":0.9,'
        '"bbox":[0.0,0.0,1.0,1.0],"attributes":{"schema_attribute_id":"value"}}],'
        '"entities":[{"name":"...","type":"...","confidence":0.9,'
        '"observation_index":0}],"claims":[]}.\n'
        f"Schema: {request.output_schema.model_dump_json()}\n"
        f"IMAGE-DERIVED OCR (PRIMARY): {json.dumps(ocr_text, ensure_ascii=False)}\n"
        f"AUXILIARY DOCUMENT CONTEXT (UNTRUSTED): {request.asset.context_text}"
    )


def _candidate_names(candidate: CandidateClaim) -> list[str]:
    names = [candidate.subject.name]
    obj = candidate.object.name if isinstance(candidate.object, EntityMention) else candidate.object
    names.append(obj)
    return [str(name) for name in names if str(name).strip()]


def _is_context_only_visual_claim(
    candidate: CandidateClaim,
    observation: VisualObservation | None,
    ocr_text: str,
    auxiliary_context: str,
) -> bool:
    primary_parts = [ocr_text]
    if observation is not None:
        primary_parts.extend(
            [
                observation.label,
                observation.description,
                json.dumps(observation.attributes, ensure_ascii=False),
            ]
        )
    primary = normalize_label(" ".join(primary_parts))
    auxiliary = normalize_label(auxiliary_context)
    for name in _candidate_names(candidate):
        normalized = normalize_label(name)
        if normalized and normalized in auxiliary and normalized not in primary:
            return True
    return False


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
        with Image.open(path) as source:
            image: Image.Image = source
            image.load()
            if image.mode not in {"RGB", "RGBA", "L", "LA", "P", "1"}:
                image = image.convert("RGB")
            if max(image.size) > self.max_image_edge:
                image.thumbnail((self.max_image_edge, self.max_image_edge))
            output = BytesIO()
            image.save(output, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(output.getvalue()).decode('ascii')}"

    async def _post(
        self, body: dict[str, Any], operation_id: str
    ) -> tuple[dict[str, Any], ProviderCallRecord]:
        return await post_chat_completion(
            base_url=self.base_url,
            api_key=self.api_key,
            body=body,
            timeout=self.timeout,
            provider="vlm",
            operation_id=operation_id,
            prompt_version=PROMPT_VERSION,
            provider_fingerprint=self.fingerprint(),
            transport=self.transport,
        )

    async def extract(self, request: VisualExtractionRequest) -> ExtractionResult:
        asset = request.asset
        prompt = _visual_prompt(request)
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
        response, first_record = await self._post(body, asset.id)
        records = [first_record]
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(
                "模型服务响应缺少 choices.message.content",
                call_records=records,
            ) from exc
        try:
            payload = parse_json_object(content)
        except (TypeError, json.JSONDecodeError):
            repair_body = dict(body)
            messages = cast(list[dict[str, Any]], body["messages"])
            repair_body["messages"] = [
                *messages,
                {"role": "assistant", "content": str(content)},
                {
                    "role": "user",
                    "content": "Return the same result as one valid JSON object only.",
                },
            ]
            repaired, repair_record = await self._post(repair_body, f"{asset.id}:repair")
            records.append(repair_record)
            try:
                payload = parse_json_object(repaired["choices"][0]["message"]["content"])
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                raise ProviderResponseError(
                    "模型服务在一次修复后仍未返回有效的结构化 JSON",
                    call_records=records,
                ) from exc
        issues = []
        if not isinstance(payload.get("claims"), list) or not isinstance(
            payload.get("observations", []), list
        ):
            raise ProviderResponseError(
                "视觉 JSON 必须包含 claims 数组及 observations 数组", call_records=records
            )
        observations: list[VisualObservation] = []
        observations_by_index: dict[int, VisualObservation] = {}
        evidence: list[EvidenceRef] = []
        warnings: list[str] = []
        uncalibrated_observations: set[int] = set()
        for index, item in enumerate(payload.get("observations", [])):
            if not isinstance(item, dict) or not isinstance(item.get("attributes", {}), dict):
                issues.append(
                    ValidationService.issue(
                        "INVALID_OBSERVATION_STRUCTURE",
                        "structure",
                        "observation",
                        stable_id("invalid-observation", asset.id, index),
                        f"observations[{index}]",
                        "视觉观察结构不合法，已隔离",
                    )
                )
                continue
            raw_bbox = item.get("bbox")
            bbox = None
            if raw_bbox is not None:
                try:
                    if not isinstance(raw_bbox, list) or len(raw_bbox) != 4:
                        raise ValueError("invalid bbox shape")
                    values = [float(v) for v in raw_bbox]
                    if not all(math.isfinite(v) and 0 <= v <= 1 for v in values):
                        raise ValueError("invalid bbox values")
                    bbox = BBox(x0=values[0], y0=values[1], x1=values[2], y1=values[3])
                except (TypeError, ValueError):
                    warnings.append(f"invalid_visual_bbox:asset={asset.id}:index={index}")
            try:
                confidence = float(item.get("confidence", 0.5))
                if not math.isfinite(confidence) or not 0 <= confidence <= 1:
                    raise ValueError("invalid confidence")
            except (TypeError, ValueError):
                confidence = 0.0
                uncalibrated_observations.add(index)
                warnings.append(f"invalid_visual_confidence:asset={asset.id}:index={index}")
            evidence_id = (
                asset.evidence_id
                if bbox is None
                else stable_id(
                    "ev", request.document.id, asset.id, "vlm", index, *cast(list[Any], raw_bbox)
                )
            )
            observation_id = stable_id(
                "observation",
                request.document.id,
                asset.id,
                index,
                item.get("label", ""),
                item.get("description", ""),
            )
            if raw_bbox is not None and bbox is None or index in uncalibrated_observations:
                issues.append(
                    ValidationService.issue(
                        "INVALID_OBSERVATION_STRUCTURE",
                        "structure",
                        "observation",
                        observation_id,
                        f"observations[{index}]",
                        "视觉观察的置信度或区域不合法，关联候选已隔离",
                        [asset.evidence_id],
                    )
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
                    confidence=confidence,
                    evidence_id=evidence_id,
                    attributes=dict(item.get("attributes", {})),
                )
            )
            observations_by_index[index] = observations[-1]
        candidates = []
        entities: list[EntityMention] = []
        ocr_context = "\n".join(block.text for block in request.ocr_blocks)
        grounding_context = ocr_context or asset.context_text
        for index, item in enumerate(payload.get("claims", [])):
            issue = validate_item(item, asset.id, index)
            if issue is not None:
                issues.append(issue)
                continue
            oi = item.get("observation_index")
            observation = (
                observations_by_index.get(oi)
                if isinstance(oi, int) and not isinstance(oi, bool)
                else None
            )
            try:
                candidate = candidate_from_payload(
                    item,
                    observation.evidence_id if observation else asset.evidence_id,
                    grounding_context,
                    modality=Modality.IMAGE,
                    source_tool="visual_extraction",
                    visual_observation_ids=[observation.id] if observation else [],
                    output_schema=request.output_schema,
                )
                if _is_context_only_visual_claim(
                    candidate, observation, ocr_context, asset.context_text
                ):
                    candidate.context_only_visual_claim = True
                    warnings.append(
                        f"context_only_visual_claim:asset={asset.id}:candidate={candidate.id}"
                    )
                candidates.append(candidate)
                if (
                    isinstance(oi, int)
                    and oi in uncalibrated_observations
                    or observation is None
                    and uncalibrated_observations
                ):
                    candidate.uncalibrated_visual_confidence = True
            except (KeyError, TypeError, ValueError):
                issues.append(
                    ValidationService.issue(
                        "INVALID_CANDIDATE_STRUCTURE",
                        "structure",
                        "candidate",
                        stable_id("invalid-candidate", asset.id, index),
                        f"claims[{index}]",
                        "视觉候选字段不合法，已隔离",
                        summary=summarize(item),
                    )
                )
        for index, item in enumerate(payload.get("entities", [])):
            if not isinstance(item, dict):
                warnings.append(f"visual_entity_invalid:asset={asset.id}:index={index}")
                continue
            oi = item.get("observation_index")
            observation = (
                observations_by_index.get(oi)
                if isinstance(oi, int) and not isinstance(oi, bool)
                else None
            )
            name = str(item.get("name", "")).strip()
            entity_type = str(item.get("type", item.get("entity_type", ""))).strip()
            if not name or not entity_type:
                warnings.append(f"visual_entity_invalid:asset={asset.id}:index={index}")
                continue
            evidence_id = observation.evidence_id if observation else asset.evidence_id
            entities.append(
                EntityMention(
                    id=stable_id("mention", request.document.id, evidence_id, name, entity_type),
                    name=name,
                    entity_type=entity_type,
                    context=grounding_context,
                    modality=Modality.IMAGE,
                    evidence_ids=[evidence_id],
                    confidence=float(item.get("confidence", 0.5)),
                )
            )
        if request.task_mode == TaskMode.ENTITY_EXTRACTION:
            candidates = []
        return ExtractionResult(
            candidates=candidates,
            entities=entities,
            observations=observations,
            evidence=evidence,
            warnings=warnings,
            call_records=records,
            validation=ValidationService.merge(ValidationResult(), issues),
        )
