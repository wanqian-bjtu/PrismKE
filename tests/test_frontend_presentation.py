from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

import frontend.presentation as presentation
from frontend.i18n import EN_BY_ZH, normalize_locale, tr


class FakeGradio:
    def __init__(self) -> None:
        self.skips: list[object] = []

    def skip(self) -> object:
        value = object()
        self.skips.append(value)
        return value

    @staticmethod
    def update(**values: Any) -> dict[str, Any]:
        return values


def test_user_facing_enum_labels_keep_internal_values_separate() -> None:
    assert presentation.media_type_label("image") == "Image"
    assert presentation.media_type_label("page_render") == "Page render"
    assert presentation.status_label("running") == "Running"
    assert presentation.decision_label("defer") == "Defer"
    assert presentation.visual_target_label("visual_assertion") == "Visual assertion"
    assert presentation.media_type_label("image", "zh-CN") == "图片"
    assert presentation.status_label("running", "zh-CN") == "运行中"
    assert presentation.media_type_label("future_type") == "future_type"


def test_locale_catalog_has_stable_defaults_and_complete_pairs() -> None:
    assert normalize_locale(None) == "en"
    assert normalize_locale("invalid") == "en"
    assert normalize_locale("zh-CN") == "zh-CN"
    assert tr("工作区") == "Workspace"
    assert tr("工作区", "zh-CN") == "工作区"
    assert all(source and translated for source, translated in EN_BY_ZH.items())


def test_empty_dropdown_is_disabled_and_sentinel_normalizes_to_none() -> None:
    gr = FakeGradio()
    empty = presentation.dropdown_update(gr, [], empty_label="暂无运行")
    assert empty == {
        "choices": [("暂无运行", "")],
        "value": "",
        "interactive": False,
    }
    assert presentation.normalize_optional("") is None
    assert presentation.normalize_optional("run-1") == "run-1"

    populated = presentation.dropdown_update(
        gr,
        [("运行一", "run-1")],
        empty_label="暂无运行",
        value="run-1",
    )
    assert populated["choices"] == [("运行一", "run-1")]
    assert populated["value"] == "run-1"
    assert populated["interactive"] is True


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "reviewer, reason and request_id are required",
            "Enter the reviewer, review reason, and request ID.",
        ),
        ("stale version 3", "The data version has changed. Refresh the page and try again."),
        ("请上传 Schema 文件", "Upload a Schema file."),
        (
            "Schema 文本无效: internal parser details",
            "The Schema is invalid. Check its JSON/YAML syntax and field constraints.",
        ),
    ],
)
def test_expected_errors_have_stable_english_messages(raw: str, expected: str) -> None:
    assert presentation.error_message(ValueError(raw)) == expected


def test_expected_errors_can_be_rendered_in_chinese() -> None:
    error = ValueError("reviewer, reason and request_id are required")
    assert presentation.error_message(error, "zh-CN") == "请填写审核人、审核原因和请求编号。"


def test_unknown_error_is_redacted_and_has_reference_number() -> None:
    message = presentation.error_message(RuntimeError("secret backend traceback in English"))
    assert "secret backend traceback" not in message
    assert message.startswith("The operation failed. Refresh and try again")
    assert "error reference:" in message
    chinese = presentation.error_message(
        RuntimeError("secret backend traceback in English"), "zh-CN"
    )
    assert chinese.startswith("操作失败，请刷新后重试")
    assert "错误编号：" in chinese


@pytest.mark.asyncio
async def test_guard_preserves_all_outputs_and_notifies_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gr = FakeGradio()
    notifications: list[str] = []
    monkeypatch.setattr(
        presentation,
        "notify_error",
        lambda error: notifications.append(presentation.error_message(error)) or "",
    )

    async def fail() -> tuple[str, str]:
        raise ValueError("请先选择媒体出现记录")

    result = await presentation.guard_ui(gr, fail, 2)()
    assert result == tuple(gr.skips)
    assert notifications == ["Select a media occurrence first."]


def test_frontend_never_raises_gradio_error_directly() -> None:
    root = Path(__file__).resolve().parents[1] / "frontend"
    violations: list[str] = []
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Raise) or not isinstance(node.exc, ast.Call):
                continue
            function = node.exc.func
            if (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and function.value.id == "gr"
                and function.attr == "Error"
            ):
                violations.append(f"{path.name}:{node.lineno}")
    assert violations == []


def test_gradio_literal_ui_strings_are_registered_for_english() -> None:
    root = Path(__file__).resolve().parents[1] / "frontend"
    component_names = {
        "Accordion",
        "Button",
        "Checkbox",
        "Dataframe",
        "Dropdown",
        "File",
        "HTML",
        "Image",
        "JSON",
        "Markdown",
        "Number",
        "Radio",
        "Slider",
        "Tab",
        "Textbox",
    }
    positional_text = {"Accordion", "Button", "HTML", "Markdown", "Tab"}
    visible_keywords = {"headers", "info", "label", "placeholder", "value"}
    normalized_catalog = {" ".join(source.split()) for source in EN_BY_ZH}
    missing: list[str] = []

    for path in root.glob("*.py"):
        if path.name == "i18n.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if not isinstance(node.func.value, ast.Name) or node.func.value.id != "gr":
                continue
            component = node.func.attr
            if component not in component_names:
                continue
            values = [keyword.value for keyword in node.keywords if keyword.arg in visible_keywords]
            if component in positional_text and node.args:
                values.append(node.args[0])
            for value in values:
                for literal in ast.walk(value):
                    if not isinstance(literal, ast.Constant) or not isinstance(literal.value, str):
                        continue
                    text = literal.value
                    normalized = " ".join(text.split())
                    if (
                        any("\u4e00" <= character <= "\u9fff" for character in text)
                        and text not in EN_BY_ZH
                        and normalized not in normalized_catalog
                    ):
                        missing.append(f"{path.name}:{node.lineno}:{text!r}")

    assert missing == []
