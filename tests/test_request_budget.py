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
    budget = RequestBudget(limit=1000)
    with pytest.raises(EvaluationBudgetStop):
        await budget.reserve(budget.estimate({"messages": [{"content": "text"}]}))
    assert budget.calls == []


@pytest.mark.asyncio
async def test_inflight_reservations_are_counted() -> None:
    budget = RequestBudget(limit=10000)
    await budget.reserve(6000)
    with pytest.raises(EvaluationBudgetStop):
        await budget.reserve(6000)


def test_image_estimation_does_not_account_base64_as_text() -> None:
    budget = RequestBudget()
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,SECRET"}}
    assert budget.estimate({"messages": [{"content": [image]}]}) == 8192 + 4096 + 1024
    assert "SECRET" not in json.dumps(budget.calls)


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
