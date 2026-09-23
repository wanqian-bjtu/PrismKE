"""Selectable validation issue review, sharing the application service."""

from typing import Any

from frontend.layout import page_header
from frontend.review import ReviewController
from src.workflow import PrismKEService


def build_validation_tab(gr: Any, service: PrismKEService) -> None:
    controller = ReviewController(service)
    with gr.Tab("校验问题", id="validation"):
        page_header(gr, "validation")
        with gr.Row():
            run = gr.Dropdown(label="校验运行", choices=controller.runs(), value=None)
            stage = gr.Dropdown(
                label="校验阶段",
                choices=["全部", "structure", "schema", "reference", "evidence"],
                value="全部",
            )
            code = gr.Dropdown(label="问题代码", choices=["全部"], value="全部")
            status = gr.Dropdown(
                label="问题状态", choices=["open", "excluded", "全部"], value="open"
            )
        refresh = gr.Button("刷新校验问题")
        summary = gr.Textbox(label="校验汇总", interactive=False)
        table = gr.Dataframe(headers=["问题代码", "阶段", "状态", "说明"], interactive=False)
        issue = gr.Dropdown(label="选择校验问题", choices=[])
        with gr.Accordion("问题详情", open=False, elem_classes="technical-detail"):
            detail = gr.JSON(label="问题与候选影响")
        evidence = gr.Dropdown(label="问题证据", choices=[])
        evidence_text = gr.Textbox(label="校验证据文本", interactive=False)
        evidence_image = gr.Image(label="校验证据区域", interactive=False, visible=False)
        reviewer = gr.Textbox(label="校验审核人")
        comment = gr.Textbox(label="排除意见")
        confirm = gr.Checkbox(label="确认排除此候选，保留原始问题及审计")
        exclude = gr.Button("排除候选", variant="stop", interactive=False)
        output = gr.Textbox(label="校验操作结果", interactive=False)

        async def load(
            run_id: str | None, selected_stage: str, selected_code: str, selected_status: str
        ) -> tuple[Any, ...]:
            if not run_id:
                return (
                    "请选择运行",
                    [],
                    gr.update(choices=[], value=None),
                    gr.update(choices=["全部"], value="全部"),
                )
            report = await service.validate_run(run_id)
            codes = sorted({i.code for i in report.issues})
            issues = [
                i
                for i in report.issues
                if (selected_stage == "全部" or i.stage == selected_stage)
                and (selected_code == "全部" or i.code == selected_code)
                and (selected_status == "全部" or i.status == selected_status)
            ]
            return (
                f"阻断问题 {report.blocking_count} · 正常事实 {report.passed_count}",
                [[i.code, i.stage, i.status, i.message] for i in issues],
                gr.update(
                    choices=[(f"{i.code} · {i.message}", i.id) for i in issues],
                    value=issues[0].id if issues else None,
                ),
                gr.update(
                    choices=["全部", *codes],
                    value=selected_code if selected_code in codes else "全部",
                ),
            )

        async def select(run_id: str | None, issue_id: str | None) -> tuple[Any, ...]:
            if not run_id or not issue_id:
                return {}, gr.update(choices=[], value=None), gr.update(interactive=False)
            report = await service.validate_run(run_id)
            item = next((i for i in report.issues if i.id == issue_id), None)
            if item is None:
                return {}, gr.update(choices=[], value=None), gr.update(interactive=False)
            return (
                item.model_dump(mode="json"),
                gr.update(
                    choices=item.evidence_ids,
                    value=item.evidence_ids[0] if item.evidence_ids else None,
                ),
                gr.update(interactive=item.status == "open" and "exclude" in item.allowed_actions),
            )

        async def preview(run_id: str | None, eid: str | None) -> tuple[Any, Any]:
            if not eid or not run_id:
                return "无可定位证据", gr.update(value=None, visible=False)
            try:
                text, image = await controller.evidence(run_id, eid)
                return text, gr.update(value=image, visible=image is not None)
            except Exception:
                return "证据读取失败或完整性校验失败", gr.update(value=None, visible=False)

        async def submit(run_id: str, issue_id: str, name: str, note: str, confirmed: bool) -> str:
            if not confirmed:
                return "请先确认排除影响"
            try:
                await service.exclude_validation_issue(run_id, issue_id, name, note)
                return "已排除候选；原始问题和审核审计已保留。请刷新队列并继续处理。"
            except ValueError as exc:
                return str(exc)

        for trigger in (refresh.click, run.change, stage.input, code.input, status.input):
            trigger(load, [run, stage, code, status], [summary, table, issue, code])
        issue.change(select, [run, issue], [detail, evidence, exclude])
        evidence.change(preview, [run, evidence], [evidence_text, evidence_image])
        exclude.click(submit, [run, issue, reviewer, comment, confirm], [output]).then(
            load, [run, stage, code, status], [summary, table, issue, code]
        ).then(lambda: False, outputs=[confirm])
