from __future__ import annotations

import json

import httpx
import pytest

from prismke.models import (
    DocumentIR,
    EvidenceKind,
    EvidenceRef,
    ExtractionRequest,
    Modality,
    OutputSchema,
    TextBlock,
)
from prismke.providers import OpenAICompatibleLLMProvider


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
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
        )

    provider = OpenAICompatibleLLMProvider(
        "https://example.test/v1",
        "secret",
        "model",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.extract(ExtractionRequest(document=document, output_schema=schema))
    assert result.candidates[0].subject.name == "A"
