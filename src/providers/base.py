"""Model provider extension boundaries."""

from __future__ import annotations

from typing import Protocol

from src.domain import (
    EntityAdvice,
    EntityAdviceRequest,
    ExtractionRequest,
    ExtractionResult,
    FusionAdvice,
    FusionAdviceRequest,
    OCRRequest,
    OCRResult,
    ProviderCallRecord,
    ReflectionRequest,
    ReflectionResult,
    VisualExtractionRequest,
)


class SemanticAdvisor(Protocol):
    def fingerprint(self) -> str: ...

    async def advise_entity(
        self, request: EntityAdviceRequest
    ) -> tuple[EntityAdvice, ProviderCallRecord | None]: ...

    async def advise_fusion(
        self, request: FusionAdviceRequest
    ) -> tuple[FusionAdvice, ProviderCallRecord | None]: ...


class LLMProvider(Protocol):
    def fingerprint(self) -> str: ...

    async def extract(self, request: ExtractionRequest) -> ExtractionResult: ...


class VLMProvider(Protocol):
    def fingerprint(self) -> str: ...

    async def extract(self, request: VisualExtractionRequest) -> ExtractionResult: ...


class OCRProvider(Protocol):
    def fingerprint(self) -> str: ...

    async def recognize(self, request: OCRRequest) -> OCRResult: ...


class EmbeddingProvider(Protocol):
    def fingerprint(self) -> str: ...

    async def encode(self, texts: list[str]) -> list[list[float]]: ...


class ReflectionProvider(Protocol):
    def fingerprint(self) -> str: ...

    async def reflect(self, request: ReflectionRequest) -> ReflectionResult: ...
