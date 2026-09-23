"""Loopback-only offline browser fixture; never use a production runtime."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import uvicorn

from src.api import create_app
from src.core.settings import Settings
from src.domain import ExtractionRequest, ExtractionResult
from src.providers import MockLLMProvider
from src.workflow import PrismKEService


class GatedMockProvider(MockLLMProvider):
    def __init__(self, release: Path) -> None:
        self.release = release
        self.calls = 0

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        self.calls += 1
        while not self.release.exists():
            await asyncio.sleep(0.05)
        return await super().extract(request)


def main() -> None:
    root = Path(os.environ["PRISMKE_EXECUTION_DEMO_RUNTIME"]).resolve()
    project = Path(__file__).resolve().parents[1]
    if not root.is_relative_to(project / "runtime") or root.exists():
        raise ValueError("fixture requires a fresh directory inside project runtime")
    settings = Settings(
        _env_file=None,
        runtime_dir=root,
        graph_store="json",
        embedding_provider="disabled",
        api_host="127.0.0.1",
        api_port=8006,
    )
    service = PrismKEService(settings)
    provider = GatedMockProvider(root / "release")

    def mock_only(name: str) -> MockLLMProvider:
        if name != "mock":
            raise ValueError("offline fixture only supports mock")
        return provider

    service.provider = mock_only  # type: ignore[method-assign]
    app = create_app(settings, service)

    @app.post("/offline-test/release")
    async def release() -> dict[str, bool]:
        provider.release.touch()
        return {"released": True}

    @app.get("/offline-test/calls")
    async def calls() -> dict[str, int]:
        return {"calls": provider.calls}

    uvicorn.run(app, host="127.0.0.1", port=8006)


if __name__ == "__main__":
    main()
