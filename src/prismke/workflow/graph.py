"""Persistent LangGraph execution and exact-node recovery."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from prismke.domain import WorkflowState
from prismke.parsing import ParserRegistry
from prismke.persistence.base import EvidenceStore, GraphStore
from prismke.persistence.checkpoints import open_checkpointer
from prismke.persistence.runs import RunRepository
from prismke.providers.base import LLMProvider
from prismke.workflow.nodes import WorkflowNodes


class GraphState(TypedDict, total=False):
    payload: dict[str, Any]


Node = Callable[[GraphState], Awaitable[GraphState]]


class PrismKEWorkflow:
    def __init__(
        self,
        provider: LLMProvider,
        graph_store: GraphStore,
        evidence_store: EvidenceStore,
        checkpoint_path: Path,
        runs: RunRepository,
        parsers: ParserRegistry | None = None,
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self.runs = runs
        self.nodes = WorkflowNodes(
            provider, graph_store, evidence_store, parsers or ParserRegistry()
        )

    @staticmethod
    def _state(graph_state: GraphState) -> WorkflowState:
        return WorkflowState.model_validate(graph_state["payload"])

    def _node(
        self,
        name: str,
        handler: Callable[[WorkflowState], Awaitable[WorkflowState]],
    ) -> Node:
        async def wrapped(graph_state: GraphState) -> GraphState:
            state = self._state(graph_state)
            try:
                state = await handler(state)
            except Exception as exc:
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

    @staticmethod
    def _after_risk(graph_state: GraphState) -> str:
        state = PrismKEWorkflow._state(graph_state)
        return "review" if state.status == "awaiting_review" else "continue"

    def _build_graph(self, checkpointer: Any) -> Any:
        builder = StateGraph(GraphState)
        ordered = [
            ("ingest", self.nodes.ingest),
            ("parse_document", self.nodes.parse_document),
            ("persist_evidence", self.nodes.persist_evidence),
            ("load_schema", self.nodes.load_schema),
            ("extract_claims", self.nodes.extract_claims),
            ("resolve_entities", self.nodes.resolve_entities),
            ("normalize_claims", self.nodes.normalize_claims),
            ("detect_conflicts", self.nodes.detect_conflicts),
            ("route_by_risk", self.nodes.route_by_risk),
        ]
        for name, handler in ordered:
            builder.add_node(name, cast(Any, self._node(name, handler)))
        builder.add_node(
            "prepare_graph_commit",
            cast(Any, self._node("prepare_graph_commit", self.nodes.prepare_graph_commit)),
        )
        builder.add_node(
            "commit_graph", cast(Any, self._node("commit_graph", self.nodes.commit_graph))
        )
        builder.add_edge(START, "ingest")
        for (left, _), (right, _) in zip(ordered, ordered[1:], strict=False):
            builder.add_edge(left, right)
        builder.add_conditional_edges(
            "route_by_risk",
            self._after_risk,
            {"review": END, "continue": "prepare_graph_commit"},
        )
        builder.add_edge("prepare_graph_commit", "commit_graph")
        builder.add_edge("commit_graph", END)
        return builder.compile(checkpointer=checkpointer)

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

    async def resume(self, run_id: str) -> WorkflowState | None:
        failed_summary = self.runs.load(run_id)
        async with open_checkpointer(self.checkpoint_path) as saver:
            graph = self._build_graph(saver)
            config = self._config(run_id)
            snapshot = await graph.aget_state(config)
            if not snapshot.values:
                return None
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
