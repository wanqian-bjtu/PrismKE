"""OpenAI-compatible text extraction provider."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx

from prismke.core.errors import ProviderResponseError
from prismke.core.ids import stable_id
from prismke.domain import ExtractionRequest, ExtractionResult, ProviderCallRecord
from prismke.providers.common import candidate_from_payload, parse_json_object
from prismke.providers.http_client import post_chat_completion

PROMPT_VERSION = "schema-claims-v1"
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
            transport=self.transport,
        )

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        blocks = [
            {"evidence_id": block.evidence_id, "text": block.text}
            for block in request.document.text_blocks
        ]
        prompt = (
            "Extract factual claims from the supplied blocks under the supplied schema. "
            "Return a JSON object with key 'claims'. Each claim must contain subject, "
            "relation, object, subject_type, optional object_type, confidence, and "
            "evidence_id. Subject and object must be exact surface forms from the source "
            "block; never return entity catalog IDs, values beginning with 'entity:', "
            "translations, or canonical names absent from the source. Choose relation "
            "direction so the subject type satisfies domain and the object type satisfies "
            "range; use the inverse relation ID when the sentence has the inverse direction. "
            "Never invent an evidence_id.\n"
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
        warnings: list[str] = []
        for item in payload.get("claims", []):
            evidence_id = str(item.get("evidence_id", ""))
            if evidence_id not in evidence:
                warnings.append("provider_returned_unknown_evidence_id")
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
        return ExtractionResult(
            candidates=candidates,
            warnings=warnings,
            call_records=records,
        )
