from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prismke.api import create_app
from prismke.core.settings import Settings
from prismke.workflow import PrismKEService


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
        response = client.get(
            "/api/v1/health", headers={"Authorization": "Bearer test-token"}
        )
    assert response.status_code == 200
    assert response.json()["graph"]["backend"] == "json"


def test_upload_run_uses_shared_service(tmp_path: Path, schema_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    app = create_app(settings, service, mount_ui=False)
    document = (
        b"PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n"
    )
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
        state = client.get(f"/api/v1/runs/{run_id}")
        claims = client.get(f"/api/v1/runs/{run_id}/claims")
    assert state.status_code == 200
    assert state.json()["status"] == "completed"
    assert len(claims.json()) == 1


def test_unknown_run_returns_not_found(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    with TestClient(create_app(settings, mount_ui=False)) as client:
        response = client.get("/api/v1/runs/missing")
    assert response.status_code == 404
