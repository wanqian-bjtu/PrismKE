"""Review correction previews and tail-only, auditable compensation workflows."""

from typing import TYPE_CHECKING, Any, cast

from prismke.core.ids import canonical_hash, stable_id
from prismke.domain import (
    CandidateClaim,
    Claim,
    ClaimStatus,
    EntityMention,
    GraphChange,
    GraphCommit,
    ReviewDecision,
    WorkflowState,
    utc_now,
)
from prismke.domain.reviews import CorrectionGuard, ReviewCorrection, ReviewEvent
from prismke.persistence.reviews import ReviewRepository

if TYPE_CHECKING:
    from prismke.workflow.service import PrismKEService


def compensation_commit(
    state: WorkflowState,
    transaction: GraphCommit,
    proposal: ReviewCorrection,
    current_claims: dict[str, Claim],
    current_entities: dict[str, Any],
) -> GraphCommit:
    """Replace only affected resources, never apply ordinary append/merge semantics."""
    candidate_ids = set(proposal.preview["candidate_ids"])
    now = utc_now()
    replacements = {
        c.id: c.model_copy(deep=True)
        for c in transaction.claims
        if set(c.source_candidate_ids) & candidate_ids
    }
    for claim in replacements.values():
        claim.tx_from, claim.tx_to = now, None
    for claim_id in proposal.affected_claim_ids:
        if claim_id not in replacements:
            old = current_claims[claim_id].model_copy(deep=True)
            old.tx_to = now
            replacements[claim_id] = old
    transaction.claims = list(replacements.values())
    needed = {
        e
        for c in replacements.values()
        if c.tx_to is None
        for e in (c.subject_id, c.object_entity_id)
        if e
    }
    # Existing canonical entities are not rewritten by an identity correction.
    transaction.entities = [
        e for e in state.entities if e.id in needed and e.id not in current_entities
    ]
    transaction.conflicts = []
    changes = [
        GraphChange(
            resource_type="claim",
            resource_id=c.id,
            action="update" if c.id in current_claims else "create",
            before=current_claims[c.id].model_dump(mode="json") if c.id in current_claims else None,
            after=c.model_dump(mode="json"),
        )
        for c in transaction.claims
    ]
    changes.extend(
        GraphChange(
            resource_type="entity",
            resource_id=e.id,
            action="create",
            after=e.model_dump(mode="json"),
        )
        for e in transaction.entities
    )
    expected = dict(proposal.preview["expected_resources"])
    for change in changes:
        key = f"{change.resource_type}:{change.resource_id}"
        if key not in expected:
            if change.before is not None:
                raise ValueError("correction would modify an unpreviewed existing resource")
            expected[key] = None
    guard = CorrectionGuard(
        source_event_id=proposal.source_event_id,
        reviewer=proposal.reviewer,
        reason=proposal.reason,
        expected_resources=expected,
    )
    transaction.correction_guard = guard
    revision = transaction.revision
    revision.id = stable_id("revision", "correction", proposal.id)
    revision.parent_id = proposal.parent_revision_id
    revision.changes = changes
    revision.claim_ids = sorted(replacements)
    revision.entity_ids = sorted(needed)
    revision.conflict_ids = []
    revision.correction_guard = guard
    revision.created_at = now
    return transaction


class CorrectionService:
    def __init__(self, service: "PrismKEService") -> None:
        self.service = service
        self.reviews = service.reviews
        self.repository: ReviewRepository = self.reviews.repository

    async def propose(
        self,
        run_id: str,
        source_event_id: str,
        action: str,
        selected_entity_id: str | None,
        expected_version: int,
        reviewer: str,
        reason: str,
        request_id: str,
    ) -> ReviewCorrection:
        if not reviewer.strip() or not reason.strip() or not request_id.strip():
            raise ValueError("reviewer, reason and request_id are required")
        self.reviews.compatible(self.service.show_run(run_id))
        with self.service.runs.mutation_lock(run_id):
            await self.reviews.recover(run_id)
            correction_id = stable_id("correction", run_id, request_id)
            try:
                prior = self.repository.correction(correction_id)
            except KeyError:
                prior = None
            if prior:
                if (
                    prior.source_event_id,
                    prior.action,
                    prior.selected_entity_id,
                    prior.expected_version,
                    prior.reviewer,
                    prior.reason,
                ) != (
                    source_event_id,
                    action,
                    selected_entity_id,
                    expected_version,
                    reviewer.strip(),
                    reason.strip(),
                ):
                    raise ValueError("correction request id reused with different proposal")
                return prior
            state = self.service.show_run(run_id)
            if state.pending_correction_id:
                raise ValueError("finish the current correction before proposing another")
            source = next(
                (e for e in self.repository.events(run_id) if e.id == source_event_id), None
            )
            if source is None or source.action in {"defer", "commit_correction"}:
                raise ValueError("select a final review decision")
            tasks = state.entity_review_tasks if source.kind == "entity" else state.review_tasks
            task = next((t for t in tasks if t.id == source.task_id), None)
            final_events = [
                e
                for e in self.repository.events(run_id)
                if e.task_id == source.task_id and e.action != "commit_correction"
            ]
            if (
                task is None
                or task.status != "resolved"
                or not final_events
                or final_events[-1].id != source.id
            ):
                raise ValueError("source event is no longer the current decision")
            if task.version != expected_version:
                raise ValueError("stale review version")
            originals = [CandidateClaim.model_validate(c) for c in self.repository.original(run_id)]
            allowed = (
                {"link", "create", "reject"} if source.kind == "entity" else {"approve", "reject"}
            )
            if action not in allowed:
                raise ValueError("invalid replacement decision")
            if source.kind == "entity":
                entity_task = cast(Any, task)
                candidate_ids = {
                    c.id
                    for c in originals
                    if c.subject.id == entity_task.mention_id
                    or isinstance(c.object, EntityMention)
                    and c.object.id == entity_task.mention_id
                }
                if action == "link" and selected_entity_id not in {
                    c.entity_id for c in entity_task.candidates
                }:
                    raise ValueError("replacement is not a candidate")
            else:
                claim = next(c for c in state.claims if c.id == cast(Any, task).claim_id)
                candidate_ids = set(claim.source_candidate_ids)
            persisted = await self.service.graph_store.list_claims()
            affected = [c for c in persisted if set(c.source_candidate_ids) & candidate_ids]
            blocked: list[str] = []
            own_ids = {c.id for c in originals}
            for claim in affected:
                if not claim.source_run_ids:
                    blocked.append(f"MISSING_CLAIM_RUN_PROVENANCE: {claim.id}")
                elif set(claim.source_run_ids) != {run_id}:
                    blocked.append(f"SHARED_RUN_SUPPORT: {claim.id}")
                if set(claim.source_candidate_ids) - own_ids:
                    blocked.append(f"SHARED_CLAIM: {claim.id}")
                for evidence_id in claim.evidence_ids:
                    ref = await self.service.evidence_store.get(evidence_id)
                    if state.document is None or ref.document_id != state.document.id:
                        blocked.append(f"SHARED_DOCUMENT_SUPPORT: {claim.id}")
            parent = await self.service.graph_store.latest_revision()
            committed = state.status == "completed"
            if committed and any(
                c.id not in {a.id for a in affected}
                for c in state.claims
                if set(c.source_candidate_ids) & candidate_ids
                and c.status in {ClaimStatus.APPROVED, ClaimStatus.AUTO_APPROVED}
            ):
                blocked.append("CURRENT_GRAPH_DOES_NOT_MATCH_RUN")
            expected = {
                f"claim:{c.id}": canonical_hash(c.model_dump(mode="json")) for c in affected
            }
            for entity in state.entities:
                current = await self.service.graph_store.get_entity(entity.id)
                if current:
                    expected[f"entity:{current.id}"] = canonical_hash(
                        current.model_dump(mode="json")
                    )
            proposal = ReviewCorrection(
                id=correction_id,
                run_id=run_id,
                source_event_id=source.id,
                task_id=source.task_id,
                kind=source.kind,
                action=cast(Any, action),
                selected_entity_id=selected_entity_id,
                expected_version=expected_version,
                reviewer=reviewer.strip(),
                reason=reason.strip(),
                parent_revision_id=parent.id if parent else None,
                affected_claim_ids=[c.id for c in affected],
                blocked_reasons=sorted(set(blocked)),
                preview={
                    "candidate_ids": sorted(candidate_ids),
                    "committed": committed,
                    "expected_resources": expected,
                    "before_decision": source.after,
                    "expected_last_event_id": task.last_event_id,
                    "claims": [c.model_dump(mode="json") for c in affected],
                    "impact": "重新审核受影响事实，确认后补偿写图"
                    if committed
                    else "保留历史，从原始候选重新计算；不会调用模型",
                },
            )
            self.repository.propose(proposal)
            return proposal

    async def apply(self, correction_id: str, confirm: bool) -> WorkflowState:
        if not confirm:
            raise ValueError("explicit confirmation required")
        proposal = self.repository.correction(correction_id)
        with self.service.runs.mutation_lock(proposal.run_id):
            await self.reviews.recover(proposal.run_id)
            state = self.service.show_run(proposal.run_id)
            self.reviews.compatible(state)
            request_id = f"apply:{proposal.id}"
            if self.repository.request(state.run_id, request_id):
                return state
            if proposal.blocked_reasons:
                raise ValueError("; ".join(proposal.blocked_reasons))
            parent = await self.service.graph_store.latest_revision()
            if (parent.id if parent else None) != proposal.parent_revision_id:
                raise ValueError("graph changed; create a new preview")
            tasks = state.entity_review_tasks if proposal.kind == "entity" else state.review_tasks
            task = cast(Any, next(t for t in tasks if t.id == proposal.task_id))
            if (
                task.version != proposal.expected_version
                or task.last_event_id != proposal.preview["expected_last_event_id"]
            ):
                raise ValueError("stale review version; create a new preview")
            before = task.model_dump(mode="json")
            state.correction_tail_only = True
            if proposal.kind == "entity":
                target = (
                    proposal.selected_entity_id
                    if proposal.action == "link"
                    else task.proposed_entity_id
                )
                if proposal.action != "reject":
                    if target is None:
                        raise ValueError("replacement entity unavailable")
                    entity = next((e for e in state.entities if e.id == target), None)
                    if entity is None:
                        entity = await self.service.graph_store.get_entity(target)
                    if entity is None or not entity.active:
                        raise ValueError("replacement entity unavailable")
                    if entity.id not in {e.id for e in state.entities}:
                        state.entities.append(entity)
                    state.mention_to_entity[task.mention_id] = entity.id
                    task.selected_entity_id = entity.id
                task.decision = proposal.action
                state.candidates = self.reviews.filtered_candidates(state)
                affected = set(proposal.preview["candidate_ids"])
                affected_claim_ids = {
                    c.id for c in state.claims if set(c.source_candidate_ids) & affected
                }
                state.superseded_review_tasks.extend(
                    t.model_copy(deep=True)
                    for t in state.review_tasks
                    if t.claim_id in affected_claim_ids
                )
                state.review_tasks = [
                    t for t in state.review_tasks if t.claim_id not in affected_claim_ids
                ]
                state.current_node = "resolve_entities"
                state.claims, state.conflicts = [], []
            else:
                task.decision = ReviewDecision(proposal.action)
                claim = next(c for c in state.claims if c.id == task.claim_id)
                claim.status = (
                    ClaimStatus.APPROVED if proposal.action == "approve" else ClaimStatus.REJECTED
                )
                state.current_node = "route_by_risk"
            task.version += 1
            task.reviewer, task.review_comment = proposal.reviewer, proposal.reason
            task.resolved_at = utc_now()
            event_id = stable_id("review-event", state.run_id, request_id)
            task.last_event_id = event_id
            self.reviews.update_status(state)
            if proposal.preview["committed"]:
                state.pending_correction_id = proposal.id
            event = ReviewEvent(
                id=event_id,
                request_id=request_id,
                run_id=state.run_id,
                task_id=task.id,
                kind=proposal.kind,
                action=proposal.action,
                version=task.version,
                reviewer=proposal.reviewer,
                reason=proposal.reason,
                before=before,
                after=task.model_dump(mode="json"),
                supersedes_event_id=proposal.source_event_id,
                correction_id=proposal.id,
            )
            self.repository.append(event, state.model_dump(mode="json"), proposal.expected_version)
            return await self.reviews.project(event, state.model_dump(mode="json"))

    async def confirm(self, state: WorkflowState, reviewer: str) -> WorkflowState:
        assert state.pending_correction_id and state.graph_commit
        proposal = self.repository.correction(state.pending_correction_id)
        tasks = state.entity_review_tasks if proposal.kind == "entity" else state.review_tasks
        task = cast(Any, next(t for t in tasks if t.id == proposal.task_id))
        before = task.model_dump(mode="json")
        request_id = f"commit:{proposal.id}"
        if self.repository.request(state.run_id, request_id):
            return self.service.show_run(state.run_id)
        old_version = task.version
        task.version += 1
        event_id = stable_id("review-event", state.run_id, request_id)
        task.last_event_id = event_id
        event = ReviewEvent(
            id=event_id,
            request_id=request_id,
            run_id=state.run_id,
            task_id=task.id,
            kind=proposal.kind,
            action="commit_correction",
            version=task.version,
            reviewer=reviewer.strip(),
            reason=proposal.reason,
            before=before,
            after=task.model_dump(mode="json"),
            supersedes_event_id=before["last_event_id"],
            correction_id=proposal.id,
        )
        state.graph_commit.revision.review_events = [
            e.model_dump(mode="json") for e in [*self.repository.events(state.run_id), event]
        ]
        state.revision = state.graph_commit.revision
        state.status, state.current_node = "completed", "commit_graph"
        state.pending_correction_id = None
        state.submission_confirmed = True
        self.repository.append(event, state.model_dump(mode="json"), old_version)
        return await self.reviews.project(event, state.model_dump(mode="json"))
