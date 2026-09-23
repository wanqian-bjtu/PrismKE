"""Shared, sanitized OpenAI-compatible HTTP transport."""

from __future__ import annotations

import asyncio
import re
from time import perf_counter
from typing import Any, Literal

import httpx

from src.core.errors import ProviderRequestError
from src.core.execution_control import current_execution
from src.core.ids import canonical_hash, stable_id
from src.domain import ProviderCallRecord
from src.providers.pricing import estimate_cost_cny


def _usage(payload: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    usage = payload.get("usage") or {}
    if not isinstance(usage, dict):
        return None, None, None
    input_raw = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_raw = usage.get("completion_tokens", usage.get("output_tokens"))
    if type(input_raw) is not int or type(output_raw) is not int:
        return None, None, None
    input_tokens, output_tokens = input_raw, output_raw
    if min(input_tokens, output_tokens) < 0:
        return None, None, None
    total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
    if type(total_tokens) is not int or total_tokens != input_tokens + output_tokens:
        return None, None, None
    return input_tokens, output_tokens, total_tokens


def _failure(status: int | None, kind: str) -> tuple[str, str]:
    if status == 401:
        return "authentication_failed", "模型服务鉴权失败（HTTP 401），请检查 API Key"
    if status == 403:
        return "access_denied", "模型服务拒绝访问（HTTP 403），请检查免费额度、余额、地域和模型权限"
    if status == 404:
        return "not_found", "模型服务地址或模型不存在（HTTP 404），请检查 Base URL 和模型名称"
    if status == 429:
        return "rate_limited", "模型服务触发限流（HTTP 429），重试后仍未恢复"
    if status is not None and status >= 500:
        return "server_error", f"模型服务暂时不可用（HTTP {status}），重试后仍未恢复"
    if kind == "timeout":
        return "timeout", "模型服务请求超时，重试后仍未恢复"
    if kind == "network":
        return "network_error", "无法连接模型服务，重试后仍未恢复"
    return "request_failed", "模型服务请求失败"


def _record(
    *,
    provider: Literal["llm", "vlm", "governance", "fusion"],
    operation_id: str,
    requested_model: str,
    prompt_version: str,
    started: float,
    retry_count: int,
    status: Literal["succeeded", "failed"],
    payload: dict[str, Any] | None = None,
    error_code: str | None = None,
) -> ProviderCallRecord:
    payload = payload or {}
    input_tokens, output_tokens, total_tokens = _usage(payload)
    response_model = str(payload["model"]) if payload.get("model") else None
    estimated_cost, snapshot = (
        estimate_cost_cny(response_model or requested_model, input_tokens, output_tokens)
        if input_tokens is not None and output_tokens is not None
        else (None, None)
    )
    request_id = payload.get("id")
    return ProviderCallRecord(
        id=stable_id(
            "provider-call",
            provider,
            operation_id,
            requested_model,
            str(request_id or "none"),
            status,
            retry_count,
        ),
        provider=provider,
        operation_id=operation_id,
        requested_model=requested_model,
        response_model=response_model,
        request_id=str(request_id) if request_id else None,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=round((perf_counter() - started) * 1000, 3),
        retry_count=retry_count,
        status=status,
        error_code=error_code,
        prompt_version=prompt_version,
        estimated_cost_cny=estimated_cost,
        pricing_snapshot=snapshot,
    )


async def post_chat_completion(
    *,
    base_url: str,
    api_key: str,
    body: dict[str, Any],
    timeout: float,
    provider: Literal["llm", "vlm", "governance", "fusion"],
    operation_id: str,
    prompt_version: str,
    transport: httpx.AsyncBaseTransport | None = None,
    provider_fingerprint: str | None = None,
) -> tuple[dict[str, Any], ProviderCallRecord]:
    """Post one chat completion with bounded retry and sanitized failures."""

    started = perf_counter()
    headers = {"Authorization": f"Bearer {api_key}"}
    retry_count = 0
    delay = 0.5
    control = current_execution.get()
    for attempt in range(3):
        key = stable_id(
            "http-request",
            provider,
            operation_id,
            base_url.rstrip("/"),
            prompt_version,
            canonical_hash(body),
            attempt,
        )
        if control:
            cached = control.begin_request(
                key,
                {
                    "provider": provider,
                    "operation_id": operation_id,
                    "model": str(body["model"]),
                    "prompt_version": prompt_version,
                    "provider_fingerprint": provider_fingerprint,
                    "input_hash": canonical_hash(body),
                    "http_attempt": attempt,
                },
            )
            if cached is not None:
                return cached, _record(
                    provider=provider,
                    operation_id=operation_id,
                    requested_model=str(body["model"]),
                    prompt_version=prompt_version,
                    started=started,
                    retry_count=attempt,
                    status="succeeded",
                    payload=cached,
                )
        try:
            async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
                response = await client.post(
                    f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=body
                )
            if control and response.is_error:
                control.finish_request(
                    key, "unknown" if response.status_code >= 500 else "rejected", None, False
                )
            if (
                response.status_code == 429 or (response.status_code >= 500 and not control)
            ) and attempt < 2:
                retry_count += 1
                await asyncio.sleep(delay)
                delay *= 2
                continue
            if response.is_error:
                code, message = _failure(response.status_code, "http")
                record = _record(
                    provider=provider,
                    operation_id=operation_id,
                    requested_model=str(body["model"]),
                    prompt_version=prompt_version,
                    started=started,
                    retry_count=retry_count,
                    status="failed",
                    error_code=code,
                )
                raise ProviderRequestError(message, call_record=record)
            try:
                payload = dict(response.json())
            except ValueError as exc:
                if control:
                    control.finish_request(key, "unknown", None, False)
                record = _record(
                    provider=provider,
                    operation_id=operation_id,
                    requested_model=str(body["model"]),
                    prompt_version=prompt_version,
                    started=started,
                    retry_count=retry_count,
                    status="failed",
                    error_code="invalid_response",
                )
                raise ProviderRequestError("模型服务返回了无效 JSON", call_record=record) from exc
            if control:
                # Only response fields required for replay; never persist the request or headers.
                safe = {k: payload[k] for k in ("id", "model", "choices", "usage") if k in payload}

                def scrub(value: Any) -> Any:
                    if isinstance(value, str):
                        return re.sub(
                            r"data:image/[^\s\"]+",
                            "[image omitted]",
                            value.replace(api_key, "[secret omitted]"),
                        )
                    if isinstance(value, dict):
                        return {
                            k: scrub(v)
                            for k, v in value.items()
                            if k not in {"authorization", "api_key", "image_url"}
                        }
                    if isinstance(value, list):
                        return [scrub(v) for v in value]
                    return value

                safe = scrub(safe)
                control.finish_request(key, "completed", safe, _usage(payload)[2] is not None)
                payload = safe
            return payload, _record(
                provider=provider,
                operation_id=operation_id,
                requested_model=str(body["model"]),
                prompt_version=prompt_version,
                started=started,
                retry_count=retry_count,
                status="succeeded",
                payload=payload,
            )
        except ProviderRequestError:
            raise
        except httpx.TimeoutException as exc:
            kind = "timeout"
            if control:
                control.finish_request(key, "unknown", None, False)
            if attempt < 2 and not control:
                retry_count += 1
                await asyncio.sleep(delay)
                delay *= 2
                continue
            code, message = _failure(None, kind)
            record = _record(
                provider=provider,
                operation_id=operation_id,
                requested_model=str(body["model"]),
                prompt_version=prompt_version,
                started=started,
                retry_count=retry_count,
                status="failed",
                error_code=code,
            )
            raise ProviderRequestError(message, call_record=record) from exc
        except httpx.NetworkError as exc:
            if control:
                control.finish_request(key, "unknown", None, False)
            if attempt < 2 and not control:
                retry_count += 1
                await asyncio.sleep(delay)
                delay *= 2
                continue
            code, message = _failure(None, "network")
            record = _record(
                provider=provider,
                operation_id=operation_id,
                requested_model=str(body["model"]),
                prompt_version=prompt_version,
                started=started,
                retry_count=retry_count,
                status="failed",
                error_code=code,
            )
            raise ProviderRequestError(message, call_record=record) from exc
        except asyncio.CancelledError:
            if control:
                control.finish_request(key, "unknown", None, False)
            raise
    raise RuntimeError("unreachable")
