"""Gradio UI mounted on the PrismKE FastAPI application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from prismke.domain import ReviewDecision
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

    async def neighborhood(entity_id: str, depth: int) -> dict[str, Any]:
        result = await service.graph_store.get_neighborhood(entity_id, depth)
        return result.model_dump(mode="json")

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
            review_claim_id = gr.Textbox(label="Claim ID")
            review_decision = gr.Radio(
                ["approve", "reject"], value="approve", label="审核决定"
            )
            review_button = gr.Button("提交审核", variant="primary")
            review_summary = gr.JSON(label="审核后的运行状态")
            review_claims = gr.Dataframe(headers=claim_headers, interactive=False)
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
            graph_output = gr.JSON(label="实体邻域")
            graph_button.click(neighborhood, [entity_id, depth], [graph_output])

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
