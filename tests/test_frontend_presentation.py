from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

import frontend.presentation as presentation


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
    assert presentation.media_type_label("image") == "图片"
    assert presentation.media_type_label("page_render") == "页面渲染"
    assert presentation.status_label("running") == "运行中"
    assert presentation.decision_label("defer") == "暂缓"
    assert presentation.visual_target_label("visual_assertion") == "视觉断言"
    assert presentation.media_type_label("future_type") == "future_type"


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
            "请填写审核人、审核原因和请求编号。",
        ),
        ("stale version 3", "当前数据版本已更新，请刷新页面后重试。"),
        ("请上传 Schema 文件", "请上传 Schema 文件"),
        (
            "Schema 文本无效: internal parser details",
            "Schema 内容格式无效，请检查 JSON/YAML 语法和字段约束。",
        ),
    ],
)
def test_expected_errors_have_stable_chinese_messages(raw: str, expected: str) -> None:
    assert presentation.error_message(ValueError(raw)) == expected


def test_unknown_error_is_redacted_and_has_reference_number() -> None:
    message = presentation.error_message(RuntimeError("secret backend traceback in English"))
    assert "secret backend traceback" not in message
    assert message.startswith("操作失败，请刷新后重试")
    assert "错误编号：" in message


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
    assert notifications == ["请先选择媒体出现记录"]


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
