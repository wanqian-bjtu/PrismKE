"""Replaceable boundaries for parsers, model providers, and graph stores."""

from __future__ import annotations

from typing import Protocol

from prismke.models import (
    CanonicalEntity,
    Claim,
    ConflictSet,
    DocumentIR,
    ExtractionRequest,
    ExtractionResult,
    GraphRevision,
    SourceDocument,
    VisualExtractionRequest,
)


class ParserAdapter(Protocol):
    def supports(self, media_type: str) -> bool: ...

    async def parse(self, source: SourceDocument) -> DocumentIR: ...


class LLMProvider(Protocol):
    async def extract(self, request: ExtractionRequest) -> ExtractionResult: ...


class VLMProvider(Protocol):
    async def extract(self, request: VisualExtractionRequest) -> ExtractionResult: ...


class GraphStore(Protocol):
    async def list_entities(self) -> list[CanonicalEntity]: ...

    async def list_claims(self) -> list[Claim]: ...

    async def latest_revision(self) -> GraphRevision | None: ...

    async def upsert_entity(self, entity: CanonicalEntity) -> None: ...

    async def append_claim(self, claim: Claim) -> None: ...

    async def open_conflict(self, conflict: ConflictSet) -> None: ...

    async def commit_revision(self, revision: GraphRevision) -> None: ...
