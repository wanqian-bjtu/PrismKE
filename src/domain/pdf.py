"""Auditable PDF parser selection and fallback contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class PDFParseMode(StrEnum):
    AUTO = "auto"
    PYMUPDF = "pymupdf"
    MINERU = "mineru"


class PDFParserName(StrEnum):
    PYMUPDF = "pymupdf"
    MINERU = "mineru"


class PDFComplexityThresholds(BaseModel):
    no_text_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    short_text_chars: int = Field(default=80, ge=0)
    short_text_ratio: float = Field(default=0.30, ge=0.0, le=1.0)
    table_ratio: float = Field(default=0.10, ge=0.0, le=1.0)
    drawing_count: int = Field(default=5, ge=1)
    drawing_ratio: float = Field(default=0.20, ge=0.0, le=1.0)
    multicolumn_ratio: float = Field(default=0.20, ge=0.0, le=1.0)


class PDFComplexityReport(BaseModel):
    total_pages: int = Field(ge=1)
    no_native_text_pages: list[int] = Field(default_factory=list)
    short_text_pages: list[int] = Field(default_factory=list)
    table_candidate_pages: list[int] = Field(default_factory=list)
    drawing_dense_pages: list[int] = Field(default_factory=list)
    unstable_multicolumn_pages: list[int] = Field(default_factory=list)
    native_text_characters: int = Field(ge=0)
    thresholds: PDFComplexityThresholds
    reason_codes: list[str] = Field(default_factory=list)

    @property
    def requires_mineru(self) -> bool:
        return bool(self.reason_codes)


class PDFParseDecision(BaseModel):
    requested_mode: PDFParseMode
    actual_parser: PDFParserName
    reason_codes: list[str] = Field(default_factory=list)
    complexity: PDFComplexityReport
    parser_version: str
    parser_fingerprint: str
    config_fingerprint: str
    mineru_job_id: str | None = None
    mineru_status: str | None = None
    artifact_manifest_hash: str | None = None


class PDFParserFallbackEvent(BaseModel):
    sequence: int | None = None
    run_id: str
    operator: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    expected_execution_version: int = Field(ge=0)
    from_parser: PDFParserName = PDFParserName.MINERU
    to_parser: PDFParserName = PDFParserName.PYMUPDF
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
