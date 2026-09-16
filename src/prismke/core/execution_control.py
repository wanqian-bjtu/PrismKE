"""Cooperative control propagates into LangGraph branches and native OCR threads."""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel


class ExecutionPaused(Exception):
    """A control boundary, not a failed extraction or a retry."""


class ExecutionControl(Protocol):
    def check(self) -> None: ...
    def node(self, name: str) -> None: ...
    def commit_started(self, revision_id: str) -> None: ...
    def commit_finished(self) -> None: ...
    def begin_request(self, key: str, metadata: dict[str, Any]) -> dict[str, Any] | None: ...
    def finish_request(
        self, key: str, status: str, payload: dict[str, Any] | None, usage_known: bool
    ) -> None: ...
    def result(self, key: str) -> dict[str, Any] | None: ...
    def put_result(self, key: str, value: dict[str, Any]) -> None: ...


current_execution: ContextVar[ExecutionControl | None] = ContextVar("execution", default=None)
Model = TypeVar("Model", bound=BaseModel)


def check_execution() -> None:
    control = current_execution.get()
    if control:
        control.check()


async def cached_operation(
    key: str, model: type[Model], call: Callable[[], Awaitable[Model]]
) -> Model:
    control = current_execution.get()
    if not control:
        return await call()
    control.check()
    old = control.result(key)
    if old is not None:
        return model.model_validate(old)
    value = await call()
    control.put_result(key, value.model_dump(mode="json"))
    return value
