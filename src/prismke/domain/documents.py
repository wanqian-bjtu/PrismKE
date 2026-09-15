"""Document intermediate representation and evidence coordinates."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

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


class CoordinateSpace(StrEnum):
    PDF_POINTS = "pdf_points"
    IMAGE_PIXELS = "image_pixels"
    NORMALIZED = "normalized"


class LocalizationLevel(StrEnum):
    TEXT_SPAN = "text_span"
    REGION = "region"
    ASSET = "asset"


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
    modality: Modality = Modality.TEXT
    source_media_asset_id: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class MediaAsset(BaseModel):
    id: str
    path: str
    media_type: str
    width: int | None = None
    height: int | None = None
    page_number: int | None = None
    evidence_id: str
    blob_hash: str | None = None
    origin: Literal[
        "source_image",
        "pdf_embedded",
        "pdf_page_render",
        "docx_embedded",
        "html_embedded",
        "markdown_embedded",
    ] = "source_image"
    source_ref: str | None = None
    context_text: str = ""
    requires_ocr: bool = False


class DocumentPage(BaseModel):
    id: str
    page_number: int = Field(ge=1)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    requires_ocr: bool = False
    text_block_ids: list[str] = Field(default_factory=list)
    media_asset_ids: list[str] = Field(default_factory=list)


class VisualObservation(BaseModel):
    id: str
    media_asset_id: str
    label: str
    description: str = ""
    bbox: BBox | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_id: str
    attributes: dict[str, Any] = Field(default_factory=dict)


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
    coordinate_space: CoordinateSpace | None = None
    canvas_width: float | None = Field(default=None, gt=0)
    canvas_height: float | None = Field(default=None, gt=0)
    localization_level: LocalizationLevel | None = None


class DocumentIR(BaseModel):
    id: str
    source_path: str
    source_hash: str
    media_type: str
    pages: list[DocumentPage] = Field(default_factory=list)
    text_blocks: list[TextBlock] = Field(default_factory=list)
    media_assets: list[MediaAsset] = Field(default_factory=list)
    visual_observations: list[VisualObservation] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
