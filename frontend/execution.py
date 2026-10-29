"""Execution controls use the same durable service as CLI and API frontend."""

from pathlib import Path
from typing import Any
from uuid import uuid4

from frontend.i18n import tr
from frontend.layout import compact_dropdown, page_header
from frontend.presentation import (
    dropdown_update,
    empty_dropdown_kwargs,
    guard_ui,
    status_label,
)
from frontend.run_presentation import (
    branch_label,
    friendly_run_choices,
    local_time,
    node_label,
    provider_usage_label,
    workflow_node_guide,
)
from src.domain import RequestReconciliation
from src.workflow import PrismKEService


def build_execution_tab(
    service: PrismKEService,
    llm_api_key_input: Any | None = None,
    vlm_api_key_input: Any | None = None,
    language_switch: Any | None = None,
) -> Any:
    import gradio as gr

    locale_control = language_switch or gr.State(False)

    def action_help(
        execution: dict[str, Any], can_resume: bool, locale: object
    ) -> str:
        if execution["status"] == "completed":
            return tr("安全取消：已完成任务不可取消。恢复运行：已完成任务不可恢复。", locale)
        cancel = (
            tr("安全取消：当前任务正在排队或执行，可请求在安全检查点停止。", locale)
            if execution["can_cancel"]
            else tr("安全取消：仅排队中、运行中或正在取消的任务可用。", locale)
        )
        resume = (
            tr("恢复运行：当前阻断条件已解除，可从检查点继续。", locale)
            if can_resume
            else tr("恢复运行：仅中断、失败、凭据缺失或审核完成后可继续的任务可用。", locale)
        )
        return f"{cancel}\n\n{resume}"

    def refresh(run_id: str | None, chinese: bool = False) -> tuple[Any, ...]:
        locale = "zh-CN" if chinese else "en"
        states = service.runs.list(limit=1000)
        choices = friendly_run_choices(service, states, locale=locale)
        if run_id not in {s.run_id for s in states}:
            run_id = states[0].run_id if states else None
        if not run_id:
            return (
                dropdown_update(gr, [], empty_label=tr("暂无运行", locale)),
                f"### {tr('尚无执行任务', locale)}",
                tr("尚无 PDF 解析决定。", locale),
                [],
                [],
                {},
                [],
                dropdown_update(gr, [], empty_label=tr("暂无待核对请求", locale)),
                0,
                gr.update(interactive=False),
                gr.update(interactive=False),
                gr.update(interactive=False),
                gr.update(interactive=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                tr("尚未选择任务。", locale),
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
            [
                e.version,
                status_label(e.status, locale),
                node_label(e.node, locale),
                e.reason or "",
                local_time(e.created_at),
            ]
            for e in service.executions.repository.events(run_id)
        ]
        branch_rows = [
            [
                branch_label(item.branch, locale),
                status_label(item.status, locale),
                f"{item.completed}/{item.total if item.total is not None else '?'}",
                item.current_asset or "",
                local_time(item.updated_at),
            ]
            for item in branches
        ]
        request_rows = [
            [
                item["request_id"],
                status_label(item["status"], locale),
                node_label(item["metadata"].get("node", ""), locale),
                item["metadata"].get("asset_id") or tr("文档级", locale),
                provider_usage_label(item, locale),
            ]
            for item in requests
        ]
        state = service.show_run(run_id)
        is_pdf = Path(state.input_path).suffix.lower() == ".pdf"
        parse_view = service.pdf_parse_view(run_id)
        decision = parse_view["decision"]
        if decision is None:
            parser_summary = (
                f"Requested mode: `{parse_view['mode']}` · PDF preflight not completed"
                if locale == "en"
                else f"请求模式：`{parse_view['mode']}` · 尚未完成 PDF 预检"
            )
            fallback_available = False
        else:
            metrics = decision.complexity
            if locale == "en":
                parser_summary = (
                    f"**Requested mode** `{decision.requested_mode}` · **Actual parser** "
                    f"`{decision.actual_parser}` · **Reasons** "
                    f"`{', '.join(decision.reason_codes) or 'None'}`\n\n"
                    f"Pages {metrics.total_pages} · Pages without native text "
                    f"{len(metrics.no_native_text_pages)} · Short-text pages "
                    f"{len(metrics.short_text_pages)} · Table candidates "
                    f"{len(metrics.table_candidate_pages)} · Drawing-dense pages "
                    f"{len(metrics.drawing_dense_pages)} · Unstable multi-column pages "
                    f"{len(metrics.unstable_multicolumn_pages)}"
                )
            else:
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
                if locale == "en":
                    parser_summary += (
                        f"\n\nMinerU status "
                        f"`{status_label(decision.mineru_status or 'pending', locale)}` · "
                        f"Job `{decision.mineru_job_id or 'Not created'}` · "
                        f"Artifact manifest "
                        f"`{(decision.artifact_manifest_hash or 'Not generated')[:16]}`"
                    )
                else:
                    parser_summary += (
                        f"\n\nMinerU 状态 "
                        f"`{status_label(decision.mineru_status or 'pending', locale)}` · "
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
            f"### {status_label(execution['status'], locale)}\n"
            f"{tr('业务状态', locale)}：`{status_label(progress['status'], locale)}` · "
            f"{tr('当前节点', locale)}：`{node_label(execution['node'], locale)}` · "
            f"{tr('尝试次数', locale)}：{execution['attempt']} · "
            f"{tr('未知请求', locale)}：{len(unknown)}\n\n"
            f"{tr('实体待审', locale)} {progress['entity_pending']} · "
            f"{tr('事实待审', locale)} {progress['claim_pending']} · "
            f"{tr('校验问题', locale)} {progress['validation_pending']}"
        )
        request_choices = [item["request_id"] for item in unknown]
        return (
            dropdown_update(
                gr,
                choices,
                empty_label=tr("暂无运行", locale),
                value=run_id,
            ),
            summary,
            parser_summary,
            branch_rows,
            event_rows,
            execution,
            request_rows,
            dropdown_update(
                gr,
                request_choices,
                empty_label=tr("暂无待核对请求", locale),
                value=request_choices[0] if request_choices else None,
            ),
            execution["version"],
            gr.update(interactive=execution["can_cancel"]),
            gr.update(interactive=progress["can_resume"]),
            gr.update(interactive=bool(request_choices)),
            gr.update(interactive=fallback_available),
            gr.update(visible=is_pdf),
            gr.update(visible=fallback_available),
            gr.update(visible=bool(request_choices)),
            action_help(execution, progress["can_resume"], locale),
        )

    def cancel(run_id: str, operator: str, reason: str, version: int) -> str:
        task = service.executions.cancel(run_id, operator, reason, uuid4().hex, version)
        return f"取消请求已保存：{status_label(task.status, 'zh-CN')}"

    def resume(
        run_id: str,
        version: int,
        llm_api_key: str = "",
        vlm_api_key: str = "",
    ) -> str:
        service.attach_run_credentials(
            run_id,
            llm_api_key=llm_api_key,
            vlm_api_key=vlm_api_key,
        )
        service.executions.enqueue(run_id, "resume", expected_version=version)
        return "恢复已排队"

    def reconcile(
        run_id: str,
        request_id: str,
        outcome: str,
        operator: str,
        reason: str,
        version: int,
    ) -> str:
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

    def approve_pdf_fallback(
        run_id: str,
        operator: str,
        reason: str,
        version: int,
    ) -> str:
        result = service.approve_pdf_parser_fallback(
            run_id,
            operator,
            reason,
            uuid4().hex,
            version,
        )
        return f"降级已审计并排队：执行版本 {result['version']}"

    with gr.Tab("执行任务", id="execution"):
        page_header(gr, "execution")
        with gr.Row(equal_height=True, elem_classes="compact-action-row"):
            with gr.Row(scale=4, equal_height=True, elem_classes="compact-action-fields"):
                run = compact_dropdown(
                    gr,
                    label="运行",
                    min_width=0,
                    **empty_dropdown_kwargs("暂无运行"),
                )
            refresh_button = gr.Button(
                "刷新",
                scale=1,
                min_width=140,
                elem_classes="compact-action-button",
            )
        summary = gr.Markdown("### 尚无执行任务")
        with gr.Accordion("PDF 解析决定", open=False, visible=False) as parser_panel:
            parser_summary = gr.Markdown("尚无 PDF 解析决定。")
            gr.Markdown(
                "自动模式选择 MinerU 后不会静默回退。只有解析阻断时，"
                "操作者填写身份与原因，才可改用 PyMuPDF 重试。"
            )
            with gr.Group(visible=False) as fallback_group:
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
        with gr.Accordion("工作流节点说明", open=False):
            gr.Markdown(workflow_node_guide("zh-CN"))
        with gr.Row():
            operator = gr.Textbox(label="取消操作者")
            reason = gr.Textbox(label="取消原因")
        with gr.Row():
            cancel_button = gr.Button("安全取消", interactive=False)
            resume_button = gr.Button("恢复运行", interactive=False)
        operation_help = gr.Markdown("尚未选择任务。", elem_classes="operation-help")
        output = gr.Textbox(label="执行操作结果", interactive=False)

        with gr.Accordion(
            "未知 Provider 请求核对", open=False, visible=False
        ) as reconciliation_panel:
            gr.Markdown(
                "只有经人工确认“未发送”或“未计费”的请求可重新派发；可能已计费的请求仍保持阻断。"
            )
            request_table = gr.Dataframe(
                headers=["请求 ID", "状态", "节点", "资产", "用量"],
                interactive=False,
                wrap=True,
            )
            request_id = gr.Dropdown(label="待核对请求", **empty_dropdown_kwargs("暂无待核对请求"))
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
            parser_panel,
            fallback_group,
            reconciliation_panel,
            operation_help,
        ]
        refresh_inputs = [run, locale_control]
        timer.tick(
            guard_ui(gr, refresh, 17),
            refresh_inputs,
            outputs,
            show_progress="hidden",
        )
        refresh_button.click(guard_ui(gr, refresh, 17), refresh_inputs, outputs)
        run.input(guard_ui(gr, refresh, 17), refresh_inputs, outputs)
        locale_control.change(guard_ui(gr, refresh, 17), refresh_inputs, outputs)
        cancel_button.click(guard_ui(gr, cancel), [run, operator, reason, version], output).then(
            guard_ui(gr, refresh, 17), refresh_inputs, outputs
        )
        resume_inputs = [run, version]
        if llm_api_key_input is not None and vlm_api_key_input is not None:
            resume_inputs.extend([llm_api_key_input, vlm_api_key_input])
        resume_button.click(guard_ui(gr, resume), resume_inputs, output).then(
            guard_ui(gr, refresh, 17), refresh_inputs, outputs
        )
        reconcile_button.click(
            guard_ui(gr, reconcile),
            [
                run,
                request_id,
                outcome,
                reconcile_operator,
                reconcile_reason,
                version,
            ],
            reconcile_output,
        ).then(guard_ui(gr, refresh, 17), refresh_inputs, outputs)
        fallback_button.click(
            guard_ui(gr, approve_pdf_fallback),
            [run, fallback_operator, fallback_reason, version],
            fallback_output,
        ).then(guard_ui(gr, refresh, 17), refresh_inputs, outputs)
    return run
