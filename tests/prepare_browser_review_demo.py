"""Prepare a synthetic offline workspace for the browser lifecycle test."""

from __future__ import annotations

import asyncio
from pathlib import Path

from test_review_workspace import paused_source

from prismke.workflow.review_workspace import import_review_run


async def main() -> None:
    source = Path("runtime/browser-review-source")
    target = Path("runtime/browser-review-mock")
    service, state = await paused_source(source, Path("unused"), conflict=True)
    await import_review_run(service.settings.runtime_dir, state.run_id, target)
    print(state.run_id)


if __name__ == "__main__":
    asyncio.run(main())
