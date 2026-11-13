"""Candidate approval preserves schema/evidence guards and downstream review."""

from pathlib import Path

import httpx
import pytest

from frontend.i18n import tr
from frontend.validation import ACTION_CHOICES, _preview_comparison
from src.core.settings import Settings
from src.domain import SchemaIndex, TaskMode, ValidationResult
from src.governance.validation import ValidationService
from src.governance.validation.actions import APPROVAL_REQUIRED, candidate_actions
from src.providers import OpenAICompatibleLLMProvider, OpenAICompatibleVLMProvider
from src.workflow import PrismKEService


async def invalid_run(tmp_path: Path, schema_path: Path, subject_type: str = "Software"):
    source = tmp_path / "source.md"
    source.write_text(
        f"PrismKE | unknown | OpenAI | {subject_type} | Organization | 0.95",
        encoding="utf-8",
    )
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    state = await service.run(
        source, schema_path, "mock",
        task_mode=TaskMode.JOINT_ENTITY_RELATION_DISAMBIGUATION,
    )
    return service, state


@pytest.mark.asyncio
async def test_unknown_relation_repair_approve_restart_and_resume(tmp_path, schema_path):
    service, state = await invalid_run(tmp_path, schema_path)
    try:
        ids = [item.id for item in state.validation.issues if item.status == "open"]
        # Simulate a historical checkpoint with the old exclude-only action list.
        for item in state.validation.issues:
            item.allowed_actions = ["exclude"]
        service.runs.save(state)
        report = await service.validate_run(state.run_id)
        assert {"replace_relation", "approve", "defer"} <= set(report.issues[0].allowed_actions)
        preview = await service.preview_validation_correction(state.run_id, ids, "approve", {}, 0)
        assert not preview["can_apply"]
        assert preview["remaining_issues"][0]["code"] == "UNKNOWN_RELATION"
        assert "UNKNOWN_RELATION" in _preview_comparison(preview, "zh-CN")
        with pytest.raises(ValueError, match="still violates"):
            await service.apply_validation_correction(
                state.run_id, ids, "approve", {}, "tester", "checked", "invalid-pass", 0
            )
        fixed = await service.apply_validation_correction(
            state.run_id, ids, "replace_relation", {"relation": "developed_by"},
            "tester", "correct relation", "fix-1", 0,
        )
        assert fixed.status == "awaiting_review"
        assert fixed.validation.blocking_count == 1
        assert fixed.candidates[0].id != state.candidates[0].id
        assert await service.graph_store.list_claims() == []
        pending = [i for i in fixed.validation.issues if i.status == "open"]
        assert len(pending) == 1 and pending[0].code == APPROVAL_REQUIRED
        pending_ids = [pending[0].id]
        with pytest.raises(ValueError, match="stale"):
            await service.preview_validation_correction(state.run_id, pending_ids, "approve", {}, 0)
        args = (state.run_id, pending_ids, "approve", {}, "tester", "verified", "pass-1", 1)
        approved = await service.apply_validation_correction(*args)
        assert approved.validation.blocking_count == 0
        assert approved.candidates == fixed.candidates
        assert approved.validation_corrections[-1].action == "approve"
        event = approved.validation_corrections[-1]
        assert event.before == event.after
        repeated = await service.apply_validation_correction(*args)
        assert repeated.validation_version == 2
        assert len(repeated.validation_corrections) == 2
        assert await service.graph_store.list_claims() == []
        await service.close()
        service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
        refreshed = await service.validate_run(state.run_id)
        assert refreshed.blocking_count == 0
        assert any(i.status == "approved" for i in refreshed.issues)
        resumed = await service.resume(state.run_id)
        assert resumed.validation.blocking_count == 0
        assert resumed.candidates[0].relation == "developed_by"
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_type_policy_literal_endpoint_and_evidence_guards(tmp_path, schema_path):
    service, state = await invalid_run(tmp_path, schema_path)
    try:
        candidate = state.candidates[0]
        candidate.subject.entity_type = "Mystery"
        candidate.relation = "developed_by"
        state.validation = ValidationResult(issues=await ValidationService().candidates(
            [candidate], SchemaIndex(state.output_schema), state.document, service.evidence_store
        ))
        state.validation = ValidationService.merge(state.validation, [])
        service.runs.save(state)
        issue = next(i for i in state.validation.issues if i.code == "UNKNOWN_ENTITY_TYPE")
        assert "replace_entity_type" in candidate_actions(candidate, [issue])
        literal = candidate.model_copy(update={"object": "literal"})
        domain = issue.model_copy(update={"code": "SCHEMA_DOMAIN_RANGE"})
        assert "swap_endpoints" not in candidate_actions(literal, [domain])
        evidence = issue.model_copy(update={"code": "CORRUPT_EVIDENCE", "stage": "evidence"})
        assert candidate_actions(candidate, [issue, evidence]) == ["approve", "exclude", "defer"]
        # A forged persisted whitelist must never enable unrelated repair actions.
        evidence.allowed_actions = ["replace_relation", "approve"]
        assert "replace_relation" not in candidate_actions(candidate, [evidence])
        fixed = await service.apply_validation_correction(
            state.run_id, [i.id for i in state.validation.issues], "replace_entity_type",
            {"endpoint": "subject", "entity_type": "Software"}, "tester",
            "correct type", "type-fix", 0,
        )
        assert fixed.candidates[0].subject.entity_type == "Software"
        assert fixed.validation.blocking_count == 1
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_evidence_changed_after_preview_prevents_approval(tmp_path, schema_path):
    service, state = await invalid_run(tmp_path, schema_path)
    try:
        ids = [i.id for i in state.validation.issues if i.status == "open"]
        fixed = await service.apply_validation_correction(
            state.run_id, ids, "replace_relation", {"relation": "developed_by"},
            "tester", "fix", "fix-1", 0,
        )
        pending_ids = [i.id for i in fixed.validation.issues if i.status == "open"]
        preview = await service.preview_validation_correction(
            state.run_id, pending_ids, "approve", {}, 1
        )
        assert preview["can_apply"]
        ref = fixed.document.evidence[0]
        service.evidence_store._blob_path(ref.source_hash).write_bytes(b"tampered")
        with pytest.raises(ValueError, match="still violates"):
            await service.apply_validation_correction(
                state.run_id, pending_ids, "approve", {}, "tester", "checked", "pass-1", 1
            )
        assert service.show_run(state.run_id).validation_version == 1
        assert await service.graph_store.list_claims() == []
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_model_requests_use_600_seconds(monkeypatch, tmp_path):
    monkeypatch.delenv("PRISMKE_REQUEST_TIMEOUT", raising=False)
    monkeypatch.delenv("PRISMKE_VLM_TIMEOUT", raising=False)
    settings = Settings(_env_file=None, runtime_dir=tmp_path)
    assert settings.request_timeout == settings.vlm_timeout == 600
    observed = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request.extensions["timeout"])
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    for provider_type in (OpenAICompatibleLLMProvider, OpenAICompatibleVLMProvider):
        provider = provider_type("https://example.test/v1", "test", "mock",
                                 transport=httpx.MockTransport(handler))
        await provider._post({"model": "mock", "messages": []}, "timeout-test")
    assert len(observed) == 2
    assert all(all(value == 600 for value in timeout.values()) for timeout in observed)
    assert ("审核通过", "approve") in ACTION_CHOICES
    assert tr("审核通过", "en") == "Approve validation"


def test_approved_issue_reopens_when_validation_fails_again():
    issue = ValidationService.issue(
        "UNKNOWN_RELATION", "schema", "candidate", "c1", "relation", "x"
    )
    issue.status = "approved"
    fresh = issue.model_copy(update={"status": "open"})
    report = ValidationService.merge(ValidationResult(issues=[issue]), [fresh])
    assert report.blocking_count == 1 and report.issues[0].status == "open"
