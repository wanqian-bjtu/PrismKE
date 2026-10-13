"""Cheap, read-only PDF complexity inspection for parser routing."""

from __future__ import annotations

from math import ceil
from pathlib import Path
from typing import Any

import pymupdf

from src.core.ids import canonical_hash
from src.domain import PDFComplexityReport, PDFComplexityThresholds


def _required(total: int, ratio: float, minimum: int) -> int:
    return max(minimum, ceil(total * ratio))


def _unstable_multicolumn(page: Any, blocks: list[tuple[float, float, float, float]]) -> bool:
    if len(blocks) < 4:
        return False
    width = float(page.rect.width)
    midpoint = width / 2
    left = [item for item in blocks if (item[0] + item[2]) / 2 < midpoint]
    right = [item for item in blocks if (item[0] + item[2]) / 2 >= midpoint]
    if len(left) < 2 or len(right) < 2:
        return False
    overlap = min(max(item[3] for item in left), max(item[3] for item in right)) - max(
        min(item[1] for item in left), min(item[1] for item in right)
    )
    if overlap <= 0:
        return False
    sides = ["left" if (item[0] + item[2]) / 2 < midpoint else "right" for item in blocks]
    switches = sum(current != previous for previous, current in zip(sides, sides[1:], strict=False))
    return switches >= 2


def inspect_pdf(path: Path, thresholds: PDFComplexityThresholds) -> PDFComplexityReport:
    no_text: list[int] = []
    short_text: list[int] = []
    tables: list[int] = []
    drawings: list[int] = []
    multicolumn: list[int] = []
    native_characters = 0
    with pymupdf.open(path) as pdf:  # type: ignore[no-untyped-call]
        total = len(pdf)
        if total < 1:
            raise ValueError("PDF has no pages")
        for page_index, page in enumerate(pdf):
            page_number = page_index + 1
            text = page.get_text("text").strip()
            native_characters += len(text)
            if not text:
                no_text.append(page_number)
            if len(text) < thresholds.short_text_chars:
                short_text.append(page_number)
            try:
                if len(page.find_tables().tables) > 0:
                    tables.append(page_number)
            except Exception:
                pass
            if len(page.get_drawings()) >= thresholds.drawing_count:
                drawings.append(page_number)
            raw_blocks = page.get_text("blocks")
            boxes: list[tuple[float, float, float, float]] = [
                (float(item[0]), float(item[1]), float(item[2]), float(item[3]))
                for item in raw_blocks
                if item[4].strip()
            ]
            if _unstable_multicolumn(page, boxes):
                multicolumn.append(page_number)
    reasons: list[str] = []
    if len(no_text) >= _required(total, thresholds.no_text_ratio, 1):
        reasons.append("NO_NATIVE_TEXT_RATIO")
    if len(short_text) >= _required(total, thresholds.short_text_ratio, 2):
        reasons.append("LOW_NATIVE_TEXT_RATIO")
    if len(tables) >= _required(total, thresholds.table_ratio, 1):
        reasons.append("TABLE_DENSE")
    if len(drawings) >= _required(total, thresholds.drawing_ratio, 1):
        reasons.append("DRAWING_DENSE")
    if len(multicolumn) >= _required(total, thresholds.multicolumn_ratio, 1):
        reasons.append("MULTICOLUMN_ORDER_UNSTABLE")
    return PDFComplexityReport(
        total_pages=total,
        no_native_text_pages=no_text,
        short_text_pages=short_text,
        table_candidate_pages=tables,
        drawing_dense_pages=drawings,
        unstable_multicolumn_pages=multicolumn,
        native_text_characters=native_characters,
        thresholds=thresholds,
        reason_codes=reasons,
    )


def complexity_fingerprint(thresholds: PDFComplexityThresholds) -> str:
    return canonical_hash(thresholds.model_dump(mode="json"))
