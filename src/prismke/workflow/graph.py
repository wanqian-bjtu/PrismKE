"""Persistent LangGraph execution and exact-node recovery."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from prismke.core.execution_control import ExecutionPaused, current_execution
from prismke.domain import WorkflowState
from prismke.governance.validation import ValidationService
from prismke.parsing import ParserRegistry
from prismke.persistence.base import EvidenceStore, GraphStore
from prismke.persistence.checkpoints import open_checkpointer
from prismke.persistence.reviews import ReviewRepository
from prismke.persistence.runs import RunRepository
from prismke.providers.base import (
    EmbeddingProvider,
    LLMProvider,
    OCRProvider,
    SemanticAdvisor,
    VLMProvider,
)
from prismke.workflow.nodes import WorkflowNodes
from prismke.workflow.reflection import BoundedReflectionService


class GraphState(TypedDict, total=False):
    payload: dict[str, Any]
    text_branch: dict[str, Any]
    visual_branch: dict[str, Any]


Node = Callable[[GraphState], Awaitable[GraphState]]


class PrismKEWorkflow:
    def __init__(
        self,
        provider: LLMProvider,
        ocr_provider: OCRProvider,
        vlm_provider: VLMProvider,
        graph_store: GraphStore,
        evidence_store: EvidenceStore,
        checkpoint_path: Path,
        runs: RunRepository,
        parsers: ParserRegistry | None = None,
        *,
        embedding_provider: EmbeddingProvider | None = None,
        entity_top_k: int = 10,
        entity_auto_link_threshold: float = 0.88,
        entity_review_threshold: float = 0.65,
        entity_min_margin: float = 0.08,
        review_only: bool = False,
        reflection_service: BoundedReflectionService | None = None,
        semantic_advisor: SemanticAdvisor | None = None,
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self.runs = runs
        self.reviews = ReviewRepository(runs.directory.parent / "reviews.sqlite")
        self.review_only = review_only
        # Direct workflow construction must use the same evidence verifier as the service.
        from prismke.persistence import JSONGraphStore, Neo4jGraphStore

        if isinstance(graph_store, (JSONGraphStore, Neo4jGraphStore)):
            graph_store.evidence_store = evidence_store
        self.nodes = WorkflowNodes(
            provider,
            ocr_provider,
            vlm_provider,
            graph_store,
            evidence_store,
            parsers or ParserRegistry(),
            embedding_provider=embedding_provider,
            entity_top_k=entity_top_k,
            entity_auto_link_threshold=entity_auto_link_threshold,
            entity_review_threshold=entity_review_threshold,
            entity_min_margin=entity_min_margin,
            reflection_service=reflection_service,
            semantic_advisor=semantic_advisor,
        )
        self.nodes.review_repository = self.reviews

    @staticmethod
    def _state(graph_state: GraphState) -> WorkflowState:
        return WorkflowState.model_validate(graph_state["payload"])

    @staticmethod
    def _record_provider_failure(state: WorkflowState, exc: Exception) -> None:
        records = getattr(exc, "call_records", None)
        if records is None:
            record = getattr(exc, "call_record", None)
            records = [record] if record is not None else []
        known = {item.id for item in state.provider_calls}
        state.provider_calls.extend(item for item in records if item.id not in known)

    def _node(
        self,
        name: str,
        handler: Callable[[WorkflowState], Awaitable[WorkflowState]],
    ) -> Node:
        async def wrapped(graph_state: GraphState) -> GraphState:
            state = self._state(graph_state)
            try:
                control = current_execution.get()
                if control:
                    control.node(name)
                state = await handler(state)
            except ExecutionPaused:
                raise
            except Exception as exc:
                self._record_provider_failure(state, exc)
                state.status = "failed"
                state.failed_node = name
                state.current_node = name
                state.retry_count += 1
                state.errors.append(f"{name}:{type(exc).__name__}:{exc}")
                self.runs.save(state)
                raise
            state.current_node = name
            state.failed_node = None
            self.runs.save(state)
            return {"payload": state.model_dump(mode="json")}

        return wrapped

    def _branch_node(
        self,
        name: str,
        output_key: str,
        handler: Callable[[WorkflowState], Awaitable[WorkflowState]],
    ) -> Node:
        async def wrapped(graph_state: GraphState) -> GraphState:
            state = self._state(graph_state).model_copy(deep=True)
            try:
                control = current_execution.get()
                if control:
                    control.node(name)
                state = await handler(state)
            except ExecutionPaused:
                raise
            except Exception as exc:
                self._record_provider_failure(state, exc)
                state.status = "failed"
                state.failed_node = name
                state.current_node = name
                state.retry_count += 1
                state.errors.append(f"{name}:{type(exc).__name__}:{exc}")
                self.runs.save(state)
                raise
            return cast(GraphState, {output_key: state.model_dump(mode="json")})

        return wrapped

    async def _join_modalities(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        text_state = WorkflowState.model_validate(graph_state["text_branch"])
        visual_state = WorkflowState.model_validate(graph_state["visual_branch"])
        state.text_candidates = text_state.text_candidates
        state.visual_candidates = visual_state.visual_candidates
        state.modality_status = {
            **state.modality_status,
            **text_state.modality_status,
            **visual_state.modality_status,
        }
        state.modality_errors = {
            **state.modality_errors,
            **text_state.modality_errors,
            **visual_state.modality_errors,
        }
        traces = [*state.agent_traces, *text_state.agent_traces, *visual_state.agent_traces]
        state.agent_traces = list({item.id: item for item in traces}.values())
        state.document = visual_state.document
        state.validation = ValidationService.merge(
            state.validation, [*text_state.validation.issues, *visual_state.validation.issues]
        )
        calls = [
            *state.provider_calls,
            *text_state.provider_calls,
            *visual_state.provider_calls,
        ]
        state.provider_calls = list({item.id: item for item in calls}.values())
        state.warnings = list(
            dict.fromkeys([*state.warnings, *text_state.warnings, *visual_state.warnings])
        )
        try:
            control = current_execution.get()
            if control:
                control.node("align_modalities")
            state = await self.nodes.align_modalities(state)
        except ExecutionPaused:
            raise
        except Exception as exc:
            state.status = "failed"
            state.failed_node = "align_modalities"
            state.current_node = "align_modalities"
            state.retry_count += 1
            state.errors.append(f"align_modalities:{type(exc).__name__}:{exc}")
            self.runs.save(state)
            raise
        state.current_node = "align_modalities"
        state.failed_node = None
        state.original_candidates = [c.model_copy(deep=True) for c in state.candidates]
        self.reviews.archive(state.run_id, [c.model_dump(mode="json") for c in state.candidates])
        self.runs.save(state)
        return {"payload": state.model_dump(mode="json")}

    @staticmethod
    def _after_risk(graph_state: GraphState) -> str:
        state = PrismKEWorkflow._state(graph_state)
        return "review" if state.status == "awaiting_review" else "continue"

    @staticmethod
    def _after_entity_resolution(graph_state: GraphState) -> str:
        state = PrismKEWorkflow._state(graph_state)
        return "review" if state.status == "awaiting_review" else "continue"

    def _build_graph(self, checkpointer: Any) -> Any:
        if self.review_only:
            return self._build_review_graph(checkpointer)
        builder = StateGraph(GraphState)
        before_extraction = [
            ("ingest", self.nodes.ingest),
            ("parse_document", self.nodes.parse_document),
            ("materialize_visual_assets", self.nodes.materialize_visual_assets),
            ("run_ocr", self.nodes.run_ocr),
            ("persist_evidence", self.nodes.persist_evidence),
            ("load_schema", self.nodes.load_schema),
        ]
        after_resolution = [
            ("normalize_claims", self.nodes.normalize_claims),
            ("detect_conflicts", self.nodes.detect_conflicts),
            ("route_by_risk", self.nodes.route_by_risk),
        ]
        for name, handler in [*before_extraction, *after_resolution]:
            builder.add_node(name, cast(Any, self._node(name, handler)))
        builder.add_node(
            "resolve_entities",
            cast(Any, self._node("resolve_entities", self.nodes.resolve_entities)),
        )
        builder.add_node(
            "extract_text_claims",
            cast(
                Any,
                self._branch_node(
                    "extract_text_claims", "text_branch", self.nodes.extract_text_claims
                ),
            ),
        )
        builder.add_node(
            "extract_visual_claims",
            cast(
                Any,
                self._branch_node(
                    "extract_visual_claims",
                    "visual_branch",
                    self.nodes.extract_visual_claims,
                ),
            ),
        )
        builder.add_node("align_modalities", cast(Any, self._join_modalities))
        builder.add_node(
            "reflect_candidates",
            cast(Any, self._node("reflect_candidates", self.nodes.reflect_candidates)),
        )
        builder.add_node(
            "prepare_graph_commit",
            cast(Any, self._node("prepare_graph_commit", self.nodes.prepare_graph_commit)),
        )
        builder.add_node(
            "commit_graph", cast(Any, self._node("commit_graph", self.nodes.commit_graph))
        )
        builder.add_edge(START, "ingest")
        for (left, _), (right, _) in zip(before_extraction, before_extraction[1:], strict=False):
            builder.add_edge(left, right)
        builder.add_edge("load_schema", "extract_text_claims")
        builder.add_edge("load_schema", "extract_visual_claims")
        builder.add_edge(["extract_text_claims", "extract_visual_claims"], "align_modalities")
        builder.add_edge("align_modalities", "reflect_candidates")
        builder.add_edge("reflect_candidates", "resolve_entities")
        builder.add_conditional_edges(
            "resolve_entities",
            self._after_entity_resolution,
            {"review": END, "continue": "normalize_claims"},
        )
        for (left, _), (right, _) in zip(after_resolution, after_resolution[1:], strict=False):
            builder.add_edge(left, right)
        builder.add_conditional_edges(
            "route_by_risk",
            self._after_risk,
            {"review": END, "continue": "prepare_graph_commit"},
        )
        builder.add_edge("prepare_graph_commit", "commit_graph")
        builder.add_edge("commit_graph", END)
        return builder.compile(checkpointer=checkpointer)

    def _build_review_graph(self, checkpointer: Any) -> Any:
        """A tail-only graph: no parser, OCR, model or entity retrieval nodes exist."""
        builder = StateGraph(GraphState)

        async def forbidden(_: GraphState) -> GraphState:
            raise ValueError("review workspace cannot execute entity resolution or extraction")

        builder.add_node("resolve_entities", cast(Any, forbidden))
        for name in (
            "normalize_claims",
            "detect_conflicts",
            "route_by_risk",
            "prepare_graph_commit",
            "commit_graph",
        ):
            builder.add_node(name, cast(Any, self._node(name, getattr(self.nodes, name))))
        builder.add_edge(START, "resolve_entities")
        builder.add_conditional_edges(
            "resolve_entities",
            self._after_entity_resolution,
            {"review": END, "continue": "normalize_claims"},
        )
        builder.add_edge("normalize_claims", "detect_conflicts")
        builder.add_edge("detect_conflicts", "route_by_risk")
        builder.add_conditional_edges(
            "route_by_risk",
            self._after_risk,
            {"review": END, "continue": "prepare_graph_commit"},
        )
        builder.add_conditional_edges(
            "prepare_graph_commit",
            lambda value: (
                "commit"
                if (
                    self._state(value).submission_confirmed
                    or (
                        not self._state(value).review_workspace
                        and not self._state(value).pending_correction_id
                    )
                )
                else "preview"
            ),
            {"commit": "commit_graph", "preview": END},
        )
        builder.add_edge("commit_graph", END)
        return builder.compile(checkpointer=checkpointer)

    async def confirm_submission(self, state: WorkflowState) -> WorkflowState:
        retry_commit = state.status == "failed" and state.failed_node == "commit_graph"
        if not self.review_only or (
            state.current_node != "prepare_graph_commit" and not retry_commit
        ):
            raise ValueError("run is not at the isolated submission preview")
        state.submission_confirmed = True
        async with open_checkpointer(self.checkpoint_path) as saver:
            graph = self._build_graph(saver)
            config = self._config(state.run_id)
            await graph.aupdate_state(
                config,
                {"payload": state.model_dump(mode="json")},
                as_node="prepare_graph_commit",
            )
            result = await graph.ainvoke(None, config)
        return self._state(cast(GraphState, result))

    @staticmethod
    def _config(run_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": run_id}}

    async def invoke(self, state: WorkflowState) -> WorkflowState:
        async with open_checkpointer(self.checkpoint_path) as saver:
            graph = self._build_graph(saver)
            result = await graph.ainvoke(
                {"payload": state.model_dump(mode="json")}, self._config(state.run_id)
            )
        return self._state(cast(GraphState, result))

    async def execution_snapshot(self, run_id: str) -> dict[str, Any]:
        async with open_checkpointer(self.checkpoint_path) as saver:
            graph = self._build_graph(saver)
            snapshot = await graph.aget_state(self._config(run_id))
            return {"exists": bool(snapshot.values), "next": list(snapshot.next)}

    async def resume(self, run_id: str) -> WorkflowState | None:
        failed_summary = self.runs.load(run_id)
        async with open_checkpointer(self.checkpoint_path) as saver:
            graph = self._build_graph(saver)
            config = self._config(run_id)
            snapshot = await graph.aget_state(config)
            if not snapshot.values:
                return None
            if self.review_only:
                allowed = {
                    "normalize_claims",
                    "detect_conflicts",
                    "route_by_risk",
                    "prepare_graph_commit",
                }
                if set(snapshot.next) - allowed:
                    raise ValueError("checkpoint would return to a forbidden node")
                if not snapshot.next:
                    raise ValueError("no review continuation is scheduled")
            result = await graph.ainvoke(None, config)
        state = self._state(cast(GraphState, result))
        state.retry_count = max(state.retry_count, failed_summary.retry_count)
        state.errors = list(dict.fromkeys([*failed_summary.errors, *state.errors]))
        self.runs.save(state)
        return state

    async def record_review(self, state: WorkflowState) -> bool:
        async with open_checkpointer(self.checkpoint_path) as saver:
            graph = self._build_graph(saver)
            config = self._config(state.run_id)
            snapshot = await graph.aget_state(config)
            if not snapshot.values:
                return False
            await graph.aupdate_state(
                config,
                {"payload": state.model_dump(mode="json")},
                as_node="route_by_risk",
            )
        self.runs.save(state)
        return True

    async def record_entity_review(self, state: WorkflowState) -> bool:
        async with open_checkpointer(self.checkpoint_path) as saver:
            graph = self._build_graph(saver)
            config = self._config(state.run_id)
            snapshot = await graph.aget_state(config)
            if not snapshot.values:
                return False
            await graph.aupdate_state(
                config,
                {"payload": state.model_dump(mode="json")},
                as_node="resolve_entities",
            )
        self.runs.save(state)
        return True

    async def record_completed_review(self, state: WorkflowState) -> bool:
        async with open_checkpointer(self.checkpoint_path) as saver:
            graph = self._build_graph(saver)
            config = self._config(state.run_id)
            snapshot = await graph.aget_state(config)
            if not snapshot.values:
                return False
            await graph.aupdate_state(
                config, {"payload": state.model_dump(mode="json")}, as_node="commit_graph"
            )
        self.runs.save(state)
        return True
