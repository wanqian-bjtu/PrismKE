from __future__ import annotations

import json

import httpx
import pytest

from src.core.errors import ProviderRequestError, ProviderResponseError
from src.domain import (
    DocumentIR,
    EntityCatalogItem,
    EntityTypeDef,
    EvidenceKind,
    EvidenceRef,
    ExtractionRequest,
    Modality,
    OutputSchema,
    TaskMode,
    TextBlock,
)
from src.providers import OpenAICompatibleLLMProvider


@pytest.mark.asyncio
async def test_openai_provider_with_mock_transport() -> None:
    evidence = EvidenceRef(
        id="ev:1",
        kind=EvidenceKind.TEXT_SPAN,
        document_id="doc:1",
        source_hash="a" * 64,
        modality=Modality.TEXT,
        char_start=0,
        char_end=4,
    )
    document = DocumentIR(
        id="doc:1",
        source_path="sample.txt",
        source_hash="a" * 64,
        media_type="text/plain",
        text_blocks=[TextBlock(id="b:1", text="fact", evidence_id="ev:1")],
        evidence=[evidence],
    )
    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])

    def handler(request: httpx.Request) -> httpx.Response:
        payload = {
            "claims": [
                {
                    "subject": "A",
                    "relation": "r",
                    "object": "B",
                    "subject_type": "Thing",
                    "confidence": 0.8,
                    "evidence_id": "ev:1",
                }
            ]
        }
        return httpx.Response(
            200,
            json={
                "id": "req-safe-1",
                "model": "qwen3.7-flash-2026-07-15",
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "total_tokens": 120,
                },
                "choices": [{"message": {"content": json.dumps(payload)}}],
            },
        )

    provider = OpenAICompatibleLLMProvider(
        "https://example.test/v1",
        "secret",
        "model",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.extract(ExtractionRequest(document=document, output_schema=schema))
    assert result.candidates[0].subject.name == "A"
    assert result.call_records[0].requested_model == "model"
    assert result.call_records[0].response_model == "qwen3.7-flash-2026-07-15"
    assert result.call_records[0].total_tokens == 120
    assert result.call_records[0].status == "succeeded"


@pytest.mark.asyncio
async def test_schema_information_mode_parses_attributes_and_events() -> None:
    evidence = EvidenceRef(
        id="ev:info",
        kind=EvidenceKind.TEXT_SPAN,
        document_id="doc:info",
        source_hash="a" * 64,
        modality=Modality.TEXT,
        char_start=0,
        char_end=20,
    )
    document = DocumentIR(
        id="doc:info",
        source_path="sample.txt",
        source_hash="a" * 64,
        media_type="text/plain",
        text_blocks=[TextBlock(id="b:info", text="Alice joined Acme.", evidence_id=evidence.id)],
        evidence=[evidence],
    )
    schema = OutputSchema(
        schema_id="info",
        version="1",
        entity_types=[EntityTypeDef(id="Person"), EntityTypeDef(id="Organization")],
        relations=[],
    )

    def handler(_: httpx.Request) -> httpx.Response:
        payload = {
            "entities": [
                {
                    "name": "Alice",
                    "entity_type": "Person",
                    "confidence": 0.9,
                    "evidence_id": evidence.id,
                }
            ],
            "claims": [],
            "attributes": [
                {
                    "subject": "Alice",
                    "subject_type": "Person",
                    "field": "role",
                    "value": "Engineer",
                    "confidence": 0.8,
                    "evidence_id": evidence.id,
                }
            ],
            "events": [
                {
                    "event_type": "EmploymentStart",
                    "trigger": "joined",
                    "confidence": 0.85,
                    "evidence_id": evidence.id,
                    "arguments": [
                        {
                            "role": "employee",
                            "value": "Alice",
                            "value_type": "Person",
                            "evidence_ids": [evidence.id],
                        }
                    ],
                }
            ],
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
        )

    provider = OpenAICompatibleLLMProvider(
        "https://example.test/v1",
        "secret",
        "model",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.extract(
        ExtractionRequest(
            document=document,
            output_schema=schema,
            task_mode=TaskMode.SCHEMA_INFORMATION_EXTRACTION,
        )
    )
    assert result.entities[0].name == "Alice"
    assert result.attributes[0].field == "role"
    assert result.events[0].event_type == "EmploymentStart"
    assert result.events[0].arguments[0].role == "employee"


@pytest.mark.asyncio
async def test_openai_provider_grounds_catalog_ids_to_source_surface_forms() -> None:
    evidence = EvidenceRef(
        id="ev:source",
        kind=EvidenceKind.TEXT_SPAN,
        document_id="doc:source",
        source_hash="a" * 64,
        modality=Modality.TEXT,
        char_start=0,
        char_end=24,
    )
    document = DocumentIR(
        id="doc:source",
        source_path="sample.md",
        source_hash="a" * 64,
        media_type="text/markdown",
        text_blocks=[
            TextBlock(
                id="block:source",
                text="北辰实验室开发了 AuroraGraph。",
                evidence_id=evidence.id,
            )
        ],
        evidence=[evidence],
    )
    schema = OutputSchema(
        schema_id="source-grounding",
        version="1",
        entity_types=[EntityTypeDef(id="Software"), EntityTypeDef(id="Organization")],
        relations=[],
        entity_catalog=[
            EntityCatalogItem(
                id="entity:northstar-labs",
                name="Northstar Labs",
                type="Organization",
                aliases=["北辰实验室"],
            ),
            EntityCatalogItem(
                id="entity:harbor-research",
                name="Harbor Research",
                type="Organization",
            ),
            EntityCatalogItem(
                id="entity:auroragraph",
                name="AuroraGraph",
                type="Software",
            ),
        ],
    )

    def handler(request: httpx.Request) -> httpx.Response:
        request_payload = json.loads(request.content)
        prompt = request_payload["messages"][0]["content"]
        assert "exact surface forms" in prompt
        payload = {
            "claims": [
                {
                    "subject": "entity:harbor-research",
                    "relation": "developed_by",
                    "object": "entity:auroragraph",
                    "subject_type": "Organization",
                    "object_type": "Software",
                    "confidence": 0.9,
                    "evidence_id": evidence.id,
                }
            ]
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
        )

    provider = OpenAICompatibleLLMProvider(
        "https://example.test/v1",
        "secret",
        "model",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.extract(ExtractionRequest(document=document, output_schema=schema))
    assert result.candidates[0].subject.name == "北辰实验室"
    assert result.candidates[0].object.name == "AuroraGraph"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "code", "message"),
    [
        (401, "authentication_failed", "API Key"),
        (403, "access_denied", "免费额度"),
        (404, "not_found", "Base URL"),
    ],
)
async def test_provider_errors_are_actionable_and_sanitized(
    status: int, code: str, message: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(status, text="server-secret-response")

    provider = OpenAICompatibleLLMProvider(
        "https://example.test/v1",
        "sk-super-secret",
        "qwen3.7-flash",
        transport=httpx.MockTransport(handler),
    )
    document = DocumentIR(
        id="doc:error",
        source_path="sample.txt",
        source_hash="a" * 64,
        media_type="text/plain",
    )
    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])
    with pytest.raises(ProviderRequestError, match=message) as caught:
        await provider.extract(ExtractionRequest(document=document, output_schema=schema))
    assert caught.value.call_record.error_code == code
    assert "sk-super-secret" not in str(caught.value)
    assert "server-secret-response" not in str(caught.value)


@pytest.mark.asyncio
async def test_provider_retries_rate_limit_then_records_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        del request
        calls += 1
        if calls < 3:
            return httpx.Response(429)
        return httpx.Response(
            200,
            json={
                "id": "req-retried",
                "model": "qwen3.7-flash",
                "choices": [{"message": {"content": '{"claims": []}'}}],
            },
        )

    provider = OpenAICompatibleLLMProvider(
        "https://example.test/v1",
        "secret",
        "qwen3.7-flash",
        transport=httpx.MockTransport(handler),
    )
    document = DocumentIR(
        id="doc:retry",
        source_path="sample.txt",
        source_hash="a" * 64,
        media_type="text/plain",
    )
    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])
    result = await provider.extract(ExtractionRequest(document=document, output_schema=schema))
    assert calls == 3
    assert result.call_records[0].retry_count == 2


@pytest.mark.asyncio
async def test_provider_stops_after_one_json_repair() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        del request
        calls += 1
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not-json"}}]},
        )

    provider = OpenAICompatibleLLMProvider(
        "https://example.test/v1",
        "secret",
        "qwen3.7-flash",
        transport=httpx.MockTransport(handler),
    )
    document = DocumentIR(
        id="doc:repair",
        source_path="sample.txt",
        source_hash="a" * 64,
        media_type="text/plain",
    )
    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])
    with pytest.raises(ProviderResponseError) as caught:
        await provider.extract(ExtractionRequest(document=document, output_schema=schema))
    assert calls == 2
    assert len(caught.value.call_records) == 2
