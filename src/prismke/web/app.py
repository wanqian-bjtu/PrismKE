"""Gradio UI mounted on the PrismKE FastAPI application."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import orjson

from prismke.domain import CanonicalEntity, ReviewDecision
from prismke.workflow import PrismKEService


def _state_summary(state: Any) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "status": state.status,
        "current_node": state.current_node,
        "warnings": state.warnings,
        "errors": state.errors,
        "provider_calls": [item.model_dump(mode="json") for item in state.provider_calls],
    }


def _claim_rows(state: Any) -> list[list[Any]]:
    return [
        [
            claim.id,
            claim.subject_id,
            claim.relation_id,
            claim.object_entity_id or claim.object_literal,
            claim.confidence,
            claim.status.value,
            ", ".join(claim.evidence_ids),
        ]
        for claim in state.claims
    ]


def mount_gradio(app: Any, service: PrismKEService) -> Any:
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError("Web UI is not installed; run `uv sync --extra web`") from exc

    async def run_document(
        document: str,
        schema: str,
        provider: str,
        ocr_provider: str,
        vlm_provider: str,
    ) -> tuple[dict[str, Any], list[list[Any]], str]:
        state = await service.run(
            Path(document),
            Path(schema),
            provider,
            ocr_provider,
            vlm_provider,
        )
        return _state_summary(state), _claim_rows(state), state.run_id

    def load_run(run_id: str) -> tuple[dict[str, Any], list[list[Any]]]:
        state = service.show_run(run_id)
        return _state_summary(state), _claim_rows(state)

    async def review_claim(
        run_id: str, claim_id: str, decision: str
    ) -> tuple[dict[str, Any], list[list[Any]]]:
        state = await service.review(run_id, claim_id, ReviewDecision(decision))
        return _state_summary(state), _claim_rows(state)

    def load_review_queue(
        run_id: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[list[Any]]]:
        state = service.show_run(run_id)
        return (
            [item.model_dump(mode="json") for item in state.review_tasks],
            [item.model_dump(mode="json") for item in state.conflicts],
            _claim_rows(state),
        )

    async def show_evidence(evidence_id: str) -> tuple[dict[str, Any], str | None]:
        evidence = await service.evidence_store.get(evidence_id)
        output = service.settings.runtime_dir / "ui" / f"{evidence_id.replace(':', '_')}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            output.write_bytes(await service.evidence_store.crop(evidence_id))
            preview: str | None = str(output)
        except Exception:
            preview = None
        return evidence.model_dump(mode="json"), preview

    async def neighborhood(entity_id: str, depth: int) -> tuple[Any, dict[str, Any]]:
        import networkx as nx
        import plotly.graph_objects as go

        result = await service.graph_store.get_neighborhood(entity_id, depth)
        graph = nx.Graph()
        labels: dict[str, str] = {}
        kinds: dict[str, str] = {}
        for entity in result.entities:
            graph.add_node(entity.id)
            labels[entity.id] = entity.name
            kinds[entity.id] = "entity"
        for claim in result.claims:
            target = claim.object_entity_id or f"literal:{claim.id}"
            if claim.object_literal is not None:
                graph.add_node(target)
                labels[target] = claim.object_literal
                kinds[target] = "literal"
            graph.add_edge(claim.subject_id, target, label=claim.relation_id)
        positions = nx.spring_layout(graph, seed=42) if graph.nodes else {}
        edge_x: list[float | None] = []
        edge_y: list[float | None] = []
        for left, right in graph.edges:
            edge_x.extend([positions[left][0], positions[right][0], None])
            edge_y.extend([positions[left][1], positions[right][1], None])
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line={"color": "#9ca3af", "width": 1.5},
                hoverinfo="skip",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[positions[node][0] for node in graph.nodes],
                y=[positions[node][1] for node in graph.nodes],
                mode="markers+text",
                text=[labels.get(node, node) for node in graph.nodes],
                textposition="top center",
                marker={
                    "size": 18,
                    "color": [
                        "#0f766e" if kinds.get(node) == "entity" else "#f97316"
                        for node in graph.nodes
                    ],
                },
                customdata=list(graph.nodes),
                hovertemplate="%{text}<br>%{customdata}<extra></extra>",
            )
        )
        figure.update_layout(
            height=520,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            showlegend=False,
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor="white",
        )
        return figure, result.model_dump(mode="json")

    async def revisions() -> list[list[Any]]:
        items = await service.graph_store.list_revisions()
        return [
            [item.id, item.parent_id, item.run_id, item.created_at.isoformat(), len(item.changes)]
            for item in items
        ]

    async def revision_diff(from_id: str, to_id: str) -> dict[str, Any]:
        result = await service.graph_store.diff_revisions(from_id, to_id)
        return result.model_dump(mode="json")

    async def rollback(revision_id: str, confirmed: bool) -> dict[str, Any]:
        if not confirmed:
            raise gr.Error("请先确认补偿回滚操作")
        result = await service.graph_store.rollback_revision(revision_id)
        service.audit.record(
            "rollback", revision_id, {"compensation_revision_id": result.id, "source": "ui"}
        )
        return result.model_dump(mode="json")

    async def health() -> dict[str, Any]:
        result = await service.graph_store.healthcheck()
        return result.model_dump(mode="json")

    async def search_entities(
        query: str, entity_type: str, limit: int
    ) -> list[dict[str, Any]]:
        return [
            item.model_dump(mode="json")
            for item in await service.search_entities(query, entity_type, limit)
        ]

    def entity_reviews(status: str) -> list[dict[str, Any]]:
        return [
            item.model_dump(mode="json")
            for item in service.list_entity_reviews(None if status == "all" else status)
        ]

    async def entity_history(entity_id: str) -> list[dict[str, Any]]:
        return [
            item.model_dump(mode="json")
            for item in await service.entity_history(entity_id)
        ]

    async def review_entity_task(
        task_id: str,
        run_id: str,
        action: str,
        selected_entity_id: str,
        reviewer: str,
    ) -> dict[str, Any]:
        if action in {"approve", "reject_operation"}:
            revision = await service.review_entity_operation(
                task_id, action == "approve", reviewer or None
            )
            return revision.model_dump(mode="json") if revision else {"status": "rejected"}
        if action not in {"link", "create", "reject"}:
            raise ValueError(f"unsupported entity review action: {action}")
        state = await service.review_entity(
            run_id,
            task_id,
            cast(Literal["link", "create", "reject"], action),
            selected_entity_id or None,
        )
        return _state_summary(state)

    async def propose_merge(
        source_ids: str, target_id: str, reasons: str
    ) -> dict[str, Any]:
        task = await service.propose_entity_merge(
            [item.strip() for item in source_ids.split(",") if item.strip()],
            target_id.strip(),
            [item.strip() for item in reasons.split(";") if item.strip()],
        )
        return task.model_dump(mode="json")

    async def propose_split(
        source_id: str,
        target_entities_json: str,
        assignments_json: str,
        reasons: str,
    ) -> dict[str, Any]:
        target_payloads = orjson.loads(target_entities_json)
        assignments = orjson.loads(assignments_json)
        task = await service.propose_entity_split(
            source_id.strip(),
            [CanonicalEntity.model_validate(item) for item in target_payloads],
            {str(key): str(value) for key, value in assignments.items()},
            [item.strip() for item in reasons.split(";") if item.strip()],
        )
        return task.model_dump(mode="json")

    claim_headers = ["Claim ID", "主语", "关系", "宾语", "置信度", "状态", "证据"]
    with gr.Blocks(title="PrismKE 研究工作台") as demo:
        gr.Markdown("# PrismKE 研究工作台")
        with gr.Tab("构建与运行"):
            with gr.Row():
                document_input = gr.File(label="文档", type="filepath")
                schema_input = gr.File(label="Schema", type="filepath")
            with gr.Row():
                provider_input = gr.Dropdown(
                    ["mock", "openai-compatible"], value="mock", label="文本模型"
                )
                ocr_input = gr.Dropdown(
                    ["disabled", "mock", "paddle"], value="disabled", label="OCR"
                )
                vlm_input = gr.Dropdown(
                    ["disabled", "mock", "openai-compatible"],
                    value="disabled",
                    label="视觉模型",
                )
            run_button = gr.Button("开始构建", variant="primary")
            run_id_output = gr.Textbox(label="Run ID")
            run_summary = gr.JSON(label="运行状态")
            claim_table = gr.Dataframe(headers=claim_headers, interactive=False, label="Claim")
            run_button.click(
                run_document,
                [document_input, schema_input, provider_input, ocr_input, vlm_input],
                [run_summary, claim_table, run_id_output],
            )
            reload_button = gr.Button("刷新运行状态")
            reload_button.click(
                load_run, [run_id_output], [run_summary, claim_table]
            )

        with gr.Tab("冲突审核"):
            review_run = gr.Textbox(label="Run ID")
            review_load = gr.Button("加载审核队列")
            with gr.Row():
                review_tasks = gr.JSON(label="待审核任务")
                review_conflicts = gr.JSON(label="冲突集合")
            review_claim_id = gr.Textbox(label="Claim ID")
            review_decision = gr.Radio(
                ["approve", "reject"], value="approve", label="审核决定"
            )
            review_button = gr.Button("提交审核", variant="primary")
            review_summary = gr.JSON(label="审核后的运行状态")
            review_claims = gr.Dataframe(headers=claim_headers, interactive=False)
            review_load.click(
                load_review_queue,
                [review_run],
                [review_tasks, review_conflicts, review_claims],
            )
            review_button.click(
                review_claim,
                [review_run, review_claim_id, review_decision],
                [review_summary, review_claims],
            )

        with gr.Tab("证据"):
            evidence_id = gr.Textbox(label="Evidence ID")
            evidence_button = gr.Button("读取证据")
            evidence_metadata = gr.JSON(label="证据元数据")
            evidence_preview = gr.Image(label="证据定位", type="filepath")
            evidence_button.click(
                show_evidence, [evidence_id], [evidence_metadata, evidence_preview]
            )

        with gr.Tab("图谱"):
            entity_id = gr.Textbox(label="Entity ID")
            depth = gr.Slider(1, 3, value=1, step=1, label="邻域深度")
            graph_button = gr.Button("查询邻域")
            graph_plot = gr.Plot(label="实体邻域图")
            graph_output = gr.JSON(label="实体邻域")
            graph_button.click(
                neighborhood, [entity_id, depth], [graph_plot, graph_output]
            )

        with gr.Tab("实体治理"):
            with gr.Row():
                entity_query = gr.Textbox(label="名称、别名或上下文")
                entity_type = gr.Textbox(label="实体类型")
                entity_limit = gr.Slider(1, 20, value=10, step=1, label="候选数")
            entity_search_button = gr.Button("检索候选")
            entity_search_output = gr.JSON(label="候选及评分分解")
            entity_search_button.click(
                search_entities,
                [entity_query, entity_type, entity_limit],
                [entity_search_output],
            )
            with gr.Accordion("证据与候选邻域", open=False):
                with gr.Row():
                    with gr.Column(min_width=280):
                        mention_evidence_id = gr.Textbox(label="提及 Evidence ID")
                        mention_evidence_button = gr.Button("查看提及证据")
                        mention_evidence_metadata = gr.JSON(label="提及证据")
                        mention_evidence_preview = gr.Image(label="证据区域", type="filepath")
                    with gr.Column(min_width=280):
                        candidate_entity_id = gr.Textbox(label="候选 Entity ID")
                        candidate_neighborhood_button = gr.Button("查看候选邻域")
                        candidate_neighborhood_plot = gr.Plot(label="候选邻域")
                        candidate_neighborhood_output = gr.JSON(label="邻域事实与证据引用")
                mention_evidence_button.click(
                    show_evidence, [mention_evidence_id],
                    [mention_evidence_metadata, mention_evidence_preview],
                )
                candidate_neighborhood_button.click(
                    neighborhood, [candidate_entity_id, gr.State(1)],
                    [candidate_neighborhood_plot, candidate_neighborhood_output],
                )
            with gr.Row():
                entity_review_status = gr.Dropdown(
                    ["pending", "resolved", "all"], value="pending", label="审核状态"
                )
                entity_review_load = gr.Button("刷新实体审核队列")
            entity_review_queue = gr.JSON(label="实体链接、合并与拆分任务")
            entity_review_load.click(
                entity_reviews, [entity_review_status], [entity_review_queue]
            )
            with gr.Row():
                entity_task_id = gr.Textbox(label="Task ID")
                entity_run_id = gr.Textbox(label="Run ID（链接审核时填写）")
                entity_review_action = gr.Dropdown(
                    ["link", "create", "reject", "approve", "reject_operation"],
                    value="link",
                    label="审核动作",
                )
            with gr.Row():
                selected_entity_id = gr.Textbox(label="选择的 Entity ID")
                entity_reviewer = gr.Textbox(label="审核人")
            entity_review_button = gr.Button("提交实体审核", variant="primary")
            entity_review_output = gr.JSON(label="审核结果")
            entity_review_button.click(
                review_entity_task,
                [
                    entity_task_id,
                    entity_run_id,
                    entity_review_action,
                    selected_entity_id,
                    entity_reviewer,
                ],
                [entity_review_output],
            )
            gr.Markdown("### 实体合并建议")
            merge_sources = gr.Textbox(label="源 Entity ID，逗号分隔")
            merge_target = gr.Textbox(label="保留的 Entity ID")
            merge_reasons = gr.Textbox(label="理由，分号分隔")
            merge_button = gr.Button("创建合并审核任务")
            merge_output = gr.JSON(label="合并建议")
            merge_button.click(
                propose_merge,
                [merge_sources, merge_target, merge_reasons],
                [merge_output],
            )
            gr.Markdown("### 实体拆分建议")
            split_source = gr.Textbox(label="原 Entity ID")
            split_targets = gr.Code(
                label="新实体 JSON 数组", language="json", value="[]"
            )
            split_assignments = gr.Code(
                label="Claim 到新 Entity 的映射 JSON", language="json", value="{}"
            )
            split_reasons = gr.Textbox(label="理由，分号分隔")
            split_button = gr.Button("创建拆分审核任务")
            split_output = gr.JSON(label="拆分建议")
            split_button.click(
                propose_split,
                [split_source, split_targets, split_assignments, split_reasons],
                [split_output],
            )
            with gr.Accordion("实体治理历史", open=False):
                history_entity_id = gr.Textbox(label="实体 Entity ID")
                history_button = gr.Button("查询治理与回滚历史")
                history_output = gr.JSON(label="实体 Revision 历史")
                history_button.click(entity_history, [history_entity_id], [history_output])

        with gr.Tab("版本"):
            revision_button = gr.Button("刷新版本")
            revision_table = gr.Dataframe(
                headers=["Revision ID", "父版本", "Run ID", "时间", "变更数"],
                interactive=False,
            )
            revision_button.click(revisions, outputs=[revision_table])
            with gr.Row():
                from_revision = gr.Textbox(label="起始 Revision")
                to_revision = gr.Textbox(label="目标 Revision")
            diff_button = gr.Button("比较版本")
            diff_output = gr.JSON(label="版本差异")
            diff_button.click(revision_diff, [from_revision, to_revision], [diff_output])
            rollback_revision_id = gr.Textbox(label="要回滚的 Revision")
            rollback_confirm = gr.Checkbox(label="我确认创建补偿 Revision")
            rollback_button = gr.Button("执行回滚", variant="stop")
            rollback_output = gr.JSON(label="补偿 Revision")
            rollback_button.click(
                rollback,
                [rollback_revision_id, rollback_confirm],
                [rollback_output],
            )

        with gr.Tab("健康状态"):
            health_button = gr.Button("检查连接")
            health_output = gr.JSON(label="服务状态")
            health_button.click(health, outputs=[health_output])

    return gr.mount_gradio_app(app, demo, path="/ui")
