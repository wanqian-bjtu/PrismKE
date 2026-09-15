"""LangGraph workflow for the PrismKE v0.1 vertical slice."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from prismke.checkpoint import RunRepository, SQLiteCheckpointStore
from prismke.governance import (
    EntityResolver,
    collect_mentions,
    detect_conflicts,
    normalize_claims,
    route_by_risk,
)
from prismke.ids import stable_id
from prismke.interfaces import GraphStore, LLMProvider
from prismke.models import (
    ClaimStatus,
    GraphRevision,
    SourceDocument,
    WorkflowState,
)
from prismke.parsers import ParserRegistry
from prismke.schema import SchemaIndex, load_schema


class GraphState(TypedDict, total=False):
    payload: dict[str, Any]


Node = Callable[[GraphState], Awaitable[GraphState]]


class PrismKEWorkflow:
    def __init__(
        self,
        provider: LLMProvider,
        graph_store: GraphStore,
        checkpoints: SQLiteCheckpointStore,
        runs: RunRepository,
    ) -> None:
        self.provider = provider
        self.graph_store = graph_store
        self.checkpoints = checkpoints
        self.runs = runs
        self.parsers = ParserRegistry()
        self.graph = self._build_graph()

    def _state(self, graph_state: GraphState) -> WorkflowState:
        return WorkflowState.model_validate(graph_state["payload"])

    def _snapshot(self, state: WorkflowState, node: str) -> GraphState:
        state.current_node = node
        self.checkpoints.save(state)
        self.runs.save(state)
        return {"payload": state.model_dump(mode="json")}

    def _node(self, name: str, handler: Node) -> Node:
        async def wrapped(graph_state: GraphState) -> GraphState:
            state = self._state(graph_state)
            try:
                return await handler(graph_state)
            except Exception as exc:
                state.status = "failed"
                state.errors.append(f"{name}:{type(exc).__name__}:{exc}")
                state.current_node = name
                state.retry_count += 1
                self.checkpoints.save(state)
                self.runs.save(state)
                raise

        return wrapped

    def _build_graph(self) -> Any:
        builder = StateGraph(GraphState)
        ordered_nodes: list[tuple[str, Node]] = [
            ("ingest", self._ingest),
            ("parse_document", self._parse_document),
            ("load_schema", self._load_schema),
            ("extract_claims", self._extract_claims),
            ("resolve_entities", self._resolve_entities),
            ("normalize_claims", self._normalize_claims),
            ("detect_conflicts", self._detect_conflicts),
            ("route_by_risk", self._route_by_risk),
            ("persist_graph", self._persist_graph),
            ("commit_revision", self._commit_revision),
        ]
        for name, handler in ordered_nodes:
            builder.add_node(name, self._node(name, handler))
        builder.add_edge(START, ordered_nodes[0][0])
        for (left, _), (right, _) in zip(ordered_nodes, ordered_nodes[1:], strict=True):
            builder.add_edge(left, right)
        builder.add_edge(ordered_nodes[-1][0], END)
        return builder.compile()

    async def _ingest(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        if not SourceDocument(path=state.input_path).path.is_file():
            raise FileNotFoundError(state.input_path)
        return self._snapshot(state, "ingest")

    async def _parse_document(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        if state.document is None:
            state.document = await self.parsers.parse(SourceDocument(path=state.input_path))
            state.warnings.extend(state.document.warnings)
        return self._snapshot(state, "parse_document")

    async def _load_schema(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        if state.schema is None:
            state.schema = load_schema(SourceDocument(path=state.schema_path).path)
        return self._snapshot(state, "load_schema")

    async def _extract_claims(self, graph_state: GraphState) -> GraphState:
        from prismke.models import ExtractionRequest

        state = self._state(graph_state)
        if not state.candidates:
            assert state.document is not None and state.schema is not None
            result = await self.provider.extract(
                ExtractionRequest(document=state.document, schema=state.schema)
            )
            state.candidates = result.candidates
            state.warnings.extend(result.warnings)
        return self._snapshot(state, "extract_claims")

    async def _resolve_entities(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        if not state.entities:
            assert state.schema is not None
            resolver = EntityResolver(
                SchemaIndex(state.schema), await self.graph_store.list_entities()
            )
            resolution = resolver.resolve(collect_mentions(state.candidates))
            state.entities = resolution.entities
            state.warnings.extend(
                f"review_required:{mention_id}:{','.join(reasons)}"
                for mention_id, reasons in resolution.review_reasons.items()
            )
        return self._snapshot(state, "resolve_entities")

    async def _normalize_claims(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        if not state.claims:
            assert state.schema is not None
            resolver = EntityResolver(SchemaIndex(state.schema), state.entities)
            resolution = resolver.resolve(collect_mentions(state.candidates))
            entities = {item.id: item for item in resolution.entities}
            state.entities = list(entities.values())
            state.claims = normalize_claims(
                state.candidates,
                SchemaIndex(state.schema),
                entities,
                resolution.mention_to_entity,
            )
        return self._snapshot(state, "normalize_claims")

    async def _detect_conflicts(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        state.conflicts = detect_conflicts(
            state.claims, await self.graph_store.list_claims()
        )
        return self._snapshot(state, "detect_conflicts")

    async def _route_by_risk(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        state.claims, new_reviews = route_by_risk(
            state.run_id, state.claims, state.conflicts
        )
        resolved = {item.claim_id: item for item in state.review_tasks if item.status == "resolved"}
        state.review_tasks = [
            resolved.get(item.claim_id, item) for item in new_reviews
        ]
        state.status = (
            "awaiting_review"
            if any(item.status == "pending" for item in state.review_tasks)
            else "running"
        )
        return self._snapshot(state, "route_by_risk")

    async def _persist_graph(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        for entity in state.entities:
            await self.graph_store.upsert_entity(entity)
        for claim in state.claims:
            if claim.status in {ClaimStatus.AUTO_APPROVED, ClaimStatus.APPROVED}:
                await self.graph_store.append_claim(claim)
        for conflict in state.conflicts:
            await self.graph_store.open_conflict(conflict)
        return self._snapshot(state, "persist_graph")

    async def _commit_revision(self, graph_state: GraphState) -> GraphState:
        state = self._state(graph_state)
        if state.status == "awaiting_review":
            return self._snapshot(state, "commit_revision")
        accepted_claim_ids = [
            claim.id
            for claim in state.claims
            if claim.status in {ClaimStatus.AUTO_APPROVED, ClaimStatus.APPROVED}
        ]
        parent = await self.graph_store.latest_revision()
        state.revision = GraphRevision(
            id=stable_id("revision", state.run_id, *accepted_claim_ids),
            run_id=state.run_id,
            parent_id=parent.id if parent else None,
            entity_ids=sorted({claim.subject_id for claim in state.claims}),
            claim_ids=accepted_claim_ids,
            conflict_ids=[item.id for item in state.conflicts],
        )
        await self.graph_store.commit_revision(state.revision)
        state.status = "completed"
        return self._snapshot(state, "commit_revision")

    async def invoke(self, state: WorkflowState) -> WorkflowState:
        result = await self.graph.ainvoke({"payload": state.model_dump(mode="json")})
        return self._state(cast(GraphState, result))
