from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from prismke.cli import app
from prismke.core.errors import EvidenceIntegrityError
from prismke.core.ids import stable_id
from prismke.core.settings import Settings
from prismke.domain import (
    Claim,
    ClaimStatus,
    ExtractionRequest,
    ExtractionResult,
    GraphCommit,
    GraphRevision,
    ReviewDecision,
    SourceDocument,
    WorkflowState,
)
from prismke.parsing import ParserRegistry
from prismke.parsing.adapters import TextParser
from prismke.persistence import FileEvidenceStore, JSONGraphStore, RunRepository
from prismke.providers import DisabledOCRProvider, DisabledVLMProvider, MockLLMProvider
from prismke.workflow import PrismKEService, PrismKEWorkflow
from prismke.workflow.nodes import WorkflowNodes


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
    await service.review(state.run_id, claim_id, ReviewDecision.APPROVE)
    completed = await service.resume(state.run_id)
    assert completed.status == "completed"
    assert completed.claims[0].status == ClaimStatus.APPROVED


@pytest.mark.asyncio
async def test_failed_node_resumes_without_repeating_parser(
    tmp_path: Path, schema_path: Path
) -> None:
    class CountingTextParser(TextParser):
        calls = 0

        async def parse(self, source: SourceDocument):  # type: ignore[no-untyped-def]
            self.calls += 1
            return await super().parse(source)

    class FlakyProvider:
        calls = 0

        def fingerprint(self) -> str:
            return stable_id("provider", "flaky")

        async def extract(self, request: ExtractionRequest) -> ExtractionResult:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("simulated provider outage")
            return await MockLLMProvider().extract(request)

    sample = tmp_path / "sample.md"
    sample.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime"
    parser = CountingTextParser()
    provider = FlakyProvider()
    runs = RunRepository(runtime / "runs")
    state = WorkflowState(
        run_id="run:recover",
        input_path=str(sample),
        schema_path=str(schema_path),
        provider_name="mock",
        provider_fingerprint=provider.fingerprint(),
    )
    runs.save(state)
    workflow = PrismKEWorkflow(
        provider,
        DisabledOCRProvider(),
        DisabledVLMProvider(),
        JSONGraphStore(runtime / "graph"),
        FileEvidenceStore(runtime / "evidence"),
        runtime / "checkpoints.sqlite3",
        runs,
        ParserRegistry([parser]),
    )
    with pytest.raises(RuntimeError, match="simulated provider outage"):
        await workflow.invoke(state)
    assert runs.load(state.run_id).failed_node == "extract_text_claims"
    recovered = await workflow.resume(state.run_id)
    assert recovered is not None
    assert recovered.status == "completed"
    assert parser.calls == 1
    assert provider.calls == 2


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


@pytest.mark.asyncio
async def test_commit_rejects_missing_evidence(tmp_path: Path) -> None:
    graph_store = JSONGraphStore(tmp_path / "graph")
    nodes = WorkflowNodes(
        MockLLMProvider(),
        DisabledOCRProvider(),
        DisabledVLMProvider(),
        graph_store,
        FileEvidenceStore(tmp_path / "evidence"),
        ParserRegistry(),
    )
    claim = Claim(
        id="claim:missing",
        subject_id="entity:missing",
        relation_id="r",
        object_literal="value",
        confidence=0.9,
        evidence_ids=["ev:missing"],
        status=ClaimStatus.AUTO_APPROVED,
    )
    revision = GraphRevision(
        id="revision:missing",
        run_id="run:missing",
        claim_ids=[claim.id],
    )
    state = WorkflowState(
        run_id="run:missing",
        input_path="missing",
        schema_path="missing",
        graph_commit=GraphCommit(claims=[claim], revision=revision),
    )
    with pytest.raises(EvidenceIntegrityError, match="invalid evidence"):
        await nodes.commit_graph(state)
