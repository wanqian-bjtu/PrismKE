import json
from pathlib import Path

import httpx
import pytest

from prismke.domain import DocumentIR, ExtractionRequest, ExtractionResult, OutputSchema, TextBlock
from prismke.evaluation.document_validation import _EvaluationLLM, text_batches, validate_documents
from prismke.evaluation.request_budget import BudgetedTransport, EvaluationBudgetStop, RequestBudget
from prismke.providers.openai_compatible import OpenAICompatibleLLMProvider


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
    import prismke.evaluation.request_budget as module

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
async def test_validation_invalid_budget_does_not_create_runtime(tmp_path):
    from prismke.core.settings import Settings

    output = tmp_path / "output"
    with pytest.raises(ValueError, match="budget must"):
        await validate_documents(
            Path("missing.json"), Settings(), output, token_limit=100, stop_at=100
        )
    assert not output.exists()
