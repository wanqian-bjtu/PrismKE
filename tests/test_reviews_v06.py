import os
from pathlib import Path
from uuid import uuid4

import pytest
from test_review_workspace import paused_source

from prismke.core.ids import canonical_hash
from prismke.core.settings import Settings
from prismke.domain import ReviewDecision
from prismke.persistence import Neo4jGraphStore
from prismke.persistence.reviews import ReviewRepository
from prismke.workflow import PrismKEService


@pytest.mark.asyncio
async def test_defer_version_and_idempotency(tmp_path: Path, schema_path: Path) -> None:
    service, state = await paused_source(tmp_path / "source", schema_path)
    with pytest.raises(ValueError, match="reviewer"):
        await service.review_entity(state.run_id, "task:entity", "create")
    with pytest.raises(ValueError):
        await service.review_entity(state.run_id, "task:entity", "defer", reviewer="tester")
    state = await service.review_entity(
        state.run_id,
        "task:entity",
        "defer",
        reviewer="tester",
        comment="need evidence",
        expected_version=0,
        request_id="defer-1",
    )
    assert state.entity_review_tasks[0].version == 1
    assert state.entity_review_tasks[0].status == "pending"
    with pytest.raises(ValueError, match="pending reviews"):
        await service.resume(state.run_id)
    with pytest.raises(ValueError, match="stale"):
        await service.review_entity(
            state.run_id, "task:entity", "create", reviewer="tester", expected_version=0
        )
    await service.review_entity(
        state.run_id,
        "task:entity",
        "create",
        reviewer="tester",
        expected_version=1,
        request_id="create-1",
    )
    await service.review_entity(
        state.run_id,
        "task:entity",
        "create",
        reviewer="tester",
        expected_version=1,
        request_id="create-1",
    )
    events = service.reviews.repository.events(state.run_id)
    assert len(events) == 2 and events[1].supersedes_event_id == events[0].id
    with pytest.raises(ValueError, match="reused"):
        await service.review_entity(
            state.run_id,
            "task:entity",
            "reject",
            reviewer="tester",
            comment="exclude",
            request_id="create-1",
        )


@pytest.mark.asyncio
async def test_exclusion_retains_archive_and_can_be_corrected(
    tmp_path: Path, schema_path: Path
) -> None:
    service, state = await paused_source(tmp_path / "source", schema_path)
    before = canonical_hash(service.reviews.repository.original(state.run_id))
    state = await service.review_entity(
        state.run_id,
        "task:entity",
        "reject",
        reviewer="tester",
        comment="wrong mention",
        request_id="exclude",
    )
    assert not state.candidates and state.original_candidates
    event = service.reviews.repository.events(state.run_id)[0]
    proposal = await service.corrections.propose(
        state.run_id, event.id, "create", None, 1, "tester", "identity clarified", "restore"
    )
    assert not proposal.blocked_reasons
    with pytest.raises(ValueError, match="confirmation"):
        await service.corrections.apply(proposal.id, False)
    state = await service.corrections.apply(proposal.id, True)
    assert len(state.candidates) == 1
    state = await service.resume(state.run_id)
    assert len(state.claims) == 1 and state.status == "awaiting_review"
    assert canonical_hash(service.reviews.repository.original(state.run_id)) == before
    events = service.reviews.repository.events(state.run_id)
    assert len(events) == 2 and events[1].supersedes_event_id == event.id
    assert (await service.corrections.apply(proposal.id, True)).run_id == state.run_id


@pytest.mark.asyncio
async def test_projection_failure_restart_replays_once(tmp_path: Path, schema_path: Path) -> None:
    service, state = await paused_source(tmp_path / "source", schema_path)
    audit = service.audit.record

    # Projection writes a synchronous audit, so inject a synchronous failure.
    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("disk fault")

    service.audit.record = fail  # type: ignore[method-assign]
    with pytest.raises(OSError, match="disk fault"):
        await service.review_entity(
            state.run_id, "task:entity", "create", reviewer="tester", request_id="one"
        )
    assert len(service.reviews.repository.events(state.run_id)) == 1
    assert service.review_progress(state.run_id)["review_sync_pending"]
    assert not service.review_progress(state.run_id)["can_resume"]
    service.audit.record = audit  # type: ignore[method-assign]
    restarted = PrismKEService(Settings(_env_file=None, runtime_dir=service.settings.runtime_dir))
    await restarted.reviews.recover(state.run_id)
    await restarted.review_entity(
        state.run_id, "task:entity", "create", reviewer="tester", request_id="one"
    )
    assert len(restarted.reviews.repository.events(state.run_id)) == 1
    assert not restarted.review_progress(state.run_id)["review_sync_pending"]


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["json", "neo4j"])
async def test_committed_fact_correction_and_restore(
    tmp_path: Path, schema_path: Path, backend: str
) -> None:
    if backend == "neo4j" and os.getenv("PRISMKE_TEST_NEO4J") != "1":
        pytest.skip("dedicated Neo4j fixture required")
    service, state = await paused_source(
        tmp_path / "source", schema_path, name=f"Review-v06-{uuid4().hex}"
    )
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
    await service.review_entity(state.run_id, "task:entity", "create", reviewer="tester")
    state = await service.resume(state.run_id)
    claim_id = state.claims[0].id
    await service.review(state.run_id, claim_id, ReviewDecision.APPROVE, "tester")
    state = await service.resume(state.run_id)
    assert state.status == "completed"
    original = await service.graph_store.get_claim(claim_id)
    source = service.reviews.repository.events(state.run_id)[-1]
    proposal = await service.corrections.propose(
        state.run_id, source.id, "reject", None, 1, "tester", "fact not supported", "reject-fact"
    )
    await service.corrections.apply(proposal.id, True)
    state = await service.resume(state.run_id)
    assert state.current_node == "prepare_graph_commit" and state.pending_correction_id
    assert (await service.graph_store.get_claim(claim_id)).tx_to is None
    state = await service.confirm_review_commit(state.run_id, "tester")
    assert state.status == "completed"
    assert (await service.graph_store.get_claim(claim_id)).tx_to is not None
    assert state.revision.review_events and len(state.revision.changes) == 1
    # The confirmation event advances the task version but preserves the semantic decision.
    assert state.review_tasks[0].version == 3
    restored = await service.graph_store.rollback_revision(state.revision.id)
    assert restored.parent_id == state.revision.id
    assert (await service.graph_store.get_claim(claim_id)).model_dump() == original.model_dump()
    await service.close()


def test_repository_is_immutable(tmp_path: Path) -> None:
    repository = ReviewRepository(tmp_path / "reviews.sqlite")
    repository.archive("run:1", [{"id": "candidate:1"}])
    with pytest.raises(ValueError, match="immutable"):
        repository.archive("run:1", [])
    with repository.connect() as c, pytest.raises(Exception, match="immutable"):
        c.execute("DELETE FROM archives")


@pytest.mark.asyncio
async def test_correction_api_requires_confirm_and_preserves_events(
    tmp_path: Path, schema_path: Path
) -> None:
    from fastapi.testclient import TestClient

    from prismke.api import create_app

    service, state = await paused_source(tmp_path / "source", schema_path)
    with TestClient(create_app(service.settings, service, mount_ui=False)) as client:
        path = "/api/v1/entity-reviews/task:entity"
        assert (
            client.post(
                path, json={"run_id": state.run_id, "action": "defer", "reviewer": "tester"}
            ).status_code
            == 409
        )
        deferred = client.post(
            path,
            json={
                "run_id": state.run_id,
                "action": "defer",
                "reviewer": "tester",
                "comment": "need evidence",
                "expected_version": 0,
                "request_id": "defer",
            },
        )
        assert deferred.status_code == 200
        assert (
            client.post(
                path,
                json={
                    "run_id": state.run_id,
                    "action": "create",
                    "reviewer": "tester",
                    "expected_version": 0,
                },
            ).status_code
            == 409
        )
        assert (
            client.post(
                path,
                json={
                    "run_id": state.run_id,
                    "action": "reject",
                    "reviewer": "tester",
                    "comment": "wrong mention",
                    "expected_version": 1,
                },
            ).status_code
            == 200
        )
        events = client.get(f"/api/v1/runs/{state.run_id}/review-events").json()
        assert len(events) == 2
        proposal = client.post(
            f"/api/v1/runs/{state.run_id}/review-corrections",
            json={
                "source_event_id": events[-1]["id"],
                "action": "create",
                "expected_version": 2,
                "reviewer": "tester",
                "reason": "identity clarified",
                "request_id": "restore",
            },
        )
        assert proposal.status_code == 202
        correction_id = proposal.json()["id"]
        apply = f"/api/v1/review-corrections/{correction_id}/apply"
        assert client.post(apply, json={"confirm": False}).status_code == 422
        assert client.post(apply, json={"confirm": True}).status_code == 200
        assert client.post(apply, json={"confirm": True}).status_code == 200
        assert len(client.get(f"/api/v1/runs/{state.run_id}/review-events").json()) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("fault", ["event", "checkpoint"])
async def test_review_write_failures_are_recoverable(
    tmp_path: Path,
    schema_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    service, state = await paused_source(tmp_path / "source", schema_path)
    if fault == "event":

        def fail(*args: object) -> None:
            raise OSError("ledger fault")

        monkeypatch.setattr(service.reviews.repository, "append", fail)
    else:
        original = service.review_tail_workflow

        def workflow(payload: object) -> object:
            instance = original(payload)

            async def fail(payload: object) -> bool:
                raise OSError("checkpoint fault")

            instance.record_entity_review = fail
            return instance

        monkeypatch.setattr(service, "review_tail_workflow", workflow)
    with pytest.raises(OSError):
        await service.review_entity(
            state.run_id, "task:entity", "create", reviewer="tester", request_id="fault-1"
        )
    assert len(service.reviews.repository.events(state.run_id)) == (0 if fault == "event" else 1)
    if fault == "event":
        assert service.show_run(state.run_id).entity_review_tasks[0].status == "pending"
    monkeypatch.undo()
    await service.reviews.recover(state.run_id)
    await service.review_entity(
        state.run_id, "task:entity", "create", reviewer="tester", request_id="fault-1"
    )
    assert len(service.reviews.repository.events(state.run_id)) == 1


@pytest.mark.asyncio
async def test_correction_preview_stale_and_shared_support(
    tmp_path: Path, schema_path: Path
) -> None:
    from prismke.domain import GraphCommit, GraphRevision

    service, state = await paused_source(tmp_path / "source", schema_path)
    await service.review_entity(state.run_id, "task:entity", "create", reviewer="tester")
    state = await service.resume(state.run_id)
    await service.review(state.run_id, state.claims[0].id, ReviewDecision.APPROVE, "tester")
    state = await service.resume(state.run_id)
    source = service.reviews.repository.events(state.run_id)[-1]
    proposal = await service.corrections.propose(
        state.run_id, source.id, "reject", None, 1, "tester", "recheck", "preview"
    )
    await service.graph_store.commit(
        GraphCommit(
            revision=GraphRevision(
                id="revision:later", parent_id=state.revision.id, run_id="other-run"
            )
        )
    )
    with pytest.raises(ValueError, match="graph changed"):
        await service.corrections.apply(proposal.id, True)
    # A second run supporting the same canonical claim must block correction.
    claim = await service.graph_store.get_claim(state.claims[0].id)
    claim.source_run_ids.append("run:other")
    graph = service.graph_store.snapshot()
    graph["claims"][claim.id] = claim.model_dump(mode="json")
    service.graph_store._write_atomic(graph)
    blocked = await service.corrections.propose(
        state.run_id, source.id, "reject", None, 1, "tester", "recheck", "shared-preview"
    )
    assert any("SHARED_RUN" in r for r in blocked.blocked_reasons)
    with pytest.raises(ValueError, match="SHARED_RUN"):
        await service.corrections.apply(blocked.id, True)


@pytest.mark.asyncio
async def test_restore_fact_through_new_correction(tmp_path: Path, schema_path: Path) -> None:
    service, state = await paused_source(tmp_path / "source", schema_path)
    await service.review_entity(state.run_id, "task:entity", "create", reviewer="tester")
    state = await service.resume(state.run_id)
    await service.review(state.run_id, state.claims[0].id, ReviewDecision.APPROVE, "tester")
    state = await service.resume(state.run_id)
    source = service.reviews.repository.events(state.run_id)[-1]
    proposal = await service.corrections.propose(
        state.run_id, source.id, "reject", None, 1, "tester", "rejected", "reject"
    )
    await service.corrections.apply(proposal.id, True)
    await service.resume(state.run_id)
    state = await service.confirm_review_commit(state.run_id, "tester")
    source = next(
        e for e in reversed(service.reviews.repository.events(state.run_id)) if e.action == "reject"
    )
    proposal = await service.corrections.propose(
        state.run_id, source.id, "approve", None, 3, "tester", "new verification", "restore"
    )
    await service.corrections.apply(proposal.id, True)
    await service.resume(state.run_id)
    state = await service.confirm_review_commit(state.run_id, "tester")
    current = await service.graph_store.get_claim(state.claims[0].id)
    assert current.tx_to is None and current.status.value == "approved"
    assert len(await service.graph_store.list_revisions()) == 3


@pytest.mark.asyncio
async def test_committed_entity_exclusion_is_exact_compensation(
    tmp_path: Path, schema_path: Path
) -> None:
    service, state = await paused_source(tmp_path / "source", schema_path)
    await service.review_entity(state.run_id, "task:entity", "create", reviewer="tester")
    state = await service.resume(state.run_id)
    await service.review(state.run_id, state.claims[0].id, ReviewDecision.APPROVE, "tester")
    state = await service.resume(state.run_id)
    original_claim_id = state.claims[0].id
    source = service.reviews.repository.events(state.run_id)[0]
    proposal = await service.corrections.propose(
        state.run_id, source.id, "reject", None, 1, "tester", "wrong mention", "exclude-entity"
    )
    await service.corrections.apply(proposal.id, True)
    state = await service.resume(state.run_id)
    assert not state.claims and state.original_candidates
    state = await service.confirm_review_commit(state.run_id, "tester")
    assert (await service.graph_store.get_claim(original_claim_id)).tx_to is not None
    assert len(state.superseded_review_tasks) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["json", "neo4j"])
async def test_identity_correction_requires_new_fact_review(
    tmp_path: Path,
    schema_path: Path,
    backend: str,
) -> None:
    from prismke.domain import CanonicalEntity, EntityCandidate

    if backend == "neo4j" and os.getenv("PRISMKE_TEST_NEO4J") != "1":
        pytest.skip("dedicated Neo4j fixture required")
    service, state = await paused_source(
        tmp_path / "source", schema_path, name=f"Identity-v06-{uuid4().hex}"
    )
    target = CanonicalEntity(
        id=f"entity:alternate-{uuid4().hex}", name="Alternate System", entity_type="Software"
    )
    state.entities.append(target)
    state.entity_review_tasks[0].candidates.append(
        EntityCandidate(
            entity_id=target.id,
            retrieval_score=0.8,
            name_score=0.8,
            context_score=0.8,
            final_score=0.8,
        )
    )
    await service.review_tail_workflow(state).record_entity_review(state)
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
    await service.review_entity(state.run_id, "task:entity", "create", reviewer="tester")
    state = await service.resume(state.run_id)
    old_claim_id = state.claims[0].id
    await service.review(state.run_id, old_claim_id, ReviewDecision.APPROVE, "tester")
    state = await service.resume(state.run_id)
    source = service.reviews.repository.events(state.run_id)[0]
    proposal = await service.corrections.propose(
        state.run_id,
        source.id,
        "link",
        target.id,
        1,
        "tester",
        "identity correction",
        "link-correction",
    )
    await service.corrections.apply(proposal.id, True)
    state = await service.resume(state.run_id)
    assert state.status == "awaiting_review" and len(state.review_tasks) == 1
    assert state.review_tasks[0].status == "pending" and state.claims[0].id != old_claim_id
    with pytest.raises(ValueError):
        await service.confirm_review_commit(state.run_id, "tester")
    await service.review(state.run_id, state.claims[0].id, ReviewDecision.APPROVE, "tester")
    state = await service.resume(state.run_id)
    assert state.current_node == "prepare_graph_commit"
    state = await service.confirm_review_commit(state.run_id, "tester")
    assert (await service.graph_store.get_claim(old_claim_id)).tx_to is not None
    assert (await service.graph_store.get_claim(state.claims[0].id)).subject_id == target.id
    await service.graph_store.rollback_revision(state.revision.id)
    assert (await service.graph_store.get_claim(old_claim_id)).tx_to is None
    assert (await service.graph_store.get_claim(state.claims[0].id)).tx_to is not None
    await service.close()


@pytest.mark.asyncio
async def test_compensation_failure_replays_same_revision(
    tmp_path: Path,
    schema_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, state = await paused_source(tmp_path / "source", schema_path)
    await service.review_entity(state.run_id, "task:entity", "create", reviewer="tester")
    state = await service.resume(state.run_id)
    await service.review(state.run_id, state.claims[0].id, ReviewDecision.APPROVE, "tester")
    state = await service.resume(state.run_id)
    graph_before = service.graph_store.path.read_bytes()
    source = service.reviews.repository.events(state.run_id)[-1]
    proposal = await service.corrections.propose(
        state.run_id, source.id, "reject", None, 1, "tester", "unsupported", "failure"
    )
    await service.corrections.apply(proposal.id, True)
    await service.resume(state.run_id)

    async def fail(payload: object) -> None:
        raise OSError("graph write fault")

    monkeypatch.setattr(service.graph_store, "commit", fail)
    with pytest.raises(OSError):
        await service.confirm_review_commit(state.run_id, "tester")
    assert service.graph_store.path.read_bytes() == graph_before
    assert service.review_progress(state.run_id)["review_sync_pending"]
    monkeypatch.undo()
    restarted = PrismKEService(Settings(_env_file=None, runtime_dir=service.settings.runtime_dir))
    await restarted.reviews.recover(state.run_id)
    await restarted.reviews.recover(state.run_id)
    assert len(await restarted.graph_store.list_revisions()) == 2
    assert (await restarted.graph_store.get_claim(state.claims[0].id)).tx_to is not None
