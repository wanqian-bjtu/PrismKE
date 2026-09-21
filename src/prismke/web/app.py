"""Gradio UI mounted on the PrismKE FastAPI application."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import orjson

from prismke import __version__
from prismke.domain import CanonicalEntity, ReviewDecision
from prismke.web.review import build_review_tabs
from prismke.web.validation import build_validation_tab
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
        allow_remote_assets: bool,
    ) -> tuple[dict[str, Any], list[list[Any]], str]:
        state, created = service.create_run(
            Path(document),
            Path(schema),
            provider,
            ocr_provider,
            vlm_provider,
            allow_remote_assets,
        )
        if created:
            service.executions.enqueue(state.run_id, "execute")
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

    async def search_entities(query: str, entity_type: str, limit: int) -> list[dict[str, Any]]:
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
        return [item.model_dump(mode="json") for item in await service.entity_history(entity_id)]

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
            reviewer or None,
        )
        return _state_summary(state)

    async def propose_merge(source_ids: str, target_id: str, reasons: str) -> dict[str, Any]:
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

    async def dashboard() -> tuple[str, list[list[Any]], dict[str, Any]]:
        summary = await service.workspace_summary()
        counts = summary["run_counts"]
        headline = (
            f"### 工作区概览\n"
            f"运行 {sum(counts.values())} · 执行中 {counts.get('running', 0)} · "
            f"待审核 {summary['pending_reviews']} · 阻断问题 {summary['blocking_issues']} · "
            f"工作器 {summary['worker_status']}"
        )
        recent = []
        for state in service.runs.list(limit=10):
            execution = service.executions.view(state.run_id)
            recent.append(
                [
                    (
                        state.document.source_filename
                        if state.document
                        else Path(state.input_path).name
                    ),
                    state.status,
                    execution["status"],
                    execution["node"],
                    execution["updated_at"] or "",
                ]
            )
        return headline, recent, summary["graph_health"]

    def sidebar_run(run_id: str | None) -> tuple[Any, str]:
        states = service.runs.list(limit=1000)
        choices = [
            (f"{Path(state.input_path).name} · {state.status}", state.run_id) for state in states
        ]
        if run_id not in {state.run_id for state in states}:
            run_id = states[0].run_id if states else None
        if not run_id:
            return gr.update(choices=choices, value=None), "尚无运行"
        progress = service.review_progress(run_id)
        execution = progress["execution"]
        text = (
            f"业务：{progress['status']}\n执行：{execution['status']}\n"
            f"节点：{execution['node']}\n实体待审：{progress['entity_pending']} · "
            f"事实待审：{progress['claim_pending']} · 校验：{progress['validation_pending']}"
        )
        return gr.update(choices=choices, value=run_id), text

    def save_settings(
        llm_base_url: str,
        llm_model: str,
        llm_key: str,
        clear_llm: bool,
        vlm_base_url: str,
        vlm_model: str,
        vlm_key: str,
        clear_vlm: bool,
        ocr_device: str,
        ocr_lang: str,
        ocr_model: str,
        graph_store: str,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_database: str,
        neo4j_password: str,
        clear_neo4j: bool,
        operator: str,
    ) -> dict[str, Any]:
        values: dict[str, Any] = {
            "llm_base_url": llm_base_url,
            "llm_model": llm_model or None,
            "vlm_base_url": vlm_base_url,
            "vlm_model": vlm_model or None,
            "ocr_device": ocr_device,
            "ocr_lang": ocr_lang,
            "ocr_model": ocr_model,
            "graph_store": graph_store,
            "neo4j_uri": neo4j_uri,
            "neo4j_user": neo4j_user,
            "neo4j_database": neo4j_database,
        }
        if llm_key.strip():
            values["llm_api_key"] = llm_key.strip()
        if vlm_key.strip():
            values["vlm_api_key"] = vlm_key.strip()
        if neo4j_password.strip():
            values["neo4j_password"] = neo4j_password.strip()
        clear = []
        if clear_llm:
            clear.append("llm_api_key")
        if clear_vlm:
            clear.append("vlm_api_key")
        if clear_neo4j:
            clear.append("neo4j_password")
        return service.update_settings(values, clear, operator)

    claim_headers = ["Claim ID", "主语", "关系", "宾语", "置信度", "状态", "证据"]
    public_settings = service.settings_view()
    css = """
    #workspace-tabs > .tab-nav { display: none !important; }
    #workspace-sidebar { border-right: 1px solid #e5e7eb; background: #fafafa; }
    #workspace-sidebar .wrap { gap: 8px; }
    .workspace-title h1 { font-size: 24px !important; margin: 0 0 4px; letter-spacing: 0; }
    .workspace-section { max-width: 1500px; margin: 0 auto; }
    .technical-detail { border: 1px solid #e5e7eb; border-radius: 6px; }
    @media (max-width: 768px) {
      .workspace-title h1 { font-size: 20px !important; }
      .gradio-container { padding: 10px !important; }
    }
    """
    with gr.Blocks(
        title="PrismKE 研究工作台", fill_height=True, analytics_enabled=False
    ) as demo:
        with gr.Sidebar(open=True, elem_id="workspace-sidebar"):
            gr.Markdown(f"## PrismKE\n`{__version__}`")
            if service.review_metadata:
                gr.Markdown("**隔离审核工作区**\n\n原评测只读，抽取调用禁用。")
            navigation = gr.Radio(
                [
                    ("总览", "overview"),
                    ("新建构建", "build"),
                    ("执行任务", "execution"),
                    ("实体审核", "entity-review"),
                    ("事实审核", "claim-review"),
                    ("校验问题", "validation"),
                    ("审核历史与纠正", "corrections"),
                    ("证据", "evidence"),
                    ("图谱", "graph"),
                    ("实体治理", "governance"),
                    ("版本管理", "revisions"),
                    ("系统状态", "health"),
                ],
                value="overview",
                label="导航",
            )
            current_run = gr.Dropdown(label="当前运行", choices=[])
            run_context = gr.Textbox(label="运行上下文", lines=5, interactive=False)
            refresh_context = gr.Button("刷新运行")
            with gr.Accordion("构建配置", open=True):
                schema_input = gr.File(label="Schema", type="filepath")
                provider_input = gr.Dropdown(
                    ["mock", "openai-compatible"], value="mock", label="文本 Provider"
                )
                ocr_input = gr.Dropdown(
                    ["disabled", "mock", "paddle"], value="disabled", label="OCR Provider"
                )
                vlm_input = gr.Dropdown(
                    ["disabled", "mock", "openai-compatible"],
                    value="disabled",
                    label="视觉 Provider",
                )
                allow_remote = gr.Checkbox(
                    label="允许远程资源", value=service.settings.allow_remote_assets
                )
            with gr.Accordion("模型与后端设置", open=False):
                llm_base = gr.Textbox(label="LLM Base URL", value=public_settings["llm_base_url"])
                llm_model = gr.Textbox(label="LLM 模型别名", value=public_settings["llm_model"])
                llm_key = gr.Textbox(
                    label="更新 LLM API Key",
                    type="password",
                    placeholder="已配置" if public_settings["llm_api_key"] else "未配置",
                )
                clear_llm = gr.Checkbox(label="清除 LLM API Key")
                vlm_base = gr.Textbox(label="VLM Base URL", value=public_settings["vlm_base_url"])
                vlm_model = gr.Textbox(label="VLM 模型别名", value=public_settings["vlm_model"])
                vlm_key = gr.Textbox(
                    label="更新 VLM API Key",
                    type="password",
                    placeholder="已配置" if public_settings["vlm_api_key"] else "未配置",
                )
                clear_vlm = gr.Checkbox(label="清除 VLM API Key")
                ocr_device = gr.Textbox(label="OCR 设备", value=public_settings["ocr_device"])
                ocr_lang = gr.Textbox(label="OCR 语言", value=public_settings["ocr_lang"])
                ocr_model = gr.Textbox(label="OCR 模型", value=public_settings["ocr_model"])
                graph_store = gr.Dropdown(
                    ["json", "neo4j"], value=public_settings["graph_store"], label="图存储"
                )
                neo4j_uri = gr.Textbox(label="Neo4j URI", value=public_settings["neo4j_uri"])
                neo4j_user = gr.Textbox(label="Neo4j 用户", value=public_settings["neo4j_user"])
                neo4j_database = gr.Textbox(
                    label="Neo4j 数据库", value=public_settings["neo4j_database"]
                )
                neo4j_password = gr.Textbox(
                    label="更新 Neo4j 密码",
                    type="password",
                    placeholder="已配置" if public_settings["neo4j_password"] else "未配置",
                )
                clear_neo4j = gr.Checkbox(label="清除 Neo4j 密码")
                config_operator = gr.Textbox(label="配置操作者")
                save_config = gr.Button("保存设置", variant="primary")
                config_outcome = gr.JSON(label="设置结果")

        with gr.Tabs(selected="overview", elem_id="workspace-tabs") as workspace_tabs:
            with gr.Tab("总览", id="overview"):
                gr.Markdown(f"# PrismKE 研究工作台 · {__version__}", elem_classes="workspace-title")
                overview = gr.Markdown()
                refresh_overview = gr.Button("刷新总览")
                recent_runs = gr.Dataframe(
                    headers=["文档", "业务状态", "执行状态", "节点", "更新时间"],
                    interactive=False,
                    wrap=True,
                    label="最近运行",
                )
                graph_health = gr.JSON(label="图存储健康状态")

            with gr.Tab("新建构建", id="build"):
                gr.Markdown("## 新建知识构建")
                document_input = gr.File(label="文档", type="filepath")
                gr.Markdown("Schema 与 Provider 配置位于左侧。开始前请确认预算和远程资源策略。")
                run_button = gr.Button("开始构建", variant="primary")
                run_id_output = gr.Textbox(label="Run ID")
                run_summary = gr.JSON(label="运行状态")
                claim_table = gr.Dataframe(
                    headers=claim_headers, interactive=False, label="Claim", wrap=True
                )
                reload_button = gr.Button("刷新运行状态")

            build_review_tabs(service)
            from prismke.web.execution import build_execution_tab

            build_execution_tab(service)

            with gr.Tab("证据", id="evidence"):
                gr.Markdown("## 证据查看")
                evidence_id = gr.Textbox(label="Evidence ID")
                evidence_button = gr.Button("读取证据")
                evidence_metadata = gr.JSON(label="证据元数据")
                evidence_preview = gr.Image(label="证据定位", type="filepath")
                evidence_button.click(
                    show_evidence, [evidence_id], [evidence_metadata, evidence_preview]
                )

            with gr.Tab("图谱", id="graph"):
                gr.Markdown("## 图谱浏览")
                entity_id = gr.Textbox(label="Entity ID")
                depth = gr.Slider(1, 3, value=1, step=1, label="邻域深度")
                graph_button = gr.Button("查询邻域")
                graph_plot = gr.Plot(label="实体邻域图")
                graph_output = gr.JSON(label="实体邻域")
                graph_button.click(
                    neighborhood, [entity_id, depth], [graph_plot, graph_output]
                )

            with gr.Tab("实体治理", id="governance"):
                gr.Markdown("## 实体治理")
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
                            mention_evidence_preview = gr.Image(
                                label="证据区域", type="filepath"
                            )
                        with gr.Column(min_width=280):
                            candidate_entity_id = gr.Textbox(label="候选 Entity ID")
                            candidate_neighborhood_button = gr.Button("查看候选邻域")
                            candidate_neighborhood_plot = gr.Plot(label="候选邻域")
                            candidate_neighborhood_output = gr.JSON(
                                label="邻域事实与证据引用"
                            )
                    mention_evidence_button.click(
                        show_evidence,
                        [mention_evidence_id],
                        [mention_evidence_metadata, mention_evidence_preview],
                    )
                    candidate_neighborhood_button.click(
                        neighborhood,
                        [candidate_entity_id, gr.State(1)],
                        [candidate_neighborhood_plot, candidate_neighborhood_output],
                    )
                gr.Markdown("### 合并与拆分审核（原有高级操作）")
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
                    history_button.click(
                        entity_history, [history_entity_id], [history_output]
                    )

            build_validation_tab(gr, service)

            with gr.Tab("版本", id="revisions"):
                gr.Markdown("## 版本管理")
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
                diff_button.click(
                    revision_diff, [from_revision, to_revision], [diff_output]
                )
                rollback_revision_id = gr.Textbox(label="要回滚的 Revision")
                rollback_confirm = gr.Checkbox(label="我确认创建补偿 Revision")
                rollback_button = gr.Button("执行回滚", variant="stop")
                rollback_output = gr.JSON(label="补偿 Revision")
                rollback_button.click(
                    rollback,
                    [rollback_revision_id, rollback_confirm],
                    [rollback_output],
                )

            with gr.Tab("健康状态", id="health"):
                gr.Markdown("## 系统状态")
                health_button = gr.Button("检查连接")
                health_output = gr.JSON(label="服务状态")
                health_button.click(health, outputs=[health_output])

        navigation.change(lambda page: gr.Tabs(selected=page), navigation, workspace_tabs)
        refresh_context.click(sidebar_run, [current_run], [current_run, run_context])
        current_run.change(sidebar_run, [current_run], [current_run, run_context])
        demo.load(sidebar_run, [current_run], [current_run, run_context])
        demo.load(dashboard, outputs=[overview, recent_runs, graph_health])
        refresh_overview.click(dashboard, outputs=[overview, recent_runs, graph_health])
        run_button.click(
            run_document,
            [
                document_input,
                schema_input,
                provider_input,
                ocr_input,
                vlm_input,
                allow_remote,
            ],
            [run_summary, claim_table, run_id_output],
        ).then(sidebar_run, [run_id_output], [current_run, run_context])
        reload_button.click(load_run, [run_id_output], [run_summary, claim_table])
        save_config.click(
            save_settings,
            [
                llm_base,
                llm_model,
                llm_key,
                clear_llm,
                vlm_base,
                vlm_model,
                vlm_key,
                clear_vlm,
                ocr_device,
                ocr_lang,
                ocr_model,
                graph_store,
                neo4j_uri,
                neo4j_user,
                neo4j_database,
                neo4j_password,
                clear_neo4j,
                config_operator,
            ],
            config_outcome,
        )

    return gr.mount_gradio_app(app, demo, path="/ui", css=css)
