"""Candidate-grouped validation review and deterministic correction UI."""

from __future__ import annotations

from collections import defaultdict
from html import escape
from typing import Any
from uuid import uuid4

from frontend.i18n import normalize_locale, tr
from frontend.layout import page_header
from frontend.presentation import (
    dropdown_kwargs,
    dropdown_update,
    empty_dropdown_kwargs,
    guard_ui,
    status_label,
)
from frontend.review import ReviewController
from src.domain import ValidationAction
from src.persistence.execution import ExecutionConflict
from src.workflow import PrismKEService

ACTION_CHOICES = [
    ("交换主语与宾语", "swap_endpoints"),
    ("改选关系", "replace_relation"),
    ("修正实体类型", "replace_entity_type"),
    ("修正实体链接", "replace_entity_link"),
    ("排除候选", "exclude"),
    ("暂缓处理", "defer"),
]

ACTION_HELP = {
    "swap_endpoints": (
        "交换主语与宾语",
        "关系语义正确但方向相反时使用；系统交换两端并重新执行确定性校验。",
    ),
    "replace_relation": (
        "改选关系",
        "主语和宾语正确但关系选错时使用；只能选择当前 Schema 中已有关系。",
    ),
    "replace_entity_type": (
        "修正实体类型",
        "实体正确但类型识别错误时使用；选择端点和 Schema 中允许的实体类型。",
    ),
    "replace_entity_link": (
        "修正实体链接",
        "提及链接到错误规范实体时使用；可改链到已有实体，留空表示保持 NIL。",
    ),
    "exclude": (
        "排除候选",
        "候选本身是误抽取时使用；候选不再进入后续处理，但原问题和审计保留。",
    ),
    "defer": (
        "暂缓处理",
        "证据不足时使用；候选保持不变，运行继续阻断且不会自动恢复。",
    ),
}

RESUME_ERROR_HELP = {
    "CREDENTIAL_REQUIRED": (
        "缺少运行所需凭据；请在任务配置中补充凭据后手动恢复。",
        "Required credentials are missing. Add them in task configuration, then resume manually.",
    ),
    "STALE_EXECUTION_VERSION": (
        "执行版本已变化；请刷新任务状态后重试恢复。",
        "The execution version changed. Refresh the task state before retrying resume.",
    ),
    "EXECUTION_BUSY": (
        "已有其他执行操作进行中；请等待其结束后再恢复。",
        "Another execution operation is active. Wait for it to finish before resuming.",
    ),
    "CHECKPOINT_MISSING": (
        "运行检查点不可用，无法自动恢复；请查看执行详情。",
        "The run checkpoint is unavailable, so automatic resume is not possible. "
        "Check execution details.",
    ),
    "UNKNOWN_PROVIDER_REQUEST": (
        "存在结果未知的模型请求；请先在执行任务页完成请求核对。",
        "A provider request has an unknown outcome. Reconcile it on the execution page first.",
    ),
    "REVIEW_SYNC_PENDING": (
        "审核状态仍在同步；请刷新后再恢复。",
        "Review state is still synchronizing. Refresh before resuming.",
    ),
}


def _action_help(action: str | None, locale: object = "zh-CN") -> str:
    if not action or action not in ACTION_HELP:
        return tr("请选择修正动作以查看说明。", locale)
    title, description = ACTION_HELP[action]
    return f"**{tr(title, locale)}**：{tr(description, locale)}"


def _resume_error_help(error: str, locale: object) -> str:
    code = error.strip()
    messages = RESUME_ERROR_HELP.get(code)
    if messages is None:
        return code
    return messages[0] if normalize_locale(locale) == "zh-CN" else messages[1]


def _candidate_values(value: dict[str, Any] | None) -> dict[str, str]:
    if value is None:
        return {}
    subject = value.get("subject") or {}
    object_value = value.get("object") or {}
    if not isinstance(subject, dict):
        subject = {"name": subject}
    if not isinstance(object_value, dict):
        object_value = {"literal": object_value}
    return {
        "subject": str(subject.get("name") or ""),
        "subject_type": str(subject.get("entity_type") or subject.get("type") or ""),
        "subject_link": str(subject.get("entity_id") or subject.get("canonical_id") or "NIL"),
        "relation": str(value.get("relation") or value.get("relation_id") or ""),
        "object": str(object_value.get("name") or object_value.get("literal") or ""),
        "object_type": str(
            object_value.get("entity_type") or object_value.get("type") or ""
        ),
        "object_link": str(
            object_value.get("entity_id") or object_value.get("canonical_id") or "NIL"
        ),
    }


def _preview_comparison(payload: dict[str, Any], locale: object) -> str:
    before = _candidate_values(payload.get("before"))
    after = _candidate_values(payload.get("after"))
    action = str(payload.get("action") or "")
    replacement = payload.get("replacement") or {}
    if action == "replace_entity_link" and isinstance(replacement, dict):
        endpoint = str(replacement.get("endpoint") or "")
        if endpoint in {"subject", "object"}:
            after[f"{endpoint}_link"] = str(replacement.get("entity_id") or "NIL")
    labels = [
        ("subject", "主语"),
        ("subject_type", "主语类型"),
        ("subject_link", "主语规范实体"),
        ("relation", "关系"),
        ("object", "宾语"),
        ("object_type", "宾语类型"),
        ("object_link", "宾语规范实体"),
    ]

    def card(title: str, values: dict[str, str], compare: dict[str, str]) -> str:
        rows = []
        for key, label in labels:
            changed = values.get(key, "") != compare.get(key, "")
            css_class = " correction-value-changed" if changed else ""
            rows.append(
                '<div class="correction-field">'
                f'<span class="correction-field-label">{escape(tr(label, locale))}</span>'
                f'<span class="correction-field-value{css_class}">'
                f'{escape(values.get(key, "") or "—")}</span></div>'
            )
        return (
            '<section class="correction-preview-card">'
            f"<h4>{escape(tr(title, locale))}</h4>{''.join(rows)}</section>"
        )

    if action == "exclude":
        after_card = (
            '<section class="correction-preview-card correction-preview-decision">'
            f"<h4>{escape(tr('修正后', locale))}</h4>"
            f"<strong>{escape(tr('候选将被排除，原问题和审计记录保留。', locale))}</strong>"
            "</section>"
        )
    elif action == "defer":
        after_card = (
            '<section class="correction-preview-card correction-preview-decision">'
            f"<h4>{escape(tr('修正后', locale))}</h4>"
            f"<strong>{escape(tr('候选保持不变，运行继续阻断。', locale))}</strong>"
            "</section>"
        )
    else:
        after_card = card("修正后", after, before)
    can_apply = bool(payload.get("can_apply"))
    issue_count = int(payload.get("remaining_issue_count") or 0)
    status = tr("可以应用", locale) if can_apply else tr("仍有阻断问题", locale)
    return (
        '<div class="correction-preview-comparison">'
        f'{card("修正前", before, after)}<div class="correction-preview-arrow" '
        f'aria-hidden="true">→</div>{after_card}</div>'
        '<div class="correction-preview-status">'
        f"<strong>{escape(status)}</strong> · "
        f"{escape(tr('剩余问题', locale))} {issue_count}</div>"
    )


def _safe(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("`", "ˋ")


def _candidate_label(
    summary: dict[str, Any], count: int, target_id: str, locale: object = "zh-CN"
) -> str:
    subject = summary.get("subject", {})
    object_value = summary.get("object", {})
    subject_name = subject.get("name", subject) if isinstance(subject, dict) else subject
    object_name = (
        object_value.get("name", object_value.get("literal", object_value))
        if isinstance(object_value, dict)
        else object_value
    )
    short = target_id.rsplit(":", 1)[-1][:6]
    issue_label = (
        f"{count} issues" if normalize_locale(locale) == "en" else f"{count}个问题"
    )
    relation = summary.get("relation", "")
    return f"{subject_name} —{relation}→ {object_name} · {issue_label} · #{short}"


def _issue_message(item: Any, locale: object = "zh-CN") -> str:
    if item.code == "SCHEMA_DOMAIN_RANGE" and item.field_path == "subject.entity_type":
        return tr("主语类型不满足关系 domain 约束", locale)
    if item.code == "SCHEMA_DOMAIN_RANGE" and item.field_path == "object.entity_type":
        return tr("宾语类型不满足关系 range 约束", locale)
    return str(item.message)


def _candidate_detail(
    issues: list[Any], validation_version: int, locale: object = "zh-CN"
) -> str:
    first = issues[0]
    summary = first.candidate_summary
    subject = summary.get("subject", {})
    object_value = summary.get("object", {})
    if not isinstance(subject, dict):
        subject = {"name": subject, "type": ""}
    if not isinstance(object_value, dict):
        object_value = {"name": object_value, "type": ""}
    domain = next(
        (
            i.expected_constraint.get("domain")
            for i in issues
            if i.field_path == "subject.entity_type"
        ),
        "",
    )
    range_value = next(
        (
            i.expected_constraint.get("range")
            for i in issues
            if i.field_path == "object.entity_type"
        ),
        "",
    )
    subject_row = (
        f"| **{tr('主语', locale)}** | {_safe(subject.get('name'))} | "
        f"{_safe(subject.get('type'))} | {_safe(domain)} |"
    )
    object_name = object_value.get("name", object_value.get("literal"))
    object_row = (
        f"| **{tr('宾语', locale)}** | {_safe(object_name)} | {_safe(object_value.get('type'))} | "
        f"{_safe(range_value)} |"
    )
    lines = [
        f"### {tr('候选', locale)} #{first.target_id.rsplit(':', 1)[-1][:6]}",
        "",
        f"| {tr('角色', locale)} | {tr('当前值', locale)} | "
        f"{tr('当前类型', locale)} | {tr('Schema 约束', locale)} |",
        "|---|---|---|---|",
        subject_row,
        f"| **{tr('关系', locale)}** | {_safe(summary.get('relation'))} | — | — |",
        object_row,
        "",
        f"**{tr('候选版本：', locale)}** {validation_version}",
        "",
        f"**{tr('问题：', locale)}**",
    ]
    for item in issues:
        lines.append(
            f"- `{item.code} · {item.field_path} · #{item.id.rsplit(':', 1)[-1][:6]}`："
            f"{_safe(_issue_message(item, locale))}"
        )
    lines.extend(
        [
            "",
            tr(
                "请先选择修正动作并预览影响。修正不会调用 LLM/VLM，也不会直接写图。",
                locale,
            ),
        ]
    )
    return "\n".join(lines)


def build_validation_tab(
    gr: Any,
    service: PrismKEService,
    *,
    navigation_group: Any,
    navigation_page: Any,
    workspace_tabs: Any,
    current_run: Any,
    language_switch: Any,
) -> Any:
    controller = ReviewController(service)
    run_choices = controller.runs("validation", locale="en")
    with gr.Tab("校验问题", id="validation"):
        page_header(gr, "validation")
        with gr.Row():
            run = gr.Dropdown(
                label="校验运行", **dropdown_kwargs(run_choices, empty_label="暂无运行")
            )
            stage = gr.Dropdown(
                label="校验阶段",
                choices=["全部", "structure", "schema", "reference", "evidence"],
                value="全部",
            )
            status = gr.Dropdown(
                label="问题状态",
                choices=["open", "deferred", "excluded", "repaired", "全部"],
                value="open",
            )
        refresh = gr.Button("刷新校验问题")
        show_all_runs = gr.Checkbox(label="显示全部运行", value=False)
        summary = gr.Markdown()
        table = gr.Dataframe(
            headers=["候选短编号", "主语", "关系", "宾语", "问题数", "状态"],
            interactive=False,
        )
        candidate = gr.Dropdown(label="选择候选", **empty_dropdown_kwargs("暂无校验候选"))
        with gr.Accordion("问题详情与安全修正", open=True):
            detail = gr.Markdown()
            with gr.Row():
                action = gr.Dropdown(label="修正动作", choices=ACTION_CHOICES)
                endpoint = gr.Dropdown(
                    label="修正端点",
                    choices=[("主语", "subject"), ("宾语", "object")],
                    value="subject",
                )
            with gr.Row():
                relation = gr.Dropdown(label="替换关系", choices=[])
                entity_type = gr.Dropdown(label="替换实体类型", choices=[])
                entity_link = gr.Dropdown(
                    label="替换规范实体 ID（留空表示保持 NIL）",
                    choices=[],
                    allow_custom_value=False,
                )
            action_explanation = gr.Markdown("请选择修正动作以查看说明。")
            with gr.Accordion("修正动作说明", open=False):
                gr.Markdown(
                    """
| 修正动作 | 适用情况 | 结果 |
|---|---|---|
| 交换主语与宾语 | 关系方向反了 | 交换两端并重新校验 |
| 改选关系 | 主宾正确、关系错误 | 仅可选择当前 Schema 关系 |
| 修正实体类型 | 实体正确、类型错误 | 修改指定端点类型并重新校验 |
| 修正实体链接 | 链接到错误规范实体 | 改链到已有实体或保持 NIL |
| 排除候选 | 候选属于误抽取 | 不进入后续处理，保留审计 |
| 暂缓处理 | 证据暂时不足 | 保持阻断，不自动恢复 |
"""
                )
            preview_button = gr.Button("预览修正影响", variant="secondary")
            preview_visual = gr.HTML(label="修正前后对比")
            with gr.Accordion("修正预览技术详情", open=False):
                preview_output = gr.JSON(label="修正预览")
            with gr.Row():
                reviewer = gr.Textbox(label="校验审核人")
                reason = gr.Textbox(label="修正原因")
                request_id = gr.Textbox(label="请求编号", value=uuid4().hex)
            confirm = gr.Checkbox(label="我已核对预览结果并确认应用")
            apply_button = gr.Button("确认应用修正", variant="primary")
        evidence = gr.Dropdown(label="问题证据", **empty_dropdown_kwargs("暂无证据"))
        evidence_text = gr.Textbox(label="校验证据文本", interactive=False)
        evidence_image = gr.Image(label="校验证据区域", interactive=False, visible=False)
        output = gr.Markdown()
        version_state = gr.State(0)
        apply_state = gr.State({})

        async def load(
            run_id: str | None,
            selected_stage: str,
            selected_status: str,
            chinese: bool,
        ) -> tuple[Any, ...]:
            locale = "zh-CN" if chinese else "en"
            if not run_id:
                return (
                    tr("请选择运行。", locale),
                    [],
                    dropdown_update(
                        gr, [], empty_label=tr("暂无校验候选", locale)
                    ),
                    0,
                )
            report = await service.validate_run(run_id)
            state = service.show_run(run_id)
            issues = [
                item
                for item in report.issues
                if (selected_stage == "全部" or item.stage == selected_stage)
                and (selected_status == "全部" or item.status == selected_status)
            ]
            grouped: dict[str, list[Any]] = defaultdict(list)
            for item in issues:
                grouped[item.target_id].append(item)
            rows, choices = [], []
            for target_id, values in grouped.items():
                item = values[0]
                subject = item.candidate_summary.get("subject", {})
                obj = item.candidate_summary.get("object", {})
                subject_name = (
                    subject.get("name", subject) if isinstance(subject, dict) else subject
                )
                object_name = (
                    obj.get("name", obj.get("literal", obj)) if isinstance(obj, dict) else obj
                )
                rows.append(
                    [
                        f"#{target_id.rsplit(':', 1)[-1][:6]}",
                        subject_name,
                        item.candidate_summary.get("relation", ""),
                        object_name,
                        len(values),
                        status_label(item.status, locale),
                    ]
                )
                choices.append(
                    (
                        _candidate_label(
                            item.candidate_summary, len(values), target_id, locale
                        ),
                        target_id,
                    )
                )
            return (
                (
                    f"### {len(issues)} issues across {len(grouped)} candidates\n\n"
                    if locale == "en"
                    else f"### {len(issues)} 个问题，涉及 {len(grouped)} 个候选\n\n"
                )
                + tr(
                    "本运行无校验问题。"
                    if not issues
                    else "请按候选处理，同一候选的 domain/range 问题无需分别排除。",
                    locale,
                ),
                rows,
                dropdown_update(
                    gr,
                    choices,
                    empty_label=tr("暂无校验候选", locale),
                    value=choices[0][1] if choices else None,
                ),
                state.validation_version,
            )

        async def select(
            run_id: str | None, target_id: str | None, chinese: bool
        ) -> tuple[Any, ...]:
            locale = "zh-CN" if chinese else "en"
            if not run_id or not target_id:
                return (
                    "",
                    dropdown_update(gr, [], empty_label=tr("暂无证据", locale)),
                    gr.update(choices=[]),
                    gr.update(choices=[]),
                    gr.update(choices=[]),
                    gr.update(choices=[]),
                )
            report = await service.validate_run(run_id)
            state = service.show_run(run_id)
            issues = [
                item
                for item in report.issues
                if item.target_id == target_id and item.status in {"open", "deferred"}
            ]
            if not issues:
                return (
                    tr("该候选已处理。", locale),
                    dropdown_update(gr, [], empty_label=tr("暂无证据", locale)),
                    gr.update(choices=[]),
                    gr.update(choices=[]),
                    gr.update(choices=[]),
                    gr.update(choices=[]),
                )
            allowed = sorted({value for item in issues for value in item.allowed_actions})
            actions = [item for item in ACTION_CHOICES if item[1] in allowed]
            evidence_ids = sorted({eid for item in issues for eid in item.evidence_ids})
            schema = state.output_schema
            graph_entities = await service.graph_store.list_entities()
            known_entities = {item.id: item for item in [*graph_entities, *state.entities]}
            entity_choices = [
                (f"{item.name} · {item.entity_type} · {item.id}", item.id)
                for item in sorted(known_entities.values(), key=lambda value: value.name.casefold())
                if item.active
            ]
            return (
                _candidate_detail(issues, state.validation_version, locale),
                dropdown_update(
                    gr,
                    evidence_ids,
                    empty_label=tr("暂无证据", locale),
                    value=evidence_ids[0] if evidence_ids else None,
                ),
                gr.update(choices=actions, value=actions[0][1] if actions else None),
                gr.update(choices=[item.id for item in schema.relations] if schema else []),
                gr.update(choices=[item.id for item in schema.entity_types] if schema else []),
                gr.update(choices=entity_choices, value=None),
            )

        def replacement_payload(
            selected_action: str,
            selected_endpoint: str,
            selected_relation: str | None,
            selected_type: str | None,
            selected_link: str | None,
        ) -> dict[str, Any]:
            if selected_action == "replace_relation":
                return {"relation": selected_relation}
            if selected_action == "replace_entity_type":
                return {"endpoint": selected_endpoint, "entity_type": selected_type}
            if selected_action == "replace_entity_link":
                return {
                    "endpoint": selected_endpoint,
                    "entity_id": (selected_link or "").strip() or None,
                }
            return {}

        async def preview(
            run_id: str,
            target_id: str,
            selected_action: ValidationAction,
            selected_endpoint: str,
            selected_relation: str | None,
            selected_type: str | None,
            selected_link: str | None,
            expected_version: int,
            chinese: bool,
        ) -> tuple[str, dict[str, Any]]:
            report = await service.validate_run(run_id)
            issue_ids = [
                item.id
                for item in report.issues
                if item.target_id == target_id and item.status in {"open", "deferred"}
            ]
            payload = await service.preview_validation_correction(
                run_id,
                issue_ids,
                selected_action,
                replacement_payload(
                    selected_action,
                    selected_endpoint,
                    selected_relation,
                    selected_type,
                    selected_link,
                ),
                expected_version,
            )
            locale = "zh-CN" if chinese else "en"
            return _preview_comparison(payload, locale), payload

        async def submit(
            run_id: str,
            target_id: str,
            selected_action: ValidationAction,
            selected_endpoint: str,
            selected_relation: str | None,
            selected_type: str | None,
            selected_link: str | None,
            name: str,
            note: str,
            rid: str,
            expected_version: int,
            confirmed: bool,
            chinese: bool,
        ) -> tuple[str, dict[str, Any]]:
            if not confirmed:
                raise ValueError("请先预览并确认修正影响")
            report = await service.validate_run(run_id)
            issue_ids = [
                item.id
                for item in report.issues
                if item.target_id == target_id and item.status in {"open", "deferred"}
            ]
            state = await service.apply_validation_correction(
                run_id,
                issue_ids,
                selected_action,
                replacement_payload(
                    selected_action,
                    selected_endpoint,
                    selected_relation,
                    selected_type,
                    selected_link,
                ),
                name,
                note,
                rid,
                expected_version,
            )
            progress = service.review_progress(run_id)
            auto_resumed = False
            resume_error = ""
            reviews_clear = not any(
                progress[key]
                for key in (
                    "entity_pending",
                    "claim_pending",
                    "visual_pending",
                    "validation_pending",
                    "review_sync_pending",
                )
            )
            retry_commit = progress["status"] == "failed" and state.failed_node == "commit_graph"
            should_resume = (
                selected_action != "defer"
                and reviews_clear
                and progress["status"] != "completed"
                and progress["node"] != "prepare_graph_commit"
                and not retry_commit
            )
            if should_resume:
                try:
                    service.executions.enqueue(
                        run_id,
                        "resume",
                        expected_version=progress["execution"]["version"],
                    )
                    auto_resumed = True
                except ExecutionConflict as exc:
                    latest = service.executions.view(run_id)
                    latest_task = service.executions.repository.get(run_id)
                    if (
                        latest["active"]
                        and latest_task is not None
                        and latest_task.operation == "resume"
                    ):
                        auto_resumed = True
                    else:
                        resume_error = str(exc)
            locale = "zh-CN" if chinese else "en"
            if locale == "en":
                message = (
                    f"**Correction applied.** Candidate version "
                    f"{state.validation_version}; {state.validation.blocking_count} "
                    "blocking issues remain."
                )
            else:
                message = (
                    f"**已应用修正。** 候选版本 {state.validation_version}，"
                    f"剩余阻断问题 {state.validation.blocking_count}。"
                )
            if auto_resumed:
                message += (
                    " The run resumed automatically from its safe checkpoint."
                    if locale == "en"
                    else " 运行已从安全检查点自动恢复。"
                )
            elif resume_error:
                error_help = _resume_error_help(resume_error, locale)
                message += (
                    f" The correction was saved, but auto-resume failed: "
                    f"{error_help} (`{resume_error}`)."
                    if locale == "en"
                    else f" 修正已保存，但自动恢复失败：{error_help}（`{resume_error}`）。"
                )
            return message, {
                "run_id": run_id,
                "auto_resumed": auto_resumed,
                "resume_error": resume_error,
            }

        def reset_form(chinese: bool) -> tuple[Any, ...]:
            locale = "zh-CN" if chinese else "en"
            return (
                gr.update(value=None),
                gr.update(value="subject"),
                gr.update(value=None),
                gr.update(value=None),
                gr.update(value=None),
                "",
                {},
                "",
                "",
                uuid4().hex,
                False,
                _action_help(None, locale),
            )

        def navigate_after_apply(result: dict[str, Any], chinese: bool) -> tuple[Any, ...]:
            if not result.get("auto_resumed"):
                return (gr.update(), gr.update(), gr.update(), gr.update())
            locale = "zh-CN" if chinese else "en"
            gr.Info(tr("全部检验问题已解决。", locale))
            return (
                gr.update(value=result["run_id"]),
                gr.update(value="build-execution"),
                gr.update(
                    choices=[("新建构建", "build"), ("执行任务", "execution")],
                    value="build",
                    visible=True,
                ),
                gr.update(selected="build"),
            )

        async def evidence_preview(
            run_id: str | None, eid: str | None, chinese: bool
        ) -> tuple[Any, Any]:
            locale = "zh-CN" if chinese else "en"
            if not eid or not run_id:
                return tr("无可定位证据", locale), gr.update(value=None, visible=False)
            text, image = await controller.evidence(run_id, eid)
            return text, gr.update(value=image, visible=image is not None)

        for trigger in (refresh.click, run.change, stage.input, status.input):
            trigger(
                guard_ui(gr, load, 4),
                [run, stage, status, language_switch],
                [summary, table, candidate, version_state],
            )
        show_all_runs.change(
            lambda include_all, chinese: dropdown_update(
                gr,
                controller.runs(
                    "validation",
                    include_all=include_all,
                    locale="zh-CN" if chinese else "en",
                ),
                empty_label=tr("暂无运行", "zh-CN" if chinese else "en"),
            ),
            [show_all_runs, language_switch],
            run,
        ).then(
            guard_ui(gr, load, 4),
            [run, stage, status, language_switch],
            [summary, table, candidate, version_state],
        )
        language_switch.change(
            guard_ui(gr, load, 4),
            [run, stage, status, language_switch],
            [summary, table, candidate, version_state],
        ).then(
            guard_ui(gr, select, 6),
            [run, candidate, language_switch],
            [detail, evidence, action, relation, entity_type, entity_link],
        ).then(
            lambda selected, chinese: _action_help(
                selected, "zh-CN" if chinese else "en"
            ),
            [action, language_switch],
            action_explanation,
        )
        candidate.change(
            guard_ui(gr, select, 6),
            [run, candidate, language_switch],
            [detail, evidence, action, relation, entity_type, entity_link],
        )
        evidence.change(
            guard_ui(gr, evidence_preview, 2),
            [run, evidence, language_switch],
            [evidence_text, evidence_image],
        )
        action.change(
            lambda selected, chinese: _action_help(
                selected, "zh-CN" if chinese else "en"
            ),
            [action, language_switch],
            action_explanation,
        )
        preview_button.click(
            guard_ui(gr, preview, 2),
            [
                run,
                candidate,
                action,
                endpoint,
                relation,
                entity_type,
                entity_link,
                version_state,
                language_switch,
            ],
            [preview_visual, preview_output],
        )
        apply_button.click(
            guard_ui(gr, submit, 2),
            [
                run,
                candidate,
                action,
                endpoint,
                relation,
                entity_type,
                entity_link,
                reviewer,
                reason,
                request_id,
                version_state,
                confirm,
                language_switch,
            ],
            [output, apply_state],
        ).then(
            reset_form,
            language_switch,
            [
                action,
                endpoint,
                relation,
                entity_type,
                entity_link,
                preview_visual,
                preview_output,
                reviewer,
                reason,
                request_id,
                confirm,
                action_explanation,
            ],
        ).then(
            guard_ui(gr, load, 4),
            [run, stage, status, language_switch],
            [summary, table, candidate, version_state],
        ).then(
            navigate_after_apply,
            [apply_state, language_switch],
            [current_run, navigation_group, navigation_page, workspace_tabs],
        )
    return run
