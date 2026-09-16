"""Shared, sanitized request accounting for bounded live evaluation only."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

import httpx


class EvaluationBudgetStop(RuntimeError):
    """Stop further live calls when budget or reliable accounting is unavailable."""


@dataclass
class RequestBudget:
    limit: int = 100_000
    stop_at: int = 90_000
    max_output_tokens: int = 4096
    total_tokens: int = 0
    reserved_tokens: int = 0
    stopped_reason: str | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    request_gate: asyncio.Lock = field(default_factory=asyncio.Lock)
    active_tasks: list[asyncio.Task[httpx.Response]] = field(default_factory=list)
    accounting_complete: bool = True

    async def settle(self) -> None:
        """Account already dispatched requests before closing a validation run."""
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)
            self.active_tasks.clear()

    def estimate(self, body: dict[str, Any]) -> int:
        text_bytes = images = 0
        for message in body.get("messages", []):
            content = message.get("content", "")
            if isinstance(content, str):
                text_bytes += len(content.encode("utf-8"))
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "image_url":
                        images += 1
                    else:
                        text_bytes += len(str(part.get("text", "")).encode("utf-8"))
        return text_bytes + images * 8192 + self.max_output_tokens + 1024

    async def reserve(self, estimate: int) -> None:
        async with self.lock:
            if self.stopped_reason or self.total_tokens >= self.stop_at:
                raise EvaluationBudgetStop(self.stopped_reason or "token stop threshold reached")
            if self.total_tokens + self.reserved_tokens + estimate > self.limit:
                self.stopped_reason = "estimated request exceeds remaining token budget"
                raise EvaluationBudgetStop(self.stopped_reason)
            self.reserved_tokens += estimate

    async def record(self, estimate: int, response: httpx.Response) -> None:
        async with self.lock:
            self.reserved_tokens -= estimate
            row: dict[str, Any] = {"status_code": response.status_code}
            if response.is_success:
                try:
                    payload = response.json()
                    usage = payload["usage"]
                    tokens = int(usage["total_tokens"])
                    if tokens <= 0:
                        raise ValueError("invalid usage")
                    row.update(
                        {
                            "model": payload.get("model"),
                            "request_id": payload.get("id"),
                            "input_tokens": int(usage.get("prompt_tokens", 0)),
                            "output_tokens": int(usage.get("completion_tokens", 0)),
                            "total_tokens": tokens,
                        }
                    )
                    self.total_tokens += tokens
                except (ValueError, KeyError, TypeError):
                    self.accounting_complete = False
                    self.stopped_reason = "model response usage unavailable; evaluation stopped"
            elif response.status_code in {401, 403, 404}:
                self.accounting_complete = False
                self.stopped_reason = (
                    f"model service access/configuration error HTTP {response.status_code}"
                )
            else:
                # Failed requests have no trustworthy billed usage; do not assume zero cost.
                self.stopped_reason = f"failed HTTP {response.status_code}; token usage uncertain"
                self.accounting_complete = False
            self.calls.append(row)
            if self.total_tokens > self.limit:
                self.stopped_reason = "actual token usage exceeded evaluation target"
            if self.stopped_reason:
                raise EvaluationBudgetStop(self.stopped_reason)


class BudgetedTransport(httpx.AsyncBaseTransport):
    def __init__(
        self, budget: RequestBudget, inner: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.budget = budget
        self.inner = inner

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(await request.aread())
        body["max_tokens"] = self.budget.max_output_tokens
        # Bound evaluation output without hidden reasoning on Bailian hybrid models.
        if "aliyuncs.com" in request.url.host and str(body.get("model", "")).startswith("qwen"):
            body["enable_thinking"] = False
        task = asyncio.create_task(self._send(request, body))
        self.budget.active_tasks.append(task)
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            self.budget.stopped_reason = "workflow interrupted; settling dispatched requests"
            raise

    async def _send(self, request: httpx.Request, body: dict[str, Any]) -> httpx.Response:
        async with self.budget.request_gate:
            return await self._send_serial(request, body)

    async def _send_serial(self, request: httpx.Request, body: dict[str, Any]) -> httpx.Response:
        estimate = self.budget.estimate(body)
        await self.budget.reserve(estimate)
        forwarded = httpx.Request(
            request.method,
            request.url,
            headers={
                key: value
                for key, value in request.headers.items()
                if key.lower() != "content-length"
            },
            json=body,
            extensions=request.extensions,
        )
        inner = self.inner or httpx.AsyncHTTPTransport()
        try:
            response = await inner.handle_async_request(forwarded)
            await response.aread()
        except Exception as exc:
            async with self.budget.lock:
                self.budget.reserved_tokens -= estimate
                self.budget.stopped_reason = "request failed; billed token usage uncertain"
                self.budget.accounting_complete = False
                self.budget.calls.append({"status": "network_failure", "usage": "unknown"})
            raise EvaluationBudgetStop(self.budget.stopped_reason) from exc
        finally:
            if self.inner is None:
                await inner.aclose()
        await self.budget.record(estimate, response)
        return response
