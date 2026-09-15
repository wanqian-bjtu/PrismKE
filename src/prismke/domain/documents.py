"""Document intermediate representation and evidence coordinates."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class Modality(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    OCR = "ocr"
    TABLE = "table"
    CHART = "chart"


class EvidenceKind(StrEnum):
    TEXT_SPAN = "text_span"
    PDF_BBOX = "pdf_bbox"
    IMAGE = "image"
    VISUAL_REGION = "visual_region"


class BBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class SourceDocument(BaseModel):
    path: Path
    media_type: str | None = None


class TextBlock(BaseModel):
    id: str
    text: str
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    bbox: BBox | None = None
    evidence_id: str


class MediaAsset(BaseModel):
    id: str
    path: str
    media_type: str
    width: int | None = None
    height: int | None = None
    page_number: int | None = None
    evidence_id: str


class EvidenceRef(BaseModel):
    id: str
    kind: EvidenceKind
    document_id: str
    source_hash: str
    modality: Modality
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    bbox: BBox | None = None
    media_asset_id: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None


class DocumentIR(BaseModel):
    id: str
    source_path: str
    source_hash: str
    media_type: str
    text_blocks: list[TextBlock] = Field(default_factory=list)
    media_assets: list[MediaAsset] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
