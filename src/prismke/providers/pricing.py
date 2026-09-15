"""Versioned list-price estimates for provider call telemetry."""

from __future__ import annotations

PRICING_SNAPSHOT = "aliyun-cn-beijing-2026-09-15-input-lte-32k"
_PER_MILLION_CNY = {
    "qwen3.7-flash": (0.2, 0.8),
    "qwen3.7-flash-2026-07-15": (0.2, 0.8),
}


def estimate_cost_cny(
    model: str, input_tokens: int, output_tokens: int
) -> tuple[float | None, str | None]:
    """Estimate short-context list price without pretending to be a bill."""

    rates = _PER_MILLION_CNY.get(model)
    if rates is None or input_tokens > 32_000:
        return None, None
    input_rate, output_rate = rates
    cost = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
    return round(cost, 8), PRICING_SNAPSHOT
