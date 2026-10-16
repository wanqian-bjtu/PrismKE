"""Gradio UI mounted on the PrismKE FastAPI application."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

import orjson

from frontend.i18n import browser_i18n_bootstrap_js
from frontend.layout import (
    build_brand_header,
    first_page,
    group_choices,
    page_choices,
    page_header,
)
from frontend.presentation import (
    decision_label,
    dropdown_update,
    empty_dropdown_kwargs,
    guard_ui,
    media_type_label,
    status_label,
    visual_target_label,
)
from frontend.review import build_review_tabs
from frontend.schema_input import resolve_schema, schema_summary
from frontend.theme import APP_CSS
from frontend.validation import build_validation_tab
from src import __version__
from src.domain import (
    CanonicalEntity,
    EntitySourceMode,
    PDFParseMode,
    ProvidedEntity,
    ReviewDecision,
    TaskMode,
)
from src.workflow import PrismKEService
from src.workflow.service import TransientProviderCredentials


def _state_summary(state: Any) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "status": state.status,
        "current_node": state.current_node,
        "warnings": state.warnings,
        "errors": state.errors,
        "provider_calls": [item.model_dump(mode="json") for item in state.provider_calls],
    }


def _state_status(state: Any, execution: dict[str, Any] | None = None) -> str:
    execution_status = (execution or {}).get("status", "未启动")
    warning_count = len(getattr(state, "warnings", []))
    error_count = len(getattr(state, "errors", []))
    return (
        f"**业务状态** `{status_label(state.status)}` · "
        f"**执行状态** `{status_label(execution_status)}` · "
        f"**当前节点** `{state.current_node or '等待中'}`  \n"
        f"警告 {warning_count} · 错误 {error_count}"
    )


def _claim_rows(state: Any) -> list[list[Any]]:
    rows = [
        [
            claim.id,
            claim.subject_id,
            claim.relation_id,
            claim.object_entity_id or claim.object_literal,
            claim.confidence,
            status_label(claim.status.value),
            ", ".join(claim.evidence_ids),
        ]
        for claim in state.claims
    ]
    if rows or state.extraction_result is None:
        return rows
    result = state.extraction_result
    decisions = {event.target_id: event.decision for event in result.review_events}
    rows.extend(
        [
            mention.id,
            mention.name,
            "实体提及",
            mention.entity_type,
            mention.confidence,
            decision_label(decisions.get(mention.id, "candidate")),
            ", ".join(mention.evidence_ids),
        ]
        for mention in result.entities
    )
    rows.extend(
        [
            claim.id,
            claim.subject.name,
            claim.relation,
            claim.object.name if hasattr(claim.object, "name") else claim.object,
            claim.confidence,
            decision_label(decisions.get(claim.id, "candidate")),
            ", ".join(claim.evidence_ids),
        ]
        for claim in result.relations
    )
    rows.extend(
        [
            attribute.id,
            attribute.subject.name,
            f"属性：{attribute.field}",
            str(attribute.value),
            attribute.confidence,
            decision_label(decisions.get(attribute.id, "candidate")),
            ", ".join(attribute.evidence_ids),
        ]
        for attribute in result.attributes
    )
    rows.extend(
        [
            event.id,
            event.trigger,
            f"事件：{event.event_type}",
            orjson.dumps([item.model_dump(mode="json") for item in event.arguments]).decode(),
            event.confidence,
            decision_label(decisions.get(event.id, "candidate")),
            ", ".join(event.evidence_ids),
        ]
        for event in result.events
    )
    return rows


def _review_target_choices(state: Any) -> list[tuple[str, str]]:
    result = getattr(state, "extraction_result", None)
    if result is None:
        return []
    choices: list[tuple[str, str]] = []
    choices.extend((f"实体 · {item.name}", f"entity|{item.id}") for item in result.entities)
    choices.extend(
        (f"关系 · {item.subject.name} / {item.relation}", f"relation|{item.id}")
        for item in result.relations
    )
    choices.extend(
        (f"属性 · {item.subject.name} / {item.field}", f"attribute|{item.id}")
        for item in result.attributes
    )
    choices.extend(
        (f"事件 · {item.event_type} / {item.trigger}", f"event|{item.id}") for item in result.events
    )
    return choices


def mount_gradio(app: Any, service: PrismKEService) -> Any:
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError("Web UI is not installed; run `uv sync --extra web`") from exc

    async def run_document(
        documents: list[str] | str | None,
        schema_source: str,
        schema_file: str | None,
        schema_text: str,
        provider: str,
        ocr_provider: str,
        vlm_provider: str,
        allow_remote_assets: bool,
        case_mode: str,
        reflection_enabled: bool,
        reflection_provider: str,
        reflection_max_attempts: int,
        reflection_token_budget: int,
        reflection_time_budget: int,
        semantic_advisor: str,
        agent_token_budget: int,
        llm_base_url: str,
        llm_model: str,
        llm_api_key: str,
        vlm_base_url: str,
        vlm_model: str,
        vlm_api_key: str,
        task_mode: str,
        entity_source_mode: str,
        provided_entities_json: str,
        pdf_parse_mode: str,
        operator: str,
    ) -> tuple[
        str,
        dict[str, Any],
        list[list[Any]],
        str,
        str,
        list[list[Any]],
        Any,
        Any,
    ]:
        if not documents:
            raise ValueError("请先上传至少一个文档")
        document_paths = [documents] if isinstance(documents, str) else documents
        schema_path, _ = resolve_schema(
            schema_source,
            schema_file,
            schema_text,
            service.settings.runtime_dir / "ui" / "schemas",
        )
        try:
            raw_entities = orjson.loads(provided_entities_json or "[]")
            provided_entities = [ProvidedEntity.model_validate(item) for item in raw_entities]
        except (TypeError, ValueError, orjson.JSONDecodeError) as exc:
            raise ValueError("实体清单必须是合法的 JSON 数组") from exc
        batch, created = service.create_batch(
            [Path(document) for document in document_paths],
            schema_path,
            task_mode=TaskMode(task_mode),
            entity_source_mode=EntitySourceMode(entity_source_mode),
            provided_entities=provided_entities,
            provider_name=provider,
            ocr_provider_name=ocr_provider,
            vlm_provider_name=vlm_provider,
            allow_remote_assets=allow_remote_assets,
            case_mode=cast(Literal["none", "good", "good_bad"], case_mode),
            reflection_enabled=reflection_enabled,
            reflection_provider_name=reflection_provider,
            reflection_max_attempts=int(reflection_max_attempts),
            reflection_token_budget=int(reflection_token_budget),
            reflection_time_budget_seconds=int(reflection_time_budget),
            semantic_advisor_name=semantic_advisor,
            agent_token_budget=int(agent_token_budget),
            llm_base_url=llm_base_url,
            llm_model=llm_model,
            vlm_base_url=vlm_base_url,
            vlm_model=vlm_model,
            operator=operator,
            credentials=TransientProviderCredentials(
                llm_api_key=llm_api_key.strip() or None,
                vlm_api_key=vlm_api_key.strip() or None,
            ),
            pdf_parse_mode=PDFParseMode(pdf_parse_mode),
        )
        first_run_id = next(
            (item.run_id for item in batch.items if item.run_id),
            "",
        )
        state = service.show_run(first_run_id) if first_run_id else None
        rows = [
            [
                item.filename,
                status_label(item.status.value),
                item.run_id or "",
                item.reused_from_item_id or "",
                item.failure_code or "",
            ]
            for item in batch.items
        ]
        return (
            f"**批次状态** `{batch.status.value}` · 文件 {len(batch.items)} · "
            f"{'新建' if created else '复用'}",
            batch.model_dump(mode="json"),
            _claim_rows(state) if state else [],
            first_run_id,
            batch.id,
            rows,
            dropdown_update(
                gr,
                [(item.filename, item.id) for item in batch.items],
                empty_label="暂无批次文件",
                value=batch.items[0].id if batch.items else None,
            ),
            dropdown_update(
                gr,
                _review_target_choices(state) if state else [],
                empty_label="暂无审核对象",
            ),
        )

    def load_build(
        run_id: str, batch_id: str
    ) -> tuple[str, dict[str, Any], list[list[Any]], list[list[Any]], Any, Any]:
        if batch_id:
            batch = service.refresh_batch(batch_id)
            rows = [
                [
                    item.filename,
                    status_label(item.status.value),
                    item.run_id or "",
                    item.reused_from_item_id or "",
                    item.failure_code or "",
                ]
                for item in batch.items
            ]
            state = service.show_run(run_id) if run_id else None
            return (
                f"**批次状态** `{batch.status.value}` · 文件 {len(batch.items)}",
                batch.model_dump(mode="json"),
                _claim_rows(state) if state else [],
                rows,
                dropdown_update(
                    gr,
                    [(item.filename, item.id) for item in batch.items],
                    empty_label="暂无批次文件",
                    value=batch.items[0].id if batch.items else None,
                ),
                dropdown_update(
                    gr,
                    _review_target_choices(state) if state else [],
                    empty_label="暂无审核对象",
                ),
            )
        status, summary, claims = load_run(run_id)
        state = service.show_run(run_id)
        return (
            status,
            summary,
            claims,
            [],
            dropdown_update(gr, [], empty_label="暂无批次文件"),
            dropdown_update(
                gr,
                _review_target_choices(state),
                empty_label="暂无审核对象",
            ),
        )

    def select_batch_result(batch_id: str, item_id: str) -> tuple[str, list[list[Any]], Any]:
        if not batch_id or not item_id:
            return "", [], dropdown_update(gr, [], empty_label="暂无审核对象")
        batch = service.refresh_batch(batch_id)
        item = next((candidate for candidate in batch.items if candidate.id == item_id), None)
        if item is None or not item.run_id:
            return "", [], dropdown_update(gr, [], empty_label="暂无审核对象")
        state = service.show_run(item.run_id)
        return (
            item.run_id,
            _claim_rows(state),
            dropdown_update(
                gr,
                _review_target_choices(state),
                empty_label="暂无审核对象",
            ),
        )

    def review_extraction_result(
        run_id: str,
        target: str,
        decision: str,
        reviewer: str,
        reason: str,
    ) -> tuple[list[list[Any]], str]:
        if not run_id or "|" not in target:
            raise ValueError("请先选择可审核的抽取结果")
        target_type, target_id = target.split("|", 1)
        state = service.show_run(run_id)
        if state.extraction_result is None:
            raise ValueError("该文件的抽取结果尚未就绪")
        service.review_extraction_result(
            run_id,
            target_type,
            target_id,
            decision,
            reviewer,
            reason,
            uuid4().hex,
            state.extraction_result.version,
        )
        updated = service.show_run(run_id)
        return _claim_rows(updated), "审核决定已保存，原候选与历史事件均保留。"

    def batch_action_view(
        batch: Any, message: str
    ) -> tuple[str, dict[str, Any], list[list[Any]], Any, str]:
        rows = [
            [
                item.filename,
                status_label(item.status.value),
                item.run_id or "",
                item.reused_from_item_id or "",
                item.failure_code or "",
            ]
            for item in batch.items
        ]
        return (
            f"**批次状态** `{batch.status.value}` · 文件 {len(batch.items)}",
            batch.model_dump(mode="json"),
            rows,
            dropdown_update(
                gr,
                [(item.filename, item.id) for item in batch.items],
                empty_label="暂无批次文件",
                value=batch.items[0].id if batch.items else None,
            ),
            message,
        )

    def retry_batch_item(
        batch_id: str, item_id: str
    ) -> tuple[str, dict[str, Any], list[list[Any]], Any, str]:
        if not batch_id or not item_id:
            raise ValueError("请先选择批次和文件")
        batch = service.retry_batch_item(batch_id, item_id)
        return batch_action_view(batch, "已重新排队，执行工作器将从安全边界恢复。")

    def exclude_batch_item(
        batch_id: str,
        item_id: str,
        operator: str,
        reason: str,
    ) -> tuple[str, dict[str, Any], list[list[Any]], Any, str]:
        if not batch_id or not item_id:
            raise ValueError("请先选择批次和文件")
        batch = service.exclude_batch_item(batch_id, item_id, operator, reason)
        return batch_action_view(batch, "已排除该文件并保留审计记录。")

    async def confirm_batch_commit(
        batch_id: str,
        reviewer: str,
        confirmed: bool,
    ) -> tuple[str, dict[str, Any], list[list[Any]], Any, str]:
        if not confirmed:
            raise ValueError("请先确认批次图提交")
        batch = await service.confirm_batch_commit(batch_id, reviewer)
        return batch_action_view(batch, f"批次已提交，Revision：`{batch.revision_id}`")

    def preview_schema(source: str, schema_file: str | None, schema_text: str) -> str:
        _, schema = resolve_schema(
            source,
            schema_file,
            schema_text,
            service.settings.runtime_dir / "ui" / "schemas",
        )
        return schema_summary(schema)

    def switch_schema_source(source: str) -> tuple[Any, Any]:
        return (
            gr.update(visible=source == "upload"),
            gr.update(visible=source == "text"),
        )

    def load_run(run_id: str) -> tuple[str, dict[str, Any], list[list[Any]]]:
        state = service.show_run(run_id)
        execution = service.executions.view(run_id)
        return _state_status(state, execution), _state_summary(state), _claim_rows(state)

    def agent_report(run_id: str | None) -> tuple[list[list[Any]], dict[str, Any]]:
        if not run_id:
            return [], {}
        state = service.show_run(run_id)
        rows = [
            [
                trace.agent,
                trace.step,
                trace.decision,
                ", ".join(trace.selected_tools),
                ", ".join(trace.reason_codes),
                trace.token_usage,
                trace.status,
            ]
            for trace in state.agent_traces
        ]
        return rows, {
            "modality_status": state.modality_status,
            "modality_errors": state.modality_errors,
            "token_usage": state.agent_token_usage,
            "token_budget": state.agent_token_budget,
            "handoffs": [item.model_dump(mode="json") for item in state.agent_handoffs],
        }

    async def media_rows(document_id: str, media_type: str) -> tuple[list[list[Any]], Any]:
        contents = {item.id: item for item in await service.graph_store.list_media_contents()}
        relations = await service.graph_store.list_media_relations()
        assertions = await service.graph_store.list_visual_assertions()
        rows: list[list[Any]] = []
        choices: list[tuple[str, str]] = []
        for occurrence in await service.graph_store.list_media_occurrences():
            content = contents.get(occurrence.media_content_id)
            if content is None or not occurrence.active:
                continue
            if document_id.strip() and occurrence.document_id != document_id.strip():
                continue
            if media_type != "全部" and content.asset_type.value != media_type:
                continue
            verified = await service.evidence_store.verify(occurrence.evidence_id)
            relation_count = sum(
                item.active and item.occurrence_id == occurrence.id for item in relations
            )
            assertion_count = sum(
                item.active and item.occurrence_id == occurrence.id for item in assertions
            )
            rows.append(
                [
                    occurrence.id,
                    media_type_label(content.asset_type.value),
                    occurrence.document_id,
                    occurrence.page_number or "",
                    occurrence.caption,
                    "有效" if verified else "无效",
                    relation_count + assertion_count,
                ]
            )
            choices.append(
                (
                    f"{media_type_label(content.asset_type.value)} · "
                    f"{occurrence.caption or occurrence.id[:16]}",
                    occurrence.id,
                )
            )
        return rows, dropdown_update(
            gr,
            choices,
            empty_label="暂无媒体出现记录",
            value=choices[0][1] if choices else None,
        )

    async def media_detail(occurrence_id: str | None) -> tuple[dict[str, Any], str | None]:
        if not occurrence_id:
            return {}, None
        occurrence = await service.graph_store.get_media_occurrence(occurrence_id)
        if occurrence is None:
            raise ValueError("媒体出现记录不存在")
        content = next(
            (
                item
                for item in await service.graph_store.list_media_contents()
                if item.id == occurrence.media_content_id
            ),
            None,
        )
        evidence, preview = await show_evidence(occurrence.evidence_id)
        return (
            {
                "occurrence": occurrence.model_dump(mode="json"),
                "content": content.model_dump(mode="json") if content else None,
                "evidence": evidence,
                "relations": [
                    item.model_dump(mode="json")
                    for item in await service.graph_store.list_media_relations()
                    if item.occurrence_id == occurrence_id
                ],
                "visual_assertions": [
                    item.model_dump(mode="json")
                    for item in await service.graph_store.list_visual_assertions()
                    if item.occurrence_id == occurrence_id
                ],
            },
            preview,
        )

    async def linked_media(target_type: str, target_id: str | None) -> list[list[Any]]:
        if not target_id:
            return []
        relations = await service.graph_store.list_media_relations()
        occurrence_ids = {
            item.occurrence_id
            for item in relations
            if item.active
            and (
                (target_type == "entity" and item.target_entity_id == target_id)
                or (target_type == "claim" and item.target_claim_id == target_id)
            )
        }
        contents = {item.id: item for item in await service.graph_store.list_media_contents()}
        return [
            [
                item.id,
                media_type_label(contents[item.media_content_id].asset_type.value),
                item.document_id,
                item.page_number or "",
                item.caption,
                item.evidence_id,
            ]
            for item in await service.graph_store.list_media_occurrences()
            if item.active and item.id in occurrence_ids and item.media_content_id in contents
        ]

    async def claim_linked_media(claim_id: str | None) -> list[list[Any]]:
        return await linked_media("claim", claim_id)

    async def entity_linked_media(entity_id: str | None) -> list[list[Any]]:
        return await linked_media("entity", entity_id)

    def visual_review_rows(run_id: str | None) -> tuple[list[list[Any]], Any]:
        if not run_id:
            return [], dropdown_update(gr, [], empty_label="暂无审核任务")
        state = service.show_run(run_id)
        choices: list[tuple[str, str]] = []
        rows: list[list[Any]] = []
        for task in state.visual_review_tasks:
            label = (
                f"{visual_target_label(task.target_type)} · {task.target_id[:18]} · "
                f"{status_label(task.status)}"
            )
            choices.append((label, task.id))
            rows.append(
                [
                    task.id,
                    visual_target_label(task.target_type),
                    task.target_id,
                    status_label(task.status),
                    decision_label(task.decision),
                    task.version,
                    ", ".join(task.reasons),
                ]
            )
        return rows, dropdown_update(
            gr,
            choices,
            empty_label="暂无审核任务",
            value=choices[0][1] if choices else None,
        )

    async def visual_review_detail(
        run_id: str | None, task_id: str | None
    ) -> tuple[dict[str, Any], str | None, int]:
        if not run_id or not task_id:
            return {}, None, 0
        state = service.show_run(run_id)
        task = next((item for item in state.visual_review_tasks if item.id == task_id), None)
        if task is None:
            raise ValueError("视觉审核任务不存在")
        if task.target_type == "media_relation":
            relation_candidate = next(
                item for item in state.candidate_media_relations if item.id == task.target_id
            )
            occurrence_id = relation_candidate.occurrence_id
            candidate_payload = relation_candidate.model_dump(mode="json")
        else:
            assertion_candidate = next(
                item for item in state.candidate_visual_assertions if item.id == task.target_id
            )
            occurrence_id = assertion_candidate.occurrence_id
            candidate_payload = assertion_candidate.model_dump(mode="json")
        occurrence = next(item for item in state.media_occurrences if item.id == occurrence_id)
        evidence, preview = await show_evidence(occurrence.evidence_id)
        return (
            {
                "task": task.model_dump(mode="json"),
                "candidate": candidate_payload,
                "occurrence": occurrence.model_dump(mode="json"),
                "evidence": evidence,
            },
            preview,
            task.version,
        )

    async def submit_visual_review(
        run_id: str,
        task_id: str,
        decision: str,
        reviewer: str,
        reason: str,
        expected_version: int,
    ) -> tuple[str, list[list[Any]], Any]:
        state = await service.review_visual(
            run_id,
            task_id,
            cast(Literal["approve", "reject", "defer"], decision),
            reviewer,
            reason,
            uuid4().hex,
            int(expected_version),
        )
        rows, choices = visual_review_rows(state.run_id)
        return f"审核已保存：`{decision_label(decision)}` · 运行 `{state.run_id}`", rows, choices

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
            raise ValueError("请先确认补偿回滚操作")
        result = await service.graph_store.rollback_revision(revision_id)
        service.audit.record(
            "rollback", revision_id, {"compensation_revision_id": result.id, "source": "ui"}
        )
        return result.model_dump(mode="json")

    def case_rows(
        case_type: str, task_type: str, language: str, include_disabled: bool
    ) -> tuple[list[list[Any]], Any]:
        records = service.list_cases(
            case_type=None if case_type == "全部" else case_type,
            task_type=None if task_type == "全部" else task_type,
            language=None if language == "全部" else language,
            active_only=not include_disabled,
        )
        rows = [
            [
                item["id"],
                item["case_type"],
                item["task_type"],
                item["language"],
                item["decision"],
                item["active"],
                item["input_summary"],
            ]
            for item in records
        ]
        choices = [
            (f"{item['case_type']} · {item['input_summary'][:48]}", item["id"]) for item in records
        ]
        return rows, dropdown_update(
            gr,
            choices,
            empty_label="暂无记录",
            value=choices[0][1] if choices else None,
        )

    def case_detail(case_id: str | None) -> dict[str, Any]:
        return service.get_case(case_id) if case_id else {}

    def disable_case_ui(
        case_id: str | None,
        operator: str,
        reason: str,
        confirmed: bool,
    ) -> dict[str, Any]:
        if not confirmed:
            raise ValueError("请先确认停用案例")
        if not case_id:
            raise ValueError("请选择案例")
        from uuid import uuid4

        return service.disable_case(
            case_id,
            operator=operator,
            reason=reason,
            request_id=uuid4().hex,
        )

    async def rebuild_cases(dry_run: bool) -> dict[str, Any]:
        return await service.rebuild_case_index(dry_run=dry_run)

    def reflection_report(run_id: str | None) -> dict[str, Any]:
        if not run_id:
            return {}
        state = service.show_run(run_id)
        return {
            "enabled": state.reflection_enabled,
            "provider": state.reflection_provider_name,
            "policy": state.reflection_policy_version,
            "case_mode": state.case_mode,
            "case_snapshot": state.case_snapshot_fingerprint,
            "retrieved_cases": [item.model_dump(mode="json") for item in state.retrieved_cases],
            "attempts": [item.model_dump(mode="json") for item in state.reflection_attempts],
            "repaired_issue_ids": state.repaired_issue_ids,
            "token_usage": state.reflection_token_usage,
            "elapsed_ms": state.reflection_elapsed_ms,
        }

    async def health() -> dict[str, Any]:
        result = await service.graph_store.healthcheck()
        return result.model_dump(mode="json")

    async def search_entities(query: str, entity_type: str, limit: int) -> list[dict[str, Any]]:
        return [
            item.model_dump(mode="json")
            for item in await service.search_entities(query, entity_type, limit)
        ]

    def evidence_runs() -> Any:
        choices = [
            (f"{Path(state.input_path).name} · {status_label(state.status)}", state.run_id)
            for state in service.runs.list(limit=1000)
        ]
        return dropdown_update(
            gr,
            choices,
            empty_label="暂无运行",
            value=choices[0][1] if choices else None,
        )

    def run_claims(run_id: str | None) -> Any:
        if not run_id:
            return dropdown_update(gr, [], empty_label="暂无 Claim")
        state = service.show_run(run_id)
        choices = [
            (
                f"{claim.subject_id} · {claim.relation_id} · "
                f"{claim.object_entity_id or claim.object_literal}",
                claim.id,
            )
            for claim in state.claims
        ]
        return dropdown_update(
            gr,
            choices,
            empty_label="暂无 Claim",
            value=choices[0][1] if choices else None,
        )

    def claim_evidence(run_id: str | None, claim_id: str | None) -> Any:
        if not run_id or not claim_id:
            return dropdown_update(gr, [], empty_label="暂无证据")
        state = service.show_run(run_id)
        claim = next((item for item in state.claims if item.id == claim_id), None)
        choices = claim.evidence_ids if claim else []
        return dropdown_update(
            gr,
            choices,
            empty_label="暂无证据",
            value=choices[0] if choices else None,
        )

    async def graph_search(query: str, entity_type: str, limit: int) -> tuple[list[list[Any]], Any]:
        candidates = await service.search_entities(query, entity_type, limit)
        entities = {item.id: item for item in await service.graph_store.list_entities()}
        rows = []
        choices = []
        for candidate in candidates:
            entity = entities.get(candidate.entity_id)
            name = entity.name if entity else candidate.entity_id
            kind = entity.entity_type if entity else entity_type
            rows.append([candidate.entity_id, name, kind, round(candidate.final_score, 4)])
            choices.append((f"{name} · {kind} · {candidate.final_score:.3f}", candidate.entity_id))
        return rows, dropdown_update(
            gr,
            choices,
            empty_label="暂无实体",
            value=choices[0][1] if choices else None,
        )

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

    async def dashboard() -> tuple[str, list[list[Any]], str]:
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
                    status_label(state.status),
                    status_label(execution["status"]),
                    execution["node"],
                    execution["updated_at"] or "",
                ]
            )
        graph = summary["graph_health"]
        graph_text = (
            f"**{graph['backend']}** · "
            f"{'健康' if graph['healthy'] else '异常'} · {graph['message']}"
        )
        return headline, recent, graph_text

    def sidebar_run(run_id: str | None) -> tuple[Any, str]:
        states = service.runs.list(limit=1000)
        choices = [
            (f"{Path(state.input_path).name} · {status_label(state.status)}", state.run_id)
            for state in states
        ]
        if run_id not in {state.run_id for state in states}:
            run_id = states[0].run_id if states else None
        if not run_id:
            return dropdown_update(gr, [], empty_label="暂无运行"), "暂无运行"
        progress = service.review_progress(run_id)
        execution = progress["execution"]
        text = (
            f"业务：{status_label(progress['status'])}\n"
            f"执行：{status_label(execution['status'])}\n"
            f"节点：{execution['node']}\n实体待审：{progress['entity_pending']} · "
            f"事实待审：{progress['claim_pending']} · "
            f"视觉待审：{progress['visual_pending']} · 校验：{progress['validation_pending']}"
        )
        return dropdown_update(
            gr,
            choices,
            empty_label="暂无运行",
            value=run_id,
        ), text

    def save_settings(
        llm_base_url: str,
        llm_model: str,
        vlm_base_url: str,
        vlm_model: str,
        ocr_device: str,
        ocr_lang: str,
        ocr_model: str,
        graph_store: str,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_database: str,
        neo4j_password: str,
        clear_neo4j_password: bool,
        operator: str,
    ) -> tuple[str, Any, Any]:
        if neo4j_password.strip() and clear_neo4j_password:
            raise ValueError("不能同时设置和清除 Neo4j 密码")
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
            "neo4j_password": neo4j_password or None,
        }
        clear_secrets = ["neo4j_password"] if clear_neo4j_password else []
        result = service.update_settings(values, clear_secrets, operator)
        settings = result["settings"]
        restart_note = " · 需要重启服务" if result["restart_required"] else ""
        return (
            f"设置已保存 · 图存储 {settings['graph_store']} · "
            f"LLM {settings['llm_model']}{restart_note}",
            gr.update(value=""),
            gr.update(value=False),
        )

    claim_headers = [
        "结果 ID",
        "主体/名称",
        "类型/关系",
        "宾语/值",
        "置信度",
        "状态",
        "证据",
    ]
    public_settings = service.settings_view()
    configured_ocr_lang = public_settings["ocr_lang"]
    if configured_ocr_lang == "ch":
        configured_ocr_lang = "mixed"
    resolved_ocr_device = public_settings["ocr_device_resolved"]
    resolved_ocr_device_label = "GPU 0" if resolved_ocr_device == "gpu:0" else "CPU"
    with gr.Blocks(
        title="PrismKE 研究工作台",
        fill_height=True,
        analytics_enabled=False,
        elem_id="prismke-workspace",
    ) as demo:
        with gr.Sidebar(open=True, elem_id="workspace-sidebar"):
            gr.Markdown(
                f"**工作区**  \nDevelopment · `{__version__}`",
                elem_classes="sidebar-status",
            )
            if service.review_metadata:
                gr.Markdown("**隔离审核工作区**\n\n原评测只读，抽取调用禁用。")
            navigation_group = gr.Dropdown(
                group_choices(),
                value="overview",
                label="功能分组",
                elem_id="navigation-group",
            )
            navigation_page = gr.Dropdown(
                page_choices("overview"),
                value="overview",
                label="具体页面",
                visible=False,
                elem_id="navigation-page",
            )
            current_run = gr.Dropdown(label="当前运行", **empty_dropdown_kwargs("暂无运行"))
            run_context = gr.Markdown("暂无运行", elem_classes="sidebar-status")
            refresh_context = gr.Button("刷新运行")
            with gr.Accordion("任务配置", open=True):
                task_mode_input = gr.Dropdown(
                    [
                        ("实体抽取", "entity_extraction"),
                        ("关系抽取", "relation_extraction"),
                        ("Schema 信息抽取", "schema_information_extraction"),
                        ("端到端实体关系抽取", "joint_entity_relation_extraction"),
                        (
                            "实体关系抽取与消歧",
                            "joint_entity_relation_disambiguation",
                        ),
                        ("完整知识构建", "knowledge_graph_construction"),
                    ],
                    value="knowledge_graph_construction",
                    label="任务模式",
                )
                pdf_parse_mode_input = gr.Dropdown(
                    [
                        ("自动判定（推荐）", "auto"),
                        ("PyMuPDF 快速解析", "pymupdf"),
                        ("MinerU 高精度解析", "mineru"),
                    ],
                    value="auto",
                    label="PDF 解析模式",
                )
                entity_source_input = gr.Dropdown(
                    [("系统自动识别", "auto"), ("使用提供实体", "provided")],
                    value="auto",
                    label="关系实体来源",
                    visible=False,
                )
                provided_entities_input = gr.Code(
                    label="实体清单 JSON",
                    language="json",
                    value="[]",
                    visible=False,
                )
                schema_source = gr.Dropdown(
                    [("上传文件", "upload"), ("文本输入", "text")],
                    value="upload",
                    label="Schema 来源",
                )
                schema_input = gr.File(label="Schema 文件", type="filepath")
                schema_text = gr.Textbox(
                    label="Schema 文本（JSON/YAML）",
                    lines=10,
                    visible=False,
                )
                validate_schema = gr.Button("校验 Schema")
                schema_result = gr.Markdown("尚未校验 Schema", elem_classes="sidebar-status")
                provider_input = gr.Dropdown(
                    ["mock", "openai-compatible"],
                    value="openai-compatible",
                    label="文本 Provider",
                )
                ocr_input = gr.Dropdown(
                    ["disabled", "mock", "paddle"], value="paddle", label="OCR Provider"
                )
                vlm_input = gr.Dropdown(
                    ["disabled", "mock", "openai-compatible"],
                    value="openai-compatible",
                    label="视觉 Provider",
                )
                allow_remote = gr.Checkbox(label="允许远程资源", value=False)
                case_mode_input = gr.Dropdown(
                    ["none", "good", "good_bad"], value="none", label="案例检索"
                )
            with gr.Accordion("高级策略", open=True):
                reflection_enabled_input = gr.Checkbox(label="启用 Reflection", value=True)
                reflection_provider_input = gr.Dropdown(
                    ["disabled", "mock", "openai-compatible"],
                    value="openai-compatible",
                    label="Reflection Provider",
                )
                reflection_attempts_input = gr.Slider(
                    0, 2, value=2, step=1, label="单候选最大修复次数"
                )
                reflection_tokens_input = gr.Number(
                    value=20_000, precision=0, label="单运行 Token 预算"
                )
                reflection_time_input = gr.Number(
                    value=180, precision=0, label="单运行时间预算（秒）"
                )
                semantic_advisor_input = gr.Dropdown(
                    ["disabled", "mock", "openai-compatible"],
                    value="openai-compatible",
                    label="治理/融合语义建议",
                )
                agent_tokens_input = gr.Number(
                    value=20_000, precision=0, label="Agent 建议 Token 预算"
                )
                gr.Markdown(
                    "默认启用受预算限制的 Reflection 与语义建议，"
                    "会产生额外模型调用；缺少 LLM Key 时将在调用前阻断。",
                    elem_classes="sidebar-status",
                )
            with gr.Accordion("模型与图存储", open=False):
                llm_base = gr.Textbox(label="LLM Base URL", value=public_settings["llm_base_url"])
                llm_model = gr.Textbox(
                    value=public_settings["llm_model"] or "qwen3.7-flash",
                    label="LLM 模型别名",
                )
                llm_api_key = gr.Textbox(
                    label="LLM API Key（当前会话）",
                    type="password",
                    placeholder="留空则使用服务器配置",
                )
                vlm_base = gr.Textbox(label="VLM Base URL", value=public_settings["vlm_base_url"])
                vlm_model = gr.Textbox(
                    value=public_settings["vlm_model"] or "qwen3.7-flash",
                    label="VLM 模型别名",
                )
                vlm_api_key = gr.Textbox(
                    label="VLM API Key（当前会话）",
                    type="password",
                    placeholder="留空则使用服务器配置",
                )
                gr.Markdown(
                    "**密钥状态**  "
                    f"LLM：{'已配置' if public_settings['llm_api_key'] else '未配置'} · "
                    f"VLM：{'已配置' if public_settings['vlm_api_key'] else '未配置'}  \n"
                    "页面输入的 API Key 仅保存在当前服务进程内，不写入运行文件或日志。"
                )
                ocr_device = gr.Dropdown(
                    [
                        (f"自动（当前：{resolved_ocr_device_label}）", "auto"),
                        ("CPU", "cpu"),
                        ("GPU 0", "gpu:0"),
                    ],
                    value=public_settings["ocr_device"],
                    label="OCR 设备",
                )
                ocr_lang = gr.Dropdown(
                    [("中英混合", "mixed"), ("英文", "en"), ("中文", "zh")],
                    value=configured_ocr_lang,
                    label="OCR 语言",
                )
                ocr_model = gr.Dropdown(
                    ["PP-OCRv5", "PP-OCRv4", "PP-OCRv3"],
                    value=public_settings["ocr_model"],
                    label="OCR 模型",
                    allow_custom_value=True,
                )
                graph_store = gr.Dropdown(
                    ["json", "neo4j"], value=public_settings["graph_store"], label="图存储"
                )
                neo4j_uri = gr.Textbox(label="Neo4j URI", value=public_settings["neo4j_uri"])
                neo4j_user = gr.Dropdown(
                    ["neo4j"],
                    value=public_settings["neo4j_user"],
                    label="Neo4j 用户",
                    allow_custom_value=True,
                )
                neo4j_database = gr.Dropdown(
                    ["neo4j"],
                    value=public_settings["neo4j_database"],
                    label="Neo4j 数据库",
                    allow_custom_value=True,
                )
                neo4j_password = gr.Textbox(
                    label="Neo4j 密码",
                    type="password",
                    placeholder="留空则保持已有密码",
                )
                clear_neo4j_password = gr.Checkbox(label="清除已保存 Neo4j 密码", value=False)
                gr.Markdown(
                    "**Neo4j 密码：** "
                    f"{'已配置' if public_settings['neo4j_password'] else '未配置'}  \n"
                    "页面不回显旧密码；新值保存到权限为 600 的私密运行配置。"
                )
                config_operator = gr.Textbox(
                    label="配置操作者",
                    value="管理员",
                    elem_id="config-operator",
                )
                save_config = gr.Button("保存设置", variant="primary")
                config_outcome = gr.Textbox(label="设置结果", interactive=False)

        language_switch = build_brand_header(gr, __version__)

        with gr.Tabs(selected="overview", elem_id="workspace-tabs") as workspace_tabs:
            with gr.Tab("总览", id="overview"):
                page_header(gr, "overview")
                overview = gr.Markdown(elem_classes="workspace-metrics")
                refresh_overview = gr.Button("刷新总览")
                recent_runs = gr.Dataframe(
                    headers=["文档", "业务状态", "执行状态", "节点", "更新时间"],
                    interactive=False,
                    wrap=True,
                    label="最近运行",
                )
                graph_health = gr.Markdown(label="图存储健康状态")

            with gr.Tab("新建构建", id="build"):
                page_header(gr, "build")
                with gr.Row(equal_height=False):
                    with gr.Column(scale=2, min_width=300):
                        document_input = gr.File(
                            label="文档（最多 20 个）",
                            type="filepath",
                            file_count="multiple",
                            file_types=[
                                ".txt",
                                ".md",
                                ".markdown",
                                ".pdf",
                                ".doc",
                                ".docx",
                                ".html",
                                ".htm",
                                ".json",
                                ".png",
                                ".jpg",
                                ".jpeg",
                                ".webp",
                                ".tif",
                                ".tiff",
                                ".bmp",
                            ],
                        )
                        run_button = gr.Button("开始构建", variant="primary")
                        reload_button = gr.Button("刷新运行状态")
                    with gr.Column(scale=3, min_width=320):
                        run_status = gr.Markdown(
                            "尚未启动构建",
                            elem_classes="workspace-metrics",
                        )
                        with gr.Accordion(
                            "技术详情",
                            open=False,
                            elem_classes="technical-detail",
                        ):
                            run_summary = gr.JSON(label="完整运行状态")
                run_id_output = gr.State()
                batch_id_output = gr.State()
                batch_table = gr.Dataframe(
                    headers=["文件", "状态", "Run ID", "复用来源", "失败代码"],
                    interactive=False,
                    label="批次文件",
                    wrap=True,
                )
                claim_table = gr.Dataframe(
                    headers=claim_headers, interactive=False, label="抽取结果", wrap=True
                )
                with gr.Accordion("批次处理", open=False):
                    batch_item_selector = gr.Dropdown(
                        label="批次文件", **empty_dropdown_kwargs("暂无批次文件")
                    )
                    batch_operator = gr.Textbox(label="操作者", value="管理员")
                    batch_reason = gr.Textbox(label="排除原因")
                    with gr.Row():
                        retry_batch_button = gr.Button("重试文件")
                        exclude_batch_button = gr.Button("排除文件", variant="stop")
                    batch_action_outcome = gr.Markdown("尚未执行批次操作")
                    with gr.Group(visible=True) as batch_commit_group:
                        batch_reviewer = gr.Textbox(label="提交审核人", value="管理员")
                        batch_commit_confirm = gr.Checkbox(
                            label="我确认将该批次的已批准事实写入图谱"
                        )
                        batch_commit_button = gr.Button("提交批次到图谱", variant="primary")
                with gr.Accordion("抽取结果审核", open=False):
                    extraction_review_target = gr.Dropdown(
                        label="审核对象", **empty_dropdown_kwargs("暂无审核对象")
                    )
                    extraction_review_decision = gr.Dropdown(
                        [("批准", "approve"), ("拒绝", "reject"), ("暂缓", "defer")],
                        value="approve",
                        label="审核决定",
                    )
                    extraction_reviewer = gr.Textbox(label="审核人", value="管理员")
                    extraction_review_reason = gr.Textbox(label="审核意见")
                    extraction_review_button = gr.Button("保存抽取审核")
                    extraction_review_outcome = gr.Markdown("尚未审核抽取结果")

            build_review_tabs(service)
            from frontend.execution import build_execution_tab

            build_execution_tab(service, llm_api_key, vlm_api_key)

            with gr.Tab("证据", id="evidence"):
                page_header(gr, "evidence")
                with gr.Row():
                    evidence_run = gr.Dropdown(label="运行", **empty_dropdown_kwargs("暂无运行"))
                    evidence_claim = gr.Dropdown(
                        label="Claim", **empty_dropdown_kwargs("暂无 Claim")
                    )
                evidence_id = gr.Dropdown(label="证据", **empty_dropdown_kwargs("暂无证据"))
                evidence_button = gr.Button("读取证据")
                evidence_preview = gr.Image(label="证据定位", type="filepath")
                with gr.Accordion("技术详情", open=False, elem_classes="technical-detail"):
                    evidence_metadata = gr.JSON(label="证据元数据")
                evidence_run.change(guard_ui(gr, run_claims), evidence_run, evidence_claim).then(
                    guard_ui(gr, claim_evidence),
                    [evidence_run, evidence_claim],
                    evidence_id,
                )
                evidence_claim.change(
                    guard_ui(gr, claim_evidence),
                    [evidence_run, evidence_claim],
                    evidence_id,
                )
                evidence_button.click(
                    guard_ui(gr, show_evidence, 2),
                    [evidence_id],
                    [evidence_metadata, evidence_preview],
                )
                with gr.Accordion("Claim 关联图片", open=False):
                    claim_media_button = gr.Button("查看 Claim 关联媒体")
                    claim_media_table = gr.Dataframe(
                        headers=["Occurrence ID", "类型", "文档", "页码", "标题", "Evidence ID"],
                        interactive=False,
                        wrap=True,
                    )
                claim_media_button.click(
                    guard_ui(gr, claim_linked_media),
                    evidence_claim,
                    claim_media_table,
                )

            with gr.Tab("图谱", id="graph"):
                page_header(gr, "graph")
                with gr.Row():
                    graph_query = gr.Textbox(label="实体名称或别名")
                    graph_entity_type = gr.Textbox(label="实体类型")
                    graph_limit = gr.Slider(1, 20, value=10, step=1, label="候选数")
                graph_search_button = gr.Button("搜索实体")
                graph_candidates = gr.Dataframe(
                    headers=["Entity ID", "名称", "类型", "得分"],
                    interactive=False,
                    wrap=True,
                    label="搜索结果",
                )
                entity_id = gr.Dropdown(label="选择实体", **empty_dropdown_kwargs("暂无实体"))
                depth = gr.Slider(1, 3, value=1, step=1, label="邻域深度")
                graph_search_button.click(
                    guard_ui(gr, graph_search, 2),
                    [graph_query, graph_entity_type, graph_limit],
                    [graph_candidates, entity_id],
                )
                graph_button = gr.Button("查询邻域")
                graph_plot = gr.Plot(label="实体邻域图")
                with gr.Accordion("技术详情", open=False, elem_classes="technical-detail"):
                    graph_output = gr.JSON(label="实体邻域")
                graph_button.click(
                    guard_ui(gr, neighborhood, 2),
                    [entity_id, depth],
                    [graph_plot, graph_output],
                )
                with gr.Accordion("实体关联图片", open=False):
                    entity_media_button = gr.Button("展开实体关联媒体")
                    entity_media_table = gr.Dataframe(
                        headers=["Occurrence ID", "类型", "文档", "页码", "标题", "Evidence ID"],
                        interactive=False,
                        wrap=True,
                    )
                entity_media_button.click(
                    guard_ui(gr, entity_linked_media),
                    entity_id,
                    entity_media_table,
                )

            with gr.Tab("媒体资产", id="media"):
                page_header(gr, "media")
                with gr.Row():
                    media_document_filter = gr.Textbox(label="文档 ID", placeholder="留空显示全部")
                    media_type_filter = gr.Dropdown(
                        [
                            ("全部", "全部"),
                            ("图片", "image"),
                            ("图表", "chart"),
                            ("表格", "table"),
                            ("公式", "formula"),
                            ("页面渲染", "page_render"),
                        ],
                        value="全部",
                        label="媒体类型",
                    )
                media_refresh = gr.Button("刷新媒体资产")
                media_table = gr.Dataframe(
                    headers=[
                        "Occurrence ID",
                        "类型",
                        "文档",
                        "页码",
                        "标题",
                        "证据哈希",
                        "关联知识",
                    ],
                    interactive=False,
                    wrap=True,
                    label="可查询媒体对象",
                )
                media_selector = gr.Dropdown(
                    label="选择媒体出现记录",
                    **empty_dropdown_kwargs("暂无媒体出现记录"),
                )
                with gr.Row(equal_height=False):
                    media_preview = gr.Image(label="受控证据预览", type="filepath")
                    with gr.Accordion(
                        "媒体、实体与 Claim 详情",
                        open=False,
                        elem_classes="technical-detail",
                    ):
                        media_detail_output = gr.JSON(label="媒体详情")
                media_refresh.click(
                    guard_ui(gr, media_rows, 2),
                    [media_document_filter, media_type_filter],
                    [media_table, media_selector],
                )
                media_selector.change(
                    guard_ui(gr, media_detail, 2),
                    media_selector,
                    [media_detail_output, media_preview],
                )

            with gr.Tab("视觉审核", id="visual-review"):
                page_header(gr, "visual-review")
                with gr.Row():
                    visual_review_run = gr.Dropdown(
                        label="运行", **empty_dropdown_kwargs("暂无运行")
                    )
                    visual_review_refresh = gr.Button("刷新视觉审核队列")
                visual_review_table = gr.Dataframe(
                    headers=["Task ID", "对象类型", "候选 ID", "状态", "决定", "版本", "原因"],
                    interactive=False,
                    wrap=True,
                    label="视觉审核任务",
                )
                visual_review_selector = gr.Dropdown(
                    label="选择任务", **empty_dropdown_kwargs("暂无审核任务")
                )
                with gr.Row(equal_height=False):
                    visual_review_preview = gr.Image(label="区域证据", type="filepath")
                    with gr.Accordion(
                        "候选、实体与 Schema 约束",
                        open=True,
                        elem_classes="technical-detail",
                    ):
                        visual_review_detail_output = gr.JSON(label="审核详情")
                with gr.Row():
                    visual_review_decision = gr.Dropdown(
                        [("批准", "approve"), ("拒绝", "reject"), ("暂缓", "defer")],
                        value="approve",
                        label="审核决定",
                    )
                    visual_review_reviewer = gr.Textbox(label="审核人", value="管理员")
                visual_review_reason = gr.Textbox(label="审核原因")
                visual_review_version = gr.Number(label="任务版本", value=0, interactive=False)
                visual_review_submit = gr.Button("提交视觉审核", variant="primary")
                visual_review_outcome = gr.Markdown("尚未提交视觉审核")
                visual_review_refresh.click(
                    guard_ui(gr, visual_review_rows, 2),
                    visual_review_run,
                    [visual_review_table, visual_review_selector],
                )
                visual_review_selector.change(
                    guard_ui(gr, visual_review_detail, 3),
                    [visual_review_run, visual_review_selector],
                    [
                        visual_review_detail_output,
                        visual_review_preview,
                        visual_review_version,
                    ],
                )
                visual_review_submit.click(
                    guard_ui(gr, submit_visual_review, 3),
                    [
                        visual_review_run,
                        visual_review_selector,
                        visual_review_decision,
                        visual_review_reviewer,
                        visual_review_reason,
                        visual_review_version,
                    ],
                    [visual_review_outcome, visual_review_table, visual_review_selector],
                )

            with gr.Tab("实体治理", id="governance"):
                page_header(gr, "governance")
                with gr.Row():
                    entity_query = gr.Textbox(label="名称、别名或上下文")
                    entity_type = gr.Textbox(label="实体类型")
                    entity_limit = gr.Slider(1, 20, value=10, step=1, label="候选数")
                entity_search_button = gr.Button("检索候选")
                with gr.Accordion("候选评分详情", open=False):
                    entity_search_output = gr.JSON(label="候选及评分分解")
                entity_search_button.click(
                    guard_ui(gr, search_entities),
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
                        guard_ui(gr, show_evidence, 2),
                        [mention_evidence_id],
                        [mention_evidence_metadata, mention_evidence_preview],
                    )
                    candidate_neighborhood_button.click(
                        guard_ui(gr, neighborhood, 2),
                        [candidate_entity_id, gr.State(1)],
                        [candidate_neighborhood_plot, candidate_neighborhood_output],
                    )
                with gr.Accordion("高级治理操作", open=False):
                    gr.Markdown("### 合并与拆分审核")
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
                        guard_ui(gr, review_entity_task),
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
                        guard_ui(gr, propose_merge),
                        [merge_sources, merge_target, merge_reasons],
                        [merge_output],
                    )
                    gr.Markdown("### 实体拆分建议")
                    split_source = gr.Textbox(label="原 Entity ID")
                    split_targets = gr.Code(label="新实体 JSON 数组", language="json", value="[]")
                    split_assignments = gr.Code(
                        label="Claim 到新 Entity 的映射 JSON", language="json", value="{}"
                    )
                    split_reasons = gr.Textbox(label="理由，分号分隔")
                    split_button = gr.Button("创建拆分审核任务")
                    split_output = gr.JSON(label="拆分建议")
                    split_button.click(
                        guard_ui(gr, propose_split),
                        [split_source, split_targets, split_assignments, split_reasons],
                        [split_output],
                    )
                    gr.Markdown("### 实体治理历史")
                    history_entity_id = gr.Textbox(label="实体 Entity ID")
                    history_button = gr.Button("查询治理与回滚历史")
                    history_output = gr.JSON(label="实体 Revision 历史")
                    history_button.click(
                        guard_ui(gr, entity_history),
                        [history_entity_id],
                        [history_output],
                    )

            build_validation_tab(gr, service)

            with gr.Tab("版本", id="revisions"):
                page_header(gr, "revisions")
                revision_button = gr.Button("刷新版本")
                revision_table = gr.Dataframe(
                    headers=["Revision ID", "父版本", "Run ID", "时间", "变更数"],
                    interactive=False,
                )
                revision_button.click(guard_ui(gr, revisions), outputs=[revision_table])
                with gr.Row():
                    from_revision = gr.Textbox(label="起始 Revision")
                    to_revision = gr.Textbox(label="目标 Revision")
                diff_button = gr.Button("比较版本")
                with gr.Accordion("版本差异", open=False, elem_classes="technical-detail"):
                    diff_output = gr.JSON(label="完整差异")
                diff_button.click(
                    guard_ui(gr, revision_diff),
                    [from_revision, to_revision],
                    [diff_output],
                )
                with gr.Accordion("补偿回滚", open=False):
                    rollback_revision_id = gr.Textbox(label="要回滚的 Revision")
                    rollback_confirm = gr.Checkbox(label="我确认创建补偿 Revision")
                    rollback_button = gr.Button("执行回滚", variant="stop")
                    rollback_output = gr.JSON(label="补偿 Revision")
                    rollback_button.click(
                        guard_ui(gr, rollback),
                        [rollback_revision_id, rollback_confirm],
                        [rollback_output],
                    )

            with gr.Tab("案例库", id="cases"):
                page_header(gr, "cases")
                with gr.Row():
                    case_type_filter = gr.Dropdown(
                        ["全部", "good", "bad"], value="全部", label="案例类型"
                    )
                    case_task_filter = gr.Dropdown(
                        ["全部", "entity", "claim"], value="全部", label="任务类型"
                    )
                    case_language_filter = gr.Dropdown(
                        ["全部", "zh", "en"], value="全部", label="语言"
                    )
                    case_include_disabled = gr.Checkbox(label="包含已停用", value=False)
                case_refresh = gr.Button("刷新案例")
                case_table = gr.Dataframe(
                    headers=["ID", "类型", "任务", "语言", "决定", "启用", "输入摘要"],
                    interactive=False,
                    wrap=True,
                )
                case_selector = gr.Dropdown(label="选择案例", **empty_dropdown_kwargs("暂无记录"))
                with gr.Accordion("案例详情", open=False, elem_classes="technical-detail"):
                    case_detail_output = gr.JSON(label="案例、证据与停用历史")
                with gr.Accordion("停用案例", open=False):
                    case_operator = gr.Textbox(label="操作者")
                    case_reason = gr.Textbox(label="停用原因")
                    case_confirm = gr.Checkbox(label="我确认停用该案例")
                    case_disable_button = gr.Button("停用案例", variant="stop")
                    case_disable_output = gr.JSON(label="操作结果")
                with gr.Accordion("索引维护", open=False):
                    case_dry_run = gr.Checkbox(label="仅检查", value=True)
                    case_rebuild_button = gr.Button("检查或重建索引")
                    case_rebuild_output = gr.JSON(label="索引状态")
                case_refresh.click(
                    guard_ui(gr, case_rows, 2),
                    [
                        case_type_filter,
                        case_task_filter,
                        case_language_filter,
                        case_include_disabled,
                    ],
                    [case_table, case_selector],
                )
                case_selector.change(guard_ui(gr, case_detail), case_selector, case_detail_output)
                case_disable_button.click(
                    guard_ui(gr, disable_case_ui),
                    [case_selector, case_operator, case_reason, case_confirm],
                    case_disable_output,
                ).then(
                    case_rows,
                    [
                        case_type_filter,
                        case_task_filter,
                        case_language_filter,
                        case_include_disabled,
                    ],
                    [case_table, case_selector],
                )
                case_rebuild_button.click(
                    guard_ui(gr, rebuild_cases), case_dry_run, case_rebuild_output
                )

            with gr.Tab("Reflection", id="reflection"):
                page_header(gr, "reflection")
                reflection_run = gr.Dropdown(label="运行", **empty_dropdown_kwargs("暂无运行"))
                reflection_refresh = gr.Button("查看检索与修复记录")
                with gr.Accordion("Reflection 详情", open=False, elem_classes="technical-detail"):
                    reflection_output = gr.JSON(label="Reflection 摘要")
                reflection_refresh.click(
                    guard_ui(gr, reflection_report), reflection_run, reflection_output
                )

            with gr.Tab("Agent 协作", id="agents"):
                page_header(gr, "agents")
                agent_run = gr.Dropdown(label="运行", **empty_dropdown_kwargs("暂无运行"))
                agent_refresh = gr.Button("查看轨迹")
                agent_table = gr.Dataframe(
                    headers=["Agent", "步骤", "决定", "工具", "原因", "Token", "状态"],
                    interactive=False,
                    wrap=False,
                    column_widths=[100, 170, 180, 210, 210, 80, 90],
                    label="执行与交接",
                )
                with gr.Accordion("交接与模态详情", open=False):
                    agent_details = gr.JSON(label="Agent 交接")
                agent_refresh.click(
                    guard_ui(gr, agent_report, 2),
                    agent_run,
                    [agent_table, agent_details],
                )

            with gr.Tab("健康状态", id="health"):
                page_header(gr, "health")
                health_button = gr.Button("检查连接")
                with gr.Accordion("服务详情", open=False, elem_classes="technical-detail"):
                    health_output = gr.JSON(label="服务状态")
                health_button.click(guard_ui(gr, health), outputs=[health_output])

        def switch_group(group_id: str) -> tuple[Any, Any]:
            choices = page_choices(group_id)
            target = first_page(group_id)
            return (
                gr.update(choices=choices, value=target, visible=len(choices) > 1),
                gr.update(selected=target),
            )

        navigation_group.input(
            switch_group,
            navigation_group,
            [navigation_page, workspace_tabs],
            trigger_mode="multiple",
            concurrency_limit=None,
            queue=False,
        )

        def switch_page(page: str) -> tuple[Any, Any]:
            return gr.update(value=page), gr.update(selected=page)

        navigation_page.input(
            switch_page,
            navigation_page,
            [navigation_page, workspace_tabs],
            trigger_mode="multiple",
            concurrency_limit=None,
            queue=False,
        )
        schema_source.change(
            switch_schema_source,
            schema_source,
            [schema_input, schema_text],
        )

        def switch_task_mode(mode: str) -> tuple[Any, Any, Any]:
            relation = mode == "relation_extraction"
            return (
                gr.update(visible=relation),
                gr.update(visible=False),
                gr.update(visible=mode == "knowledge_graph_construction"),
            )

        task_mode_input.change(
            switch_task_mode,
            task_mode_input,
            [entity_source_input, provided_entities_input, batch_commit_group],
        )
        entity_source_input.change(
            lambda mode: gr.update(visible=mode == "provided"),
            entity_source_input,
            provided_entities_input,
        )
        validate_schema.click(
            guard_ui(gr, preview_schema),
            [schema_source, schema_input, schema_text],
            schema_result,
        )
        language_switch.input(
            fn=None,
            inputs=language_switch,
            outputs=None,
            js="""checked => {
              window.PrismKEI18n?.setLocale(checked ? 'zh-CN' : 'en', true);
            }""",
            queue=False,
        )
        demo.load(
            fn=None,
            js=(
                """() => {"""
                + browser_i18n_bootstrap_js()
                + """
              const sidebar = document.querySelector('#workspace-sidebar');
              const nativeToggle = sidebar?.querySelector('button[aria-label="Toggle Sidebar"]');
              if (!sidebar) return;
              const legacyStorageKey = 'prismke.workspace.sidebar.width';
              const storageKey = 'prismke.workspace.sidebar.ratio';
              const clampRatio = value => Math.max(0.2, Math.min(0.3, value));
              const storedRatio = Number(localStorage.getItem(storageKey));
              const legacyWidth = Number(localStorage.getItem(legacyStorageKey));
              let sidebarRatio = Number.isFinite(storedRatio) && storedRatio >= 0.2
                ? clampRatio(storedRatio)
                : Number.isFinite(legacyWidth) && legacyWidth > 0
                  ? clampRatio(legacyWidth / window.innerWidth)
                  : 0.2;
              const widthForRatio = ratio => Math.max(260, window.innerWidth * ratio);
              const applyRatio = value => {
                sidebarRatio = clampRatio(Number(value) || 0.2);
                const width = widthForRatio(sidebarRatio);
                document.documentElement.style.setProperty(
                  '--prism-sidebar-width', `${width}px`
                );
                return width;
              };
              const applyWidth = value => {
                const requested = Number(value) || widthForRatio(0.2);
                return applyRatio(requested / window.innerWidth);
              };
              if (window.innerWidth > 900) applyRatio(sidebarRatio);
              localStorage.removeItem(legacyStorageKey);

              let toggle = document.querySelector('#workspace-sidebar-toggle');
              if (!toggle) {
                toggle = document.createElement('button');
                toggle.id = 'workspace-sidebar-toggle';
                toggle.type = 'button';
                document.body.appendChild(toggle);
                toggle.addEventListener('click', () => nativeToggle?.click());
              }
              if (nativeToggle) {
                nativeToggle.style.setProperty('display', 'none', 'important');
                nativeToggle.setAttribute('aria-hidden', 'true');
                nativeToggle.tabIndex = -1;
              }
              const syncSidebarToggle = () => {
                const isOpen = sidebar.classList.contains('open');
                const isChinese = window.PrismKEI18n?.getLocale() === 'zh-CN';
                toggle.setAttribute('aria-expanded', String(isOpen));
                toggle.setAttribute('aria-controls', 'workspace-sidebar');
                toggle.setAttribute('aria-label', isChinese ? '切换侧栏' : 'Toggle Sidebar');
                toggle.title = isChinese
                  ? (isOpen ? '收起侧栏' : '展开侧栏')
                  : (isOpen ? 'Collapse sidebar' : 'Expand sidebar');
              };
              syncSidebarToggle();
              if (!window.__prismkeSidebarObserver) {
                window.__prismkeSidebarObserver = new MutationObserver(syncSidebarToggle);
                window.__prismkeSidebarObserver.observe(sidebar, {
                  attributes: true,
                  attributeFilter: ['class'],
                });
                window.addEventListener('prismke:localechange', syncSidebarToggle);
              }
              if (!window.__prismkeSidebarResizeBound) {
                window.__prismkeSidebarResizeBound = true;
                window.addEventListener('resize', () => {
                  if (window.innerWidth > 900) applyRatio(sidebarRatio);
                });
              }
              if (!window.__prismkeNavigationBound) {
                window.__prismkeNavigationBound = true;
                const navigateLabel = rawLabel => {
                  const aliases = {
                    '版本管理': '版本',
                    '系统状态': '健康状态',
                    'Revision management': 'Version',
                    'System status': 'Health status',
                  };
                  const label = aliases[rawLabel] || rawLabel;
                  const targets = Array.from(
                    document.querySelectorAll('#workspace-tabs button')
                  ).filter((button) => button.textContent.trim() === label);
                  targets.at(-1)?.click();
                };
                const navigate = event => {
                  const input = event.target;
                  if (!(input instanceof HTMLInputElement)) return;
                  if (!input.closest('#navigation-page')) return;
                  navigateLabel(input.value);
                };
                document.addEventListener('input', navigate, true);
                document.addEventListener('change', navigate, true);
                document.addEventListener('click', event => {
                  const option = event.target.closest?.('[role="option"]');
                  if (!option) return;
                  navigateLabel(option.textContent.trim());
                }, true);
                let lastPageLabel = document.querySelector('#navigation-page input')?.value;
                window.__prismkeNavigationTimer = window.setInterval(() => {
                  const input = document.querySelector('#navigation-page input');
                  if (!input || input.value === lastPageLabel) return;
                  lastPageLabel = input.value;
                  navigateLabel(input.value);
                }, 100);
              }
              let resizer = sidebar.querySelector('#workspace-resizer');
              if (!resizer) {
                resizer = document.createElement('div');
                resizer.id = 'workspace-resizer';
                resizer.tabIndex = 0;
                resizer.setAttribute('role', 'separator');
                resizer.setAttribute('aria-orientation', 'vertical');
                resizer.setAttribute(
                  'aria-label',
                  window.PrismKEI18n?.getLocale() === 'zh-CN'
                    ? '调整工作区宽度'
                    : 'Resize workspace sidebar'
                );
                sidebar.appendChild(resizer);
                let dragging = false;
                resizer.addEventListener('pointerdown', event => {
                  if (window.innerWidth <= 900) return;
                  dragging = true;
                  resizer.dataset.dragging = 'true';
                  resizer.setPointerCapture(event.pointerId);
                });
                resizer.addEventListener('pointermove', event => {
                  if (!dragging) return;
                  const width = applyWidth(event.clientX);
                  resizer.setAttribute('aria-valuenow', String(width));
                });
                const finish = () => {
                  if (!dragging) return;
                  dragging = false;
                  delete resizer.dataset.dragging;
                  localStorage.setItem(storageKey, String(sidebarRatio));
                };
                resizer.addEventListener('pointerup', finish);
                resizer.addEventListener('pointercancel', finish);
                resizer.addEventListener('keydown', event => {
                  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
                  event.preventDefault();
                  const next = event.key === 'Home' ? 0.2 : event.key === 'End' ? 0.3 :
                    sidebarRatio + (event.key === 'ArrowRight' ? 0.01 : -0.01);
                  const width = applyRatio(next);
                  localStorage.setItem(storageKey, String(sidebarRatio));
                  resizer.setAttribute('aria-valuenow', String(width));
                });
              }
              if (window.innerWidth <= 900 && sidebar?.classList.contains('open')) {
                toggle?.click();
              }
            }"""
            ),
        )
        refresh_context.click(
            guard_ui(gr, sidebar_run, 2), [current_run], [current_run, run_context]
        )
        current_run.change(guard_ui(gr, sidebar_run, 2), [current_run], [current_run, run_context])
        demo.load(guard_ui(gr, sidebar_run, 2), [current_run], [current_run, run_context])
        demo.load(guard_ui(gr, evidence_runs), outputs=evidence_run).then(
            guard_ui(gr, run_claims), evidence_run, evidence_claim
        ).then(
            guard_ui(gr, claim_evidence),
            [evidence_run, evidence_claim],
            evidence_id,
        )
        demo.load(guard_ui(gr, evidence_runs), outputs=reflection_run)
        demo.load(guard_ui(gr, evidence_runs), outputs=agent_run)
        demo.load(guard_ui(gr, evidence_runs), outputs=visual_review_run).then(
            guard_ui(gr, visual_review_rows, 2),
            visual_review_run,
            [visual_review_table, visual_review_selector],
        )
        demo.load(
            guard_ui(gr, media_rows, 2),
            [media_document_filter, media_type_filter],
            [media_table, media_selector],
        )
        demo.load(
            guard_ui(gr, case_rows, 2),
            [
                case_type_filter,
                case_task_filter,
                case_language_filter,
                case_include_disabled,
            ],
            [case_table, case_selector],
        )
        demo.load(guard_ui(gr, dashboard, 3), outputs=[overview, recent_runs, graph_health])
        refresh_overview.click(
            guard_ui(gr, dashboard, 3), outputs=[overview, recent_runs, graph_health]
        )
        run_button.click(
            guard_ui(gr, run_document, 8),
            [
                document_input,
                schema_source,
                schema_input,
                schema_text,
                provider_input,
                ocr_input,
                vlm_input,
                allow_remote,
                case_mode_input,
                reflection_enabled_input,
                reflection_provider_input,
                reflection_attempts_input,
                reflection_tokens_input,
                reflection_time_input,
                semantic_advisor_input,
                agent_tokens_input,
                llm_base,
                llm_model,
                llm_api_key,
                vlm_base,
                vlm_model,
                vlm_api_key,
                task_mode_input,
                entity_source_input,
                provided_entities_input,
                pdf_parse_mode_input,
                config_operator,
            ],
            [
                run_status,
                run_summary,
                claim_table,
                run_id_output,
                batch_id_output,
                batch_table,
                batch_item_selector,
                extraction_review_target,
            ],
        ).then(
            guard_ui(gr, sidebar_run, 2),
            [run_id_output],
            [current_run, run_context],
        )
        reload_button.click(
            guard_ui(gr, load_build, 6),
            [run_id_output, batch_id_output],
            [
                run_status,
                run_summary,
                claim_table,
                batch_table,
                batch_item_selector,
                extraction_review_target,
            ],
        )
        batch_item_selector.change(
            guard_ui(gr, select_batch_result, 3),
            [batch_id_output, batch_item_selector],
            [run_id_output, claim_table, extraction_review_target],
        )
        extraction_review_button.click(
            guard_ui(gr, review_extraction_result, 2),
            [
                run_id_output,
                extraction_review_target,
                extraction_review_decision,
                extraction_reviewer,
                extraction_review_reason,
            ],
            [claim_table, extraction_review_outcome],
        )
        batch_action_outputs = [
            run_status,
            run_summary,
            batch_table,
            batch_item_selector,
            batch_action_outcome,
        ]
        retry_batch_button.click(
            guard_ui(gr, retry_batch_item, 5),
            [batch_id_output, batch_item_selector],
            batch_action_outputs,
        )
        exclude_batch_button.click(
            guard_ui(gr, exclude_batch_item, 5),
            [batch_id_output, batch_item_selector, batch_operator, batch_reason],
            batch_action_outputs,
        )
        batch_commit_button.click(
            guard_ui(gr, confirm_batch_commit, 5),
            [batch_id_output, batch_reviewer, batch_commit_confirm],
            batch_action_outputs,
        )
        save_config.click(
            guard_ui(gr, save_settings, 3),
            [
                llm_base,
                llm_model,
                vlm_base,
                vlm_model,
                ocr_device,
                ocr_lang,
                ocr_model,
                graph_store,
                neo4j_uri,
                neo4j_user,
                neo4j_database,
                neo4j_password,
                clear_neo4j_password,
                config_operator,
            ],
            [config_outcome, neo4j_password, clear_neo4j_password],
        )

    return gr.mount_gradio_app(app, demo, path="/ui", css=APP_CSS)
