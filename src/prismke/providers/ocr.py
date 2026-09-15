"""Disabled, mock, and PaddleOCR implementations."""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any

from prismke.core.ids import stable_id
from prismke.domain import (
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
        self.device, self.lang, self.model = device, lang, model
        self._engine: Any = None

    def fingerprint(self) -> str:
        return stable_id("provider", "paddleocr", self.device, self.lang, self.model, "v1")

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                paddleocr = import_module("paddleocr")
            except ImportError as exc:
                raise RuntimeError("PaddleOCR is not installed; run 'uv sync --extra ocr'") from exc
            self._engine = paddleocr.PaddleOCR(
                lang=self.lang,
                ocr_version=self.model,
                device=self.device,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
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
        engine = self._get_engine()
        blocks: list[TextBlock] = []
        evidence: list[EvidenceRef] = []
        warnings: list[str] = []
        for asset in request.document.media_assets:
            if not (asset.requires_ocr or asset.origin == "source_image"):
                continue
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
            except Exception as exc:
                warnings.append(f"ocr_failed:asset={asset.id}:{type(exc).__name__}:{exc}")
        return OCRResult(text_blocks=blocks, evidence=evidence, warnings=warnings)

    async def recognize(self, request: OCRRequest) -> OCRResult:
        return await asyncio.to_thread(self._recognize_sync, request)
