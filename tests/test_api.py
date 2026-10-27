from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.core.errors import GraphIntegrityError
from src.core.settings import Settings
from src.workflow import PrismKEService


def wait_execution(client: TestClient, run_id: str) -> None:
    for _ in range(500):
        response = client.get(f"/api/v1/runs/{run_id}/execution")
        if not response.json()["active"]:
            return
        time.sleep(0.02)
    raise AssertionError("execution timed out")


def test_non_loopback_binding_requires_token(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        api_host="0.0.0.0",
        api_token=None,
    )
    with pytest.raises(ValueError, match="PRISMKE_API_TOKEN"):
        create_app(settings, mount_ui=False)


def test_health_endpoint_and_bearer_auth(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        api_host="0.0.0.0",
        api_token="test-token",
    )
    with TestClient(create_app(settings, mount_ui=False)) as client:
        assert client.get("/api/v1/health").status_code == 401
        response = client.get("/api/v1/health", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    assert response.json()["graph"]["backend"] == "json"


def test_upload_run_uses_shared_service(tmp_path: Path, schema_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    app = create_app(settings, service, mount_ui=False)
    document = b"PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n"
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            files={
                "document": ("sample.md", document, "text/markdown"),
                "schema": ("schema.yaml", schema_path.read_bytes(), "application/yaml"),
            },
            data={"provider": "mock"},
        )
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        wait_execution(client, run_id)
        state = client.get(f"/api/v1/runs/{run_id}")
        claims = client.get(f"/api/v1/runs/{run_id}/claims")
    assert state.status_code == 200
    assert state.json()["status"] == "completed"
    assert len(claims.json()) == 1


def test_run_export_is_sanitized_and_source_is_opt_in(
    tmp_path: Path, schema_path: Path
) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    app = create_app(settings, service, mount_ui=False)
    document = b"PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n"
    required = {
        "manifest.json",
        "results.json",
        "schema_snapshot.json",
        "entities.csv",
        "mentions.csv",
        "relations.csv",
        "attributes.csv",
        "events.csv",
        "media.csv",
        "evidence.csv",
        "validation_issues.csv",
        "candidate_graph.json",
        "evidence_manifest.json",
    }
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            files={
                "document": ("sample.md", document, "text/markdown"),
                "schema": ("schema.yaml", schema_path.read_bytes(), "application/yaml"),
            },
            data={"provider": "mock", "task_mode": "entity_extraction"},
        )
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        wait_execution(client, run_id)

        archive_response = client.get(f"/api/v1/runs/{run_id}/export")
        assert archive_response.status_code == 200
        with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
            names = set(archive.namelist())
            assert required <= names
            assert not any(name.startswith("source/") for name in names)
            evidence_manifest = json.loads(archive.read("evidence_manifest.json"))
            assert evidence_manifest
            assert all(item["verified"] is True for item in evidence_manifest)
            payload = b"".join(archive.read(name) for name in names)
            assert b"api_key" not in payload.lower()
            assert str(tmp_path).encode() not in payload

        source_response = client.get(
            f"/api/v1/runs/{run_id}/export", params={"include_source": "true"}
        )
        assert source_response.status_code == 200
        with zipfile.ZipFile(io.BytesIO(source_response.content)) as archive:
            assert any(name.startswith("source/") for name in archive.namelist())


def test_unknown_run_returns_not_found(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    with TestClient(create_app(settings, mount_ui=False)) as client:
        response = client.get("/api/v1/runs/missing")
    assert response.status_code == 404


def test_review_and_resume_commit_an_awaiting_claim(tmp_path: Path, schema_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    app = create_app(settings, service, mount_ui=False)
    document = b"PrismKE | developed_by | OpenAI | Software | Organization | 0.70\n"

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            files={
                "document": ("review.md", document, "text/markdown"),
                "schema": ("schema.yaml", schema_path.read_bytes(), "application/yaml"),
            },
            data={"provider": "mock"},
        )
        run_id = response.json()["run_id"]
        wait_execution(client, run_id)
        awaiting = client.get(f"/api/v1/runs/{run_id}").json()
        assert awaiting["status"] == "awaiting_review"
        task_id = awaiting["review_tasks"][0]["id"]

        review = client.post(
            f"/api/v1/reviews/{task_id}", json={"decision": "approve", "reviewer": "tester"}
        )
        assert review.status_code == 200
        assert review.json()["review_tasks"][0]["status"] == "resolved"

        resumed = client.post(f"/api/v1/runs/{run_id}/resume")
        assert resumed.status_code == 202
        wait_execution(client, run_id)
        completed = client.get(f"/api/v1/runs/{run_id}").json()

    assert completed["status"] == "completed"
    assert completed["claims"][0]["status"] == "approved"


def test_revision_diff_and_rollback_endpoints(tmp_path: Path, schema_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    app = create_app(settings, service, mount_ui=False)

    with TestClient(app) as client:
        revision_ids: list[str] = []
        for index, organization in enumerate(("OpenAI", "Anthropic"), start=1):
            document = (
                f"PrismKE | developed_by | {organization} | Software | Organization | 0.92\n"
            ).encode()
            response = client.post(
                "/api/v1/runs",
                files={
                    "document": (f"sample-{index}.md", document, "text/markdown"),
                    "schema": (
                        "schema.yaml",
                        schema_path.read_bytes(),
                        "application/yaml",
                    ),
                },
                data={"provider": "mock"},
            )
            wait_execution(client, response.json()["run_id"])
            state = client.get(f"/api/v1/runs/{response.json()['run_id']}").json()
            assert state["status"] == "completed"
            revision_ids.append(state["revision"]["id"])

        revisions = client.get("/api/v1/revisions")
        assert revisions.status_code == 200
        assert len(revisions.json()) == 2

        diff = client.get(
            "/api/v1/revisions/diff",
            params={"from": revision_ids[0], "to": revision_ids[1]},
        )
        assert diff.status_code == 200
        assert diff.json()["changes"]

        rollback = client.post(
            f"/api/v1/revisions/{revision_ids[1]}/rollback",
            json={"confirm": True},
        )

    assert rollback.status_code == 200
    assert rollback.json()["parent_id"] == revision_ids[1]
    assert "rollback" in rollback.json()["run_id"]


def test_rollback_integrity_error_returns_conflict(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    service.graph_store.rollback_revision = AsyncMock(  # type: ignore[method-assign]
        side_effect=GraphIntegrityError("legacy revision cannot be rolled back")
    )
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        response = client.post("/api/v1/revisions/rev:legacy/rollback", json={"confirm": True})
    assert response.status_code == 409
    assert response.json()["detail"] == "legacy revision cannot be rolled back"
