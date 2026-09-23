import json
from pathlib import Path

import httpx
import pytest

from src.domain import (
    DocumentIR,
    ExtractionRequest,
    ExtractionResult,
    OCRRequest,
    OutputSchema,
    TextBlock,
)
from src.evaluation.document_validation import (
    _EvaluationLLM,
    _ReusedOCR,
    text_batches,
    validate_documents,
)
from src.evaluation.request_budget import BudgetedTransport, EvaluationBudgetStop, RequestBudget
from src.providers.ocr import DisabledOCRProvider
from src.providers.openai_compatible import OpenAICompatibleLLMProvider


@pytest.mark.asyncio
async def test_reused_ocr_rejects_changed_source_or_incomplete_stage():
    original = DisabledOCRProvider()
    doc = DocumentIR(id="doc", source_path="source", source_hash="a" * 64, media_type="text/plain")
    state = {
        "run_id": "old",
        "status": "failed",
        "failed_node": "extract_visual_claims",
        "ocr_provider_fingerprint": original.fingerprint(),
        "document": doc.model_dump(mode="json"),
    }
    request = OCRRequest(document=doc)
    reused = _ReusedOCR(original, state)
    assert "evaluation_reused_ocr_run:old" in (await reused.recognize(request)).warnings
    state["document"]["source_hash"] = "b" * 64
    with pytest.raises(ValueError, match="source hash mismatch"):
        await reused.recognize(request)
    state["failed_node"] = "run_ocr"
    with pytest.raises(ValueError, match="stage did not complete"):
        await reused.recognize(request)


@pytest.mark.parametrize("limit,stop", [(0, 0), (100, 100), (100, -1)])
def test_invalid_budget_fails_before_requests(limit, stop):
    with pytest.raises(ValueError):
        RequestBudget(limit=limit, stop_at=stop)


@pytest.mark.asyncio
async def test_ledger_is_pending_before_network_and_accumulates_across_documents(tmp_path):
    ledger = tmp_path / "ledger.json"
    budget = RequestBudget(limit=300000, stop_at=270000, ledger_path=ledger)

    def response(request):
        saved = json.loads(ledger.read_text())
        assert saved["calls"][-1]["status"] == "pending"
        return httpx.Response(200, json={"model": "test", "usage": {"total_tokens": 20}})

    async with httpx.AsyncClient(
        transport=BudgetedTransport(budget, httpx.MockTransport(response))
    ) as client:
        for case in ["D01", "D02"]:
            budget.case_id = case
            await client.post("https://test.invalid/chat", json={"messages": []})
    await budget.settle()
    saved = json.loads(ledger.read_text())
    assert saved["total_tokens"] == 40
    assert [row["case_id"] for row in saved["calls"]] == ["D01", "D02"]
    assert all(row["status"] == "succeeded" for row in saved["calls"])


@pytest.mark.asyncio
async def test_ledger_write_failure_blocks_network(tmp_path, monkeypatch):
    import src.evaluation.request_budget as module

    def fail(*args):
        raise OSError("disk unavailable")

    def network(request):
        pytest.fail("request dispatched despite unavailable ledger")

    monkeypatch.setattr(module.os, "replace", fail)
    budget = RequestBudget(ledger_path=tmp_path / "ledger.json")
    async with httpx.AsyncClient(
        transport=BudgetedTransport(budget, httpx.MockTransport(network))
    ) as client:
        with pytest.raises(EvaluationBudgetStop, match="ledger write failed"):
            await client.post("https://test.invalid/chat", json={"messages": []})
    await budget.settle()


def test_unsettled_ledger_is_not_reset(tmp_path):
    ledger = tmp_path / "ledger.json"
    raw = '{"calls":[{"request_number":1,"status":"pending"}]}'
    ledger.write_text(raw)
    with pytest.raises(EvaluationBudgetStop, match="unsettled requests"):
        RequestBudget(ledger_path=ledger)
    assert ledger.read_text() == raw


@pytest.mark.asyncio
async def test_explicit_ledger_continuation_preserves_round_budget(tmp_path):
    ledger = tmp_path / "ledger.json"
    first = RequestBudget(limit=300000, stop_at=270000, ledger_path=ledger)
    number = await first.reserve(100)
    await first.record(100, httpx.Response(200, json={"usage": {"total_tokens": 20}}), number)
    continued = RequestBudget(limit=300000, stop_at=270000, ledger_path=ledger, resume_ledger=True)
    assert continued.total_tokens == 20
    assert await continued.reserve(100) == 2
    with pytest.raises(EvaluationBudgetStop, match="unsettled"):
        RequestBudget(limit=300000, stop_at=270000, ledger_path=ledger, resume_ledger=True)


def test_batches_preserve_order_evidence_and_coordinates():
    blocks = [
        TextBlock(id=f"block{i}", text="中文" * 1000, evidence_id=f"ev{i}", page_number=i)
        for i in range(5)
    ]
    batches = text_batches(blocks)
    assert [len(batch) for batch in batches] == [2, 2, 1]
    assert [block for batch in batches for block in batch] == blocks
    assert all(sum(len(block.text.encode()) for block in batch) <= 12000 for batch in batches)
    oversized = TextBlock(id="big", text="a" * 13000, evidence_id="big")
    assert text_batches([blocks[0], oversized, blocks[1]]) == [
        [blocks[0]],
        [oversized],
        [blocks[1]],
    ]


@pytest.mark.asyncio
async def test_explicit_budget_extension_is_audited_and_never_resets_usage(tmp_path):
    ledger = tmp_path / "ledger.json"
    first = RequestBudget(limit=300000, stop_at=270000, ledger_path=ledger)
    number = await first.reserve(100)
    await first.record(100, httpx.Response(200, json={"usage": {"total_tokens": 20}}), number)
    with pytest.raises(EvaluationBudgetStop, match="parameters must not change"):
        RequestBudget(limit=500000, stop_at=450000, ledger_path=ledger, resume_ledger=True)
    extended = RequestBudget(
        limit=500000,
        stop_at=450000,
        ledger_path=ledger,
        resume_ledger=True,
        extend_budget=True,
    )
    saved = json.loads(ledger.read_text())
    assert extended.total_tokens == saved["total_tokens"] == 20
    assert len(saved["calls"]) == 1
    assert saved["budget_amendments"][0]["previous_limit"] == 300000
    assert saved["budget_amendments"][0]["tokens_already_used"] == 20
    with pytest.raises(EvaluationBudgetStop, match="parameters must not change"):
        RequestBudget(
            limit=300000,
            stop_at=270000,
            ledger_path=ledger,
            resume_ledger=True,
            extend_budget=True,
        )
    saved["accounting_complete"] = False
    ledger.write_text(json.dumps(saved))
    with pytest.raises(EvaluationBudgetStop, match="uncertain ledger"):
        RequestBudget(
            limit=600000,
            stop_at=550000,
            ledger_path=ledger,
            resume_ledger=True,
            extend_budget=True,
        )


@pytest.mark.asyncio
async def test_evaluation_provider_processes_every_batch_without_replacing_document_id(monkeypatch):
    blocks = [TextBlock(id=f"b{i}", text="x" * 7000, evidence_id=f"ev{i}") for i in range(3)]
    document = DocumentIR(
        id="doc",
        source_path="sample.pdf",
        source_hash="a" * 64,
        media_type="application/pdf",
        text_blocks=blocks,
    )
    seen = []

    async def extract(self, request):
        assert request.document.id == "doc"
        seen.extend(block.evidence_id for block in request.document.text_blocks)
        return ExtractionResult()

    monkeypatch.setattr(OpenAICompatibleLLMProvider, "extract", extract)
    provider = _EvaluationLLM("https://test.invalid", "not-a-real-key", "test")
    result = await provider.extract(
        ExtractionRequest(
            document=document,
            output_schema=OutputSchema(
                schema_id="test", version="1", entity_types=[], relations=[]
            ),
        )
    )
    assert seen == ["ev0", "ev1", "ev2"]
    assert "evaluation_text_batches_completed:3" in result.warnings


@pytest.mark.asyncio
async def test_completed_text_batches_are_cached_without_new_calls(tmp_path, monkeypatch):
    block = TextBlock(id="b", text="original", evidence_id="ev")
    document = DocumentIR(
        id="doc",
        source_path="x.txt",
        source_hash="a" * 64,
        media_type="text/plain",
        text_blocks=[block],
    )
    request = ExtractionRequest(
        document=document,
        output_schema=OutputSchema(schema_id="test", version="1", entity_types=[], relations=[]),
    )
    calls = 0

    async def extract(self, request):
        nonlocal calls
        calls += 1
        return ExtractionResult()

    monkeypatch.setattr(OpenAICompatibleLLMProvider, "extract", extract)
    provider = _EvaluationLLM("https://test.invalid", "test", "test")
    provider.cache_dir = tmp_path
    await provider.extract(request)
    result = await provider.extract(request)
    assert calls == 1
    assert "evaluation_text_batch_cache_hit" in result.warnings


@pytest.mark.asyncio
async def test_verified_text_cache_reuses_body_but_extracts_new_ocr(monkeypatch):
    from src.core.ids import stable_id

    body = TextBlock(id="body", text="original", evidence_id="ev0")
    ocr = TextBlock(id="ocr", text="new image text", evidence_id="ev1", modality="ocr")
    old = DocumentIR(
        id="doc",
        source_path="x.md",
        source_hash="a" * 64,
        media_type="text/markdown",
        text_blocks=[body],
    )
    schema = OutputSchema(schema_id="test", version="1", entity_types=[], relations=[])
    provider = _EvaluationLLM("https://test.invalid", "test", "test")
    base = OpenAICompatibleLLMProvider.fingerprint(provider)
    provider.cached_state = {
        "run_id": "old",
        "status": "awaiting_review",
        "document": old.model_dump(mode="json"),
        "output_schema": schema.model_dump(mode="json"),
        "text_candidates": [],
        "warnings": [],
        "provider_fingerprint": stable_id(
            "provider", base, "evaluation-output-limit-v3", 4096, 12000
        ),
        "provider_calls": [
            {
                "provider": "llm",
                "requested_model": "test",
                "status": "succeeded",
                "prompt_version": "schema-claims-v1",
            }
        ],
    }
    seen = []

    async def extract(self, request):
        seen.extend(block.id for block in request.document.text_blocks)
        return ExtractionResult()

    monkeypatch.setattr(OpenAICompatibleLLMProvider, "extract", extract)
    result = await provider.extract(
        ExtractionRequest(
            document=old.model_copy(update={"text_blocks": [body, ocr]}), output_schema=schema
        )
    )
    assert seen == ["ocr"]
    assert "evaluation_reused_text_run:old" in result.warnings


@pytest.mark.asyncio
async def test_validation_invalid_budget_does_not_create_runtime(tmp_path):
    from src.core.settings import Settings

    output = tmp_path / "output"
    with pytest.raises(ValueError, match="budget must"):
        await validate_documents(
            Path("missing.json"), Settings(), output, token_limit=100, stop_at=100
        )
    assert not output.exists()
