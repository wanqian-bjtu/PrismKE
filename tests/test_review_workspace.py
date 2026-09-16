from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock

import orjson
import pytest
from fastapi.testclient import TestClient

from prismke.api import create_app
from prismke.core.ids import file_sha256
from prismke.core.settings import Settings
from prismke.domain import EntityCandidate, EntityReviewTask, ReviewDecision, WorkflowState
from prismke.persistence import Neo4jGraphStore
from prismke.providers import DisabledOCRProvider, DisabledVLMProvider, MockLLMProvider
from prismke.web.review import ReviewController
from prismke.workflow import PrismKEService
from prismke.workflow.review_details import risk_flags
from prismke.workflow.review_workspace import import_review_run


async def paused_source(
    root: Path,
    schema_path: Path,
    conflict: bool = False,
) -> tuple[PrismKEService, WorkflowState]:
    root.mkdir()
    document = root / "sample.md"
    if conflict:
        schema_path = root / "schema.yaml"
        schema_path.write_text(
            "schema_id: conflict\nversion: '1'\nstrict: true\n"
            "entity_types:\n  - id: Software\n  - id: Organization\n"
            "relations:\n  - id: developed_by\n    functional: true\n"
            "    domain: [Software]\n    range: [Organization]\n",
            encoding="utf-8",
        )
    document.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.70\n"
        + (
            "PrismKE | developed_by | Anthropic | Software | Organization | 0.70\n"
            if conflict
            else ""
        ),
        encoding="utf-8",
    )
    service = PrismKEService(
        Settings(_env_file=None, runtime_dir=root, embedding_provider="disabled")
    )
    state = await service.run(document, schema_path, "mock")
    mention = state.candidates[0].subject
    state.current_node = "resolve_entities"
    state.claims, state.review_tasks = [], []
    state.provider_fingerprint = "evaluation-only:original-text"
    state.vlm_provider_fingerprint = "evaluation-only:original-visual"
    state.entity_review_tasks = [
        EntityReviewTask(
            id="task:entity",
            run_id=state.run_id,
            mention_id=mention.id,
            task_type="link",
            proposed_entity_id=state.mention_to_entity[mention.id],
            candidates=[
                EntityCandidate(
                    entity_id=state.mention_to_entity[mention.id],
                    retrieval_score=0.8,
                    name_score=0.8,
                    context_score=0.8,
                    final_score=0.8,
                )
            ],
            reasons=["cross_language_duplicate_protection"],
        )
    ]
    workflow = service._workflow(
        MockLLMProvider(), DisabledOCRProvider(), DisabledVLMProvider(), False
    )
    assert await workflow.record_entity_review(state)
    return service, state


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["json", "neo4j"])
async def test_import_review_resume_preview_commit_and_rollback(
    tmp_path: Path,
    schema_path: Path,
    backend: str,
) -> None:
    if backend == "neo4j" and os.getenv("PRISMKE_TEST_NEO4J") != "1":
        pytest.skip("live review loop requires a dedicated Neo4j test instance")
    source, old = await paused_source(tmp_path / "source", schema_path)
    original_hash = file_sha256(source.runs._target(old.run_id))
    graph_hash = file_sha256(source.graph_store.path)  # type: ignore[attr-defined]
    target = tmp_path / "review"
    state = await import_review_run(source.settings.runtime_dir, old.run_id, target)
    store = None
    if backend == "neo4j":
        settings = Settings()
        store = Neo4jGraphStore(
            settings.neo4j_uri,
            settings.neo4j_user,
            settings.neo4j_password or "test",
            settings.neo4j_database,
        )
    service = PrismKEService(Settings(_env_file=None, runtime_dir=target), graph_store=store)
    starting_claim_ids = {claim.id for claim in await service.graph_store.list_claims()}
    starting_revisions = len(await service.graph_store.list_revisions())
    service.provider = lambda _: (_ for _ in ()).throw(AssertionError("LLM constructed"))  # type: ignore[method-assign]
    service.ocr_provider = lambda _: (_ for _ in ()).throw(AssertionError("OCR constructed"))  # type: ignore[method-assign]
    service.vlm_provider = lambda _: (_ for _ in ()).throw(AssertionError("VLM constructed"))  # type: ignore[method-assign]
    assert len(state.entity_review_tasks) == 1
    with pytest.raises(ValueError, match="pending reviews"):
        await service.resume(state.run_id)
    with pytest.raises(ValueError, match="reviewer is required"):
        await service.review_entity(state.run_id, "task:entity", "create")
    detail = await service.entity_review_detail(state.run_id, "task:entity")
    assert detail["mention"]["name"] == "PrismKE"
    assert detail["risk_flags"]
    controller = ReviewController(service)
    assert len(await controller.queue(state.run_id, "entity", "pending", "flagged")) == 1
    text, preview = await controller.evidence(state.run_id, state.document.evidence[0].id)  # type: ignore[union-attr]
    assert "PrismKE" in text and preview is None
    await service.review_entity(
        state.run_id, "task:entity", "create", reviewer="tester", comment="source checked"
    )
    with pytest.raises(ValueError, match="already been resolved"):
        await service.review_entity(state.run_id, "task:entity", "reject", reviewer="tester")
    state = await service.resume(state.run_id)
    assert state.status == "awaiting_review"
    task = state.review_tasks[0]
    await service.review(state.run_id, task.claim_id, ReviewDecision.APPROVE, "tester", "checked")
    with pytest.raises(ValueError, match="already been resolved"):
        await service.review(state.run_id, task.claim_id, ReviewDecision.REJECT)
    state = await service.resume(state.run_id)
    assert state.current_node == "prepare_graph_commit"
    assert {claim.id for claim in await service.graph_store.list_claims()} == starting_claim_ids
    assert service.review_progress(state.run_id)["can_commit"]
    state = await service.confirm_review_commit(state.run_id, "tester")
    assert state.status == "completed"
    assert state.graph_commit is not None
    assert await service.graph_store.get_claim(state.graph_commit.claims[0].id) is not None
    with pytest.raises(ValueError):
        await service.confirm_review_commit(state.run_id, "tester")
    assert state.revision is not None
    compensation = await service.graph_store.rollback_revision(state.revision.id)
    assert (await service.graph_store.get_claim(task.claim_id)).tx_to is not None  # type: ignore[union-attr]
    assert len(await service.graph_store.list_revisions()) == starting_revisions + 2
    assert (await service.graph_store.diff_revisions(state.revision.id, compensation.id)).changes
    assert file_sha256(source.runs._target(old.run_id)) == original_hash
    assert file_sha256(source.graph_store.path) == graph_hash  # type: ignore[attr-defined]
    assert state.provider_calls == old.provider_calls
    assert '"reviewer":"tester"' in service.settings.audit_path.read_text(encoding="utf-8").replace(
        " ", ""
    )
    await service.close()


@pytest.mark.asyncio
async def test_conflict_review_keeps_peer_independent(tmp_path: Path, schema_path: Path) -> None:
    source, state = await paused_source(tmp_path / "source", schema_path, conflict=True)
    target = tmp_path / "review"
    await import_review_run(source.settings.runtime_dir, state.run_id, target)
    service = PrismKEService(Settings(_env_file=None, runtime_dir=target))
    await service.review_entity(state.run_id, "task:entity", "create", reviewer="tester")
    state = await service.resume(state.run_id)
    assert len(state.conflicts) == 1 and len(state.claims) == 2
    first, second = state.review_tasks
    detail = service.claim_review_detail(state.run_id, first.id)
    assert len(detail["conflict_peers"]) == 1
    await service.review(state.run_id, first.claim_id, ReviewDecision.APPROVE, "tester")
    assert service.show_run(state.run_id).review_tasks[1].status == "pending"
    with pytest.raises(ValueError, match="pending reviews"):
        await service.resume(state.run_id)
    await service.review(state.run_id, second.claim_id, ReviewDecision.REJECT, "tester")
    state = await service.resume(state.run_id)
    assert state.graph_commit is not None and len(state.graph_commit.claims) == 1
    assert not await service.graph_store.list_claims()


@pytest.mark.asyncio
async def test_import_rejects_overwrite_tampering_and_wrong_pause(
    tmp_path: Path,
    schema_path: Path,
) -> None:
    source, state = await paused_source(tmp_path / "source", schema_path)
    target = tmp_path / "review"
    target.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        await import_review_run(source.settings.runtime_dir, state.run_id, target)
    ref = state.document.evidence[0]  # type: ignore[union-attr]
    source.evidence_store._blob_path(ref.source_hash).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="invalid source evidence"):
        await import_review_run(source.settings.runtime_dir, state.run_id, tmp_path / "tampered")
    assert not (tmp_path / "tampered").exists()


@pytest.mark.asyncio
async def test_review_api_details_auth_and_no_extraction(
    tmp_path: Path,
    schema_path: Path,
) -> None:
    source, state = await paused_source(tmp_path / "source", schema_path)
    target = tmp_path / "review"
    await import_review_run(source.settings.runtime_dir, state.run_id, target)
    settings = Settings(_env_file=None, runtime_dir=target, api_token="test-token")
    with TestClient(create_app(settings, mount_ui=False)) as client:
        assert client.get("/api/v1/runs").status_code == 401
        client.headers["Authorization"] = "Bearer test-token"
        assert client.get("/api/v1/runs").json()[0]["entity_pending"] == 1
        assert (
            client.get(f"/api/v1/runs/{state.run_id}/entity-reviews/task:entity").status_code == 200
        )
        assert client.post(f"/api/v1/runs/{state.run_id}/resume").status_code == 409
        response = client.post(
            "/api/v1/entity-reviews/task:entity",
            json={
                "run_id": state.run_id,
                "action": "create",
                "reviewer": "tester",
            },
        )
        assert response.status_code == 200
        assert (
            client.post(
                "/api/v1/entity-reviews/task:entity",
                json={
                    "run_id": state.run_id,
                    "action": "reject",
                    "reviewer": "tester",
                },
            ).status_code
            == 409
        )
        assert client.post(f"/api/v1/runs/{state.run_id}/resume").status_code == 202
        claim_task = client.get(f"/api/v1/runs/{state.run_id}").json()["review_tasks"][0]
        assert (
            client.get(f"/api/v1/runs/{state.run_id}/reviews/{claim_task['id']}").status_code == 200
        )


def test_risk_flags_are_hints_not_aliases() -> None:
    assert risk_flags(["p1", "o5"], ["authored_by"], ["cross_language_match"])
    assert not risk_flags(["OpenAI"], ["supports"], [])


@pytest.mark.asyncio
async def test_evidence_failure_is_explicit(tmp_path: Path) -> None:
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path))
    text, image = await ReviewController(service).evidence("missing", "missing")
    assert "证据读取失败" in text and image is None


@pytest.mark.asyncio
async def test_import_rejects_checkpoint_and_provenance_changes(
    tmp_path: Path,
    schema_path: Path,
) -> None:
    source, state = await paused_source(tmp_path / "source", schema_path)
    state.current_node = "run_ocr"
    source.runs.save(state)
    with pytest.raises(ValueError, match="completed extraction"):
        await import_review_run(source.settings.runtime_dir, state.run_id, tmp_path / "bad")
    state.current_node = "resolve_entities"
    state.warnings.append("summary changed without checkpoint")
    source.runs.save(state)
    with pytest.raises(ValueError, match="checkpoint does not match"):
        await import_review_run(source.settings.runtime_dir, state.run_id, tmp_path / "bad2")
    assert not (tmp_path / "bad2").exists()


@pytest.mark.asyncio
async def test_commit_failure_preserves_isolated_graph(
    tmp_path: Path,
    schema_path: Path,
) -> None:
    source, state = await paused_source(tmp_path / "source", schema_path)
    target = tmp_path / "review"
    await import_review_run(source.settings.runtime_dir, state.run_id, target)
    service = PrismKEService(Settings(_env_file=None, runtime_dir=target))
    await service.review_entity(state.run_id, "task:entity", "create", reviewer="tester")
    state = await service.resume(state.run_id)
    await service.review(
        state.run_id, state.review_tasks[0].claim_id, ReviewDecision.APPROVE, "tester"
    )
    await service.close()
    await service.resume(state.run_id)
    path = target / "graph" / "graph.json"
    before = path.read_bytes()
    original_commit = service.graph_store.commit
    service.graph_store.commit = AsyncMock(side_effect=RuntimeError("transaction failed"))  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="transaction failed"):
        await service.confirm_review_commit(state.run_id, "tester")
    assert path.read_bytes() == before
    assert service.show_run(state.run_id).status == "failed"
    assert not orjson.loads(path.read_bytes())["claims"]
    service.graph_store.commit = original_commit  # type: ignore[method-assign]
    assert (await service.confirm_review_commit(state.run_id, "tester")).status == "completed"
