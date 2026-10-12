"""One durable worker per workspace, with conservative restart reconciliation."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from filelock import FileLock, Timeout

from src.core.errors import LegacyCheckpointError
from src.core.execution_control import ExecutionPaused, current_execution
from src.core.ids import canonical_hash, file_sha256
from src.domain.execution import (
    BranchProgress,
    ExecutionStatus,
    ExecutionTask,
    RequestReconciliation,
)
from src.persistence.execution import ExecutionConflict, ExecutionRepository
from src.providers.base import EmbeddingProvider, LLMProvider, OCRProvider, VLMProvider

if TYPE_CHECKING:
    from src.domain import WorkflowState
    from src.workflow.service import PrismKEService

ACTIVE = {"queued", "running", "cancelling"}


class RunControl:
    def __init__(self, manager: ExecutionManager, run_id: str) -> None:
        self.manager = manager
        self.run_id = run_id
        self.critical = False
        self.closed = False

    def check(self) -> None:
        if self.critical:
            return
        if self.closed or self.manager.stopping:
            raise ExecutionPaused("SERVER_SHUTDOWN")
        task = self.manager.repository.get(self.run_id)
        if task and task.cancel_requested:
            raise ExecutionPaused("USER_CANCEL")
        if self.manager.repository.unknown(self.run_id, include_sent=False):
            raise ExecutionPaused("UNKNOWN_PROVIDER_USAGE")

    def node(self, name: str) -> None:
        self.check()
        self.manager.repository.change(self.run_id, lambda t: setattr(t, "node", name))

    def commit_started(self, revision_id: str) -> None:
        self.check()
        self.manager.repository.change(
            self.run_id, lambda t: setattr(t, "commit_revision_id", revision_id)
        )
        self.critical = True

    def commit_finished(self) -> None:
        self.manager.repository.change(self.run_id, lambda t: setattr(t, "commit_applied", True))

    def begin_request(self, key: str, metadata: dict[str, Any]) -> dict[str, Any] | None:
        self.check()
        task = self.manager.repository.get(self.run_id)
        return self.manager.repository.begin_request(
            self.run_id,
            key,
            {
                **metadata,
                "attempt": task.attempt if task else 0,
                "node": task.node if task else None,
            },
        )

    def finish_request(
        self, key: str, status: str, payload: dict[str, Any] | None, usage_known: bool
    ) -> None:
        self.manager.repository.finish_request(self.run_id, key, status, payload, usage_known)

    def result(self, key: str) -> dict[str, Any] | None:
        return self.manager.repository.result(self.run_id, key)

    def put_result(self, key: str, value: dict[str, Any]) -> None:
        self.manager.repository.put_result(self.run_id, key, value)


class ExecutionManager:
    def __init__(self, service: PrismKEService) -> None:
        self.service = service
        self.repository = ExecutionRepository(service.settings.runtime_dir / "executions.sqlite")
        self.owner = FileLock(str(service.settings.runtime_dir / "execution-owner.lock"), timeout=0)
        self.worker: asyncio.Task[None] | None = None
        self.stopping = False
        self.failures: dict[str, Exception] = {}
        self.lifecycle = asyncio.Lock()
        self.persistent = False
        self.waiters = 0

    def register(self, state: WorkflowState) -> ExecutionTask:
        task = self.repository.get(state.run_id)
        if task:
            return task
        return self.repository.register(
            ExecutionTask(
                run_id=state.run_id,
                input_hash=file_sha256(Path(state.input_path)),
                schema_hash=file_sha256(Path(state.schema_path)),
                node=state.current_node,
                status=self.business_status(state) if state.document else "queued",
            )
        )

    def ensure_accepting(self) -> None:
        if self.stopping and self.persistent:
            raise ExecutionConflict("WORKER_SHUTTING_DOWN")

    def set_status(self, run_id: str, status: ExecutionStatus) -> None:
        self.repository.change(run_id, lambda t: setattr(t, "status", status))

    @staticmethod
    def business_status(
        state: WorkflowState,
    ) -> Literal["awaiting_review", "awaiting_commit", "completed", "failed", "interrupted"]:
        if state.status == "completed":
            return "completed"
        if state.status == "failed":
            return "failed"
        if state.status == "awaiting_review":
            return "awaiting_review"
        if state.current_node == "prepare_graph_commit":
            return "awaiting_commit"
        return "interrupted"

    def compatible(self, state: WorkflowState) -> None:
        from src.workflow.service import PIPELINE_VERSION

        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError(
                "LEGACY_EXECUTION_READ_ONLY: use the matching released workflow"
            )

    def blockers(self, state: WorkflowState, *, include_sent: bool = True) -> str | None:
        if self.service.missing_run_credentials(state):
            return "CREDENTIAL_REQUIRED"
        if self.service.reviews.repository.pending(state.run_id):
            return "REVIEW_SYNC_PENDING"
        if self.repository.unknown(state.run_id, include_sent=include_sent):
            return "UNKNOWN_PROVIDER_REQUEST"
        if (
            state.validation.blocking_count
            or any(t.status == "pending" for t in state.entity_review_tasks)
            or any(t.status == "pending" for t in state.review_tasks)
        ):
            return "AWAITING_REVIEW"
        return None

    def enqueue(
        self,
        run_id: str,
        operation: Literal["execute", "resume", "confirm"],
        *,
        expected_version: int | None = None,
        reviewer: str | None = None,
    ) -> ExecutionTask:
        self.ensure_accepting()
        state = self.service.show_run(run_id)
        self.compatible(state)
        task = self.register(state)
        if expected_version is not None and task.version != expected_version:
            raise ExecutionConflict("STALE_EXECUTION_VERSION")
        if task.status in ACTIVE:
            if task.operation != operation:
                raise ExecutionConflict("EXECUTION_BUSY")
            return task
        blocked = self.blockers(state)
        if blocked:
            raise ExecutionConflict(blocked)
        progress = self.service.review_progress(run_id)
        if operation == "confirm":
            if not reviewer or not reviewer.strip() or not progress["can_commit"]:
                raise ExecutionConflict("SUBMISSION_CONFIRMATION_REQUIRED")
        elif operation == "resume" and not progress["can_resume"]:
            raise ExecutionConflict("RUN_NOT_RESUMABLE")
        elif operation == "execute":
            raise ExecutionConflict("USE_RESUME_FOR_EXISTING_EXECUTION")

        def update(t: ExecutionTask) -> None:
            if t.status in ACTIVE:
                raise ExecutionConflict("EXECUTION_BUSY")
            t.status = "queued"
            t.operation = operation
            t.reviewer = reviewer
            t.cancel_requested = False
            t.error_code = None
            t.reason = None
            t.commit_revision_id = None
            t.commit_applied = False

        return self.repository.change(run_id, update, expected_version)

    def cancel(
        self, run_id: str, operator: str, reason: str, request_id: str, expected_version: int
    ) -> ExecutionTask:
        self.compatible(self.service.show_run(run_id))
        if not all(s.strip() for s in [operator, reason, request_id]):
            raise ExecutionConflict("CANCEL_OPERATOR_REASON_REQUIRED")

        def update(t: ExecutionTask) -> None:
            if t.status not in ACTIVE:
                raise ExecutionConflict("EXECUTION_NOT_ACTIVE")
            t.cancel_requested = True
            t.operator = operator.strip()
            t.reason = reason.strip()
            t.status = "cancelled" if t.status == "queued" else "cancelling"

        return self.repository.change(
            run_id,
            update,
            expected_version,
            (
                request_id,
                canonical_hash([operator.strip(), reason.strip(), expected_version]),
            ),
        )

    def view(self, run_id: str) -> dict[str, Any]:
        state = self.service.show_run(run_id)
        task = self.repository.get(run_id)
        from src.workflow.service import PIPELINE_VERSION

        legacy = state.pipeline_version != PIPELINE_VERSION
        status = task.status if task else self.business_status(state)
        active = task is not None and task.status in ACTIVE
        blocked = self.blockers(state, include_sent=not active)
        hard_blocks = {
            "PROJECTION_SYNC_PENDING",
            "EXECUTION_INPUT_CHANGED",
            "PROVIDER_CONFIGURATION_CHANGED",
            "CREDENTIAL_REQUIRED",
            "EXECUTION_EVIDENCE_INVALID",
            "CHECKPOINT_MISSING",
        }
        if task and task.error_code in hard_blocks:
            blocked = blocked or task.error_code
        # A final manual decision changes business state before the next attempt is enqueued.
        if (
            task
            and not active
            and task.status in {"awaiting_review", "awaiting_commit", "completed"}
        ):
            status = self.business_status(state)
        return {
            "run_id": run_id,
            "status": status,
            "business_status": state.status,
            "version": task.version if task else 0,
            "attempt": task.attempt if task else 0,
            "node": task.node
            if task and task.status in ACTIVE | {"cancelled", "interrupted", "failed"}
            else state.current_node,
            "updated_at": task.updated_at.isoformat() if task else None,
            "reason": task.reason if task else None,
            "error_code": "LEGACY_EXECUTION_READ_ONLY"
            if legacy
            else blocked or (task.error_code if task else None),
            "unknown_requests": self.repository.unknown(run_id, include_sent=not active),
            "active": active,
            "can_cancel": bool(active and not legacy),
            "blocked": bool(legacy or blocked),
        }

    def branch_progress(self, run_id: str) -> list[BranchProgress]:
        state = self.service.show_run(run_id)
        task = self.repository.get(run_id)
        updated = task.updated_at if task else state.revision.created_at if state.revision else None
        if updated is None:
            from datetime import UTC, datetime

            updated = datetime.now(UTC)
        node = task.node if task else state.current_node
        active = bool(task and task.status in ACTIVE)
        failed = bool(task and task.status == "failed")
        calls = state.provider_calls
        document = state.document
        text_total = 1 if document and document.text_blocks else 0
        text_done = min(
            text_total,
            sum(c.provider == "llm" and c.status == "succeeded" for c in calls),
        )
        visual_total = len(document.media_assets) if document else 0
        visual_done = min(
            visual_total,
            sum(c.provider == "vlm" and c.status == "succeeded" for c in calls),
        )
        ocr_total = (
            sum(asset.requires_ocr for asset in document.media_assets) if document else 0
        )
        node_order = [
            "ingest",
            "parse_document",
            "materialize_visual_assets",
            "run_ocr",
            "persist_evidence",
            "load_schema",
            "extract_text_claims",
            "extract_visual_claims",
            "align_modalities",
            "resolve_entities",
            "normalize_claims",
            "detect_conflicts",
            "route_by_risk",
            "prepare_graph_commit",
            "commit_graph",
        ]
        position = node_order.index(node) if node in node_order else -1

        def status(completed: int, total: int, start: str, done: str) -> str:
            if total == 0:
                return "disabled"
            if completed >= total or (done in node_order and position > node_order.index(done)):
                return "completed"
            if failed and node == start:
                return "failed"
            if active and node == start:
                return "running"
            return "pending"

        ocr_done = ocr_total if position > node_order.index("run_ocr") else 0
        commit_done = int(state.revision is not None or bool(task and task.commit_applied))
        commit_total = int(state.task_mode.permits_graph_commit and state.batch_id is None)
        return [
            BranchProgress(
                branch="text",
                status=status(text_done, text_total, "extract_text_claims", "extract_text_claims"),
                completed=text_done,
                total=text_total,
                updated_at=updated,
            ),
            BranchProgress(
                branch="visual",
                status=status(
                    visual_done,
                    visual_total,
                    "extract_visual_claims",
                    "extract_visual_claims",
                ),
                completed=visual_done,
                total=visual_total,
                current_asset=None,
                updated_at=updated,
            ),
            BranchProgress(
                branch="ocr",
                status=status(ocr_done, ocr_total, "run_ocr", "run_ocr"),
                completed=ocr_done,
                total=ocr_total,
                updated_at=updated,
            ),
            BranchProgress(
                branch="commit",
                status=status(commit_done, commit_total, "commit_graph", "commit_graph"),
                completed=commit_done,
                total=commit_total,
                updated_at=updated,
            ),
        ]

    def reconcile_request(
        self, run_id: str, decision: RequestReconciliation
    ) -> dict[str, Any]:
        self.compatible(self.service.show_run(run_id))
        event = self.repository.reconcile_request(run_id, decision)
        return {
            "event": event.model_dump(mode="json"),
            "execution": self.view(run_id),
            "requests": self.repository.requests(run_id),
        }

    def health(self) -> dict[str, Any]:
        tasks = self.repository.list_tasks()
        return {
            "worker": "stopping"
            if self.stopping
            else "running"
            if self.worker and not self.worker.done()
            else "stopped",
            "queued": sum(t.status == "queued" for t in tasks),
            "recovery_blocked": sum(
                t.status == "interrupted" and bool(t.error_code) for t in tasks
            ),
        }

    async def start(self, *, persistent: bool = True) -> None:
        async with self.lifecycle:
            await self._start()
            self.persistent = self.persistent or persistent

    async def _start(self) -> None:
        if self.worker and not self.worker.done():
            return
        if self.owner.is_locked:
            self.owner.release()
        try:
            self.owner.acquire()
        except Timeout as exc:
            raise ExecutionConflict(
                "WORKSPACE_WORKER_BUSY: use existing Web/API or a separate runtime"
            ) from exc
        self.stopping = False
        try:
            await self.reconcile()
            self.worker = asyncio.create_task(self._work(), name="prismke-execution-worker")
        except BaseException:
            self.owner.release()
            raise

    async def reconcile(self) -> None:
        for task in self.repository.list_tasks():
            if task.status not in ACTIVE | {"interrupted"}:
                continue
            try:
                state = self.service.show_run(task.run_id)
                self.compatible(state)
                with self.service.runs.mutation_lock(task.run_id):
                    await self.service.reviews.recover(task.run_id)
                state = self.service.show_run(task.run_id)
                if task.commit_revision_id:
                    revisions = await self.service.graph_store.list_revisions(limit=1000)
                    if task.commit_revision_id in {r.id for r in revisions}:
                        if (
                            state.graph_commit
                            and state.graph_commit.revision.id == task.commit_revision_id
                        ):
                            state.status = "completed"
                            state.revision = state.graph_commit.revision
                            self.service.runs.save(state)
                        self.repository.change(
                            task.run_id, lambda t: setattr(t, "status", "completed")
                        )
                        continue
                    raise ExecutionConflict("SUBMISSION_CONFIRMATION_REQUIRED")
                if task.cancel_requested:
                    self.repository.change(task.run_id, lambda t: setattr(t, "status", "cancelled"))
                    continue
                if (
                    state.status == "awaiting_review"
                    and not self.service.reviews.repository.pending(task.run_id)
                ):
                    self.set_status(task.run_id, "awaiting_review")
                    continue
                if task.operation == "confirm":
                    self.set_status(task.run_id, "awaiting_commit")
                    continue
                blocked = self.blockers(state)
                if blocked:
                    raise ExecutionConflict(blocked)
                await self.preflight(state, task)
                if state.current_node == "prepare_graph_commit" and (
                    state.review_workspace or state.pending_correction_id
                ):
                    self.set_status(task.run_id, "awaiting_commit")
                    continue
                if (
                    state.status in {"completed", "awaiting_review", "failed"}
                    and task.status == "queued"
                ):
                    self.set_status(task.run_id, self.business_status(state))
                    continue
                workflow = self.service.review_workflow(state)
                snapshot = await workflow.execution_snapshot(task.run_id)
                if snapshot["exists"] and not snapshot["next"]:
                    self.set_status(task.run_id, self.business_status(state))
                    continue
                if not snapshot["exists"] and task.attempt and state.document:
                    raise ExecutionConflict("CHECKPOINT_MISSING")

                def requeue(t: ExecutionTask, checkpoint: dict[str, Any] = snapshot) -> None:
                    t.status = "queued"
                    t.operation = "resume" if checkpoint["exists"] else "execute"
                    t.error_code = None
                    t.reason = "SAFE_RESTART_RECOVERY" if t.attempt else None

                self.repository.change(task.run_id, requeue)
            except Exception as exc:
                code = str(exc) if isinstance(exc, ExecutionConflict) else type(exc).__name__

                def block(t: ExecutionTask, error: str = code) -> None:
                    t.status = "interrupted"
                    t.error_code = error

                self.repository.change(task.run_id, block)

    async def settle_committed(self, run_id: str) -> bool:
        task = self.repository.get(run_id)
        if not task or not task.commit_revision_id:
            return False
        revisions = await self.service.graph_store.list_revisions(limit=1000)
        if not any(r.id == task.commit_revision_id for r in revisions):
            return False
        state = self.service.show_run(run_id)
        state.status = "completed"
        state.current_node = "commit_graph"
        self.service.runs.save(state)

        def settle(t: ExecutionTask) -> None:
            t.status = "completed"
            t.commit_applied = True
            t.error_code = None
            if t.cancel_requested:
                t.reason = "CANCEL_TOO_LATE_COMMIT_COMPLETED"

        self.repository.change(run_id, settle)
        return True

    async def preflight(self, state: WorkflowState, task: ExecutionTask) -> None:
        self.compatible(state)
        if (
            file_sha256(Path(state.input_path)) != task.input_hash
            or file_sha256(Path(state.schema_path)) != task.schema_hash
        ):
            raise ExecutionConflict("EXECUTION_INPUT_CHANGED")
        self.service._validate_entity_policy(state)
        tail_nodes = {
            "resolve_entities",
            "normalize_claims",
            "detect_conflicts",
            "route_by_risk",
            "prepare_graph_commit",
            "commit_graph",
        }
        if not (
            state.review_workspace or state.correction_tail_only or state.current_node in tail_nodes
        ):
            pairs: list[tuple[LLMProvider | OCRProvider | VLMProvider | EmbeddingProvider, str]] = [
                (self.service.provider_for_state(state), state.provider_fingerprint),
                (
                    self.service.ocr_provider(state.ocr_provider_name),
                    state.ocr_provider_fingerprint,
                ),
                (
                    self.service.vlm_provider_for_state(state),
                    state.vlm_provider_fingerprint,
                ),
                (self.service.embedding_provider(), state.embedding_provider_fingerprint),
            ]
            if any(p.fingerprint() != expected for p, expected in pairs):
                raise ExecutionConflict("PROVIDER_CONFIGURATION_CHANGED")
        if state.document and state.current_node not in {
            "ingest",
            "parse_document",
            "materialize_visual_assets",
            "run_ocr",
        }:
            for evidence in state.document.evidence:
                if not await self.service.evidence_store.verify(evidence.id):
                    raise ExecutionConflict("EXECUTION_EVIDENCE_INVALID")

    async def _work(self) -> None:
        while not self.stopping:
            task = next((t for t in self.repository.list_tasks() if t.status == "queued"), None)
            if task is None:
                await asyncio.sleep(0.05)
                continue
            control = RunControl(self, task.run_id)
            token = current_execution.set(control)
            try:
                with self.service.runs.mutation_lock(task.run_id):
                    await self.preflight(self.service.show_run(task.run_id), task)

                    def claim(t: ExecutionTask) -> None:
                        if t.status != "queued":
                            raise ExecutionPaused("USER_CANCEL")
                        t.status = "running"
                        t.attempt += 1

                    self.repository.change(task.run_id, claim)
                    if task.operation == "execute":
                        state = await self.service._execute_run(task.run_id)
                    elif task.operation == "resume":
                        initial = self.service.show_run(task.run_id)
                        if (
                            task.attempt == 0
                            and not initial.document
                            and initial.current_node == "ingest"
                        ):
                            state = await self.service._execute_run(task.run_id)
                        else:
                            state = await self.service._resume(task.run_id)
                    else:
                        state = await self.service._confirm_review_commit(
                            task.run_id, task.reviewer or ""
                        )

                    def finish(t: ExecutionTask, result: WorkflowState = state) -> None:
                        t.status = self.business_status(result)
                        t.node = result.current_node
                        if t.cancel_requested and result.status == "completed":
                            t.reason = "CANCEL_TOO_LATE_COMMIT_COMPLETED"

                    self.repository.change(task.run_id, finish)
            except ExecutionPaused as exc:
                reason = str(exc)

                def pause(t: ExecutionTask, code: str = reason) -> None:
                    t.status = "cancelled" if code == "USER_CANCEL" else "interrupted"
                    t.error_code = code

                self.repository.change(task.run_id, pause)
            except asyncio.CancelledError:
                if not await self.settle_committed(task.run_id):
                    self.set_status(task.run_id, "interrupted")
                raise
            except Exception as exc:
                try:
                    if await self.settle_committed(task.run_id):
                        continue
                except Exception:
                    self.set_status(task.run_id, "interrupted")
                    self.repository.change(
                        task.run_id, lambda t: setattr(t, "error_code", "PROJECTION_SYNC_PENDING")
                    )
                    continue
                self.failures[task.run_id] = exc
                error = type(exc).__name__

                def fail(t: ExecutionTask, code: str = error) -> None:
                    t.status = "failed"
                    t.error_code = code

                self.repository.change(task.run_id, fail)
            finally:
                control.closed = True
                current_execution.reset(token)
                self.service.release_run_credentials(task.run_id)

    async def wait(self, run_id: str) -> WorkflowState:
        while True:
            task = self.repository.get(run_id)
            if task and task.status not in ACTIVE:
                if task.status == "failed":
                    raise self.failures.get(
                        run_id, ExecutionConflict(task.error_code or "EXECUTION_FAILED")
                    )
                return self.service.show_run(run_id)
            if not self.worker or self.worker.done():
                raise ExecutionConflict("WORKER_NOT_RUNNING")
            await asyncio.sleep(0.02)

    async def run_wait(
        self,
        run_id: str,
        operation: Literal["execute", "resume", "confirm"],
        reviewer: str | None = None,
    ) -> WorkflowState:
        self.waiters += 1
        try:
            await self.start(persistent=False)
            existing = self.repository.get(run_id)
            if not existing or existing.status not in ACTIVE:
                with self.service.runs.mutation_lock(run_id):
                    await self.service.reviews.recover(run_id)
            self.enqueue(run_id, operation, reviewer=reviewer)
            return await self.wait(run_id)
        finally:
            self.waiters -= 1
            if not self.persistent and not self.waiters and self.owner.is_locked:
                await self.stop()

    async def stop(self) -> None:
        self.stopping = True
        try:
            if self.worker and not self.worker.done():
                try:
                    await asyncio.wait_for(asyncio.shield(self.worker), timeout=30)
                except TimeoutError:
                    self.worker.cancel()
                    with suppress(asyncio.CancelledError):
                        await self.worker
        finally:
            self.owner.release()
            self.persistent = False
