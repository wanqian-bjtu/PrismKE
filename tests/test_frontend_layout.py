from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from frontend.layout import (
    NAVIGATION_GROUPS,
    PAGE_META,
    TAGLINE,
    TAGLINE_ZH,
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
    "media",
    "visual-review",
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
    assert len(page_ids) == 17
    assert len(page_ids) == len(set(page_ids))
    assert set(page_ids) == EXPECTED_PAGE_IDS == set(PAGE_META)
    assert len(NAVIGATION_GROUPS) == 10
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
    assert by_id["settings-outcome"]["type"] == "markdown"

    assert TAGLINE in response.text
    assert TAGLINE_ZH in response.text

    by_label = {
        component["props"].get("label"): component
        for component in components
        if component["props"].get("label")
    }
    assert by_label["Schema 来源"]["type"] == "dropdown"
    assert by_label["LLM 模型别名"]["type"] == "textbox"
    assert by_label["VLM 模型别名"]["type"] == "textbox"
    assert by_label["LLM API Key（当前会话）"]["props"]["type"] == "password"
    assert by_label["VLM API Key（当前会话）"]["props"]["type"] == "password"
    assert not by_label["LLM API Key（当前会话）"]["props"].get("value")
    assert not by_label["VLM API Key（当前会话）"]["props"].get("value")
    assert by_label["Neo4j 密码"]["props"]["type"] == "password"
    assert not by_label["Neo4j 密码"]["props"].get("value")
    assert by_label["清除已保存 Neo4j 密码"]["props"]["value"] is False
    assert by_label["启用 Reflection"]["props"]["value"] is True
    assert by_label["Reflection Provider"]["props"]["value"] == "openai-compatible"
    assert by_label["单候选最大修复次数"]["props"]["value"] == 2
    assert by_label["单运行 Token 预算"]["props"]["value"] == 20_000
    assert by_label["单运行时间预算（秒）"]["props"]["value"] == 180
    assert by_label["治理/融合语义建议"]["props"]["value"] == "openai-compatible"
    assert by_label["Agent 建议 Token 预算"]["props"]["value"] == 20_000
    assert by_label["配置操作者"]["props"]["value"] == "管理员"
    assert [choice[1] for choice in by_label["任务模式"]["props"]["choices"]] == [
        "entity_extraction",
        "relation_extraction",
        "schema_information_extraction",
        "joint_entity_relation_extraction",
        "joint_entity_relation_disambiguation",
        "knowledge_graph_construction",
    ]
    assert by_label["任务模式"]["props"]["value"] == "knowledge_graph_construction"
    assert by_label["文档（最多 20 个）"]["props"]["file_count"] == "multiple"
    assert [choice[1] for choice in by_label["OCR 设备"]["props"]["choices"]] == [
        "auto",
        "cpu",
        "gpu:0",
    ]
    assert [choice[1] for choice in by_label["OCR 语言"]["props"]["choices"]] == [
        "mixed",
        "en",
        "zh",
    ]
    assert [choice[0] for choice in by_label["媒体类型"]["props"]["choices"]] == [
        "全部",
        "图片",
        "图表",
        "表格",
        "公式",
        "页面渲染",
    ]
    assert by_label["当前任务"]["props"]["choices"] == [["暂无任务", ""]]
    assert by_label["当前任务"]["props"]["interactive"] is False
    assert by_label["选择媒体出现记录"]["props"]["choices"] == [["暂无媒体出现记录", ""]]
    assert by_label["选择媒体出现记录"]["props"]["interactive"] is False

    advanced = next(
        component
        for component in components
        if component["type"] == "accordion" and component["props"].get("label") == "高级策略"
    )
    assert advanced["props"]["open"] is True

    decision_labels = {"审核决定", "替代决定", "核对结论", "审核动作"}
    for component in components:
        if component["props"].get("label") in decision_labels:
            assert component["type"] == "dropdown"
