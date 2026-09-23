from __future__ import annotations

import asyncio
import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import orjson
import pytest
from fastapi.testclient import TestClient
from filelock import Timeout

from src.api import create_app
from src.core.errors import ProviderRequestError
from src.core.execution_control import ExecutionPaused, current_execution
from src.core.settings import Settings
from src.domain import ExtractionResult, ReviewDecision
from src.persistence.execution import ExecutionConflict
from src.persistence.neo4j_graph import Neo4jGraphStore
from src.providers import MockLLMProvider
from src.providers.http_client import _usage, post_chat_completion
from src.workflow import PrismKEService
from src.workflow.execution import RunControl


def fixture(tmp_path: Path, schema_path: Path) -> tuple[PrismKEService, str, Path]:
    sample = tmp_path / "sample.md"
    sample.write_text("ExecutionDemo | developed_by | TestOrg | Software | Organization | 0.92\n")
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    state, created = service.create_run(sample, schema_path, "mock")
    assert created
    return service, state.run_id, sample


class SlowProvider(MockLLMProvider):
    def __init__(self) -> None:
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.calls = 0

    async def extract(self, request: object) -> ExtractionResult:
        self.calls += 1
        self.entered.set()
        await self.release.wait()
        return await super().extract(request)  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["json", "neo4j"])
async def test_cancel_resume_review_commit_and_rollback(
    tmp_path: Path, schema_path: Path, backend: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if backend == "neo4j" and os.getenv("PRISMKE_TEST_NEO4J") != "1":
        pytest.skip("dedicated Neo4j fixture required")
    sample = tmp_path / "sample.md"
    name = f"Execution-{uuid4().hex}"
    sample.write_text(f"{name} | developed_by | Org-{name} | Software | Organization | 0.7\n")
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    if backend == "neo4j":
        settings = Settings()
        assert settings.neo4j_uri == "bolt://127.0.0.1:17687"
        service.graph_store = Neo4jGraphStore(
            settings.neo4j_uri,
            settings.neo4j_user,
            settings.neo4j_password or "test",
            settings.neo4j_database,
            evidence_store=service.evidence_store,
        )
    provider = SlowProvider()
    monkeypatch.setattr(service, "provider", lambda _: provider)
    state, _ = service.create_run(sample, schema_path, "mock")
    await service.executions.start()
    await asyncio.wait_for(provider.entered.wait(), 10)
    service.executions.cancel(
        state.run_id, "tester", "pause", "cancel", service.executions.view(state.run_id)["version"]
    )
    provider.release.set()
    await service.executions.wait(state.run_id)
    assert service.executions.view(state.run_id)["status"] == "cancelled"
    state = await service.resume(state.run_id)
    assert state.status == "awaiting_review"
    assert provider.calls == 1
    for task in state.review_tasks:
        if task.status == "pending":
            await service.review(state.run_id, task.claim_id, ReviewDecision.APPROVE, "tester")
    state = await service.resume(state.run_id)
    assert state.status == "completed"
    for claim in state.graph_commit.claims:
        assert await service.graph_store.get_claim(claim.id)
        assert all([await service.evidence_store.verify(eid) for eid in claim.evidence_ids])
    compensation = await service.graph_store.rollback_revision(state.revision.id)
    assert compensation.parent_id == state.revision.id
    assert (await service.graph_store.get_claim(state.claims[0].id)).tx_to is not None
    await service.close()


def test_creation_is_unique(tmp_path: Path, schema_path: Path) -> None:
    service, run_id, sample = fixture(tmp_path, schema_path)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(lambda _: service.create_run(sample, schema_path, "mock"), range(8))
        )
    assert all(s.run_id == run_id and not created for s, created in results)
    assert len(service.executions.repository.list_tasks()) == 1
    assert len(service.executions.repository.events(run_id)) == 1


def test_shutdown_rejects_new_execution_without_persisting_it(
    tmp_path: Path, schema_path: Path
) -> None:
    service, run_id, sample = fixture(tmp_path, schema_path)
    service.executions.persistent = True
    service.executions.stopping = True
    version = service.executions.view(run_id)["version"]
    with pytest.raises(ExecutionConflict, match="WORKER_SHUTTING_DOWN"):
        service.executions.enqueue(run_id, "execute")
    sample.write_text("different input")
    with pytest.raises(ExecutionConflict, match="WORKER_SHUTTING_DOWN"):
        service.create_run(sample, schema_path, "mock")
    assert len(service.executions.repository.list_tasks()) == 1
    assert service.executions.view(run_id)["version"] == version


def test_competing_first_creation(tmp_path: Path, schema_path: Path) -> None:
    sample = tmp_path / "first.md"
    sample.write_text("FirstDemo | developed_by | TestOrg | Software | Organization | 0.92\n")
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(lambda _: service.create_run(sample, schema_path, "mock"), range(8))
        )
    assert sum(created for _, created in results) == 1
    assert len({state.run_id for state, _ in results}) == 1
    assert len(service.executions.repository.list_tasks()) == 1


@pytest.mark.asyncio
async def test_public_duplicate_execution_joins_existing_attempt(
    tmp_path: Path, schema_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    provider = SlowProvider()
    monkeypatch.setattr(service, "provider", lambda _: provider)
    first = asyncio.create_task(service.execute_run(run_id))
    await asyncio.wait_for(provider.entered.wait(), 10)
    second = asyncio.create_task(service.execute_run(run_id))
    await asyncio.sleep(0.1)
    provider.release.set()
    results = await asyncio.wait_for(asyncio.gather(first, second), 10)
    assert all(state.status == "completed" for state in results)
    assert provider.calls == 1
    assert service.executions.repository.get(run_id).attempt == 1
    await service.close()


@pytest.mark.asyncio
async def test_post_commit_projection_failure_settles_from_revision(
    tmp_path: Path, schema_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    original = service._execute_run

    async def fail_after_commit(identifier: str):
        await original(identifier)
        raise OSError("synthetic post-commit projection failure")

    monkeypatch.setattr(service, "_execute_run", fail_after_commit)
    state = await service.execute_run(run_id)
    assert state.status == "completed"
    assert service.executions.view(run_id)["status"] == "completed"
    assert len(await service.graph_store.list_revisions()) == 1
    await service.close()


def test_cancel_version_idempotency_and_immutable_events(tmp_path: Path, schema_path: Path) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    manager = service.executions
    with pytest.raises(ExecutionConflict, match="STALE"):
        manager.cancel(run_id, "tester", "stop", "cancel-1", 999)
    with pytest.raises(ExecutionConflict, match="REQUIRED"):
        manager.cancel(run_id, " ", "stop", "cancel-1", 0)
    first = manager.cancel(run_id, "tester", "stop", "cancel-1", 0)
    second = manager.cancel(run_id, "tester", "stop", "cancel-1", 0)
    assert first.model_dump() == second.model_dump()
    assert first.status == "cancelled"
    with pytest.raises(ExecutionConflict, match="REUSED"):
        manager.cancel(run_id, "tester", "different", "cancel-1", 0)
    with manager.repository.connect() as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM events")


@pytest.mark.asyncio
async def test_single_worker_owner_and_queue_cancel(tmp_path: Path, schema_path: Path) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    service.executions.cancel(run_id, "tester", "not needed", "cancel", 0)
    await service.executions.start()
    other = PrismKEService(service.settings)
    with pytest.raises(ExecutionConflict, match="WORKSPACE_WORKER_BUSY"):
        await other.executions.start()
    assert service.executions.view(run_id)["status"] == "cancelled"
    assert service.executions.repository.get(run_id).attempt == 0
    await other.close()
    await service.close()


@pytest.mark.asyncio
async def test_queue_cancel_resumes_first_execution_without_checkpoint(
    tmp_path: Path, schema_path: Path
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    service.executions.cancel(run_id, "tester", "pause queue", "cancel", 0)
    state = await service.resume(run_id)
    assert state.status == "completed"
    assert service.executions.repository.get(run_id).attempt == 1
    assert len(await service.graph_store.list_revisions()) == 1
    await service.close()


@pytest.mark.asyncio
async def test_cancel_settles_result_and_resume_does_not_repeat_extraction(
    tmp_path: Path,
    schema_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    provider = SlowProvider()
    monkeypatch.setattr(service, "provider", lambda _: provider)
    await service.executions.start()
    await asyncio.wait_for(provider.entered.wait(), 10)
    with pytest.raises(Timeout):
        await service.review_entity(run_id, "missing", "create", reviewer="tester")
    version = service.executions.view(run_id)["version"]
    service.executions.cancel(run_id, "tester", "pause", "cancel", version)
    assert service.executions.view(run_id)["status"] == "cancelling"
    provider.release.set()
    await service.executions.wait(run_id)
    assert service.executions.view(run_id)["status"] == "cancelled"
    assert service.show_run(run_id).retry_count == 0
    assert provider.calls == 1
    service.executions.enqueue(run_id, "resume")
    completed = await service.executions.wait(run_id)
    assert completed.status == "completed" and provider.calls == 1
    assert len(await service.graph_store.list_revisions()) == 1
    await service.close()


@pytest.mark.asyncio
async def test_duplicate_enqueue_does_not_add_attempt(
    tmp_path: Path,
    schema_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    provider = SlowProvider()
    monkeypatch.setattr(service, "provider", lambda _: provider)
    await service.executions.start()
    await asyncio.wait_for(provider.entered.wait(), 10)
    for _ in range(5):
        service.executions.enqueue(run_id, "execute")
    assert service.executions.repository.get(run_id).attempt == 1
    provider.release.set()
    await service.executions.wait(run_id)
    assert provider.calls == 1
    await service.close()


async def http_call(transport: httpx.MockTransport) -> object:
    return await post_chat_completion(
        base_url="https://test.invalid/v1",
        api_key="sensitive-test-key",
        body={"model": "test-model", "messages": [{"role": "user", "content": "text"}]},
        timeout=1,
        provider="llm",
        operation_id="document",
        prompt_version="test-v1",
        provider_fingerprint="test-provider-v1",
        transport=transport,
    )


@pytest.mark.asyncio
async def test_http_response_replay_and_private_journal(tmp_path: Path, schema_path: Path) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "id": "request-1",
                "model": "test-model",
                "authorization": "sensitive-test-key",
                "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
                "choices": [
                    {"message": {"content": "sensitive-test-key data:image/png;base64,AAAA"}}
                ],
            },
        )

    token = current_execution.set(RunControl(service.executions, run_id))
    try:
        await http_call(httpx.MockTransport(handler))
        await http_call(httpx.MockTransport(handler))
    finally:
        current_execution.reset(token)
    assert calls == 1 and service.executions.repository.unknown(run_id) == 0
    with service.executions.repository.connect() as db:
        data = db.execute("SELECT response,metadata FROM requests").fetchone()
        assert b"sensitive-test-key" not in data[0] and b"base64,AAAA" not in data[0]
        assert b"messages" not in data[1]
        metadata = orjson.loads(data[1])
        assert metadata["provider_fingerprint"] == "test-provider-v1"
        assert metadata["latency_ms"] >= 0
        assert metadata["dispatched_at"] <= metadata["settled_at"]
    await service.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["usage_missing", "timeout", "network", "server_error"])
async def test_uncertain_requests_block_restart_and_resend(
    tmp_path: Path,
    schema_path: Path,
    mode: str,
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if mode == "timeout":
            raise httpx.ReadTimeout("timeout", request=request)
        if mode == "network":
            raise httpx.ReadError("disconnect", request=request)
        return httpx.Response(500 if mode == "server_error" else 200, json={"choices": []})

    token = current_execution.set(RunControl(service.executions, run_id))
    try:
        if mode == "usage_missing":
            _, record = await http_call(httpx.MockTransport(handler))
            assert record.total_tokens is None and record.estimated_cost_cny is None
        else:
            with pytest.raises(ProviderRequestError):
                await http_call(httpx.MockTransport(handler))
        with pytest.raises(ExecutionPaused, match="UNKNOWN"):
            await http_call(httpx.MockTransport(handler))
    finally:
        current_execution.reset(token)
    assert calls == 1
    await service.executions.start()
    view = service.executions.view(run_id)
    assert view["status"] == "interrupted" and view["unknown_requests"] == 1
    assert view["error_code"] == "UNKNOWN_PROVIDER_REQUEST"
    await service.close()


@pytest.mark.asyncio
async def test_cancel_prevents_429_retry(tmp_path: Path, schema_path: Path) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        service.executions.cancel(run_id, "tester", "stop", "cancel", 0)
        return httpx.Response(429)

    token = current_execution.set(RunControl(service.executions, run_id))
    try:
        with pytest.raises(ExecutionPaused, match="USER_CANCEL"):
            await http_call(httpx.MockTransport(handler))
    finally:
        current_execution.reset(token)
    assert calls == 1 and service.executions.repository.unknown(run_id) == 0
    await service.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("phase", ["begin_request", "finish_request"])
async def test_request_journal_failure_stops_calls(
    tmp_path: Path,
    schema_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    calls = 0

    def fail(*args: object, **kwargs: object) -> None:
        raise sqlite3.OperationalError("disk write failed")

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200, json={"choices": [], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
        )

    monkeypatch.setattr(service.executions.repository, phase, fail)
    token = current_execution.set(RunControl(service.executions, run_id))
    try:
        with pytest.raises(sqlite3.OperationalError):
            await http_call(httpx.MockTransport(handler))
    finally:
        current_execution.reset(token)
    assert calls == (0 if phase == "begin_request" else 1)
    if phase == "finish_request":
        assert service.executions.repository.unknown(run_id) == 1
    await service.close()


@pytest.mark.asyncio
async def test_changed_input_blocks_auto_resume(tmp_path: Path, schema_path: Path) -> None:
    service, run_id, sample = fixture(tmp_path, schema_path)
    sample.write_text("changed")
    await service.executions.start()
    assert service.executions.view(run_id)["error_code"] == "EXECUTION_INPUT_CHANGED"
    assert service.executions.view(run_id)["blocked"]
    assert not service.review_progress(run_id)["can_resume"]
    assert service.executions.repository.get(run_id).attempt == 0
    await service.close()


@pytest.mark.parametrize(
    "usage", [None, {}, "invalid", {"prompt_tokens": True, "completion_tokens": 1}]
)
def test_unknown_usage_never_becomes_zero(usage: object) -> None:
    assert _usage({"usage": usage}) == (None, None, None)


@pytest.mark.asyncio
async def test_cancel_after_graph_commit_reports_completion(
    tmp_path: Path,
    schema_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    entered, release = asyncio.Event(), asyncio.Event()
    original = service.graph_store.commit

    async def commit(transaction: object) -> None:
        await original(transaction)
        entered.set()
        await release.wait()

    monkeypatch.setattr(service.graph_store, "commit", commit)
    await service.executions.start()
    await asyncio.wait_for(entered.wait(), 10)
    service.executions.cancel(
        run_id, "tester", "stop", "cancel", service.executions.view(run_id)["version"]
    )
    release.set()
    await service.executions.wait(run_id)
    assert service.executions.view(run_id)["status"] == "completed"
    assert service.executions.view(run_id)["reason"] == "CANCEL_TOO_LATE_COMMIT_COMPLETED"
    assert len(await service.graph_store.list_revisions()) == 1
    await service.close()


@pytest.mark.asyncio
async def test_independent_process_restart_auto_recovers_without_reparsing(
    tmp_path: Path,
    schema_path: Path,
) -> None:
    sample = tmp_path / "sample.md"
    sample.write_text("RestartDemo | developed_by | TestOrg | Software | Organization | 0.92\n")
    runtime = tmp_path / "runtime"
    code = r"""
import asyncio,sys
from pathlib import Path
from src.workflow import PrismKEService
from src.providers import MockLLMProvider
from src.core.settings import Settings
from src.core.execution_control import ExecutionPaused
from src.parsing import ParserRegistry
runtime,sample,schema=map(Path,sys.argv[1:])
original=ParserRegistry.parse
async def parse(self,source):
    counter=runtime/'parse-count.txt'
    counter.write_text(str(int(counter.read_text())+1) if counter.exists() else '1')
    return await original(self,source)
ParserRegistry.parse=parse
class Pause(MockLLMProvider):
    async def extract(self,request):
        raise ExecutionPaused('SERVER_SHUTDOWN')
async def main():
    service=PrismKEService(Settings(_env_file=None,runtime_dir=runtime))
    service.provider=lambda _:Pause()
    state=await service.run(sample,schema,'mock')
    (runtime/'run-id.txt').write_text(state.run_id)
    await service.close()
asyncio.run(main())
"""
    process = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", code, str(runtime), str(sample), str(schema_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert process.returncode == 0, process.stderr
    run_id = (runtime / "run-id.txt").read_text()
    service = PrismKEService(Settings(_env_file=None, runtime_dir=runtime))
    assert service.executions.view(run_id)["status"] == "interrupted"
    await service.executions.start()
    result = await service.executions.wait(run_id)
    assert result.status == "completed"
    assert service.executions.repository.get(run_id).attempt == 2
    assert (runtime / "parse-count.txt").read_text() == "1"
    assert len(await service.graph_store.list_revisions()) == 1
    await service.close()


def test_execution_api_cancel_and_events(tmp_path: Path, schema_path: Path) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    service.executions.cancel(run_id, "tester", "do not start", "pre-cancel", 0)
    with TestClient(create_app(service.settings, service, mount_ui=False)) as client:
        view = client.get(f"/api/v1/runs/{run_id}/execution").json()
        assert view["status"] == "cancelled" and view["can_resume"]
        assert client.post(f"/api/v1/runs/{run_id}/cancel", json={}).status_code == 422
        assert len(client.get(f"/api/v1/runs/{run_id}/execution-events").json()) == 2
        assert client.get("/api/v1/runs/missing/execution").status_code == 404
        stale = client.post(f"/api/v1/runs/{run_id}/resume", json={"expected_version": 999})
        assert stale.status_code == 409
        health = client.get("/api/v1/health").json()
        assert health["execution"]["worker"] == "running"


@pytest.mark.asyncio
async def test_task_write_failure_prevents_initial_run(
    tmp_path: Path,
    schema_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    sample = tmp_path / "sample.md"
    sample.write_text("text")

    def fail(*args: object) -> None:
        raise sqlite3.OperationalError("disk failed")

    monkeypatch.setattr(service.executions.repository, "register", fail)
    with pytest.raises(sqlite3.OperationalError):
        service.create_run(sample, schema_path, "mock")
    assert service.runs.list() == []
    await service.close()


@pytest.mark.asyncio
async def test_checkpoint_failure_is_not_silently_completed(
    tmp_path: Path,
    schema_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, run_id, _ = fixture(tmp_path, schema_path)
    monkeypatch.setattr(
        service, "_execute_run", AsyncMock(side_effect=OSError("checkpoint failed"))
    )
    with pytest.raises(OSError):
        await service.execute_run(run_id)
    assert service.executions.view(run_id)["status"] == "failed"
    await service.close()
