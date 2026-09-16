"""Execution controls use the same durable service as CLI and API."""

from typing import Any
from uuid import uuid4

from prismke.workflow import PrismKEService


def build_execution_tab(service: PrismKEService) -> None:
    import gradio as gr

    def refresh(run_id: str | None) -> tuple[Any, ...]:
        states = service.runs.list(limit=1000)
        choices = [
            (f"{s.run_id} · {service.executions.view(s.run_id)['status']}", s.run_id)
            for s in states
        ]
        if run_id not in {s.run_id for s in states}:
            run_id = states[0].run_id if states else None
        if not run_id:
            return (
                gr.Dropdown(choices=choices),
                {},
                [],
                0,
                gr.Button(interactive=False),
                gr.Button(interactive=False),
            )
        progress = service.review_progress(run_id)
        execution = progress["execution"]
        rows = [
            [e.version, e.status, e.node, e.reason or "", e.created_at.isoformat()]
            for e in service.executions.repository.events(run_id)
        ]
        return (
            gr.Dropdown(choices=choices, value=run_id),
            execution,
            rows,
            execution["version"],
            gr.Button(interactive=execution["can_cancel"]),
            gr.Button(interactive=progress["can_resume"]),
        )

    def cancel(run_id: str, operator: str, reason: str, version: int) -> str:
        try:
            task = service.executions.cancel(run_id, operator, reason, uuid4().hex, version)
            return f"取消请求已保存：{task.status}"
        except ValueError as exc:
            return f"取消未执行：{exc}；请刷新后核对状态"

    def resume(run_id: str, version: int) -> str:
        try:
            service.executions.enqueue(run_id, "resume", expected_version=version)
            return "恢复已排队"
        except ValueError as exc:
            return f"恢复被阻断：{exc}"

    with gr.Tab("执行任务"):
        run = gr.Dropdown(label="执行运行", choices=[])
        refresh_button = gr.Button("刷新任务")
        status = gr.JSON(label="执行状态")
        events = gr.Dataframe(
            headers=["版本", "状态", "节点", "原因", "时间"], label="执行轨迹", interactive=False
        )
        with gr.Row():
            operator = gr.Textbox(label="取消操作者")
            reason = gr.Textbox(label="取消原因")
        with gr.Row():
            cancel_button = gr.Button("安全取消", interactive=False)
            resume_button = gr.Button("恢复运行", interactive=False)
        output = gr.Textbox(label="执行操作结果", interactive=False)
        version = gr.State(0)
        timer = gr.Timer(2)
        outputs = [run, status, events, version, cancel_button, resume_button]
        timer.tick(refresh, [run], outputs, show_progress="hidden")
        refresh_button.click(refresh, [run], outputs)
        run.input(refresh, [run], outputs)
        cancel_button.click(cancel, [run, operator, reason, version], output).then(
            refresh, [run], outputs
        )
        resume_button.click(resume, [run, version], output).then(refresh, [run], outputs)
