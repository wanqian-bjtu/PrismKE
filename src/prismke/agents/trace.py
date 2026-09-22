"""Compact, idempotent agent handoffs and decision traces."""

from __future__ import annotations

import re

from prismke.core.ids import stable_id
from prismke.domain.agents import AgentHandoff, AgentRole, AgentTrace
from prismke.domain.workflow import WorkflowState

ALLOWED_TOOLS: dict[AgentRole, frozenset[str]] = {
    "extraction": frozenset({"ocr", "text_llm", "vision_vlm", "modality_alignment"}),
    "governance": frozenset(
        {"entity_resolver", "semantic_advisor", "schema_validation", "claim_normalizer"}
    ),
    "fusion_review": frozenset(
        {"reflection", "conflict_detector", "semantic_advisor", "risk_router"}
    ),
}


def safe_reason_code(value: str) -> str:
    normalized = value.strip().lower()
    if re.fullmatch(r"[a-z][a-z0-9_]{0,63}", normalized):
        return normalized
    return "model_reason_untrusted"


def trace_step(
    state: WorkflowState,
    agent: AgentRole,
    step: str,
    decision: str,
    *,
    tools: tuple[str, ...] = (),
    reasons: tuple[str, ...] = (),
    input_ids: tuple[str, ...] = (),
    output_ids: tuple[str, ...] = (),
    model_fingerprint: str | None = None,
    token_usage: int | None = None,
    latency_ms: float | None = None,
    status: str = "succeeded",
) -> None:
    unknown = set(tools) - ALLOWED_TOOLS[agent]
    if unknown:
        raise ValueError(f"tools not allowed for {agent}: {sorted(unknown)}")
    trace = AgentTrace(
        id=stable_id("agent-trace", state.run_id, agent, step, *input_ids, *output_ids),
        run_id=state.run_id,
        agent=agent,
        step=step,
        selected_tools=list(tools),
        decision=decision,
        reason_codes=list(reasons),
        input_ids=list(input_ids),
        output_ids=list(output_ids),
        model_fingerprint=model_fingerprint,
        token_usage=token_usage,
        latency_ms=latency_ms,
        status=status,
    )
    existing = {item.id: index for index, item in enumerate(state.agent_traces)}
    if trace.id in existing:
        state.agent_traces[existing[trace.id]] = trace
    else:
        state.agent_traces.append(trace)


def handoff(
    state: WorkflowState,
    agent: AgentRole,
    *,
    input_ids: tuple[str, ...],
    output_ids: tuple[str, ...],
    evidence_ids: tuple[str, ...] = (),
    issue_ids: tuple[str, ...] = (),
    review_task_ids: tuple[str, ...] = (),
    next_action: str = "continue",
) -> None:
    item = AgentHandoff(
        id=stable_id("agent-handoff", state.run_id, agent, *input_ids, *output_ids),
        run_id=state.run_id,
        agent=agent,
        input_ids=list(input_ids),
        output_ids=list(output_ids),
        evidence_ids=list(evidence_ids),
        issue_ids=list(issue_ids),
        review_task_ids=list(review_task_ids),
        next_action=next_action,
    )
    existing = {record.id: index for index, record in enumerate(state.agent_handoffs)}
    if item.id in existing:
        state.agent_handoffs[existing[item.id]] = item
    else:
        state.agent_handoffs.append(item)
