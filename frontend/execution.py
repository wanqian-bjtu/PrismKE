"""Execution controls use the same durable service as CLI and API frontend."""

from typing import Any
from uuid import uuid4

from frontend.layout import page_header
from src.domain import RequestReconciliation
from src.workflow import PrismKEService


def build_execution_tab(
    service: PrismKEService,
    llm_api_key_input: Any | None = None,
    vlm_api_key_input: Any | None = None,
) -> None:
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
                gr.update(choices=choices, value=None),
                "### 尚无执行任务",
                "尚无 PDF 解析决定。",
                [],
                [],
                {},
                [],
                gr.update(choices=[], value=None),
                0,
                gr.update(interactive=False),
                gr.update(interactive=False),
                gr.update(interactive=False),
                gr.update(interactive=False),
            )
        progress = service.review_progress(run_id)
        execution = progress["execution"]
        branches = service.executions.branch_progress(run_id)
        requests = service.executions.repository.requests(run_id)
        unknown = [
            item
            for item in requests
            if (item["status"] == "sent" and not item.get("recoverable"))
            or item["status"] == "unknown"
            or (item["status"] == "completed" and not item["usage_known"])
        ]
        event_rows = [
            [e.version, e.status, e.node, e.reason or "", e.created_at.isoformat()]
            for e in service.executions.repository.events(run_id)
        ]
        branch_rows = [
            [
                item.branch,
                item.status,
                f"{item.completed}/{item.total if item.total is not None else '?'}",
                item.current_asset or "",
                item.updated_at.isoformat(),
            ]
            for item in branches
        ]
        request_rows = [
            [
                item["request_id"],
                item["status"],
                item["metadata"].get("node", ""),
                item["metadata"].get("asset_id", ""),
                "已知" if item["usage_known"] else "未知",
            ]
            for item in requests
        ]
        parse_view = service.pdf_parse_view(run_id)
        decision = parse_view["decision"]
        if decision is None:
            parser_summary = f"请求模式：`{parse_view['mode']}` · 尚未完成 PDF 预检"
            fallback_available = False
        else:
            metrics = decision.complexity
            parser_summary = (
                f"**请求模式** `{decision.requested_mode}` · **实际解析器** "
                f"`{decision.actual_parser}` · **原因** "
                f"`{', '.join(decision.reason_codes) or '无'}`\n\n"
                f"页数 {metrics.total_pages} · 无原生文本页 "
                f"{len(metrics.no_native_text_pages)} · 短文本页 "
                f"{len(metrics.short_text_pages)} · 表格候选页 "
                f"{len(metrics.table_candidate_pages)} · 绘图密集页 "
                f"{len(metrics.drawing_dense_pages)} · 多栏异常页 "
                f"{len(metrics.unstable_multicolumn_pages)}"
            )
            if decision.actual_parser == "mineru":
                parser_summary += (
                    f"\n\nMinerU 状态 `{decision.mineru_status or 'pending'}` · "
                    f"任务 `{decision.mineru_job_id or '尚未创建'}` · "
                    f"产物清单 "
                    f"`{(decision.artifact_manifest_hash or '尚未生成')[:16]}`"
                )
            fallback_available = (
                execution["status"] == "parser_blocked"
                and str(decision.requested_mode) == "auto"
                and str(decision.actual_parser) == "mineru"
                and not parse_view["fallback_approved"]
            )
        summary = (
            f"### {execution['status']}\n"
            f"业务状态：`{progress['status']}` · 当前节点：`{execution['node']}` · "
            f"尝试次数：{execution['attempt']} · 未知请求：{len(unknown)}\n\n"
            f"实体待审 {progress['entity_pending']} · 事实待审 "
            f"{progress['claim_pending']} · 校验问题 {progress['validation_pending']}"
        )
        request_choices = [item["request_id"] for item in unknown]
        return (
            gr.update(choices=choices, value=run_id),
            summary,
            parser_summary,
            branch_rows,
            event_rows,
            execution,
            request_rows,
            gr.update(
                choices=request_choices,
                value=request_choices[0] if request_choices else None,
            ),
            execution["version"],
            gr.update(interactive=execution["can_cancel"]),
            gr.update(interactive=progress["can_resume"]),
            gr.update(interactive=bool(request_choices)),
            gr.update(interactive=fallback_available),
        )

    def cancel(run_id: str, operator: str, reason: str, version: int) -> str:
        try:
            task = service.executions.cancel(run_id, operator, reason, uuid4().hex, version)
            return f"取消请求已保存：{task.status}"
        except ValueError as exc:
            return f"取消未执行：{exc}；请刷新后核对状态"

    def resume(
        run_id: str,
        version: int,
        llm_api_key: str = "",
        vlm_api_key: str = "",
    ) -> str:
        try:
            service.attach_run_credentials(
                run_id,
                llm_api_key=llm_api_key,
                vlm_api_key=vlm_api_key,
            )
            service.executions.enqueue(run_id, "resume", expected_version=version)
            return "恢复已排队"
        except ValueError as exc:
            return f"恢复被阻断：{exc}"

    def reconcile(
        run_id: str,
        request_id: str,
        outcome: str,
        operator: str,
        reason: str,
        version: int,
    ) -> str:
        try:
            result = service.executions.reconcile_request(
                run_id,
                RequestReconciliation(
                    request_id=request_id,
                    outcome=outcome,
                    operator=operator.strip(),
                    reason=reason.strip(),
                    expected_execution_version=version,
                ),
            )
            return f"核对事件已保存：{result['event']['outcome']}"
        except ValueError as exc:
            return f"核对未执行：{exc}；请刷新后重试"

    def approve_pdf_fallback(
        run_id: str,
        operator: str,
        reason: str,
        version: int,
    ) -> str:
        try:
            result = service.approve_pdf_parser_fallback(
                run_id,
                operator,
                reason,
                uuid4().hex,
                version,
            )
            return f"降级已审计并排队：执行版本 {result['version']}"
        except (KeyError, ValueError) as exc:
            return f"降级未执行：{exc}；请刷新后核对解析状态"

    with gr.Tab("执行任务", id="execution"):
        page_header(gr, "execution")
        with gr.Row():
            run = gr.Dropdown(label="运行", choices=[], scale=4)
            refresh_button = gr.Button("刷新", scale=1)
        summary = gr.Markdown("### 尚无执行任务")
        with gr.Accordion("PDF 解析决定", open=True):
            parser_summary = gr.Markdown("尚无 PDF 解析决定。")
            gr.Markdown(
                "自动模式选择 MinerU 后不会静默回退。只有解析阻断时，"
                "操作者填写身份与原因，才可改用 PyMuPDF 重试。"
            )
            with gr.Row():
                fallback_operator = gr.Textbox(label="降级确认人")
                fallback_reason = gr.Textbox(label="降级原因")
            fallback_button = gr.Button("确认使用 PyMuPDF 重试", interactive=False)
            fallback_output = gr.Textbox(label="降级结果", interactive=False)
        branches = gr.Dataframe(
            headers=["分支", "状态", "进度", "当前资产", "更新时间"],
            label="分支进度",
            interactive=False,
            wrap=True,
        )
        events = gr.Dataframe(
            headers=["版本", "状态", "节点", "原因", "时间"],
            label="执行时间线",
            interactive=False,
            wrap=True,
        )
        with gr.Row():
            operator = gr.Textbox(label="取消操作者")
            reason = gr.Textbox(label="取消原因")
        with gr.Row():
            cancel_button = gr.Button("安全取消", interactive=False)
            resume_button = gr.Button("恢复运行", interactive=False)
        output = gr.Textbox(label="执行操作结果", interactive=False)

        with gr.Accordion("未知 Provider 请求核对", open=False):
            gr.Markdown(
                "只有经人工确认“未发送”或“未计费”的请求可重新派发；可能已计费的请求仍保持阻断。"
            )
            request_table = gr.Dataframe(
                headers=["请求 ID", "状态", "节点", "资产", "用量"],
                interactive=False,
                wrap=True,
            )
            request_id = gr.Dropdown(label="待核对请求", choices=[])
            outcome = gr.Dropdown(
                [
                    ("确认未发送", "confirmed_not_sent"),
                    ("确认未计费", "confirmed_not_billed"),
                    ("可能已计费，继续阻断", "possibly_billed"),
                ],
                value="possibly_billed",
                label="核对结论",
            )
            with gr.Row():
                reconcile_operator = gr.Textbox(label="核对人")
                reconcile_reason = gr.Textbox(label="核对依据")
            reconcile_button = gr.Button("保存核对事件", interactive=False)
            reconcile_output = gr.Textbox(label="核对结果", interactive=False)

        with gr.Accordion("技术详情", open=False, elem_classes="technical-detail"):
            status = gr.JSON(label="完整执行状态")

        version = gr.State(0)
        timer = gr.Timer(2)
        outputs = [
            run,
            summary,
            parser_summary,
            branches,
            events,
            status,
            request_table,
            request_id,
            version,
            cancel_button,
            resume_button,
            reconcile_button,
            fallback_button,
        ]
        timer.tick(refresh, [run], outputs, show_progress="hidden")
        refresh_button.click(refresh, [run], outputs)
        run.input(refresh, [run], outputs)
        cancel_button.click(cancel, [run, operator, reason, version], output).then(
            refresh, [run], outputs
        )
        resume_inputs = [run, version]
        if llm_api_key_input is not None and vlm_api_key_input is not None:
            resume_inputs.extend([llm_api_key_input, vlm_api_key_input])
        resume_button.click(resume, resume_inputs, output).then(refresh, [run], outputs)
        reconcile_button.click(
            reconcile,
            [
                run,
                request_id,
                outcome,
                reconcile_operator,
                reconcile_reason,
                version,
            ],
            reconcile_output,
        ).then(refresh, [run], outputs)
        fallback_button.click(
            approve_pdf_fallback,
            [run, fallback_operator, fallback_reason, version],
            fallback_output,
        ).then(refresh, [run], outputs)
