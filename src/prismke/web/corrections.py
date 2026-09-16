"""Selectable review history and explicit correction confirmation."""

from typing import Any
from uuid import uuid4

from prismke.workflow import PrismKEService


def build_correction_tab(service: PrismKEService) -> None:
    import gradio as gr

    from prismke.web.review import ReviewController

    controller = ReviewController(service)
    with gr.Tab("审核历史与纠正"):
        run = gr.Dropdown(controller.runs(), label="纠正运行", value=None)
        refresh = gr.Button("刷新审核历史")
        task = gr.Dropdown(label="历史任务", choices=[], value=None)
        event = gr.Dropdown(label="原审核事件", choices=[], value=None)
        history = gr.JSON(label="审核历史")
        current = gr.JSON(label="当前决定与证据")
        evidence_id = gr.Dropdown(label="纠正关联证据", choices=[], value=None)
        evidence_text = gr.Textbox(label="纠正证据原文", lines=6, interactive=False)
        evidence_image = gr.Image(label="纠正证据区域", type="filepath", visible=False)
        version = gr.State(None)
        action = gr.Radio(label="替代决定", choices=[], value=None)
        candidate = gr.Dropdown(label="替代候选实体", choices=[], value=None)
        person = gr.Textbox(label="纠正审核人")
        reason = gr.Textbox(label="纠正原因", lines=3)
        preview_button = gr.Button("预览纠正影响")
        preview = gr.JSON(label="纠正影响与版本差异")
        correction = gr.State(None)
        confirmed = gr.Checkbox(label="确认应用纠正并保留历史", value=False)
        apply_button = gr.Button("确认应用纠正", variant="stop")
        outcome = gr.JSON(label="纠正状态")

        async def load_tasks(rid: str | None) -> Any:
            if not rid:
                return gr.update(choices=[], value=None)
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
            return gr.update(choices=choices, value=None)

        def load_history(rid: str, tid: str | None) -> tuple[Any, Any]:
            events = [e for e in service.reviews.repository.events(rid) if e.task_id == tid]
            return (
                gr.update(
                    choices=[
                        (f"{e.action} · {e.reviewer} · v{e.version}", e.id)
                        for e in events
                        if e.action not in {"defer", "commit_correction"}
                    ],
                    value=None,
                ),
                [e.model_dump(mode="json") for e in events],
            )

        async def load_event(rid: str, eid: str | None) -> tuple[Any, ...]:
            if not eid:
                return (
                    {},
                    None,
                    gr.update(choices=[], value=None),
                    gr.update(choices=[], value=None),
                    gr.update(choices=[], value=None),
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
                gr.update(choices=actions, value=None),
                gr.update(choices=candidates, value=None, visible=selected.kind == "entity"),
                gr.update(
                    choices=detail["evidence_ids"],
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
                raise gr.Error("请先生成纠正预览")
            try:
                state = await service.corrections.apply(cid, confirm)
            except ValueError as exc:
                raise gr.Error(str(exc)) from exc
            return service.review_progress(state.run_id)

        run.change(load_tasks, [run], [task])
        refresh.click(lambda: gr.update(choices=controller.runs()), outputs=[run]).then(
            load_tasks, [run], [task]
        )
        task.change(load_history, [run, task], [event, history])
        event.change(load_event, [run, event], [current, version, action, candidate, evidence_id])
        evidence_id.change(show_evidence, [run, evidence_id], [evidence_text, evidence_image])
        preview_button.click(
            propose,
            [run, event, action, candidate, version, person, reason],
            [preview, correction, confirmed],
        )
        apply_button.click(apply, [correction, confirmed], [outcome])
