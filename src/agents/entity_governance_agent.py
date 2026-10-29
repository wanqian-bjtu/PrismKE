"""EntityGovernanceAgent with guarded gray-zone advice."""

from __future__ import annotations

from time import perf_counter

from src.agents.budget import can_request, record_call, record_response_failure
from src.agents.trace import handoff, safe_reason_code, trace_step
from src.core.errors import ProviderResponseError
from src.core.ids import canonical_hash
from src.domain import EntityAdviceRequest, EntityMention, SchemaIndex, WorkflowState
from src.governance import SemanticEntityResolver, collect_mentions, normalize_claims
from src.governance.validation import ValidationService
from src.persistence.base import EvidenceStore, GraphStore
from src.providers.base import EmbeddingProvider, SemanticAdvisor


class EntityGovernanceAgent:
    def __init__(
        self,
        graph_store: GraphStore,
        evidence_store: EvidenceStore,
        embedding_provider: EmbeddingProvider,
        advisor: SemanticAdvisor,
        *,
        top_k: int,
        auto_link_threshold: float,
        review_threshold: float,
        min_margin: float,
    ) -> None:
        self.graph_store = graph_store
        self.evidence_store = evidence_store
        self.embedding_provider = embedding_provider
        self.advisor = advisor
        self.top_k = top_k
        self.auto_link_threshold = auto_link_threshold
        self.review_threshold = review_threshold
        self.min_margin = min_margin

    async def resolve(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None and state.document is not None
        started = perf_counter()
        # Reference issues describe the result of the previous resolution pass.
        # A correction-triggered rerun must reevaluate them instead of treating
        # them as candidate blockers before any mentions can be resolved.
        for issue in state.validation.issues:
            if issue.code == "MISSING_ENTITY_REFERENCE" and issue.status in {
                "open",
                "deferred",
            }:
                issue.status = "repaired"
        state.validation = ValidationService.merge(state.validation, [])
        issues = await ValidationService().candidates(
            state.candidates, SchemaIndex(state.output_schema), state.document, self.evidence_store
        )
        state.validation = ValidationService.merge(state.validation, issues)
        excluded = ValidationService.blocked_candidate_ids(state.candidates, state.validation)
        mentions_by_id = {item.id: item for item in state.extracted_entities}
        for mention in collect_mentions(
            [candidate for candidate in state.candidates if candidate.id not in excluded]
        ):
            mentions_by_id[mention.id] = mention
        for attribute in state.candidate_attributes:
            mentions_by_id[attribute.subject.id] = attribute.subject
        for event in state.candidate_events:
            for argument in event.arguments:
                if isinstance(argument.value, EntityMention):
                    mentions_by_id[argument.value.id] = argument.value
        mentions = list(mentions_by_id.values())
        resolver = SemanticEntityResolver(
            SchemaIndex(state.output_schema),
            self.graph_store,
            self.embedding_provider,
            run_id=state.run_id,
            top_k=self.top_k,
            auto_link_threshold=self.auto_link_threshold,
            review_threshold=self.review_threshold,
            min_margin=self.min_margin,
        )
        resolution = await resolver.resolve(mentions)
        state.entities = resolution.entities
        state.mention_to_entity = resolution.mention_to_entity
        for mention_id, entity_id in state.validation_entity_overrides.items():
            if entity_id is None:
                state.mention_to_entity.pop(mention_id, None)
                continue
            entity = next((item for item in state.entities if item.id == entity_id), None)
            if entity is None:
                entity = await self.graph_store.get_entity(entity_id)
                if entity is None or not entity.active:
                    raise ValueError("validation entity override is unavailable")
                state.entities.append(entity)
            state.mention_to_entity[mention_id] = entity_id
        state.entity_resolution_decisions = resolution.decisions or []
        resolved = {
            item.mention_id: item
            for item in state.entity_review_tasks
            if item.status == "resolved" and item.mention_id is not None
        }
        state.entity_review_tasks = [
            resolved.get(item.mention_id, item) if item.mention_id is not None else item
            for item in (resolution.review_tasks or [])
        ]
        state.warnings.extend(
            f"review_required:{mention_id}:{','.join(reasons)}"
            for mention_id, reasons in resolution.review_reasons.items()
        )
        await self._advise_gray_zone(state, mentions)
        state.status = (
            "awaiting_review"
            if any(item.status == "pending" for item in state.entity_review_tasks)
            or state.validation.blocking_count
            else "running"
        )
        trace_step(
            state,
            "governance",
            "resolve_entities",
            "review" if state.status == "awaiting_review" else "continue",
            tools=("schema_validation", "entity_resolver"),
            input_ids=tuple(item.id for item in mentions),
            output_ids=tuple(item.id for item in state.entities),
            reasons=("blocking_validation",) if state.validation.blocking_count else (),
            latency_ms=(perf_counter() - started) * 1000,
        )
        handoff(
            state,
            "governance",
            input_ids=tuple(item.id for item in mentions),
            output_ids=tuple(item.id for item in state.entities),
            evidence_ids=tuple(sorted({eid for item in mentions for eid in item.evidence_ids})),
            issue_ids=tuple(item.id for item in state.validation.issues),
            review_task_ids=tuple(item.id for item in state.entity_review_tasks),
            next_action="review" if state.status == "awaiting_review" else "continue",
        )
        return state

    async def _advise_gray_zone(self, state: WorkflowState, mentions: list[EntityMention]) -> None:
        if state.semantic_advisor_name == "disabled":
            return
        mention_by_id = {item.id: item for item in mentions}
        entities = {item.id: item for item in state.entities}
        assert state.output_schema is not None
        schema = SchemaIndex(state.output_schema)
        decisions = {item.mention_id: item for item in state.entity_resolution_decisions}
        for task in state.entity_review_tasks:
            mention_id = task.mention_id
            if (
                task.status != "pending"
                or mention_id is None
                or mention_id not in mention_by_id
                or not task.candidates
            ):
                continue
            mention = mention_by_id[mention_id]
            entity_type = schema.entity_type(mention.entity_type) or mention.entity_type
            same_type_candidates = [
                item
                for item in task.candidates
                if item.entity_id in entities
                and entities[item.entity_id].entity_type == entity_type
            ]
            if not same_type_candidates:
                continue
            if not can_request(state):
                state.warnings.append("agent_budget_exhausted:governance")
                break
            request = EntityAdviceRequest(
                mention=mention,
                candidates=same_type_candidates,
                candidate_entities=[entities[item.entity_id] for item in same_type_candidates],
            )
            started = perf_counter()
            try:
                advice, record = await self.advisor.advise_entity(request)
                record_call(state, record)
            except ProviderResponseError as exc:
                record_response_failure(state, exc)
                task.reasons.append("semantic_advice_invalid")
                trace_step(
                    state,
                    "governance",
                    f"advise:{mention_id}",
                    "review",
                    tools=("semantic_advisor",),
                    input_ids=(mention_id,),
                    reasons=("semantic_advice_invalid",),
                    status="failed",
                )
                continue
            allowed = {item.entity_id for item in same_type_candidates}
            selected = advice.selected_entity_id if advice.selected_entity_id in allowed else None
            if advice.action == "link" and selected is None:
                task.reasons.append("semantic_advice_invalid_candidate")
                continue
            # Advice never changes the resolver's link/NIL decision or auto-link thresholds.
            task.advised_action = advice.action
            task.advised_entity_id = selected
            task.reasons.append(f"semantic_advice_{advice.action}")
            task.reasons.append(f"semantic_reason:{safe_reason_code(advice.reason_code)}")
            decision = decisions.get(mention_id)
            if decision is not None:
                decision.advised_action = advice.action
                decision.advised_entity_id = selected
                decision.reasons.append(f"semantic_advice_{advice.action}")
            trace_step(
                state,
                "governance",
                f"advise:{mention_id}",
                "human_review_required",
                tools=("semantic_advisor",),
                input_ids=(mention_id, *tuple(item.entity_id for item in task.candidates)),
                output_ids=(selected,) if selected else (),
                reasons=("gray_zone", safe_reason_code(advice.reason_code)),
                model_fingerprint=self.advisor.fingerprint(),
                token_usage=record.total_tokens if record else 0,
                latency_ms=(perf_counter() - started) * 1000,
            )

    async def normalize(self, state: WorkflowState) -> WorkflowState:
        assert state.output_schema is not None and state.document is not None
        entities = {item.id: item for item in state.entities}
        blocked = ValidationService.blocked_candidate_ids(state.candidates, state.validation)
        eligible = [c for c in state.candidates if c.id not in blocked]
        issues = await ValidationService().candidates(
            eligible,
            SchemaIndex(state.output_schema),
            state.document,
            self.evidence_store,
            entities,
            state.mention_to_entity,
        )
        state.validation = ValidationService.merge(
            state.validation,
            issues,
            canonical_hash([c.model_dump(mode="json") for c in state.candidates]),
        )
        blocked.update(i.target_id for i in issues)
        state.claims = normalize_claims(
            [c for c in eligible if c.id not in blocked],
            SchemaIndex(state.output_schema),
            entities,
            state.mention_to_entity,
        )
        state.validation.passed_count = len(state.claims)
        trace_step(
            state,
            "governance",
            "normalize_claims",
            "claims_normalized",
            tools=("schema_validation", "claim_normalizer"),
            input_ids=tuple(item.id for item in eligible),
            output_ids=tuple(item.id for item in state.claims),
        )
        handoff(
            state,
            "governance",
            input_ids=tuple(item.id for item in eligible),
            output_ids=tuple(item.id for item in state.claims),
            evidence_ids=tuple(sorted({eid for item in state.claims for eid in item.evidence_ids})),
            issue_ids=tuple(item.id for item in state.validation.issues),
        )
        return state
