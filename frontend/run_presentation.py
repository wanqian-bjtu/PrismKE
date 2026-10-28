"""Consistent user-facing run names and workflow explanations."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from frontend.i18n import DEFAULT_LOCALE, normalize_locale, tr
from src.domain import TaskMode

BEIJING = ZoneInfo("Asia/Shanghai")

TASK_MODE_LABELS = {
    TaskMode.ENTITY_EXTRACTION.value: "实体抽取",
    TaskMode.RELATION_EXTRACTION.value: "关系抽取",
    TaskMode.SCHEMA_INFORMATION_EXTRACTION.value: "Schema 信息抽取",
    TaskMode.JOINT_ENTITY_RELATION_EXTRACTION.value: "端到端实体关系抽取",
    TaskMode.JOINT_ENTITY_RELATION_DISAMBIGUATION.value: "实体关系抽取与消歧",
    TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION.value: "完整知识构建",
}

BRANCH_LABELS = {
    "text": "文本抽取",
    "visual": "视觉抽取",
    "ocr": "OCR 识别",
    "commit": "图谱提交",
}

NODE_LABELS = {
    "ingest": "登记输入",
    "parse_document": "解析文档",
    "materialize_visual_assets": "生成媒体资产",
    "run_ocr": "执行 OCR",
    "persist_evidence": "持久化证据",
    "load_schema": "加载 Schema",
    "extract_text_claims": "文本候选抽取",
    "extract_visual_claims": "视觉候选抽取",
    "align_modalities": "图文候选对齐",
    "reflect_candidates": "候选反思与修复",
    "resolve_entities": "实体链接与消歧",
    "normalize_claims": "事实规范化",
    "detect_conflicts": "冲突检测",
    "route_by_risk": "风险路由",
    "finalize_extraction_result": "形成抽取结果",
    "prepare_graph_commit": "准备图谱提交",
    "commit_graph": "原子写入图谱",
}

NODE_DESCRIPTIONS = {
    "ingest": "登记输入文件、任务模式、Schema 与 Provider 配置。",
    "parse_document": "将输入解析为统一的 DocumentIR。",
    "materialize_visual_assets": "生成并校验图片、页面、表格等媒体资产。",
    "run_ocr": "只对需要文字识别的图片或页面区域执行 OCR。",
    "persist_evidence": "保存证据定位、哈希和派生产物并验证完整性。",
    "load_schema": "读取、规范化并校验本次运行使用的 Schema。",
    "extract_text_claims": "从文本证据中抽取实体、关系或其他候选。",
    "extract_visual_claims": "从视觉证据中抽取媒体关系和视觉候选。",
    "align_modalities": "对齐文本与视觉候选，保留一致或冲突证据。",
    "reflect_candidates": "按预算对候选执行反思、修复和结构化重试。",
    "resolve_entities": "执行实体链接、NIL 判定、规范化与消歧。",
    "normalize_claims": "规范化事实主语、关系、宾语和值。",
    "detect_conflicts": "识别候选之间以及图文之间的冲突。",
    "route_by_risk": "按风险和证据完整性决定自动通过或人工审核。",
    "finalize_extraction_result": "形成可查看、审核和导出的抽取结果。",
    "prepare_graph_commit": "生成确定性的 GraphCommit 预览并执行硬校验。",
    "commit_graph": "在一个事务中原子写入图谱并创建 Revision。",
}


def local_time(value: datetime | str | None, *, with_seconds: bool = True) -> str:
    """Render persisted UTC timestamps in Beijing time."""

    if value is None:
        return ""
    if isinstance(value, str):
        raw_value = value
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return raw_value
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    pattern = "%Y-%m-%d %H:%M:%S" if with_seconds else "%Y-%m-%d %H:%M"
    return value.astimezone(BEIJING).strftime(pattern)


def task_mode_label(value: Any, locale: object = DEFAULT_LOCALE) -> str:
    raw = value.value if hasattr(value, "value") else str(value)
    label = TASK_MODE_LABELS.get(raw, raw)
    return tr(label, locale) if label != raw else raw


def node_label(value: str | None, locale: object = DEFAULT_LOCALE) -> str:
    if not value:
        return ""
    label = NODE_LABELS.get(value, value)
    return tr(label, locale) if label != value else value


def branch_label(value: str, locale: object = DEFAULT_LOCALE) -> str:
    label = BRANCH_LABELS.get(value, value)
    return tr(label, locale) if label != value else value


def node_description(value: str, locale: object = DEFAULT_LOCALE) -> str:
    description = NODE_DESCRIPTIONS.get(value, "")
    return tr(description, locale) if description else ""


def workflow_node_guide(locale: object = DEFAULT_LOCALE) -> str:
    rows = [
        f"| `{node}` | {node_label(node, locale)} | {node_description(node, locale)} |"
        for node in NODE_LABELS
    ]
    return "\n".join(
        [
            f"| {tr('节点代码', locale)} | {tr('节点名称', locale)} | {tr('作用', locale)} |",
            "|---|---|---|",
            *rows,
            "",
            tr(
                "OCR、视觉与图谱提交分支会根据输入媒体、任务模式和写图资格显示为禁用。",
                locale,
            ),
        ]
    )


def provider_usage_label(item: dict[str, Any], locale: object = DEFAULT_LOCALE) -> str:
    """Render token usage without exposing a Provider response body."""

    usage = item.get("usage") or {}
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = int(input_tokens) + int(output_tokens)
    if total_tokens is None:
        return tr("未提供", locale)
    source = "输入 {input} · 输出 {output} · 总计 {total}"
    return tr(source, locale).format(
        input=input_tokens or 0,
        output=output_tokens or 0,
        total=total_tokens,
    )


def _batch_context(service: Any, state: Any) -> tuple[str, int, datetime | None]:
    if state.batch_id and service.batches.exists(state.batch_id):
        batch = service.batches.load(state.batch_id)
        if batch.items:
            return batch.items[0].filename, len(batch.items), batch.created_at
    filename = (
        state.document.source_filename
        if getattr(state, "document", None) and state.document.source_filename
        else Path(state.input_path).name
    )
    try:
        created_at = service.executions.repository.get(state.run_id).created_at
    except (AttributeError, KeyError, FileNotFoundError):
        created_at = None
    return filename or tr("未命名文件", "zh-CN"), 1, created_at


def friendly_run_label(
    service: Any,
    state: Any,
    locale: object = DEFAULT_LOCALE,
) -> str:
    """Build a readable label while keeping the dropdown value as the Run ID."""

    filename, count, created_at = _batch_context(service, state)
    if normalize_locale(locale) == "en":
        count_label = f"{count} {'file' if count == 1 else 'files'}"
    else:
        count_label = f"{count}个文件"
    return " · ".join(
        [
            task_mode_label(state.task_mode, locale),
            filename,
            count_label,
            local_time(created_at, with_seconds=False) or tr("时间未知", locale),
        ]
    )


def friendly_run_choices(
    service: Any,
    states: list[Any] | None = None,
    *,
    locale: object = DEFAULT_LOCALE,
) -> list[tuple[str, str]]:
    candidates = states if states is not None else service.runs.list(limit=1000)
    return [(friendly_run_label(service, state, locale), state.run_id) for state in candidates]
