"""Selectable review queues and verified evidence previews."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Literal, cast

from PIL import Image

from prismke.core.ids import stable_id
from prismke.domain import ReviewDecision
from prismke.workflow import PrismKEService


class ReviewController:
    def __init__(self, service: PrismKEService) -> None:
        self.service = service

    def runs(self) -> list[tuple[str, str]]:
        choices = []
        for state in self.service.runs.list(limit=1000):
            label = state.run_id
            if state.review_workspace and state.document:
                label = state.document.source_filename or "隔离导入文档"
            choices.append((f"{label} · {state.status} · {state.run_id}", state.run_id))
        return choices

    async def queue(
        self,
        run_id: str | None,
        kind: str,
        status: str,
        flagged: str,
    ) -> list[dict[str, Any]]:
        if not run_id:
            return []
        state = self.service.show_run(run_id)
        tasks = state.entity_review_tasks if kind == "entity" else state.review_tasks
        rows = []
        for task in tasks:
            if status != "all" and task.status != status:
                continue
            detail = (
                await self.service.entity_review_detail(run_id, task.id)
                if kind == "entity"
                else self.service.claim_review_detail(run_id, task.id)
            )
            if flagged == "flagged" and not detail["risk_flags"]:
                continue
            label = (
                detail["mention"]["name"]
                if detail.get("mention")
                else self.fact_label(detail["claim"])
                if kind == "claim"
                else task.id
            )
            rows.append(
                {
                    "id": task.id,
                    "label": label,
                    "status": task.status,
                    "flags": detail["risk_flags"],
                    "reasons": task.reasons,
                }
            )
        return rows

    @staticmethod
    def fact_label(claim: dict[str, Any]) -> str:
        return f"{claim['subject_name']} → {claim['relation_id']} → {claim['object_name']}"

    async def evidence(self, run_id: str, evidence_id: str) -> tuple[str, str | None]:
        try:
            ref = await self.service.evidence_store.get(evidence_id)
            state = self.service.show_run(run_id)
            if state.document is None or evidence_id not in {
                item.id for item in state.document.evidence
            }:
                raise ValueError("evidence does not belong to selected run")
            text = "\n".join(
                block.text
                for block in state.document.text_blocks
                if block.evidence_id == evidence_id
            )
            summary = (
                f"页码：{ref.page_number or '—'} · 定位："
                f"{ref.localization_level or ref.kind} · 坐标：{ref.coordinate_space or '—'}"
            )
            if text:
                summary += f"\n\n{text}"
            content = await self.service.evidence_store.crop(evidence_id)
            if ref.bbox is None and text:
                return summary, None
            with Image.open(BytesIO(content)) as image:
                output = (
                    self.service.settings.runtime_dir
                    / "ui"
                    / f"{stable_id('preview', evidence_id).replace(':', '_')}.png"
                )
                output.parent.mkdir(parents=True, exist_ok=True)
                image.convert("RGB").save(output, "PNG")
            return summary, str(output)
        except Exception:
            return "证据读取失败：文件缺失、损坏或无法生成预览，请勿据此批准。", None

    async def submit(
        self,
        run_id: str,
        task_id: str,
        kind: str,
        action: str,
        candidate_id: str | None,
        reviewer: str,
        comment: str,
        expected_version: int | None = None,
    ) -> None:
        if not reviewer.strip():
            raise ValueError("请填写审核人")
        if kind == "entity":
            if action not in {"link", "create", "reject", "defer"}:
                raise ValueError("请选择实体审核动作")
            await self.service.review_entity(
                run_id,
                task_id,
                cast(Literal["link", "create", "reject", "defer"], action),
                candidate_id,
                reviewer.strip(),
                comment,
                expected_version,
            )
        else:
            if action not in {"approve", "reject", "defer"}:
                raise ValueError("请选择事实审核动作")
            detail = self.service.claim_review_detail(run_id, task_id)
            await self.service.review(
                run_id,
                detail["claim"]["id"],
                ReviewDecision(action),
                reviewer.strip(),
                comment,
                expected_version,
            )


def build_review_tabs(service: PrismKEService) -> None:
    import gradio as gr

    controller = ReviewController(service)
    for kind, title, tab_id in (
        ("entity", "实体审核", "entity-review"),
        ("claim", "事实审核", "claim-review"),
    ):
        with gr.Tab(title, id=tab_id):
            _build_review_tab(gr, controller, kind)
    from frontend.corrections import build_correction_tab

    build_correction_tab(service)


def _build_review_tab(gr: Any, controller: ReviewController, kind: str) -> None:
    service = controller.service
    with gr.Row():
        run = gr.Dropdown(controller.runs(), label="运行", value=None)
        status = gr.Dropdown(
            [("待审核", "pending"), ("已处理", "resolved"), ("全部", "all")],
            value="pending",
            label="任务状态",
        )
        risk = gr.Dropdown([("全部", "all"), ("风险提示", "flagged")], value="all", label="风险")
        refresh = gr.Button("刷新")
    progress = gr.Textbox(label="审核进度", interactive=False)
    table = gr.Dataframe(
        headers=["对象", "状态", "风险提示", "审核原因"],
        interactive=False,
        wrap=True,
        label="任务列表",
    )
    task_ids = gr.State([])
    task_version = gr.State(None)
    task = gr.Dropdown(label="选择任务", choices=[], value=None)
    with gr.Row():
        with gr.Column(min_width=280):
            description = gr.Textbox(
                label="提及与关联事实" if kind == "entity" else "当前事实",
                lines=8,
                interactive=False,
            )
            flags = gr.Textbox(label="待核查提示", interactive=False)
            scores = gr.Dataframe(
                headers=[
                    "名称",
                    "类型",
                    "别名",
                    "召回",
                    "字符串",
                    "语义名称",
                    "上下文",
                    "邻域",
                    "综合",
                ],
                interactive=False,
                wrap=True,
                visible=kind == "entity",
                label="候选评分",
            )
            candidate = gr.Dropdown(
                label="链接候选", choices=[], value=None, visible=kind == "entity"
            )
            neighbor_button = gr.Button("查看所选候选邻域", visible=kind == "entity")
            neighbor = gr.JSON(label="候选邻域", visible=kind == "entity")
            evidence_choice = gr.Dropdown(label="当前对象证据", choices=[], value=None)
            evidence_text = gr.Textbox(label="证据原文与位置", lines=8, interactive=False)
            evidence_image = gr.Image(label="证据区域", type="filepath", visible=False)
        with gr.Column(min_width=280):
            peers = gr.Textbox(
                label="冲突对方事实", lines=8, interactive=False, visible=kind == "claim"
            )
            peer_evidence = gr.Dropdown(
                label="对方证据", choices=[], value=None, visible=kind == "claim"
            )
            peer_text = gr.Textbox(
                label="对方原文与位置", lines=8, interactive=False, visible=kind == "claim"
            )
            peer_image = gr.Image(label="对方证据区域", type="filepath", visible=kind == "claim")
            action = gr.Radio(
                [
                    ("链接候选", "link"),
                    ("创建新实体", "create"),
                    ("排除错误提及", "reject"),
                    ("暂缓判断", "defer"),
                ]
                if kind == "entity"
                else [("批准事实", "approve"), ("拒绝事实", "reject"), ("暂缓判断", "defer")],
                value=None,
                label="审核决定",
            )
            reviewer = gr.Textbox(label="审核人")
            comment = gr.Textbox(label="审核意见", lines=3)
            impact = gr.Textbox(label="操作影响", lines=4, interactive=False)
            submit = gr.Button("提交当前审核", variant="primary", interactive=False)
            resume = gr.Button("继续处理", interactive=False)
            preview = gr.JSON(label="隔离图谱提交摘要")
            confirm = gr.Checkbox(label="确认将预览内容写入隔离图谱", value=False)
            commit = gr.Button("确认写入隔离图谱", variant="stop", interactive=False)
            outcome = gr.Textbox(label="操作结果", interactive=False)

    async def load_queue(
        rid: str | None, selected_status: str, selected_risk: str
    ) -> tuple[Any, ...]:
        rows = await controller.queue(rid, kind, selected_status, selected_risk)
        p = service.review_progress(rid) if rid else {}
        return (
            [
                [row["label"], row["status"], "；".join(row["flags"]), "；".join(row["reasons"])]
                for row in rows
            ],
            [row["id"] for row in rows],
            gr.update(
                choices=[(row["label"], row["id"]) for row in rows],
                value=rows[0]["id"] if rows else None,
            ),
            f"实体待审核 {p.get('entity_pending', 0)} · 事实待审核 {p.get('claim_pending', 0)} · "
            f"校验待处理 {p.get('validation_pending', 0)} · "
            f"{p.get('status', '未选择运行')} · {p.get('node', '')}"
            + (" · 同步待恢复：继续与写图已禁用" if p.get("review_sync_pending") else ""),
            gr.update(interactive=p.get("can_resume", False)),
            p.get("submission"),
            gr.update(interactive=p.get("can_commit", False)),
            gr.update(value=False),
        )

    async def load_task(rid: str | None, tid: str | None) -> tuple[Any, ...]:
        if not rid or not tid:
            return (
                "",
                "",
                [],
                gr.update(choices=[], value=None),
                gr.update(choices=[], value=None),
                "",
                gr.update(choices=[], value=None),
                "",
                gr.update(interactive=False),
                gr.update(value=None),
                None,
            )
        detail = (
            await service.entity_review_detail(rid, tid)
            if kind == "entity"
            else service.claim_review_detail(rid, tid)
        )
        choices, score_rows = [], []
        if kind == "entity":
            mention = detail["mention"] or {}
            description_text = (
                f"{mention.get('name', '')} · {mention.get('entity_type', '')}\n"
                f"{mention.get('context', '')}\n候选差距：{detail['margin']}\n"
            )
            description_text += "\n".join(
                f"{c['subject']} → {c['relation']} → {c['object']}"
                for c in detail["related_candidates"]
            )
            for c in detail["candidates"]:
                entity = c["entity"]
                if entity is None:
                    continue
                choices.append(
                    (
                        f"{entity['name']} · {entity['entity_type']} · {c['final_score']:.3f}",
                        c["entity_id"],
                    )
                )
                score_rows.append(
                    [
                        entity["name"],
                        entity["entity_type"],
                        ", ".join(entity["aliases"]),
                        c["retrieval_score"],
                        c["name_score"],
                        c["semantic_name_score"],
                        c["context_score"],
                        c["neighborhood_score"],
                        c["final_score"],
                    ]
                )
            peer_label, peer_ids = "", []
            effect = (
                f"关联候选事实 {len(detail['related_candidates'])} 条。"
                "排除提及将阻断关联事实但保留原候选；暂缓仍阻断处理。链接或新建更新提及归属。"
            )
        else:
            c = detail["claim"]
            description_text = (
                f"{controller.fact_label(c)}\n置信度：{c['confidence']} · 状态：{c['status']}"
            )
            peer_label = "\n".join(controller.fact_label(c) for c in detail["conflict_peers"])
            peer_ids = list(
                dict.fromkeys(eid for c in detail["conflict_peers"] for eid in c["evidence_ids"])
            )
            effect = "本次决定只处理当前事实，不自动批准或拒绝冲突对方。"
        ids = detail["evidence_ids"]
        return (
            description_text,
            "\n".join([*detail["risk_flags"], *detail["task"]["reasons"]]),
            score_rows,
            gr.update(choices=choices, value=None),
            gr.update(choices=ids, value=ids[0] if ids else None),
            peer_label,
            gr.update(choices=peer_ids, value=peer_ids[0] if peer_ids else None),
            effect,
            gr.update(interactive=detail["task"]["status"] == "pending"),
            gr.update(
                value=None,
                choices=[
                    ("链接候选", "link"),
                    ("创建新实体", "create"),
                    ("排除错误提及", "reject"),
                    ("暂缓判断", "defer"),
                ]
                if kind == "entity"
                else [("拒绝事实", "reject")]
                if detail.get("allowed_actions") == ["reject"]
                else [("批准事实", "approve"), ("拒绝事实", "reject"), ("暂缓判断", "defer")],
            ),
            detail["task"]["version"],
        )

    async def evidence(rid: str | None, eid: str | None) -> tuple[str, Any]:
        text, image = await controller.evidence(rid, eid) if rid and eid else ("", None)
        return text, gr.update(value=image, visible=image is not None)

    async def submit_task(
        rid: str, tid: str, decision: str, cid: str | None, person: str, note: str, version: int
    ) -> str:
        try:
            await controller.submit(rid, tid, kind, decision, cid, person, note, version)
            return "已记录当前审核，尚未自动提交图谱。"
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    async def continue_run(rid: str) -> str:
        await service.resume(rid)
        return "已接续处理，请查看任务队列与提交摘要。"

    async def commit_run(rid: str, person: str, confirmed: bool) -> str:
        if not confirmed:
            raise gr.Error("请先确认隔离图谱提交摘要")
        await service.confirm_review_commit(rid, person)
        return "已写入隔离图谱。"

    async def show_neighbor(cid: str | None) -> Any:
        if not cid:
            raise gr.Error("请选择候选实体")
        return (await service.graph_store.get_neighborhood(cid)).model_dump(mode="json")

    def select_row(ids: list[str], event: Any) -> Any:
        return gr.update(value=ids[event.index[0]])

    select_row.__annotations__["event"] = gr.SelectData

    queue_inputs = [run, status, risk]
    queue_outputs = [table, task_ids, task, progress, resume, preview, commit, confirm]
    task_outputs = [
        description,
        flags,
        scores,
        candidate,
        evidence_choice,
        peers,
        peer_evidence,
        impact,
        submit,
        action,
        task_version,
    ]
    for trigger in (run.change, status.change, risk.change):
        trigger(load_queue, queue_inputs, queue_outputs).then(load_task, [run, task], task_outputs)
    refresh.click(lambda: gr.update(choices=controller.runs()), outputs=[run]).then(
        load_queue,
        queue_inputs,
        queue_outputs,
    ).then(load_task, [run, task], task_outputs)
    table.select(select_row, [task_ids], [task]).then(load_task, [run, task], task_outputs)
    task.input(load_task, [run, task], task_outputs)
    evidence_choice.change(evidence, [run, evidence_choice], [evidence_text, evidence_image])
    peer_evidence.change(evidence, [run, peer_evidence], [peer_text, peer_image])
    neighbor_button.click(show_neighbor, [candidate], [neighbor])
    submit.click(
        submit_task, [run, task, action, candidate, reviewer, comment, task_version], [outcome]
    ).then(
        load_queue,
        queue_inputs,
        queue_outputs,
    ).then(load_task, [run, task], task_outputs)
    for button, fn, inputs in (
        (resume, continue_run, [run]),
        (commit, commit_run, [run, reviewer, confirm]),
    ):
        button.click(fn, inputs, [outcome]).then(load_queue, queue_inputs, queue_outputs).then(
            load_task,
            [run, task],
            task_outputs,
        )
