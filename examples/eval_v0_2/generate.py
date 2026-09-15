"""Generate the copyright-free PrismKE v0.2 multimodal evaluation fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _card(path: Path, heading: str, lines: list[str], *, fmt: str = "PNG") -> None:
    image = Image.new("RGB", (960, 540), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 920, 500), outline="#1f4b99", width=5)
    draw.text((80, 80), heading, fill="#15233d", font=_font(42))
    for index, line in enumerate(lines):
        draw.text((100, 180 + index * 80), line, fill="#222222", font=_font(32))
    image.save(path, format=fmt, quality=95)


def _scan_pdf(path: Path, lines: list[str], *, chinese: bool = False) -> None:
    source = pymupdf.open()
    page = source.new_page(width=960, height=540)
    font_name = "china-s" if chinese else "helv"
    page.insert_text((70, 100), lines[0], fontsize=34, fontname=font_name)
    for index, line in enumerate(lines[1:]):
        page.insert_text((90, 200 + index * 75), line, fontsize=28, fontname=font_name)
    pixmap = page.get_pixmap(dpi=160, alpha=False)
    source.close()
    scanned = pymupdf.open()
    target = scanned.new_page(width=960, height=540)
    target.insert_image(target.rect, stream=pixmap.tobytes("jpg", jpg_quality=85))
    scanned.save(path, garbage=4, deflate=True)
    scanned.close()


def _mixed_pdf(path: Path, text: str, image_path: Path, *, image_only: bool = False) -> None:
    document = pymupdf.open()
    page = document.new_page(width=960, height=700)
    if not image_only:
        page.insert_textbox(
            pymupdf.Rect(60, 50, 900, 150),
            text,
            fontsize=22,
            fontname="helv",
        )
    page.insert_image(pymupdf.Rect(80, 180, 880, 630), filename=str(image_path))
    document.save(path, garbage=4, deflate=True)
    document.close()


def _write_text_inputs() -> None:
    (ROOT / "01_support_zh.md").write_text(
        "# 产品说明\n\nAuroraGraph 由 Northstar Labs 开发。\n\n"
        "![产品信息卡](assets/01_support.png)\n",
        encoding="utf-8",
    )
    (ROOT / "02_support_en.html").write_text(
        "<html><body><p>BeaconAI was developed by Harbor Research.</p>"
        '<figure><img src="assets/02_support.png" alt="BeaconAI product card">'
        "<figcaption>BeaconAI development record</figcaption></figure></body></html>",
        encoding="utf-8",
    )
    (ROOT / "03_conflict_zh.md").write_text(
        "# 发布说明\n\nNovaIndex 由 Northstar Labs 开发。\n\n"
        "![另一来源](assets/03_conflict.png)\n",
        encoding="utf-8",
    )
    (ROOT / "04_conflict_en.html").write_text(
        "<html><body><p>AtlasFlow was developed by Harbor Research.</p>"
        '<img src="assets/04_conflict.png" alt="conflicting developer record"></body></html>',
        encoding="utf-8",
    )
    (ROOT / "11_alias_zh.md").write_text(
        "# 机构资料\n\n北辰实验室开发了 AuroraGraph。\n",
        encoding="utf-8",
    )
    (ROOT / "12_alias_en.html").write_text(
        "<html><body><p>Northstar Laboratory developed AuroraGraph.</p></body></html>",
        encoding="utf-8",
    )


def _manifest() -> dict[str, object]:
    def claim(subject: str, relation: str, obj: str) -> dict[str, str]:
        return {"subject": subject, "relation": relation, "object": obj}

    return {
        "version": "0.2-public-1",
        "schema_path": "schema.yaml",
        "cases": [
            {
                "id": "support-zh-md",
                "input": "01_support_zh.md",
                "language": "zh",
                "scenarios": ["cross_modal_support", "region_evidence"],
                "claims": [claim("AuroraGraph", "developed_by", "Northstar Labs")],
                "expected_alignment_decisions": ["support"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "support-en-html",
                "input": "02_support_en.html",
                "language": "en",
                "scenarios": ["cross_modal_support", "html_image"],
                "claims": [claim("BeaconAI", "developed_by", "Harbor Research")],
                "expected_alignment_decisions": ["support"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "conflict-zh-md",
                "input": "03_conflict_zh.md",
                "language": "zh",
                "scenarios": ["cross_modal_conflict"],
                "claims": [
                    claim("NovaIndex", "developed_by", "Northstar Labs"),
                    claim("NovaIndex", "developed_by", "Contoso AI"),
                ],
                "expected_alignment_decisions": ["conflict"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "conflict-en-html",
                "input": "04_conflict_en.html",
                "language": "en",
                "scenarios": ["cross_modal_conflict"],
                "claims": [
                    claim("AtlasFlow", "developed_by", "Harbor Research"),
                    claim("AtlasFlow", "developed_by", "Contoso AI"),
                ],
                "expected_alignment_decisions": ["conflict"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "image-only-png",
                "input": "05_image_only.png",
                "language": "en",
                "scenarios": ["image_only", "region_evidence"],
                "claims": [claim("VisionDesk", "developed_by", "Northstar Labs")],
                "expected_alignment_decisions": ["support"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "image-only-jpeg",
                "input": "06_image_only.jpg",
                "language": "en",
                "scenarios": ["image_only"],
                "claims": [claim("ChartPilot", "developed_by", "Harbor Research")],
                "expected_alignment_decisions": ["support"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "scanned-pdf-zh",
                "input": "07_scanned_zh.pdf",
                "language": "zh",
                "scenarios": ["scanned_pdf", "ocr"],
                "claims": [claim("星图系统", "developed_by", "北辰实验室")],
                "expected_alignment_decisions": ["support"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "scanned-pdf-en",
                "input": "08_scanned_en.pdf",
                "language": "en",
                "scenarios": ["scanned_pdf", "ocr"],
                "claims": [claim("ScanGraph", "developed_by", "Harbor Research")],
                "expected_alignment_decisions": ["support"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "pdf-text-image-duplicate",
                "input": "09_text_image.pdf",
                "language": "en",
                "scenarios": ["pdf_text_ocr_duplicate", "cross_modal_support"],
                "claims": [claim("EvidenceHub", "developed_by", "Northstar Labs")],
                "expected_alignment_decisions": ["support"],
                "expected_localization_levels": ["region"],
            },
            {
                "id": "pdf-image-coarse-fallback",
                "input": "10_poster.pdf",
                "language": "en",
                "scenarios": ["whole_image_or_region_evidence"],
                "claims": [claim("PosterKG", "developed_by", "Contoso AI")],
                "expected_alignment_decisions": ["independent"],
                "expected_localization_levels": [],
            },
            {
                "id": "alias-zh",
                "input": "11_alias_zh.md",
                "language": "zh",
                "scenarios": ["cross_document_alias"],
                "claims": [claim("AuroraGraph", "developed_by", "Northstar Labs")],
                "expected_alignment_decisions": ["independent"],
                "expected_localization_levels": ["text_span"],
            },
            {
                "id": "alias-en",
                "input": "12_alias_en.html",
                "language": "en",
                "scenarios": ["cross_document_alias"],
                "claims": [claim("AuroraGraph", "developed_by", "Northstar Labs")],
                "expected_alignment_decisions": ["independent"],
                "expected_localization_levels": ["text_span"],
            },
        ],
    }


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    _card(ASSETS / "01_support.png", "AuroraGraph", ["Developed by", "Northstar Labs"])
    _card(ASSETS / "02_support.png", "BeaconAI", ["Developed by", "Harbor Research"])
    _card(ASSETS / "03_conflict.png", "NovaIndex", ["Developed by", "Contoso AI"])
    _card(ASSETS / "04_conflict.png", "AtlasFlow", ["Developed by", "Contoso AI"])
    _card(ROOT / "05_image_only.png", "VisionDesk", ["Developed by", "Northstar Labs"])
    _card(
        ROOT / "06_image_only.jpg",
        "ChartPilot",
        ["Developed by", "Harbor Research"],
        fmt="JPEG",
    )
    _card(ASSETS / "08_scan.png", "ScanGraph", ["Developed by", "Harbor Research"])
    _card(ASSETS / "09_duplicate.png", "EvidenceHub", ["Developed by", "Northstar Labs"])
    _card(ASSETS / "10_poster.png", "PosterKG", ["Developed by", "Contoso AI"])
    _scan_pdf(
        ROOT / "07_scanned_zh.pdf",
        ["星图系统", "开发机构：北辰实验室"],
        chinese=True,
    )
    _mixed_pdf(ROOT / "08_scanned_en.pdf", "", ASSETS / "08_scan.png", image_only=True)
    _mixed_pdf(
        ROOT / "09_text_image.pdf",
        "EvidenceHub was developed by Northstar Labs.",
        ASSETS / "09_duplicate.png",
    )
    _mixed_pdf(ROOT / "10_poster.pdf", "", ASSETS / "10_poster.png", image_only=True)
    _write_text_inputs()
    (ROOT / "manifest.json").write_text(
        json.dumps(_manifest(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
