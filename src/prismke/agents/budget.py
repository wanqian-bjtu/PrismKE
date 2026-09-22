"""Shared conservative budget accounting for optional semantic advice."""

from __future__ import annotations

from prismke.core.errors import ProviderResponseError
from prismke.domain import ProviderCallRecord, WorkflowState

MIN_REQUEST_RESERVE = 2_000


class UnknownAgentUsageError(RuntimeError):
    """A model response without verifiable usage must block further calls."""


def can_request(state: WorkflowState) -> bool:
    return (
        state.semantic_advisor_name != "disabled"
        and state.agent_token_usage + MIN_REQUEST_RESERVE <= state.agent_token_budget
    )


def record_call(state: WorkflowState, record: ProviderCallRecord | None) -> None:
    if record is None:
        return
    if record.id not in {item.id for item in state.provider_calls}:
        state.provider_calls.append(record)
        if record.total_tokens is None:
            raise UnknownAgentUsageError(
                "semantic advisor usage is unknown; further model calls are blocked"
            )
        state.agent_token_usage += record.total_tokens


def record_response_failure(state: WorkflowState, exc: ProviderResponseError) -> None:
    for record in getattr(exc, "call_records", []):
        record_call(state, record)
