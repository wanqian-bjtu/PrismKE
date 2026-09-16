"""Create a fresh offline synthetic review workspace with one blocking issue."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from test_review_workspace import paused_source

from prismke.providers import DisabledOCRProvider, DisabledVLMProvider, MockLLMProvider
from prismke.workflow.review_workspace import import_review_run


async def main() -> None:
    source = Path(os.getenv("PRISMKE_BROWSER_SOURCE", "runtime/browser-validation-source"))
    target = Path(os.getenv("PRISMKE_BROWSER_TARGET", "runtime/browser-validation-review"))
    if source.exists() or target.exists():
        raise ValueError("browser fixture already exists; select fresh paths")
    service, state = await paused_source(source, Path("unused"), conflict=True)
    invalid = state.candidates[0].model_copy(deep=True)
    invalid.id = "candidate:browser-invalid-relation"
    invalid.relation = "undeclared_browser_relation"
    state.candidates.append(invalid)
    workflow = service._workflow(
        MockLLMProvider(), DisabledOCRProvider(), DisabledVLMProvider(), False
    )
    await workflow.record_entity_review(state)
    await import_review_run(source, state.run_id, target)
    print(state.run_id)


if __name__ == "__main__":
    asyncio.run(main())
