from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import orjson
from fastapi.testclient import TestClient

from src.api import create_app
from src.core.settings import Settings
from src.domain import RequestReconciliation
from src.domain.execution import ExecutionTask
from src.workflow import PrismKEService


def fixture(tmp_path: Path, schema_path: Path) -> tuple[PrismKEService, str]:
    sample = tmp_path / "sample.md"
    sample.write_text(
        "WorkspaceDemo | developed_by | TestOrg | Software | Organization | 0.92\n"
    )
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    state, created = service.create_run(sample, schema_path, "mock")
    assert created
    return service, state.run_id


def interrupt_with_unknown_request(service: PrismKEService, run_id: str) -> int:
    repository = service.executions.repository
    repository.begin_request(
        run_id,
        "request-1",
        {"node": "extract_visual_claims", "asset_id": "asset-1"},
    )
    repository.finish_request(run_id, "request-1", "unknown", usage_known=False)

    def fail(task: ExecutionTask) -> None:
        task.status = "failed"
        task.reason = "UNKNOWN_PROVIDER_REQUEST"

    return repository.change(run_id, fail).version


def test_reconciliation_is_versioned_audited_and_controls_retry(
    tmp_path: Path, schema_path: Path
) -> None:
    service, run_id = fixture(tmp_path, schema_path)
    version = interrupt_with_unknown_request(service, run_id)
    result = service.executions.reconcile_request(
        run_id,
        RequestReconciliation(
            request_id="request-1",
            outcome="confirmed_not_billed",
            operator="tester",
            reason="provider console has no matching charge",
            expected_execution_version=version,
        ),
    )
    assert result["event"]["sequence"] == 1
    assert result["requests"][0]["status"] == "retryable"
    assert service.executions.repository.unknown(run_id) == 0
    assert service.executions.repository.reconciliations(run_id)[0].operator == "tester"

    with service.executions.repository.connect() as db:
        try:
            db.execute("DELETE FROM request_reconciliations")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("reconciliation events must be immutable")


def test_possibly_billed_request_remains_blocked(tmp_path: Path, schema_path: Path) -> None:
    service, run_id = fixture(tmp_path, schema_path)
    version = interrupt_with_unknown_request(service, run_id)
    service.executions.reconcile_request(
        run_id,
        RequestReconciliation(
            request_id="request-1",
            outcome="possibly_billed",
            operator="tester",
            reason="response was lost after dispatch",
            expected_execution_version=version,
        ),
    )
    assert service.executions.repository.unknown(run_id) == 1
    assert service.executions.repository.requests(run_id)[0]["status"] == "unknown"


def test_workspace_and_reconciliation_api(tmp_path: Path, schema_path: Path) -> None:
    service, run_id = fixture(tmp_path, schema_path)
    version = interrupt_with_unknown_request(service, run_id)
    with TestClient(create_app(service.settings, service, mount_ui=False)) as client:
        summary = client.get("/api/v1/workspace/summary")
        assert summary.status_code == 200
        assert summary.json()["run_counts"]["failed"] == 1
        assert client.get(f"/api/v1/runs/{run_id}/branch-progress").status_code == 200
        response = client.post(
            f"/api/v1/runs/{run_id}/requests/request-1/reconcile",
            json={
                "request_id": "request-1",
                "outcome": "confirmed_not_sent",
                "operator": "tester",
                "reason": "verified before network dispatch",
                "expected_execution_version": version,
            },
        )
        assert response.status_code == 200
        assert response.json()["requests"][0]["status"] == "retryable"
        stale = client.post(
            f"/api/v1/runs/{run_id}/requests/request-1/reconcile",
            json={
                "request_id": "request-1",
                "outcome": "confirmed_not_sent",
                "operator": "tester",
                "reason": "duplicate stale decision",
                "expected_execution_version": version,
            },
        )
        assert stale.status_code == 409


def test_runtime_settings_are_redacted_and_persisted_privately(tmp_path: Path) -> None:
    secret = "sk-private-runtime-value"
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        response = client.patch(
            "/api/v1/settings",
            json={
                "values": {
                    "llm_model": "qwen-test",
                    "llm_api_key": secret,
                },
                "operator": "tester",
            },
        )
        assert response.status_code == 200
        assert response.json()["settings"]["llm_api_key"] is True
        public = client.get("/api/v1/settings").json()
        assert public["llm_model"] == "qwen-test"
        assert public["llm_api_key"] is True
        assert secret not in orjson.dumps(public).decode()

    private_path = settings.runtime_dir / "config" / "overrides.json"
    assert secret in private_path.read_text()
    restarted = PrismKEService(Settings(_env_file=None, runtime_dir=settings.runtime_dir))
    assert restarted.settings.llm_model == "qwen-test"
    assert restarted.settings.llm_api_key == secret


def test_runtime_settings_reject_sensitive_url_parameters(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        response = client.patch(
            "/api/v1/settings",
            json={
                "values": {"llm_base_url": "https://example.test/v1?api_key=secret"},
                "operator": "tester",
            },
        )
    assert response.status_code == 422
    assert not (settings.runtime_dir / "config" / "overrides.json").exists()


def test_neo4j_password_is_private_clearable_and_conflict_safe(tmp_path: Path) -> None:
    secret = "neo4j-private-password-922"
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        saved = client.patch(
            "/api/v1/settings",
            json={"values": {"neo4j_password": secret}, "operator": "管理员"},
        )
        assert saved.status_code == 200
        assert saved.json()["settings"]["neo4j_password"] is True
        assert saved.json()["restart_required"] is True
        assert secret not in orjson.dumps(saved.json()).decode()

        conflict = client.patch(
            "/api/v1/settings",
            json={
                "values": {"neo4j_password": "replacement"},
                "clear_secrets": ["neo4j_password"],
                "operator": "管理员",
            },
        )
        assert conflict.status_code == 422
        assert service.settings.neo4j_password == secret

        cleared = client.patch(
            "/api/v1/settings",
            json={
                "values": {},
                "clear_secrets": ["neo4j_password"],
                "operator": "管理员",
            },
        )
        assert cleared.status_code == 200
        assert cleared.json()["settings"]["neo4j_password"] is False

    private_path = settings.runtime_dir / "config" / "overrides.json"
    if os.name != "nt":
        assert private_path.stat().st_mode & 0o777 == 0o600
    audit = settings.audit_path.read_text(encoding="utf-8")
    assert secret not in audit
    assert "replacement" not in audit
    assert PrismKEService(
        Settings(_env_file=None, runtime_dir=settings.runtime_dir)
    ).settings.neo4j_password is None


def test_workspace_provider_defaults_and_setting_controls(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        llm_model="custom-llm",
        ocr_device="gpu:0",
        ocr_lang="zh",
        neo4j_database="research",
    )
    service = PrismKEService(settings)
    with TestClient(create_app(settings, service)) as client:
        response = client.get("/ui/config")
        public = client.get("/api/v1/settings")
        immutable = client.patch(
            "/api/v1/settings",
            json={
                "values": {"ocr_device_resolved": "cpu"},
                "operator": "tester",
            },
        )
    assert response.status_code == 200
    assert public.status_code == 200
    assert public.json()["ocr_device_resolved"] == "gpu:0"
    assert immutable.status_code == 422
    fields = {
        component["props"]["label"]: component
        for component in response.json()["components"]
        if component["props"].get("label")
    }

    for label, value in {
        "文本 Provider": "openai-compatible",
        "OCR Provider": "paddle",
        "视觉 Provider": "openai-compatible",
    }.items():
        assert fields[label]["type"] == "dropdown"
        assert fields[label]["props"]["value"] == value
    assert fields["允许远程资源"]["props"]["value"] is False

    assert fields["LLM 模型别名"]["type"] == "textbox"
    assert fields["LLM 模型别名"]["props"]["value"] == "custom-llm"

    for label, value in {
        "OCR 设备": "gpu:0",
        "OCR 语言": "zh",
        "OCR 模型": "PP-OCRv5",
        "Neo4j 用户": "neo4j",
        "Neo4j 数据库": "research",
    }.items():
        assert fields[label]["type"] == "dropdown"
        if label not in {"OCR 设备", "OCR 语言"}:
            assert fields[label]["props"]["allow_custom_value"] is True
        assert fields[label]["props"]["value"] == value
    assert fields["Neo4j 密码"]["props"]["type"] == "password"
    assert not fields["Neo4j 密码"]["props"].get("value")
    assert fields["清除已保存 Neo4j 密码"]["props"]["value"] is False
    assert fields["图存储"]["type"] == "dropdown"
    for label in ("LLM Base URL", "VLM Base URL", "Neo4j URI"):
        assert fields[label]["type"] == "textbox"
