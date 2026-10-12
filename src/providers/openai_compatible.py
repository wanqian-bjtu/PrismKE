"""OpenAI-compatible text extraction provider."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx

from src.core.errors import ProviderResponseError
from src.core.ids import stable_id
from src.domain import (
    CandidateAttribute,
    CandidateEvent,
    CandidateEventArgument,
    EntityMention,
    ExtractionRequest,
    ExtractionResult,
    Modality,
    ProviderCallRecord,
    TaskMode,
    ValidationResult,
)
from src.governance.validation import ValidationService
from src.providers.common import candidate_from_payload, parse_json_object
from src.providers.http_client import post_chat_completion
from src.providers.validation import summarize, validate_item

PROMPT_VERSION = "task-extraction-v2"
PROTOCOL_VERSION = "chat-completions-v1"
PROVIDER_VERSION = "0.2.0"


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

    def fingerprint(self) -> str:
        return stable_id(
            "provider",
            "openai-compatible",
            self.base_url.casefold(),
            self.model,
            PROMPT_VERSION,
            PROTOCOL_VERSION,
            PROVIDER_VERSION,
        )

    async def _post(
        self, body: dict[str, Any], operation_id: str
    ) -> tuple[dict[str, Any], ProviderCallRecord]:
        return await post_chat_completion(
            base_url=self.base_url,
            api_key=self.api_key,
            body=body,
            timeout=self.timeout,
            provider="llm",
            operation_id=operation_id,
            prompt_version=PROMPT_VERSION,
            provider_fingerprint=self.fingerprint(),
            transport=self.transport,
        )

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        blocks = [
            {"evidence_id": block.evidence_id, "text": block.text}
            for block in request.document.text_blocks
        ]
        mode_instruction = {
            TaskMode.ENTITY_EXTRACTION: (
                "Extract entity mentions only. Return an 'entities' array and an empty "
                "'claims' array."
            ),
            TaskMode.RELATION_EXTRACTION: (
                "Extract relation candidates only and return them in 'claims'. Use only the "
                "provided entities when entity_source_mode is 'provided'."
            ),
            TaskMode.SCHEMA_INFORMATION_EXTRACTION: (
                "Extract entities, relation claims, attributes and events. Return arrays named "
                "'entities', 'claims', 'attributes' and 'events'."
            ),
            TaskMode.JOINT_ENTITY_RELATION_EXTRACTION: (
                "Jointly extract entity mentions and relation claims."
            ),
            TaskMode.JOINT_ENTITY_RELATION_DISAMBIGUATION: (
                "Jointly extract entity mentions and relation claims for later disambiguation."
            ),
            TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION: (
                "Extract factual relation claims for the full knowledge graph workflow."
            ),
        }[request.task_mode]
        provided_payload = json.dumps(
            [item.model_dump(mode="json") for item in request.provided_entities],
            ensure_ascii=False,
        )
        prompt = (
            f"Task mode: {request.task_mode.value}. {mode_instruction} "
            "Return a JSON object. Every entity must contain name, type, confidence and "
            "evidence_id. Each claim must contain subject, "
            "relation, object, subject_type, optional object_type, confidence, and "
            "evidence_id. Subject and object must be exact surface forms from the source "
            "block; never return entity catalog IDs, values beginning with 'entity:', "
            "translations, or canonical names absent from the source. Choose relation "
            "direction so the subject type satisfies domain and the object type satisfies "
            "range; use the inverse relation ID when the sentence has the inverse direction. "
            "Never invent an evidence_id.\n"
            f"Entity source mode: {request.entity_source_mode.value}.\n"
            f"Provided entities: {provided_payload}\n"
            f"Schema: {request.output_schema.model_dump_json()}\n"
            f"Blocks: {json.dumps(blocks, ensure_ascii=False)}"
        )
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        response, first_record = await self._post(body, request.document.id)
        records = [first_record]
        try:
            content = response["choices"][0]["message"]["content"]
            payload = parse_json_object(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            repair_body = dict(body)
            messages = cast(list[dict[str, Any]], body["messages"])
            repair_body["messages"] = [
                *messages,
                {"role": "assistant", "content": str(response)},
                {"role": "user", "content": "Return one valid JSON object only."},
            ]
            repaired, repair_record = await self._post(repair_body, f"{request.document.id}:repair")
            records.append(repair_record)
            try:
                payload = parse_json_object(repaired["choices"][0]["message"]["content"])
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                raise ProviderResponseError(
                    "模型服务在一次修复后仍未返回有效的结构化 JSON",
                    call_records=records,
                ) from exc
        evidence = {item.id: item for item in request.document.evidence}
        blocks_by_evidence = {item.evidence_id: item for item in request.document.text_blocks}
        candidates = []
        entities: list[EntityMention] = []
        attributes: list[CandidateAttribute] = []
        events: list[CandidateEvent] = []
        warnings: list[str] = []
        issues = []
        items = payload.get("claims")
        if not isinstance(items, list):
            raise ProviderResponseError("模型 JSON 缺少 claims 数组", call_records=records)
        for position, item in enumerate(items):
            issue = validate_item(item, request.document.id, position)
            if issue is not None:
                issues.append(issue)
                continue
            evidence_id = str(item.get("evidence_id", ""))
            if evidence_id not in evidence:
                warnings.append("provider_returned_unknown_evidence_id")
                issues.append(
                    ValidationService.issue(
                        "UNKNOWN_EVIDENCE",
                        "reference",
                        "candidate",
                        stable_id("invalid-candidate", request.document.id, position),
                        f"claims[{position}].evidence_id",
                        "候选引用未知证据",
                        [evidence_id] if evidence_id else [],
                        summarize(item),
                    )
                )
                continue
            context = blocks_by_evidence.get(evidence_id)
            candidates.append(
                candidate_from_payload(
                    item,
                    evidence_id,
                    context.text if context is not None else "",
                    output_schema=request.output_schema,
                )
            )
        for position, item in enumerate(payload.get("entities", [])):
            if not isinstance(item, dict):
                warnings.append(f"entity_item_invalid:{position}")
                continue
            evidence_id = str(item.get("evidence_id", ""))
            name = str(item.get("name", "")).strip()
            entity_type = str(item.get("type", item.get("entity_type", ""))).strip()
            if not name or not entity_type or evidence_id not in evidence:
                warnings.append(f"entity_item_invalid:{position}")
                continue
            context = blocks_by_evidence.get(evidence_id)
            entities.append(
                EntityMention(
                    id=stable_id("mention", request.document.id, evidence_id, name, entity_type),
                    name=name,
                    entity_type=entity_type,
                    context=context.text if context else "",
                    modality=Modality.TEXT,
                    evidence_ids=[evidence_id],
                    confidence=float(item.get("confidence", 0.5)),
                    char_start=item.get("char_start"),
                    char_end=item.get("char_end"),
                )
            )
        known_entities = {item.id for item in entities}
        for candidate in candidates:
            for mention in (candidate.subject, candidate.object):
                if isinstance(mention, EntityMention) and mention.id not in known_entities:
                    entities.append(mention)
                    known_entities.add(mention.id)
        if request.task_mode == TaskMode.SCHEMA_INFORMATION_EXTRACTION:
            mentions_by_name = {item.name.casefold(): item for item in entities}
            for position, item in enumerate(payload.get("attributes", [])):
                if not isinstance(item, dict):
                    warnings.append(f"attribute_item_invalid:{position}")
                    continue
                subject = mentions_by_name.get(str(item.get("subject", "")).casefold())
                evidence_id = str(item.get("evidence_id", ""))
                field = str(item.get("field", "")).strip()
                if subject is None or not field or evidence_id not in evidence:
                    warnings.append(f"attribute_item_invalid:{position}")
                    continue
                attributes.append(
                    CandidateAttribute(
                        id=stable_id(
                            "attribute", request.document.id, subject.id, field, item.get("value")
                        ),
                        subject=subject,
                        field=field,
                        value=item.get("value"),
                        confidence=float(item.get("confidence", 0.5)),
                        evidence_ids=[evidence_id],
                    )
                )
            for position, item in enumerate(payload.get("events", [])):
                if not isinstance(item, dict):
                    warnings.append(f"event_item_invalid:{position}")
                    continue
                evidence_id = str(item.get("evidence_id", ""))
                event_type = str(item.get("type", item.get("event_type", ""))).strip()
                trigger = str(item.get("trigger", "")).strip()
                if not event_type or not trigger or evidence_id not in evidence:
                    warnings.append(f"event_item_invalid:{position}")
                    continue
                arguments = []
                for argument in item.get("arguments", []):
                    if not isinstance(argument, dict) or not argument.get("role"):
                        continue
                    raw_value = str(argument.get("value", ""))
                    arguments.append(
                        CandidateEventArgument(
                            role=str(argument["role"]),
                            value=mentions_by_name.get(raw_value.casefold(), raw_value),
                            evidence_ids=[evidence_id],
                        )
                    )
                events.append(
                    CandidateEvent(
                        id=stable_id(
                            "event", request.document.id, event_type, trigger, evidence_id
                        ),
                        event_type=event_type,
                        trigger=trigger,
                        arguments=arguments,
                        confidence=float(item.get("confidence", 0.5)),
                        evidence_ids=[evidence_id],
                    )
                )
        return ExtractionResult(
            candidates=candidates,
            entities=entities,
            attributes=attributes,
            events=events,
            warnings=warnings,
            call_records=records,
            validation=ValidationService.merge(ValidationResult(), issues),
        )
