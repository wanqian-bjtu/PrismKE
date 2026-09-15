"""Model provider extension boundaries."""

from __future__ import annotations

from typing import Protocol

from prismke.domain import (
    ExtractionRequest,
    ExtractionResult,
    VisualExtractionRequest,
)


class LLMProvider(Protocol):
    def fingerprint(self) -> str: ...

    async def extract(self, request: ExtractionRequest) -> ExtractionResult: ...


class VLMProvider(Protocol):
    def fingerprint(self) -> str: ...

    async def extract(self, request: VisualExtractionRequest) -> ExtractionResult: ...
