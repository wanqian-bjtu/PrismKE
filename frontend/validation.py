"""Candidate-grouped validation review and deterministic correction UI."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import uuid4

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
from src.workflow import PrismKEService

ACTION_CHOICES = [
    ("交换主语与宾语", "swap_endpoints"),
    ("改选关系", "replace_relation"),
    ("修正实体类型", "replace_entity_type"),
    ("修正实体链接", "replace_entity_link"),
    ("排除候选", "exclude"),
    ("暂缓处理", "defer"),
]


def _safe(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("`", "ˋ")


def _candidate_label(summary: dict[str, Any], count: int, target_id: str) -> str:
    subject = summary.get("subject", {})
    object_value = summary.get("object", {})
    subject_name = subject.get("name", subject) if isinstance(subject, dict) else subject
    object_name = (
        object_value.get("name", object_value.get("literal", object_value))
        if isinstance(object_value, dict)
        else object_value
    )
    short = target_id.rsplit(":", 1)[-1][:6]
    return (
        f"{subject_name} —{summary.get('relation', '')}→ {object_name} · {count}个问题 · #{short}"
    )


def _issue_message(item: Any) -> str:
    if item.code == "SCHEMA_DOMAIN_RANGE" and item.field_path == "subject.entity_type":
        return "主语类型不满足关系 domain 约束"
    if item.code == "SCHEMA_DOMAIN_RANGE" and item.field_path == "object.entity_type":
        return "宾语类型不满足关系 range 约束"
    return str(item.message)


def _candidate_detail(issues: list[Any], validation_version: int) -> str:
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
        f"| **主语** | {_safe(subject.get('name'))} | "
        f"{_safe(subject.get('type'))} | {_safe(domain)} |"
    )
    object_name = object_value.get("name", object_value.get("literal"))
    object_row = (
        f"| **宾语** | {_safe(object_name)} | {_safe(object_value.get('type'))} | "
        f"{_safe(range_value)} |"
    )
    lines = [
        f"### 候选 #{first.target_id.rsplit(':', 1)[-1][:6]}",
        "",
        "| 角色 | 当前值 | 当前类型 | Schema 约束 |",
        "|---|---|---|---|",
        subject_row,
        f"| **关系** | {_safe(summary.get('relation'))} | — | — |",
        object_row,
        "",
        f"**候选版本：** {validation_version}",
        "",
        "**问题：**",
    ]
    for item in issues:
        lines.append(
            f"- `{item.code} · {item.field_path} · #{item.id.rsplit(':', 1)[-1][:6]}`："
            f"{_safe(_issue_message(item))}"
        )
    lines.extend(
        [
            "",
            "请先选择修正动作并预览影响。修正不会调用 LLM/VLM，也不会直接写图。",
        ]
    )
    return "\n".join(lines)


def build_validation_tab(gr: Any, service: PrismKEService) -> Any:
    controller = ReviewController(service)
    run_choices = controller.runs("validation")
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
            preview_button = gr.Button("预览修正影响", variant="secondary")
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

        async def load(
            run_id: str | None, selected_stage: str, selected_status: str
        ) -> tuple[Any, ...]:
            if not run_id:
                return (
                    "请选择运行。",
                    [],
                    dropdown_update(gr, [], empty_label="暂无校验候选"),
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
                        status_label(item.status, "zh-CN"),
                    ]
                )
                choices.append(
                    (_candidate_label(item.candidate_summary, len(values), target_id), target_id)
                )
            return (
                f"### {len(issues)} 个问题，涉及 {len(grouped)} 个候选\n\n"
                + (
                    "本运行无校验问题。"
                    if not issues
                    else "请按候选处理，同一候选的 domain/range 问题无需分别排除。"
                ),
                rows,
                dropdown_update(
                    gr,
                    choices,
                    empty_label="暂无校验候选",
                    value=choices[0][1] if choices else None,
                ),
                state.validation_version,
            )

        async def select(run_id: str | None, target_id: str | None) -> tuple[Any, ...]:
            if not run_id or not target_id:
                return (
                    "",
                    dropdown_update(gr, [], empty_label="暂无证据"),
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
                    "该候选已处理。",
                    dropdown_update(gr, [], empty_label="暂无证据"),
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
                _candidate_detail(issues, state.validation_version),
                dropdown_update(
                    gr,
                    evidence_ids,
                    empty_label="暂无证据",
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
        ) -> dict[str, Any]:
            report = await service.validate_run(run_id)
            issue_ids = [
                item.id
                for item in report.issues
                if item.target_id == target_id and item.status in {"open", "deferred"}
            ]
            return await service.preview_validation_correction(
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
        ) -> str:
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
            return (
                f"**已应用修正。** 候选版本 {state.validation_version}，"
                f"剩余阻断问题 {state.validation.blocking_count}。"
            )

        async def evidence_preview(run_id: str | None, eid: str | None) -> tuple[Any, Any]:
            if not eid or not run_id:
                return "无可定位证据", gr.update(value=None, visible=False)
            text, image = await controller.evidence(run_id, eid)
            return text, gr.update(value=image, visible=image is not None)

        for trigger in (refresh.click, run.change, stage.input, status.input):
            trigger(
                guard_ui(gr, load, 4),
                [run, stage, status],
                [summary, table, candidate, version_state],
            )
        show_all_runs.change(
            lambda include_all: dropdown_update(
                gr,
                controller.runs("validation", include_all=include_all),
                empty_label="暂无运行",
            ),
            show_all_runs,
            run,
        ).then(
            guard_ui(gr, load, 4),
            [run, stage, status],
            [summary, table, candidate, version_state],
        )
        candidate.change(
            guard_ui(gr, select, 6),
            [run, candidate],
            [detail, evidence, action, relation, entity_type, entity_link],
        )
        evidence.change(
            guard_ui(gr, evidence_preview, 2), [run, evidence], [evidence_text, evidence_image]
        )
        preview_button.click(
            guard_ui(gr, preview),
            [run, candidate, action, endpoint, relation, entity_type, entity_link, version_state],
            preview_output,
        )
        apply_button.click(
            guard_ui(gr, submit),
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
            ],
            output,
        ).then(
            guard_ui(gr, load, 4),
            [run, stage, status],
            [summary, table, candidate, version_state],
        ).then(lambda: (False, uuid4().hex), outputs=[confirm, request_id])
    return run
