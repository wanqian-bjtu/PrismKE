"""Review decisions, immutable events and recoverable checkpoint projections."""

from typing import TYPE_CHECKING, Any, Literal, cast
from uuid import uuid4

from src.core.errors import LegacyCheckpointError
from src.core.execution_control import current_execution
from src.core.ids import stable_id
from src.domain import CandidateClaim, ClaimStatus, EntityMention, WorkflowState, utc_now
from src.domain.reviews import ReviewEvent
from src.persistence.reviews import ReviewRepository

if TYPE_CHECKING:
    from src.workflow.service import PrismKEService


class ReviewService:
    def __init__(self, service: "PrismKEService") -> None:
        self.service = service
        self.repository = ReviewRepository(service.settings.runtime_dir / "reviews.sqlite")

    @staticmethod
    def compatible(state: WorkflowState) -> None:
        from src.workflow.service import PIPELINE_VERSION

        if state.pipeline_version != PIPELINE_VERSION:
            raise LegacyCheckpointError("旧运行只读，请使用对应发布版本接续；不迁移旧审核")

    @staticmethod
    def update_status(state: WorkflowState) -> None:
        state.status = (
            "awaiting_review"
            if (
                state.validation.blocking_count
                or any(t.status == "pending" for t in state.entity_review_tasks)
                or any(t.status == "pending" for t in state.review_tasks)
            )
            else "running"
        )
        state.graph_commit = None
        state.submission_confirmed = False

    def filtered_candidates(self, state: WorkflowState) -> list[CandidateClaim]:
        originals = [
            CandidateClaim.model_validate(c) for c in self.repository.original(state.run_id)
        ]
        rejected = {
            t.mention_id
            for t in state.entity_review_tasks
            if t.status == "resolved" and t.decision == "reject"
        }
        return [
            c
            for c in originals
            if c.subject.id not in rejected
            and not (isinstance(c.object, EntityMention) and c.object.id in rejected)
        ]

    async def project(self, event: ReviewEvent, payload: dict[str, Any]) -> WorkflowState:
        state = WorkflowState.model_validate(payload)
        try:
            workflow = self.service.review_tail_workflow(state)
            if event.correction_id and state.status == "completed":
                assert state.graph_commit is not None
                control = current_execution.get()
                if control:
                    control.commit_started(state.graph_commit.revision.id)
                await self.service.graph_store.commit(state.graph_commit)
                if control:
                    control.commit_finished()
                recorded = await workflow.record_completed_review(state)
            elif event.kind == "entity":
                recorded = await workflow.record_entity_review(state)
            else:
                recorded = await workflow.record_review(state)
            if not recorded:
                raise ValueError("review checkpoint unavailable")
            self.service.audit.record(
                "review_event",
                event.task_id,
                {"event_id": event.id, **event.model_dump(mode="json")},
            )
            self.repository.delivered(event.id)
            if state.pipeline_version == "0.9.0":
                try:
                    await self.service.cases.project_review_event(event, state)
                except Exception as exc:
                    # Case projection is replayable and must never invalidate an accepted review.
                    self.service.audit.record(
                        "case_projection_pending",
                        event.id,
                        {"error_type": type(exc).__name__},
                    )
            return state
        except Exception:
            summary = self.service.runs.load(state.run_id)
            summary.review_sync_pending = True
            self.service.runs.save(summary)
            raise

    async def recover(self, run_id: str) -> None:
        for event, payload in self.repository.pending(run_id):
            await self.project(event, payload)

    async def decide(
        self,
        run_id: str,
        task_id: str,
        kind: Literal["entity", "claim"],
        action: str,
        selected_entity_id: str | None,
        reviewer: str | None,
        reason: str | None,
        expected_version: int | None = None,
        request_id: str | None = None,
    ) -> WorkflowState:
        self.compatible(self.service.show_run(run_id))
        await self.recover(run_id)
        state = self.service.show_run(run_id)
        person, comment = (reviewer or "").strip(), (reason or "").strip()
        if not person:
            raise ValueError("reviewer is required")
        if action in {"reject", "defer"} and not comment:
            raise ValueError("排除或暂缓必须填写原因")
        request_id = request_id or uuid4().hex
        previous = self.repository.request(run_id, request_id)
        if previous:
            if (
                previous.task_id != task_id
                or previous.kind != kind
                or previous.action != action
                or previous.reviewer != person
                or previous.reason != comment
                or (
                    action == "link"
                    and previous.after.get("selected_entity_id") != selected_entity_id
                )
            ):
                raise ValueError("request id reused with a different decision")
            return state
        tasks = state.entity_review_tasks if kind == "entity" else state.review_tasks
        task = next((t for t in tasks if t.id == task_id), None)
        if task is None:
            raise KeyError("review task not found")
        task = cast(Any, task)
        if task.status != "pending":
            raise ValueError("review task has already been resolved")
        if expected_version is not None and task.version != expected_version:
            raise ValueError("stale review version")
        allowed = (
            {"link", "create", "reject", "defer"}
            if kind == "entity"
            else {"approve", "reject", "defer"}
        )
        if action not in allowed:
            raise ValueError("unsupported review action")
        before = task.model_dump(mode="json")
        old_version = task.version
        event_id = stable_id("review-event", run_id, request_id)
        if kind == "entity":
            if task.mention_id is None:
                raise ValueError("merge/split review is not a mention decision")
            if action == "link":
                if selected_entity_id not in {c.entity_id for c in task.candidates}:
                    raise ValueError("selected entity is not one of the review candidates")
                target = selected_entity_id
            elif action == "create":
                target = task.proposed_entity_id
            else:
                target = None
            if action in {"link", "create"}:
                if target is None:
                    raise ValueError("proposed entity unavailable")
                entity = next((e for e in state.entities if e.id == target), None)
                if entity is None:
                    entity = await self.service.graph_store.get_entity(target)
                    if entity is None or not entity.active:
                        raise ValueError("selected canonical entity is unavailable")
                    state.entities.append(entity)
                if not entity.active:
                    raise ValueError("selected canonical entity is unavailable")
                state.mention_to_entity[task.mention_id] = target
                task.selected_entity_id = target
                for resolution in state.entity_resolution_decisions:
                    if resolution.mention_id == task.mention_id:
                        resolution.selected_entity_id = target
                        resolution.requires_review = False
                        resolution.reasons.append(f"human_review:{action}")
            task.decision = action
        else:
            from src.domain import ReviewDecision

            task.decision = ReviewDecision(action)
            claim = next(c for c in state.claims if c.id == task.claim_id)
            claim.status = {
                "approve": ClaimStatus.APPROVED,
                "reject": ClaimStatus.REJECTED,
                "defer": ClaimStatus.REVIEW_REQUIRED,
            }[action]
        task.status = "pending" if action == "defer" else "resolved"
        task.version += 1
        task.last_event_id = event_id
        task.resolved_at = None if action == "defer" else utc_now()
        task.reviewer, task.review_comment = person, comment
        if kind == "entity" and action == "reject":
            state.candidates = self.filtered_candidates(state)
        self.update_status(state)
        event = ReviewEvent(
            id=event_id,
            request_id=request_id,
            run_id=run_id,
            task_id=task_id,
            kind=kind,
            action=action,
            version=task.version,
            reviewer=person,
            reason=comment,
            before=before,
            after=task.model_dump(mode="json"),
            supersedes_event_id=before.get("last_event_id"),
        )
        state.review_sync_pending = False
        self.repository.append(event, state.model_dump(mode="json"), old_version)
        return await self.project(event, state.model_dump(mode="json"))
