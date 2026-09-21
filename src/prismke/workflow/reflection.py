"""Case-assisted, budget-bounded candidate Reflection."""

from __future__ import annotations

from time import perf_counter

from prismke.core.ids import canonical_hash, stable_id
from prismke.domain import (
    ReflectionAttempt,
    ReflectionRequest,
    SchemaIndex,
    ValidationIssue,
    WorkflowState,
)
from prismke.governance.validation import ValidationService
from prismke.persistence.base import EvidenceStore
from prismke.providers.base import ReflectionProvider
from prismke.workflow.cases import CaseRetriever, _language

REFLECTION_POLICY_VERSION = "bounded-reflection-v1"
REFLECTION_PROMPT_VERSION = "candidate-reflection-v1"
ELIGIBLE_STAGES = {"structure", "schema", "reference", "evidence"}


class BoundedReflectionService:
    def __init__(
        self,
        provider: ReflectionProvider,
        retriever: CaseRetriever | None,
        evidence_store: EvidenceStore,
    ) -> None:
        self.provider = provider
        self.retriever = retriever
        self.evidence_store = evidence_store

    @staticmethod
    def _issues(state: WorkflowState, candidate_id: str) -> list[ValidationIssue]:
        return [
            issue
            for issue in state.validation.issues
            if issue.target_id == candidate_id
            and issue.status == "open"
            and issue.severity == "blocking"
            and issue.stage in ELIGIBLE_STAGES
        ]

    async def run(self, state: WorkflowState) -> WorkflowState:
        assert state.document is not None and state.output_schema is not None
        validation = ValidationService()
        initial = await validation.candidates(
            state.candidates,
            SchemaIndex(state.output_schema),
            state.document,
            self.evidence_store,
        )
        state.validation = validation.merge(state.validation, initial)
        if not state.reflection_enabled or state.reflection_max_attempts <= 0:
            return state
        started = perf_counter()
        schema_fingerprint = canonical_hash(state.output_schema.model_dump(mode="json"))
        allowed_evidence = [item.id for item in state.document.evidence]
        case_types = {
            "good": {"good"},
            "good_bad": {"good", "bad"},
        }.get(state.case_mode, set())
        for position, original in enumerate(list(state.candidates)):
            issues = self._issues(state, original.id)
            if not issues:
                continue
            current = original
            for attempt_number in range(1, state.reflection_max_attempts + 1):
                elapsed = perf_counter() - started
                remaining_tokens = state.reflection_token_budget - state.reflection_token_usage
                if elapsed >= state.reflection_time_budget_seconds or remaining_tokens <= 0:
                    state.reflection_attempts.append(
                        ReflectionAttempt(
                            id=stable_id(
                                "reflection-attempt", state.run_id, original.id, attempt_number
                            ),
                            run_id=state.run_id,
                            candidate_id=original.id,
                            attempt=attempt_number,
                            issue_ids=[item.id for item in issues],
                            retrieved_case_ids=[],
                            input_candidate=current.model_dump(mode="json"),
                            model_fingerprint=self.provider.fingerprint(),
                            prompt_version=REFLECTION_PROMPT_VERSION,
                            status="budget_exhausted",
                        )
                    )
                    state.warnings.append(f"reflection_budget_exhausted:{original.id}")
                    break
                retrieved = []
                if case_types and self.retriever is not None:
                    object_context = getattr(current.object, "context", "")
                    query = " | ".join(
                        [
                            current.subject.name,
                            current.relation,
                            getattr(current.object, "name", str(current.object)),
                            current.subject.context,
                            object_context,
                            " ".join(item.message for item in issues),
                        ]
                    )
                    retrieved = await self.retriever.retrieve(
                        query,
                        task_type="claim",
                        schema_fingerprint=schema_fingerprint,
                        language=_language(query),
                        case_types=case_types,
                        top_k=5,
                        use_location=f"candidate:{original.id}:attempt:{attempt_number}",
                        allowed_case_ids=set(state.case_snapshot_ids),
                    )
                    known = {(item.case_id, item.use_location) for item in state.retrieved_cases}
                    state.retrieved_cases.extend(
                        item for item in retrieved if (item.case_id, item.use_location) not in known
                    )
                request = ReflectionRequest(
                    run_id=state.run_id,
                    candidate=current,
                    issues=issues,
                    retrieved_cases=retrieved,
                    output_schema=state.output_schema,
                    allowed_evidence_ids=allowed_evidence,
                    attempt=attempt_number,
                    remaining_tokens=remaining_tokens,
                )
                try:
                    result = await self.provider.reflect(request)
                except Exception as exc:
                    state.reflection_attempts.append(
                        ReflectionAttempt(
                            id=stable_id(
                                "reflection-attempt", state.run_id, original.id, attempt_number
                            ),
                            run_id=state.run_id,
                            candidate_id=original.id,
                            attempt=attempt_number,
                            issue_ids=[item.id for item in issues],
                            retrieved_case_ids=[item.case_id for item in retrieved],
                            input_candidate=current.model_dump(mode="json"),
                            model_fingerprint=self.provider.fingerprint(),
                            prompt_version=REFLECTION_PROMPT_VERSION,
                            status="failed",
                            error_code=type(exc).__name__,
                        )
                    )
                    state.warnings.append(f"reflection_failed:{original.id}:{type(exc).__name__}")
                    break
                state.reflection_elapsed_ms = round((perf_counter() - started) * 1000, 3)
                if result.total_tokens is None:
                    state.reflection_attempts.append(
                        ReflectionAttempt(
                            id=stable_id(
                                "reflection-attempt", state.run_id, original.id, attempt_number
                            ),
                            run_id=state.run_id,
                            candidate_id=original.id,
                            attempt=attempt_number,
                            issue_ids=[item.id for item in issues],
                            retrieved_case_ids=[item.case_id for item in retrieved],
                            input_candidate=current.model_dump(mode="json"),
                            output_candidate=(
                                result.candidate.model_dump(mode="json")
                                if result.candidate
                                else None
                            ),
                            model_fingerprint=self.provider.fingerprint(),
                            prompt_version=REFLECTION_PROMPT_VERSION,
                            latency_ms=result.latency_ms,
                            status="unknown_usage",
                            error_code="missing_token_usage",
                            warnings=result.warnings,
                        )
                    )
                    state.warnings.append(f"reflection_unknown_usage:{original.id}")
                    return state
                state.reflection_token_usage += result.total_tokens
                if result.candidate is None:
                    status = "failed"
                    replacement = None
                    new_issues: list[ValidationIssue] = []
                else:
                    replacement = result.candidate.model_copy(
                        update={
                            "id": stable_id(
                                "reflected-candidate",
                                original.id,
                                attempt_number,
                                canonical_hash(result.candidate.model_dump(mode="json")),
                            )
                        }
                    )
                    new_issues = await validation.candidates(
                        [replacement],
                        SchemaIndex(state.output_schema),
                        state.document,
                        self.evidence_store,
                    )
                    status = (
                        "rejected_by_validation"
                        if any(item.severity == "blocking" for item in new_issues)
                        else "succeeded"
                    )
                state.reflection_attempts.append(
                    ReflectionAttempt(
                        id=stable_id(
                            "reflection-attempt", state.run_id, original.id, attempt_number
                        ),
                        run_id=state.run_id,
                        candidate_id=original.id,
                        attempt=attempt_number,
                        issue_ids=[item.id for item in issues],
                        retrieved_case_ids=[item.case_id for item in retrieved],
                        input_candidate=current.model_dump(mode="json"),
                        output_candidate=(
                            replacement.model_dump(mode="json") if replacement else None
                        ),
                        model_fingerprint=self.provider.fingerprint(),
                        prompt_version=REFLECTION_PROMPT_VERSION,
                        token_usage=result.total_tokens,
                        latency_ms=result.latency_ms,
                        status=status,
                        warnings=result.warnings,
                    )
                )
                if status == "succeeded" and replacement is not None:
                    state.candidates[position] = replacement
                    for issue in issues:
                        issue.status = "repaired"
                        state.repaired_issue_ids.append(issue.id)
                    state.validation = validation.merge(state.validation, new_issues)
                    break
                if replacement is None or len(new_issues) > len(issues):
                    break
                current = replacement
                issues = new_issues
        state.validation = validation.merge(state.validation, [])
        return state
