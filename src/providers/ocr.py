"""Disabled, mock, and PaddleOCR implementations."""

from __future__ import annotations

import asyncio
import re
from functools import lru_cache
from importlib import import_module
from typing import Any

from src.core.execution_control import ExecutionPaused, check_execution
from src.core.ids import stable_id
from src.domain import (
    BBox,
    CoordinateSpace,
    EvidenceKind,
    EvidenceRef,
    LocalizationLevel,
    Modality,
    OCRRequest,
    OCRResult,
    TextBlock,
)
from src.parsing.visual_assets import select_analysis_assets


@lru_cache(maxsize=1)
def detect_ocr_device() -> str:
    """Resolve automatic OCR placement using Paddle's own CUDA capability."""

    try:
        paddle = import_module("paddle")
        device = paddle.device
        compiled_check = getattr(device, "is_compiled_with_cuda", None) or getattr(
            paddle, "is_compiled_with_cuda", None
        )
        cuda = device.cuda
        if compiled_check is not None and compiled_check() and int(cuda.device_count()) > 0:
            return "gpu:0"
    except Exception:
        pass
    return "cpu"


def resolve_ocr_device(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "auto":
        return detect_ocr_device()
    if normalized == "cpu" or re.fullmatch(r"gpu:\d+", normalized):
        return normalized
    raise ValueError("ocr_device must be auto, cpu or gpu:<index>")


def resolve_ocr_language(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"ch", "mixed", "zh"}:
        return "ch"
    if normalized == "en":
        return "en"
    raise ValueError("ocr_lang must be mixed, zh, en or legacy ch")


class DisabledOCRProvider:
    def fingerprint(self) -> str:
        return "disabled"

    async def recognize(self, request: OCRRequest) -> OCRResult:
        del request
        return OCRResult()


class MockOCRProvider(DisabledOCRProvider):
    def fingerprint(self) -> str:
        return stable_id("provider", "mock-ocr", "v1")


class PaddleOCRProvider:
    def __init__(self, device: str = "cpu", lang: str = "ch", model: str = "PP-OCRv5") -> None:
        self.requested_device = device
        self.requested_language = lang
        self.device = resolve_ocr_device(device)
        self.lang = resolve_ocr_language(lang)
        self.model = model
        self._engine: Any = None

    def fingerprint(self) -> str:
        return stable_id("provider", "paddleocr", self.device, self.lang, self.model, "v2")

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                paddleocr = import_module("paddleocr")
            except ImportError as exc:
                raise RuntimeError("PaddleOCR is not installed; run 'uv sync --extra ocr'") from exc
            engine_options: dict[str, Any] = {}
            if self.device == "cpu":
                engine_options["enable_mkldnn"] = False
            self._engine = paddleocr.PaddleOCR(
                lang=self.lang,
                ocr_version=self.model,
                device=self.device,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                **engine_options,
            )
        return self._engine

    @staticmethod
    def _payload(result: Any) -> dict[str, Any]:
        value = getattr(result, "json", {})
        if callable(value):
            value = value()
        if not isinstance(value, dict):
            return {}
        nested = value.get("res", value)
        return nested if isinstance(nested, dict) else {}

    def _recognize_sync(self, request: OCRRequest) -> OCRResult:
        blocks: list[TextBlock] = []
        evidence: list[EvidenceRef] = []
        warnings: list[str] = []
        assets = [
            asset
            for asset in select_analysis_assets(request.document)
            if not (asset.origin == "pdf_page_render" and not asset.requires_ocr)
        ]
        if not assets:
            return OCRResult()
        engine = self._get_engine()
        for asset in assets:
            check_execution()
            try:
                for result_index, result in enumerate(engine.predict(asset.path)):
                    payload = self._payload(result)
                    texts = payload.get("rec_texts", [])
                    scores = payload.get("rec_scores", [])
                    polygons = payload.get("rec_polys", payload.get("dt_polys", []))
                    for index, raw_text in enumerate(texts):
                        text = str(raw_text).strip()
                        if not text:
                            continue
                        score = float(scores[index]) if index < len(scores) else 0.0
                        polygon = polygons[index] if index < len(polygons) else None
                        bbox = None
                        if polygon is not None:
                            points = list(polygon)
                            xs = [float(p[0]) for p in points]
                            ys = [float(p[1]) for p in points]
                            bbox = BBox(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys))
                        evidence_id = stable_id(
                            "ev", request.document.id, asset.id, "ocr", result_index, index, text
                        )
                        block = TextBlock(
                            id=stable_id("block", evidence_id),
                            text=text,
                            page_number=asset.page_number,
                            bbox=bbox,
                            evidence_id=evidence_id,
                            modality=Modality.OCR,
                            source_media_asset_id=asset.id,
                            confidence=score,
                        )
                        ref = EvidenceRef(
                            id=evidence_id,
                            kind=EvidenceKind.VISUAL_REGION,
                            document_id=request.document.id,
                            source_hash=asset.blob_hash or request.document.source_hash,
                            modality=Modality.OCR,
                            page_number=asset.page_number,
                            bbox=bbox,
                            media_asset_id=asset.id,
                            model_name=self.model,
                            coordinate_space=CoordinateSpace.IMAGE_PIXELS,
                            canvas_width=asset.width,
                            canvas_height=asset.height,
                            localization_level=LocalizationLevel.REGION
                            if bbox
                            else LocalizationLevel.ASSET,
                        )
                        blocks.append(block)
                        evidence.append(ref)
                        if score < 0.5:
                            warnings.append(
                                f"low_confidence_ocr:block={block.id}:score={score:.3f}"
                            )
            except ExecutionPaused:
                raise
            except Exception as exc:
                warnings.append(f"ocr_failed:asset={asset.id}:{type(exc).__name__}:{exc}")
        return OCRResult(text_blocks=blocks, evidence=evidence, warnings=warnings)

    async def recognize(self, request: OCRRequest) -> OCRResult:
        return await asyncio.to_thread(self._recognize_sync, request)
