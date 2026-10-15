"""Selectable review history and explicit correction confirmation."""

from typing import Any
from uuid import uuid4

from frontend.layout import page_header
from frontend.presentation import (
    dropdown_kwargs,
    dropdown_update,
    empty_dropdown_kwargs,
    guard_ui,
)
from src.workflow import PrismKEService


def build_correction_tab(service: PrismKEService) -> None:
    import gradio as gr

    from frontend.review import ReviewController

    controller = ReviewController(service)
    run_choices = controller.runs()
    with gr.Tab("审核历史与纠正", id="corrections"):
        page_header(gr, "corrections")
        run = gr.Dropdown(
            label="纠正运行",
            **dropdown_kwargs(run_choices, empty_label="暂无运行"),
        )
        refresh = gr.Button("刷新审核历史")
        task = gr.Dropdown(label="历史任务", **empty_dropdown_kwargs("暂无记录"))
        event = gr.Dropdown(label="原审核事件", **empty_dropdown_kwargs("暂无记录"))
        with gr.Accordion("审核历史", open=False, elem_classes="technical-detail"):
            history = gr.JSON(label="审核历史")
            current = gr.JSON(label="当前决定与证据")
        evidence_id = gr.Dropdown(label="纠正关联证据", **empty_dropdown_kwargs("暂无证据"))
        evidence_text = gr.Textbox(label="纠正证据原文", lines=6, interactive=False)
        evidence_image = gr.Image(label="纠正证据区域", type="filepath", visible=False)
        version = gr.State(None)
        action = gr.Dropdown(label="替代决定", **empty_dropdown_kwargs("暂无可用决定"))
        candidate = gr.Dropdown(label="替代候选实体", **empty_dropdown_kwargs("暂无候选实体"))
        person = gr.Textbox(label="纠正审核人")
        reason = gr.Textbox(label="纠正原因", lines=3)
        preview_button = gr.Button("预览纠正影响")
        with gr.Accordion("纠正影响", open=False, elem_classes="technical-detail"):
            preview = gr.JSON(label="纠正影响与版本差异")
        correction = gr.State(None)
        confirmed = gr.Checkbox(label="确认应用纠正并保留历史", value=False)
        apply_button = gr.Button("确认应用纠正", variant="stop")
        with gr.Accordion("技术详情", open=False, elem_classes="technical-detail"):
            outcome = gr.JSON(label="纠正状态")

        async def load_tasks(rid: str | None) -> Any:
            if not rid:
                return dropdown_update(gr, [], empty_label="暂无记录")
            events = service.reviews.repository.events(rid)
            choices = []
            for item in {e.task_id: e for e in events}.values():
                if item.kind == "entity":
                    detail = await service.entity_review_detail(rid, item.task_id)
                    label = (detail.get("mention") or {}).get("name", item.task_id)
                else:
                    detail = service.claim_review_detail(rid, item.task_id)
                    label = controller.fact_label(detail["claim"])
                choices.append((label, item.task_id))
            return dropdown_update(gr, choices, empty_label="暂无记录")

        def load_history(rid: str, tid: str | None) -> tuple[Any, Any]:
            events = [e for e in service.reviews.repository.events(rid) if e.task_id == tid]
            return (
                dropdown_update(
                    gr,
                    [
                        (f"{e.action} · {e.reviewer} · v{e.version}", e.id)
                        for e in events
                        if e.action not in {"defer", "commit_correction"}
                    ],
                    empty_label="暂无记录",
                ),
                [e.model_dump(mode="json") for e in events],
            )

        async def load_event(rid: str, eid: str | None) -> tuple[Any, ...]:
            if not eid:
                return (
                    {},
                    None,
                    dropdown_update(gr, [], empty_label="暂无可用决定"),
                    dropdown_update(gr, [], empty_label="暂无候选实体"),
                    dropdown_update(gr, [], empty_label="暂无证据"),
                )
            selected = next(e for e in service.reviews.repository.events(rid) if e.id == eid)
            detail = (
                await service.entity_review_detail(rid, selected.task_id)
                if selected.kind == "entity"
                else service.claim_review_detail(rid, selected.task_id)
            )
            candidates = [
                (f"{c['entity']['name']} · {c['entity']['entity_type']}", c["entity_id"])
                for c in detail.get("candidates", [])
                if c["entity"]
            ]
            actions = [("链接候选", "link"), ("创建新实体", "create"), ("排除错误提及", "reject")]
            if selected.kind == "claim":
                actions = [("批准事实", "approve"), ("拒绝事实", "reject")]
            return (
                detail,
                detail["task"]["version"],
                dropdown_update(gr, actions, empty_label="暂无可用决定"),
                dropdown_update(
                    gr,
                    candidates,
                    empty_label="暂无候选实体",
                    visible=selected.kind == "entity",
                ),
                dropdown_update(
                    gr,
                    detail["evidence_ids"],
                    empty_label="暂无证据",
                    value=detail["evidence_ids"][0] if detail["evidence_ids"] else None,
                ),
            )

        async def show_evidence(rid: str, eid: str | None) -> tuple[str, Any]:
            text, image = await controller.evidence(rid, eid) if eid else ("", None)
            return text, gr.update(value=image, visible=image is not None)

        async def propose(
            rid: str,
            eid: str,
            decision: str,
            entity: str | None,
            expected: int,
            reviewer: str,
            comment: str,
        ) -> tuple[Any, str, Any]:
            proposal = await service.corrections.propose(
                rid,
                eid,
                decision,
                entity if decision == "link" else None,
                expected,
                reviewer,
                comment,
                uuid4().hex,
            )
            return proposal.model_dump(mode="json"), proposal.id, gr.update(value=False)

        async def apply(cid: str | None, confirm: bool) -> Any:
            if cid is None:
                raise ValueError("请先生成纠正预览")
            state = await service.corrections.apply(cid, confirm)
            return service.review_progress(state.run_id)

        def refresh_runs() -> Any:
            choices = controller.runs()
            return dropdown_update(gr, choices, empty_label="暂无运行")

        run.change(guard_ui(gr, load_tasks), [run], [task])
        refresh.click(refresh_runs, outputs=[run]).then(guard_ui(gr, load_tasks), [run], [task])
        task.change(guard_ui(gr, load_history, 2), [run, task], [event, history])
        event.change(
            guard_ui(gr, load_event, 5),
            [run, event],
            [current, version, action, candidate, evidence_id],
        )
        evidence_id.change(
            guard_ui(gr, show_evidence, 2),
            [run, evidence_id],
            [evidence_text, evidence_image],
        )
        preview_button.click(
            guard_ui(gr, propose, 3),
            [run, event, action, candidate, version, person, reason],
            [preview, correction, confirmed],
        )
        apply_button.click(guard_ui(gr, apply), [correction, confirmed], [outcome])
