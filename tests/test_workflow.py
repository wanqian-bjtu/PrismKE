from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from prismke.checkpoint import RunRepository, SQLiteCheckpointStore
from prismke.cli import app
from prismke.models import (
    ClaimStatus,
    ExtractionRequest,
    ExtractionResult,
    ReviewDecision,
    WorkflowState,
)
from prismke.providers import MockLLMProvider
from prismke.service import PrismKEService
from prismke.settings import Settings
from prismke.stores import JSONGraphStore
from prismke.workflow import PrismKEWorkflow


@pytest.mark.asyncio
async def test_mock_vertical_slice(tmp_path: Path, schema_path: Path) -> None:
    sample = tmp_path / "sample.md"
    sample.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n",
        encoding="utf-8",
    )
    service = PrismKEService(Settings(runtime_dir=tmp_path / "runtime"))
    state = await service.run(sample, schema_path, "mock")
    assert state.status == "completed"
    assert state.claims[0].status == ClaimStatus.AUTO_APPROVED
    assert state.revision is not None
    assert len(state.revision.entity_ids) == 2
    assert "entity:prismke" in state.revision.entity_ids
    assert state.claims[0].object_entity_id in state.revision.entity_ids
    assert state.claims[0].evidence_ids


@pytest.mark.asyncio
async def test_review_then_resume(tmp_path: Path, schema_path: Path) -> None:
    sample = tmp_path / "medium.md"
    sample.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.70\n",
        encoding="utf-8",
    )
    service = PrismKEService(Settings(runtime_dir=tmp_path / "runtime"))
    state = await service.run(sample, schema_path, "mock")
    assert state.status == "awaiting_review"
    claim_id = state.claims[0].id
    service.review(state.run_id, claim_id, ReviewDecision.APPROVE)
    completed = await service.resume(state.run_id)
    assert completed.status == "completed"
    assert completed.claims[0].status == ClaimStatus.APPROVED


@pytest.mark.asyncio
async def test_failed_node_can_resume_from_sqlite_snapshot(
    tmp_path: Path, schema_path: Path
) -> None:
    class FailingProvider:
        async def extract(self, request: ExtractionRequest) -> ExtractionResult:
            del request
            raise RuntimeError("simulated provider outage")

    sample = tmp_path / "sample.md"
    sample.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    checkpoints = SQLiteCheckpointStore(runtime / "checkpoints.sqlite3")
    runs = RunRepository(runtime / "runs")
    graph_store = JSONGraphStore(runtime / "graph")
    state = WorkflowState(
        run_id="run:recover",
        input_path=str(sample),
        schema_path=str(schema_path),
        provider_name="mock",
    )
    failing = PrismKEWorkflow(FailingProvider(), graph_store, checkpoints, runs)
    with pytest.raises(RuntimeError, match="simulated provider outage"):
        await failing.invoke(state)
    saved = checkpoints.load_latest(state.run_id)
    assert saved is not None
    assert saved.current_node == "extract_claims"
    assert saved.status == "failed"
    recovered = PrismKEWorkflow(MockLLMProvider(), graph_store, checkpoints, runs)
    saved.status = "running"
    result = await recovered.invoke(saved)
    assert result.status == "completed"


def test_cli_generates_run(tmp_path: Path, schema_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    sample = tmp_path / "sample.md"
    sample.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PRISMKE_RUNTIME_DIR", str(tmp_path / "runtime"))
    result = CliRunner().invoke(
        app,
        ["run", str(sample), "--schema", str(schema_path), "--provider", "mock"],
    )
    assert result.exit_code == 0, result.output
    assert "status=completed" in result.output
