from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from frontend.layout import (
    NAVIGATION_GROUPS,
    PAGE_META,
    TAGLINE,
    all_page_ids,
    first_page,
    logo_path,
    page_choices,
)
from src.api import create_app
from src.core.settings import Settings
from src.workflow import PrismKEService

EXPECTED_PAGE_IDS = {
    "overview",
    "build",
    "execution",
    "entity-review",
    "claim-review",
    "validation",
    "evidence",
    "graph",
    "governance",
    "corrections",
    "revisions",
    "cases",
    "reflection",
    "agents",
    "health",
}


def test_navigation_groups_cover_every_workspace_page_once() -> None:
    page_ids = all_page_ids()
    assert len(page_ids) == 15
    assert len(page_ids) == len(set(page_ids))
    assert set(page_ids) == EXPECTED_PAGE_IDS == set(PAGE_META)
    assert len(NAVIGATION_GROUPS) == 9
    for group_id in NAVIGATION_GROUPS:
        choices = page_choices(group_id)
        assert choices
        assert first_page(group_id) == choices[0][1]


def test_packaged_logo_is_the_selected_transparent_asset() -> None:
    path = logo_path()
    assert path.name == "prismke-logo-4k.png"
    assert path.parent.name == "branding"
    assert path.is_file()
    assert path.stat().st_size > 100_000


def test_workspace_uses_dropdown_navigation_and_no_radio_components(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        embedding_provider="mock",
        graph_store="json",
    )
    with TestClient(create_app(settings, PrismKEService(settings))) as client:
        response = client.get("/ui/config")
    assert response.status_code == 200
    config = response.json()
    components = config["components"]
    assert all(component["type"] != "radio" for component in components)

    by_id = {
        component["props"].get("elem_id"): component
        for component in components
        if component["props"].get("elem_id")
    }
    assert by_id["navigation-group"]["type"] == "dropdown"
    assert by_id["navigation-page"]["type"] == "dropdown"
    assert by_id["workspace-logo"]["type"] == "image"

    labels = [component["props"].get("label") for component in components]
    assert "API Key" not in labels
    assert "Neo4j 密码" not in labels
    assert TAGLINE in response.text

    decision_labels = {"审核决定", "替代决定", "核对结论", "审核动作"}
    for component in components:
        if component["props"].get("label") in decision_labels:
            assert component["type"] == "dropdown"
