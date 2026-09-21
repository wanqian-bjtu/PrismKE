from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prismke.api import create_app
from prismke.core.settings import Settings
from prismke.domain import (
    CandidateClaim,
    CaseRecord,
    CaseStatusEvent,
    DocumentIR,
    EntityMention,
    EntityTypeDef,
    EvidenceKind,
    EvidenceRef,
    Modality,
    OutputSchema,
    ReflectionResult,
    RelationDef,
    ReviewEvent,
    WorkflowState,
)
from prismke.evaluation import evaluate_reflection_manifest
from prismke.persistence import CaseRepository
from prismke.providers import MockEmbeddingProvider, MockReflectionProvider
from prismke.workflow import PrismKEService
from prismke.workflow.cases import CaseRetriever, CaseService
from prismke.workflow.reflection import BoundedReflectionService


class MemoryEvidenceStore:
    def __init__(self, evidence: EvidenceRef) -> None:
        self.evidence = evidence

    async def exists(self, evidence_id: str) -> bool:
        return evidence_id == self.evidence.id

    async def verify(self, evidence_id: str) -> bool:
        return evidence_id == self.evidence.id

    async def get(self, evidence_id: str) -> EvidenceRef:
        if evidence_id != self.evidence.id:
            raise KeyError(evidence_id)
        return self.evidence


def schema() -> OutputSchema:
    return OutputSchema(
        schema_id="case-test",
        version="1",
        entity_types=[EntityTypeDef(id="Thing")],
        relations=[RelationDef(id="related_to")],
    )


def candidate(relation: str = "related_to") -> CandidateClaim:
    return CandidateClaim(
        id="candidate:one",
        subject=EntityMention(
            id="mention:one",
            name="PrismKE",
            entity_type="Thing",
            context="research system",
            evidence_ids=["evidence:one"],
        ),
        relation=relation,
        object="knowledge graph",
        confidence=0.8,
        evidence_ids=["evidence:one"],
    )


def evidence() -> EvidenceRef:
    return EvidenceRef(
        id="evidence:one",
        kind=EvidenceKind.TEXT_SPAN,
        document_id="document:one",
        source_hash="hash:one",
        modality=Modality.TEXT,
    )


def workflow_state(relation: str = "related_to") -> WorkflowState:
    ref = evidence()
    item = candidate(relation)
    return WorkflowState(
        run_id="run:v09",
        input_path="document.txt",
        schema_path="schema.yaml",
        pipeline_version="0.9.0",
        output_schema=schema(),
        document=DocumentIR(
            id="document:one",
            source_path="document.txt",
            source_hash="hash:one",
            media_type="text/plain",
            evidence=[ref],
        ),
        candidates=[item],
        original_candidates=[item],
        reflection_enabled=True,
        reflection_provider_name="mock",
        reflection_provider_fingerprint="reflection:mock:v1",
        reflection_policy_version="bounded-reflection-v1",
        reflection_max_attempts=2,
        reflection_token_budget=20_000,
        reflection_time_budget_seconds=180,
    )


def review_event(*, event_id: str = "event:one", reason: str = "confirmed") -> ReviewEvent:
    return ReviewEvent(
        id=event_id,
        request_id=event_id,
        run_id="run:v09",
        task_id="task:one",
        kind="entity",
        action="create",
        version=1,
        reviewer="researcher",
        reason=reason,
        before={"mention_id": "mention:one"},
        after={"mention_id": "mention:one"},
    )


@pytest.mark.asyncio
async def test_case_projection_requires_reason_and_verified_evidence(tmp_path: Path) -> None:
    repository = CaseRepository(tmp_path / "cases.sqlite")
    service = CaseService(repository, MemoryEvidenceStore(evidence()))
    state = workflow_state()

    assert await service.project_review_event(review_event(reason=""), state) is None
    created = await service.project_review_event(review_event(event_id="event:two"), state)

    assert created is not None
    assert created.case_type == "good"
    assert repository.by_source_event("event:two") == created
    assert await service.project_review_event(review_event(event_id="event:two"), state) == created


@pytest.mark.asyncio
async def test_case_snapshot_can_retrieve_case_disabled_after_run_creation(
    tmp_path: Path,
) -> None:
    repository = CaseRepository(tmp_path / "cases.sqlite")
    first = CaseRecord(
        id="case:first",
        run_id="run:one",
        case_type="good",
        task_type="claim",
        schema_fingerprint="schema:one",
        language="en",
        input_summary="PrismKE related knowledge graph",
        candidate_snapshot={},
        decision="approve",
        reasons=["verified"],
        evidence_ids=["evidence:one"],
        source_review_event_id="event:first",
    )
    second = first.model_copy(
        update={"id": "case:second", "source_review_event_id": "event:second"}
    )
    repository.add(first)
    repository.add(second)
    retriever = CaseRetriever(repository, MockEmbeddingProvider())
    snapshot = retriever.snapshot_ids()
    repository.disable(
        CaseStatusEvent(
            id="status:first",
            case_id=first.id,
            action="disable",
            operator="researcher",
            reason="superseded",
        )
    )

    results = await retriever.retrieve(
        "PrismKE knowledge graph",
        task_type="claim",
        schema_fingerprint="schema:one",
        language="en",
        top_k=5,
        allowed_case_ids=set(snapshot),
    )

    assert {item.case_id for item in results} == {"case:first", "case:second"}
    assert retriever.fingerprint_for(snapshot) != retriever.snapshot_fingerprint()


@pytest.mark.asyncio
async def test_reflection_repairs_candidate_and_preserves_evidence() -> None:
    state = workflow_state("unknown_relation")

    def repair(request: object) -> CandidateClaim:
        original = request.candidate
        return original.model_copy(update={"relation": "related_to"})

    result = await BoundedReflectionService(
        MockReflectionProvider(repair),
        None,
        MemoryEvidenceStore(evidence()),
    ).run(state)

    assert result.candidates[0].relation == "related_to"
    assert result.candidates[0].evidence_ids == ["evidence:one"]
    assert result.reflection_attempts[0].status == "succeeded"
    assert result.validation.blocking_count == 0
    assert result.repaired_issue_ids


@pytest.mark.asyncio
async def test_reflection_unknown_usage_stops_without_replacing_candidate() -> None:
    state = workflow_state("unknown_relation")

    class UnknownUsageProvider:
        def fingerprint(self) -> str:
            return "reflection:test:unknown"

        async def reflect(self, request: object) -> ReflectionResult:
            original = request.candidate
            return ReflectionResult(
                candidate=original.model_copy(update={"relation": "related_to"})
            )

    result = await BoundedReflectionService(
        UnknownUsageProvider(),  # type: ignore[arg-type]
        None,
        MemoryEvidenceStore(evidence()),
    ).run(state)

    assert result.candidates[0].relation == "unknown_relation"
    assert len(result.reflection_attempts) == 1
    assert result.reflection_attempts[0].status == "unknown_usage"
    assert "reflection_unknown_usage:candidate:one" in result.warnings


@pytest.mark.asyncio
async def test_reflection_never_exceeds_two_attempts() -> None:
    state = workflow_state("unknown_relation")
    result = await BoundedReflectionService(
        MockReflectionProvider(),
        None,
        MemoryEvidenceStore(evidence()),
    ).run(state)

    assert len(result.reflection_attempts) == 2
    assert all(item.status == "rejected_by_validation" for item in result.reflection_attempts)
    assert result.candidates[0].relation == "unknown_relation"


def test_case_api_lists_details_disables_and_reports_index(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        embedding_provider="mock",
    )
    service = PrismKEService(settings)
    record = CaseRecord(
        id="case:api",
        run_id="run:api",
        case_type="bad",
        task_type="claim",
        schema_fingerprint="schema:api",
        language="zh",
        input_summary="错误关系示例",
        candidate_snapshot={},
        decision="reject",
        reasons=["关系不成立"],
        evidence_ids=["evidence:api"],
        source_review_event_id="event:api",
    )
    service.case_repository.add(record)
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        listing = client.get("/api/v1/cases").json()
        assert listing[0]["id"] == record.id
        assert "vector" not in str(listing)
        assert client.get(f"/api/v1/cases/{record.id}").status_code == 200
        index = client.post("/api/v1/cases/rebuild-index", json={"dry_run": True})
        assert index.status_code == 200 and index.json()["stale_cases"] == 1
        disabled = client.post(
            f"/api/v1/cases/{record.id}/disable",
            json={
                "operator": "researcher",
                "reason": "superseded",
                "request_id": "disable-api",
            },
        )
        assert disabled.status_code == 200 and not disabled.json()["active"]


def test_run_identity_changes_when_case_snapshot_changes(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        embedding_provider="mock",
    )
    service = PrismKEService(settings)
    document = tmp_path / "document.txt"
    document.write_text("PrismKE", encoding="utf-8")
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(schema().model_dump_json(), encoding="utf-8")
    before, _ = service.create_run(document, schema_path, "mock", case_mode="good")
    service.case_repository.add(
        CaseRecord(
            id="case:new",
            run_id="run:reviewed",
            case_type="good",
            task_type="claim",
            schema_fingerprint="schema:new",
            language="en",
            input_summary="PrismKE",
            candidate_snapshot={},
            decision="approve",
            reasons=["verified"],
            evidence_ids=["evidence:new"],
            source_review_event_id="event:new",
        )
    )
    after, _ = service.create_run(document, schema_path, "mock", case_mode="good")

    assert before.run_id != after.run_id
    assert before.case_snapshot_ids == []
    assert after.case_snapshot_ids == ["case:new"]


@pytest.mark.asyncio
async def test_reflection_evaluation_builds_complete_nine_cell_matrix(tmp_path: Path) -> None:
    manifest = Path(__file__).parents[1] / "examples" / "eval_v0_9" / "manifest.json"
    report = await evaluate_reflection_manifest(
        manifest,
        tmp_path / "evaluation",
        settings=Settings(_env_file=None, runtime_dir=tmp_path / "runtime"),
        reflection_provider_name="mock",
        embedding_provider_name="mock",
        token_limit=10_000,
        stop_at=9_000,
    )

    assert len(report["configurations"]) == 9
    assert all(len(item["samples"]) == 12 for item in report["configurations"])
    assert report["metrics"]["max_attempts_per_candidate"] == 2
    assert report["metrics"]["token_usage"] == 0
    assert report["publish_ready"] is False


@pytest.mark.asyncio
async def test_reflection_evaluation_rejects_invalid_budget(tmp_path: Path) -> None:
    manifest = Path(__file__).parents[1] / "examples" / "eval_v0_9" / "manifest.json"
    with pytest.raises(ValueError, match="budget"):
        await evaluate_reflection_manifest(
            manifest,
            tmp_path / "evaluation",
            token_limit=100,
            stop_at=100,
        )
