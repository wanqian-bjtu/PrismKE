import asyncio
import json

import httpx
import pytest

from prismke.evaluation.request_budget import BudgetedTransport, EvaluationBudgetStop, RequestBudget


@pytest.mark.asyncio
async def test_budget_accounts_each_call_without_secrets() -> None:
    def response(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["max_tokens"] == 4096
        return httpx.Response(
            200,
            json={
                "model": "test",
                "id": "request1",
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 8,
                    "total_tokens": 20,
                },
            },
        )

    budget = RequestBudget()
    async with httpx.AsyncClient(
        transport=BudgetedTransport(budget, httpx.MockTransport(response))
    ) as client:
        await client.post(
            "https://test.invalid/chat",
            headers={"Authorization": "Bearer SECRET"},
            json={
                "messages": [{"content": "text"}],
                "model": "test",
            },
        )
    assert budget.total_tokens == 20
    assert budget.reserved_tokens == 0
    assert "SECRET" not in json.dumps(budget.calls)


@pytest.mark.asyncio
@pytest.mark.parametrize("payload,status", [({}, 200), ({}, 403), ({}, 429)])
async def test_unknown_usage_or_access_failure_stops_calls(payload: dict, status: int) -> None:
    budget = RequestBudget()
    transport = BudgetedTransport(
        budget, httpx.MockTransport(lambda req: httpx.Response(status, json=payload))
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(EvaluationBudgetStop):
            await client.post("https://test.invalid/chat", json={"messages": []})
    with pytest.raises(EvaluationBudgetStop):
        await budget.reserve(1)


@pytest.mark.asyncio
async def test_budget_blocks_oversized_request_before_network() -> None:
    budget = RequestBudget(limit=1000, stop_at=900)
    with pytest.raises(EvaluationBudgetStop):
        await budget.reserve(budget.estimate({"messages": [{"content": "text"}]}))
    assert budget.calls == []


@pytest.mark.asyncio
async def test_inflight_reservations_are_counted() -> None:
    budget = RequestBudget(limit=10000, stop_at=9000)
    await budget.reserve(6000)
    with pytest.raises(EvaluationBudgetStop):
        await budget.reserve(6000)


def test_image_estimation_does_not_account_base64_as_text() -> None:
    budget = RequestBudget()
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,SECRET"}}
    assert budget.estimate({"messages": [{"content": [image]}]}) == 8192 + 4096 + 1024
    assert "SECRET" not in json.dumps(budget.calls)


@pytest.mark.asyncio
async def test_parallel_branches_serialize_paid_requests() -> None:
    budget = RequestBudget(limit=10_000, stop_at=9000)
    active = peak = 0

    async def response(request: httpx.Request) -> httpx.Response:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return httpx.Response(200, json={"usage": {"total_tokens": 20}})

    async with httpx.AsyncClient(
        transport=BudgetedTransport(budget, httpx.MockTransport(response))
    ) as client:
        await asyncio.gather(
            client.post("https://test.invalid/chat", json={"messages": []}),
            client.post("https://test.invalid/chat", json={"messages": []}),
        )
    await budget.settle()
    assert peak == 1
    assert budget.total_tokens == 40


@pytest.mark.asyncio
async def test_cancelled_workflow_settles_dispatched_request_usage() -> None:
    budget = RequestBudget()
    dispatched = asyncio.Event()
    finish = asyncio.Event()

    async def response(request: httpx.Request) -> httpx.Response:
        dispatched.set()
        await finish.wait()
        return httpx.Response(200, json={"usage": {"total_tokens": 20}})

    async with httpx.AsyncClient(
        transport=BudgetedTransport(budget, httpx.MockTransport(response))
    ) as client:
        task = asyncio.create_task(client.post("https://test.invalid/chat", json={"messages": []}))
        await dispatched.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        finish.set()
        await budget.settle()
    assert budget.total_tokens == 20
    assert budget.reserved_tokens == 0
    assert budget.accounting_complete is True


@pytest.mark.asyncio
async def test_bailian_evaluation_disables_hidden_thinking_only_for_qwen() -> None:
    def response(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["enable_thinking"] is False
        return httpx.Response(200, json={"usage": {"total_tokens": 20}})

    budget = RequestBudget()
    async with httpx.AsyncClient(
        transport=BudgetedTransport(budget, httpx.MockTransport(response))
    ) as client:
        await client.post(
            "https://ws-test.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions",
            json={"model": "qwen3.7-flash", "messages": []},
        )
    await budget.settle()


@pytest.mark.asyncio
async def test_document_validation_forces_json_without_touching_production(
    tmp_path, monkeypatch
) -> None:
    from prismke.core.settings import Settings
    from prismke.domain import WorkflowState
    from prismke.evaluation.document_validation import _EvaluationService, validate_documents

    source = tmp_path / "sample.txt"
    source.write_text("test")
    schema = tmp_path / "schema.yaml"
    schema.write_text("test")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"cases": [{"id": "D1", "input_path": "sample.txt", "schema_path": "schema.yaml"}]}
        )
    )
    production = tmp_path / "production"
    graph = production / "graph/graph.json"
    graph.parent.mkdir(parents=True)
    graph.write_bytes(b"unchanged production")
    monkeypatch.setattr(_EvaluationService, "provider", lambda *args: object())
    monkeypatch.setattr(_EvaluationService, "vlm_provider", lambda *args: object())
    monkeypatch.setattr(
        _EvaluationService,
        "embedding_provider",
        lambda *args: type("Provider", (), {"fingerprint": lambda self: "test"})(),
    )

    async def run(self, *args):
        assert self.settings.graph_store == "json"
        return WorkflowState(
            run_id="test", input_path=str(source), schema_path=str(schema), status="completed"
        )

    monkeypatch.setattr(_EvaluationService, "run", run)
    result = await validate_documents(
        manifest,
        Settings(runtime_dir=production, graph_store="neo4j", embedding_provider="bge-m3"),
        tmp_path / "output",
    )
    assert result["production_json_unchanged"] is True
    assert graph.read_bytes() == b"unchanged production"


@pytest.mark.asyncio
async def test_document_validation_preserves_interrupted_case_without_traceback(
    tmp_path, monkeypatch
) -> None:
    from prismke.core.settings import Settings
    from prismke.evaluation.document_validation import _EvaluationService, validate_documents

    (tmp_path / "sample.txt").write_text("test")
    (tmp_path / "schema.yaml").write_text("test")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {"id": "D1", "input_path": "sample.txt", "schema_path": "schema.yaml"},
                    {"id": "D2", "input_path": "sample.txt", "schema_path": "schema.yaml"},
                ]
            }
        )
    )
    monkeypatch.setattr(_EvaluationService, "provider", lambda *args: object())
    monkeypatch.setattr(_EvaluationService, "vlm_provider", lambda *args: object())
    monkeypatch.setattr(
        _EvaluationService,
        "embedding_provider",
        lambda *args: type("Provider", (), {"fingerprint": lambda self: "test"})(),
    )

    async def run(self, *args):
        self.budget.stopped_reason = "estimated request exceeds remaining token budget"
        raise EvaluationBudgetStop(self.budget.stopped_reason)

    monkeypatch.setattr(_EvaluationService, "run", run)
    result = await validate_documents(
        manifest,
        Settings(runtime_dir=tmp_path / "prod", embedding_provider="bge-m3"),
        tmp_path / "output",
    )
    assert result["cases"][0]["status"] == "budget_stopped"
    assert result["unprocessed_case_ids"] == ["D2"]
    assert (tmp_path / "output/document-validation.json").is_file()
