"""Parser extension boundary."""

from __future__ import annotations

from typing import Protocol

from prismke.domain import DocumentIR, SourceDocument


class ParserAdapter(Protocol):
    def supports(self, media_type: str) -> bool: ...

    async def parse(self, source: SourceDocument) -> DocumentIR: ...
