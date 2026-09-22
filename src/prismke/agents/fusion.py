"""Evidence-aware fusion and review agent; graph writes remain outside this agent."""

from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING

from prismke.agents.budget import can_request, record_call, record_response_failure
from prismke.agents.trace import handoff, safe_reason_code, trace_step
from prismke.core.errors import ProviderResponseError
from prismke.core.ids import stable_id
from prismke.domain import (
    ClaimStatus,
    ConflictSet,
    FusionAdviceRequest,
    ReviewTask,
    SchemaIndex,
    WorkflowState,
)
from prismke.governance import detect_conflicts, route_by_risk
from prismke.persistence.base import GraphStore
from prismke.persistence.reviews import ReviewRepository
from prismke.providers.base import SemanticAdvisor

if TYPE_CHECKING:
    from prismke.workflow.reflection import BoundedReflectionService


class FusionReviewAgent:
    def __init__(
        self,
        graph_store: GraphStore,
        advisor: SemanticAdvisor,
        reflection_service: BoundedReflectionService | None = None,
    ) -> None:
        self.graph_store = graph_store
        self.advisor = advisor
        self.reflection_service = reflection_service
        self.review_repository: ReviewRepository | None = None

    async def triage_candidates(self, state: WorkflowState) -> WorkflowState:
        started = perf_counter()
        if self.reflection_service is not None:
            state = await self.reflection_service.run(state)
        trace_step(
            state,
            "fusion_review",
            "triage_candidates",
            "bounded_reflection" if state.reflection_enabled else "validation_only",
            tools=("reflection",) if self.reflection_service is not None else (),
            input_ids=tuple(item.id for item in state.original_candidates),
            output_ids=tuple(item.id for item in state.candidates),
            latency_ms=(perf_counter() - started) * 1000,
        )
        return state

    async def detect_conflicts(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None
        state.conflicts = detect_conflicts(
            state.claims, await self.graph_store.list_claims(), SchemaIndex(state.output_schema)
        )
        trace_step(
            state,
            "fusion_review",
            "detect_conflicts",
            "rule_conflicts_recorded",
            tools=("conflict_detector",),
            input_ids=tuple(item.id for item in state.claims),
            output_ids=tuple(item.id for item in state.conflicts),
        )
        if state.semantic_advisor_name != "disabled":
            await self._assess_related_groups(state)
        return state

    async def _assess_related_groups(self, state: WorkflowState) -> None:
        candidates = {item.id: item for item in state.candidates}
        claims_by_candidate = {
            candidate_id: claim
            for claim in state.claims
            for candidate_id in claim.source_candidate_ids
        }
        known_conflicts = {frozenset(item.claim_ids) for item in state.conflicts}
        for alignment in state.alignment_records:
            if alignment.decision != "related" or len(alignment.candidate_ids) != 2:
                continue
            left_id, right_id = alignment.candidate_ids
            left = claims_by_candidate.get(left_id)
            right = claims_by_candidate.get(right_id)
            if (
                left is None
                or right is None
                or left.id == right.id
                or left.subject_id != right.subject_id
                or left.relation_id != right.relation_id
                or frozenset((left.id, right.id)) in known_conflicts
            ):
                continue
            if not can_request(state):
                state.warnings.append("agent_budget_exhausted:fusion")
                state.agent_review_claim_ids.extend((left.id, right.id))
                continue
            started = perf_counter()
            try:
                advice, record = await self.advisor.advise_fusion(
                    FusionAdviceRequest(left=candidates[left_id], right=candidates[right_id])
                )
                record_call(state, record)
            except ProviderResponseError as exc:
                record_response_failure(state, exc)
                state.agent_review_claim_ids.extend((left.id, right.id))
                trace_step(
                    state,
                    "fusion_review",
                    f"assess:{alignment.id}",
                    "human_review_required",
                    tools=("semantic_advisor",),
                    input_ids=(left.id, right.id),
                    reasons=("semantic_advice_invalid",),
                    status="failed",
                )
                continue
            if advice.decision == "conflict":
                ids = sorted((left.id, right.id))
                conflict = ConflictSet(
                    id=stable_id("conflict", "semantic-review", *ids),
                    claim_ids=ids,
                    reason="semantic_conflict_requires_review",
                )
                state.conflicts.append(conflict)
                known_conflicts.add(frozenset(ids))
            elif advice.decision == "uncertain":
                state.agent_review_claim_ids.extend((left.id, right.id))
            trace_step(
                state,
                "fusion_review",
                f"assess:{alignment.id}",
                advice.decision,
                tools=("semantic_advisor",),
                input_ids=(left.id, right.id),
                output_ids=(state.conflicts[-1].id,) if advice.decision == "conflict" else (),
                reasons=("related_alignment", safe_reason_code(advice.reason_code)),
                model_fingerprint=self.advisor.fingerprint(),
                token_usage=record.total_tokens if record else 0,
                latency_ms=(perf_counter() - started) * 1000,
            )
        state.agent_review_claim_ids = sorted(set(state.agent_review_claim_ids))

    async def route_by_risk(self, state: WorkflowState) -> WorkflowState:
        state.claims, new_reviews = route_by_risk(state.run_id, state.claims, state.conflicts)
        if state.pending_correction_id and self.review_repository is not None:
            proposal = self.review_repository.correction(state.pending_correction_id)
            if proposal.kind == "entity":
                affected = set(proposal.preview["candidate_ids"])
                for claim in state.claims:
                    if (
                        set(claim.source_candidate_ids) & affected
                        and claim.status != ClaimStatus.REJECTED
                    ):
                        claim.status = ClaimStatus.REVIEW_REQUIRED
                        if claim.id not in {t.claim_id for t in new_reviews}:
                            new_reviews.append(
                                ReviewTask(
                                    id=stable_id("review", state.run_id, claim.id),
                                    run_id=state.run_id,
                                    claim_id=claim.id,
                                    reasons=["identity_correction_requires_review"],
                                )
                            )
        for claim in state.claims:
            if claim.id not in state.agent_review_claim_ids or claim.status == ClaimStatus.REJECTED:
                continue
            claim.status = ClaimStatus.REVIEW_REQUIRED
            if claim.id not in {task.claim_id for task in new_reviews}:
                new_reviews.append(
                    ReviewTask(
                        id=stable_id("review", state.run_id, claim.id, "semantic_uncertain"),
                        run_id=state.run_id,
                        claim_id=claim.id,
                        reasons=["semantic_assessment_uncertain"],
                    )
                )
        resolved = {item.claim_id: item for item in state.review_tasks if item.status == "resolved"}
        state.review_tasks = [resolved.get(item.claim_id, item) for item in new_reviews]
        if self.review_repository is not None:
            for task in state.review_tasks:
                task.version = self.review_repository.version(state.run_id, task.id)
        for task in state.review_tasks:
            if task.status != "resolved":
                continue
            claim = next(item for item in state.claims if item.id == task.claim_id)
            claim.status = (
                ClaimStatus.APPROVED
                if task.decision and task.decision.value == "approve"
                else ClaimStatus.REJECTED
            )
        state.status = (
            "awaiting_review"
            if any(item.status == "pending" for item in state.review_tasks)
            or state.validation.blocking_count
            else "running"
        )
        trace_step(
            state,
            "fusion_review",
            "route_by_risk",
            "review" if state.status == "awaiting_review" else "continue",
            tools=("risk_router",),
            input_ids=tuple(item.id for item in state.claims),
            output_ids=tuple(item.id for item in state.review_tasks),
        )
        handoff(
            state,
            "fusion_review",
            input_ids=tuple(item.id for item in state.claims),
            output_ids=tuple(item.id for item in state.conflicts),
            evidence_ids=tuple(sorted({eid for item in state.claims for eid in item.evidence_ids})),
            review_task_ids=tuple(item.id for item in state.review_tasks),
            next_action="review" if state.status == "awaiting_review" else "continue",
        )
        return state
