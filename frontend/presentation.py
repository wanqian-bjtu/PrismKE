"""User-facing labels, empty states, and non-destructive UI notifications."""

from __future__ import annotations

import hashlib
import inspect
import logging
import re
from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

EMPTY_VALUE = ""

MEDIA_TYPE_LABELS = {
    "image": "图片",
    "chart": "图表",
    "table": "表格",
    "formula": "公式",
    "page_render": "页面渲染",
}

STATUS_LABELS = {
    "pending": "待处理",
    "resolved": "已处理",
    "open": "待处理",
    "approved": "已批准",
    "rejected": "已拒绝",
    "deferred": "已暂缓",
    "excluded": "已排除",
    "queued": "排队中",
    "running": "运行中",
    "completed": "已完成",
    "succeeded": "已完成",
    "failed": "失败",
    "blocked": "已阻断",
    "parser_blocked": "解析已阻断",
    "cancelled": "已取消",
    "canceled": "已取消",
    "paused": "已暂停",
    "created": "已创建",
    "candidate": "候选",
    "active": "有效",
    "inactive": "已停用",
    "unknown": "未知",
    "sent": "已发送",
}

DECISION_LABELS = {
    "approve": "批准",
    "approved": "批准",
    "reject": "拒绝",
    "rejected": "拒绝",
    "defer": "暂缓",
    "deferred": "暂缓",
    "link": "链接候选",
    "create": "创建新实体",
}

VISUAL_TARGET_LABELS = {
    "media_relation": "媒体关系",
    "visual_assertion": "视觉断言",
}

_ERROR_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"reviewer,\s*reason\s+and\s+request_id\s+are\s+required", re.I),
        "请填写审核人、审核原因和请求编号。",
    ),
    (
        re.compile(r"reviewer.*required", re.I),
        "请填写审核人。",
    ),
    (
        re.compile(r"reason.*required", re.I),
        "请填写操作原因。",
    ),
    (
        re.compile(r"request[_ ]id.*required", re.I),
        "请填写请求编号。",
    ),
    (
        re.compile(r"expected[_ ]version|version conflict|stale version", re.I),
        "当前数据版本已更新，请刷新页面后重试。",
    ),
    (
        re.compile(r"evidence.*(unavailable|not found|missing|invalid)", re.I),
        "证据不可用或完整性校验失败，请刷新后核对。",
    ),
    (
        re.compile(r"run.*(not found|required)|run_id.*required", re.I),
        "请先选择运行。",
    ),
    (
        re.compile(r"entity.*(not found|required)|entity_id.*required", re.I),
        "请先选择实体。",
    ),
    (
        re.compile(r"media.*(not found|required)|occurrence.*(not found|required)", re.I),
        "请先选择媒体出现记录。",
    ),
    (
        re.compile(r"task.*(not found|required)|task_id.*required", re.I),
        "请先选择审核任务。",
    ),
)


def display_label(value: Any, mapping: dict[str, str]) -> str:
    """Return a localized display label without changing the stored value."""

    if value is None:
        return ""
    raw = value.value if hasattr(value, "value") else str(value)
    return mapping.get(raw, raw)


def media_type_label(value: Any) -> str:
    return display_label(value, MEDIA_TYPE_LABELS)


def status_label(value: Any) -> str:
    return display_label(value, STATUS_LABELS)


def decision_label(value: Any) -> str:
    return display_label(value, DECISION_LABELS)


def visual_target_label(value: Any) -> str:
    return display_label(value, VISUAL_TARGET_LABELS)


def normalize_optional(value: Any) -> Any | None:
    """Convert the disabled empty-dropdown sentinel to a real missing value."""

    return None if value in {None, EMPTY_VALUE} else value


def empty_dropdown_kwargs(label: str) -> dict[str, Any]:
    return {
        "choices": [(label, EMPTY_VALUE)],
        "value": EMPTY_VALUE,
        "interactive": False,
    }


def dropdown_kwargs(
    choices: Sequence[Any], *, empty_label: str, value: Any | None = None
) -> dict[str, Any]:
    if not choices:
        return empty_dropdown_kwargs(empty_label)
    return {"choices": list(choices), "value": value, "interactive": True}


def dropdown_update(
    gr: Any,
    choices: Sequence[Any],
    *,
    empty_label: str,
    value: Any | None = None,
    visible: bool | None = None,
) -> Any:
    """Build a populated update or a disabled, explicit empty-state update."""

    update = dropdown_kwargs(choices, empty_label=empty_label, value=value)
    if visible is not None:
        update["visible"] = visible
    return gr.update(**update)


def _raw_error_message(error: BaseException | str) -> str:
    if isinstance(error, str):
        return error.strip()
    message = getattr(error, "message", None)
    return str(message if message is not None else error).strip()


def error_message(error: BaseException | str) -> str:
    """Translate expected failures and redact unknown internal exceptions."""

    raw = _raw_error_message(error)
    if not raw:
        return "操作失败，请刷新后重试。"
    if raw.startswith("Schema 文本无效"):
        return "Schema 内容格式无效，请检查 JSON/YAML 语法和字段约束。"
    if raw.startswith("请") or re.search(r"[\u4e00-\u9fff]", raw):
        return raw
    for pattern, message in _ERROR_PATTERNS:
        if pattern.search(raw):
            return message
    reference = hashlib.sha256(
        f"{type(error).__name__}:{raw}".encode("utf-8", errors="replace")
    ).hexdigest()[:8]
    return f"操作失败，请刷新后重试；如问题持续，请联系管理员。错误编号：{reference}。"


def notify_error(error: BaseException | str) -> str:
    """Show one top-right red notification without raising into output components."""

    message = error_message(error)
    if isinstance(error, BaseException):
        logger.exception("UI action failed", exc_info=error)
    else:
        logger.warning("UI action failed: %s", error)
    from gradio.helpers import log_message

    log_message(
        message,
        level=cast(Any, "error"),
        title="错误",
        duration=10,
        visible=True,
    )
    return message


def _skipped_outputs(gr: Any, output_count: int) -> Any:
    if output_count == 0:
        return None
    skipped = [gr.skip() for _ in range(output_count)]
    return skipped[0] if output_count == 1 else tuple(skipped)


def guard_ui(
    gr: Any,
    function: Callable[P, R] | Callable[P, Awaitable[R]],
    output_count: int = 1,
) -> Callable[P, Any]:
    """Catch UI-bound failures, notify once, and preserve every output component."""

    if inspect.iscoroutinefunction(function):

        @wraps(function)
        async def async_guard(*args: P.args, **kwargs: P.kwargs) -> Any:
            try:
                return await cast(Callable[P, Awaitable[R]], function)(*args, **kwargs)
            except Exception as exc:
                notify_error(exc)
                return _skipped_outputs(gr, output_count)

        return async_guard

    @wraps(function)
    def sync_guard(*args: P.args, **kwargs: P.kwargs) -> Any:
        try:
            return cast(Callable[P, R], function)(*args, **kwargs)
        except Exception as exc:
            notify_error(exc)
            return _skipped_outputs(gr, output_count)

    return sync_guard
