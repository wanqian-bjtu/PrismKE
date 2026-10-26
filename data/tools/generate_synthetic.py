from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pymupdf
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

from data.tools.common import (
    SYNTHETIC_ROOT,
    atomic_write,
    canonicalize_zip,
    records,
    write_json,
)

SEED = 140013
ASSET_ROOT = Path(__file__).resolve().parent / "assets"
FONT_PATH = ASSET_ROOT / "DejaVuSans.ttf"
FIXED_DOCUMENT_TIME = datetime(2026, 1, 1, tzinfo=UTC)
FIXED_TITLE = "Nebula Technology AtlasVision X1 Research Brief"
FACTS = [
    "Nebula Technology developed AtlasVision X1 in 2026.",
    "Lead researcher Lin Yue works for Nebula Technology.",
    "AtlasVision X1 uses three blue optical sensors and one amber status light.",
    "The pilot deployment took place at Harbor Laboratory in Shanghai.",
    "Measured inspection accuracy was 94.2 percent across 500 synthetic samples.",
]


def _base_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Bundled synthetic fixture font is missing: {FONT_PATH}")
    return ImageFont.truetype(str(FONT_PATH), size=size)


def _product_image(path: Path, *, jpeg: bool) -> dict[str, list[int]]:
    image = Image.new("RGB", (1200, 800), "#F4F7FB")
    draw = ImageDraw.Draw(image)
    title_font = _base_font(54)
    label_font = _base_font(34)
    small_font = _base_font(26)
    draw.rounded_rectangle(
        (110, 120, 1090, 690),
        radius=32,
        fill="#FFFFFF",
        outline="#153B73",
        width=6,
    )
    draw.text(
        (150, 50),
        "AtlasVision X1 - Synthetic Product Image",
        fill="#10233F",
        font=title_font,
    )
    draw.rounded_rectangle(
        (240, 230, 960, 570),
        radius=28,
        fill="#DCEBFF",
        outline="#245EAA",
        width=7,
    )
    sensor_boxes: dict[str, list[int]] = {}
    for index, x in enumerate((360, 560, 760), start=1):
        box = (x, 320, x + 92, 412)
        draw.ellipse(box, fill="#1769C2", outline="#0C2E5D", width=6)
        draw.text((x + 31, 424), str(index), fill="#0C2E5D", font=small_font)
        sensor_boxes[f"blue_sensor_{index}"] = list(box)
    light_box = (845, 490, 905, 550)
    draw.ellipse(light_box, fill="#F2A900", outline="#9A5B00", width=5)
    draw.text((280, 160), "NEBULA TECHNOLOGY", fill="#153B73", font=label_font)
    draw.text((270, 610), "3 blue sensors | 1 amber status light", fill="#33445C", font=small_font)
    draw.text(
        (26, 750),
        "FICTIONAL TEST DATA - NOT A REAL PRODUCT",
        fill="#8A1C1C",
        font=small_font,
    )
    image.info.clear()
    path.parent.mkdir(parents=True, exist_ok=True)
    if jpeg:
        image.save(path, format="JPEG", quality=92, optimize=False, progressive=False, exif=b"")
    else:
        # Disable DEFLATE compression so libz/Pillow implementation differences do not
        # change the fixture bytes between Windows and Linux.
        image.save(path, format="PNG", optimize=False, compress_level=0)
    return {**sensor_boxes, "amber_light": list(light_box), "product": [240, 230, 960, 570]}


def _insert_text(
    page: pymupdf.Page,
    rect: pymupdf.Rect,
    text: str,
    size: float,
    *,
    fontname: str = "helv",
) -> None:
    spare = page.insert_textbox(
        rect,
        text,
        fontsize=size,
        fontname=fontname,
        color=(0.07, 0.14, 0.25),
        lineheight=1.25,
    )
    if spare < 0:
        raise ValueError(f"Synthetic PDF text overflowed by {-spare:.2f} points")


def _save_pdf(document: pymupdf.Document, path: Path) -> None:
    document.set_metadata({})
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(
        path,
        garbage=4,
        clean=True,
        deflate=True,
        deflate_images=True,
        no_new_id=True,
        preserve_metadata=False,
        reproducible=True,
    )
    document.close()


def _native_pdf(path: Path) -> dict[str, Any]:
    document = pymupdf.open()
    page = document.new_page(width=595, height=842)
    _insert_text(page, pymupdf.Rect(54, 62, 541, 150), FIXED_TITLE, 18)
    _insert_text(
        page,
        pymupdf.Rect(54, 155, 541, 185),
        "星河科技虚构研究简报",
        11,
        fontname="china-s",
    )
    _insert_text(
        page,
        pymupdf.Rect(54, 188, 541, 220),
        "FICTIONAL SYNTHETIC RESEARCH BRIEF",
        11,
    )
    blocks = []
    y = 260
    for index, fact in enumerate(FACTS, start=1):
        rect = pymupdf.Rect(70, y, 525, y + 62)
        _insert_text(page, rect, f"{index}. {fact}", 11)
        blocks.append({"fact": fact, "page": 1, "bbox": list(rect)})
        y += 78
    _insert_text(
        page,
        pymupdf.Rect(54, 760, 541, 800),
        "Generated test material. No real person, company, product, or measurement is represented.",
        8,
    )
    _save_pdf(document, path)
    return {"blocks": blocks, "expected_parser": "pymupdf"}


def _scanned_pdf(path: Path) -> dict[str, Any]:
    source = pymupdf.open()
    page = source.new_page(width=595, height=842)
    _insert_text(
        page,
        pymupdf.Rect(50, 70, 545, 120),
        "中英文扫描测试",
        22,
        fontname="china-s",
    )
    _insert_text(page, pymupdf.Rect(50, 125, 545, 170), "Bilingual Scan Test", 22)
    chinese = (
        "星河科技于 2026 年开发 AtlasVision X1。\n"
        "设备包含三个蓝色光学传感器和一个琥珀色状态灯。"
    )
    english = (
        "Nebula Technology developed AtlasVision X1 in 2026.\n"
        "The device contains three blue optical sensors and one amber status light."
    )
    _insert_text(
        page,
        pymupdf.Rect(70, 205, 525, 330),
        chinese,
        17,
        fontname="china-s",
    )
    _insert_text(page, pymupdf.Rect(70, 365, 525, 500), english, 17)
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
    image_bytes = pixmap.tobytes("png")
    source.close()

    scanned = pymupdf.open()
    target = scanned.new_page(width=595, height=842)
    target.insert_image(target.rect, stream=image_bytes)
    _save_pdf(scanned, path)
    return {
        "page": 1,
        "whole_page_bbox": [0, 0, 595, 842],
        "expected_parser": "mineru",
        "native_text_characters": 0,
    }


def _complex_pdf(path: Path, image_path: Path) -> dict[str, Any]:
    document = pymupdf.open()
    page1 = document.new_page(width=842, height=595)
    _insert_text(page1, pymupdf.Rect(38, 28, 804, 64), "AtlasVision X1 Multimodal Evaluation", 18)
    left = pymupdf.Rect(42, 82, 395, 500)
    _insert_text(
        page1,
        left,
        "1 Research context\n\n"
        "Nebula Technology evaluated AtlasVision X1 at Harbor Laboratory. "
        "The fictional pilot used 500 synthetic samples and reported 94.2 percent accuracy.\n\n"
        "2 Evidence policy\n\n"
        "Every extracted statement must retain page and bounding-box evidence. "
        "Visual-only quantities require human review before graph submission.",
        10,
    )
    page1.insert_image(pymupdf.Rect(470, 105, 775, 308), filename=str(image_path))
    _insert_text(page1, pymupdf.Rect(470, 315, 775, 345), "Figure 1. AtlasVision X1", 9)
    chart = pymupdf.Rect(480, 370, 760, 520)
    page1.draw_rect(chart, color=(0.2, 0.3, 0.45), width=1)
    values = [("Text", 88, "#3478C9"), ("OCR", 91, "#52A675"), ("VLM", 94.2, "#E3A72F")]
    for index, (label, value, color) in enumerate(values):
        x0 = 520 + index * 78
        height = value * 1.05
        rgb = tuple(int(color[offset : offset + 2], 16) / 255 for offset in (1, 3, 5))
        page1.draw_rect(
            pymupdf.Rect(x0, 500 - height, x0 + 45, 500),
            fill=rgb,
            color=rgb,
        )
        page1.insert_text((x0, 516), label, fontsize=8, fontname="helv")
        page1.insert_text((x0, 492 - height), str(value), fontsize=8, fontname="helv")

    page2 = document.new_page(width=595, height=842)
    _insert_text(page2, pymupdf.Rect(45, 42, 550, 84), "Evaluation Table and Formula", 17)
    columns = [45, 235, 355, 550]
    rows = [120, 165, 210, 255, 300]
    for x in columns:
        page2.draw_line((x, rows[0]), (x, rows[-1]), color=(0.3, 0.35, 0.4), width=1)
    for y in rows:
        page2.draw_line((columns[0], y), (columns[-1], y), color=(0.3, 0.35, 0.4), width=1)
    cells = [
        (55, 148, "Modality"),
        (245, 148, "Samples"),
        (365, 148, "Accuracy"),
        (55, 193, "Native text"),
        (245, 193, "500"),
        (365, 193, "88.0%"),
        (55, 238, "OCR"),
        (245, 238, "500"),
        (365, 238, "91.0%"),
        (55, 283, "VLM"),
        (245, 283, "500"),
        (365, 283, "94.2%"),
    ]
    for x, y, text in cells:
        page2.insert_text((x, y), text, fontsize=10, fontname="helv")
    _insert_text(
        page2,
        pymupdf.Rect(70, 360, 525, 430),
        "F1 = 2 * precision * recall / (precision + recall)",
        15,
    )
    for index in range(8):
        y = 500 + index * 18
        page2.draw_line((70, y), (525, y), color=(0.65, 0.68, 0.72), width=0.7)
    _save_pdf(document, path)
    return {
        "expected_parser": "mineru",
        "pages": 2,
        "media": ["image", "chart", "table", "formula"],
        "table_bbox": [45, 120, 550, 300],
        "formula_bbox": [70, 360, 525, 430],
    }


def _docx(path: Path, product_image: Path) -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)
    document.core_properties.title = FIXED_TITLE
    document.core_properties.author = "PrismKE synthetic fixture generator"
    document.core_properties.subject = "Fictional multimodal knowledge extraction fixture"
    document.core_properties.created = FIXED_DOCUMENT_TIME
    document.core_properties.modified = FIXED_DOCUMENT_TIME
    document.core_properties.last_printed = FIXED_DOCUMENT_TIME
    for style_name in ("Title", "Heading 1", "Heading 2"):
        style = document.styles[style_name]
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.name = "Arial"
        paragraph_properties = style.element.find(qn("w:pPr"))
        if paragraph_properties is not None:
            border = paragraph_properties.find(qn("w:pBdr"))
            if border is not None:
                paragraph_properties.remove(border)
    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(FIXED_TITLE)
    run.font.name = "Arial"
    run.font.size = Pt(21)
    run.font.color.rgb = RGBColor(0, 0, 0)
    intro = document.add_paragraph()
    intro.alignment = WD_ALIGN_PARAGRAPH.CENTER
    intro.add_run("FICTIONAL TEST DATA - no real organization, person, or product").bold = True
    document.add_heading("Research summary", level=1)
    for fact in FACTS:
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.add_run(fact)
    document.add_picture(str(product_image), width=Inches(5.7))
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption = document.add_paragraph("Figure 1  AtlasVision X1 synthetic product image")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table = document.add_table(rows=4, cols=3)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "Modality"
    table.rows[0].cells[1].text = "Samples"
    table.rows[0].cells[2].text = "Accuracy"
    for row, values in zip(
        table.rows[1:],
        [("Native text", "500", "88.0%"), ("OCR", "500", "91.0%"), ("VLM", "500", "94.2%")],
        strict=True,
    ):
        for cell, value in zip(row.cells, values, strict=True):
            cell.text = value
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            properties = cell._tc.get_or_add_tcPr()
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), "DCEBFF" if row_index == 0 else "FFFFFF")
            properties.append(shading)
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for cell_run in paragraph.runs:
                    cell_run.font.size = Pt(10)
                    if row_index == 0:
                        cell_run.bold = True
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("PrismKE synthetic fixture | seed 140013")
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(path)
    canonicalize_zip(path)


def _text_variants(root: Path) -> None:
    plain = f"{FIXED_TITLE}\n\n" + "\n".join(f"- {fact}" for fact in FACTS)
    atomic_write(root / "native" / "research-brief.txt", (plain + "\n").encode())
    markdown = (
        f"# {FIXED_TITLE}\n\n"
        "> Fictional test data.\n\n"
        "## Facts\n\n"
        + "\n".join(f"- {fact}" for fact in FACTS)
        + "\n"
    )
    atomic_write(root / "native" / "research-brief.md", markdown.encode())
    items = "".join(f"<li>{fact}</li>" for fact in FACTS)
    html = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{FIXED_TITLE}</title></head><body><main><h1>{FIXED_TITLE}</h1>"
        f"<p><strong>Fictional test data.</strong></p><ul>{items}</ul></main></body></html>\n"
    )
    atomic_write(root / "native" / "research-brief.html", html.encode())


def _nested_json(path: Path) -> None:
    payload = {
        "dataset": {"name": "PrismKE synthetic multimodal fixture", "fictional": True},
        "organization": {
            "name": "Nebula Technology",
            "name_zh": "星河科技",
            "founded": 2021,
            "location": {"city": "Shanghai", "site": "Harbor Laboratory"},
            "researchers": [
                {"name": "Lin Yue", "role": "lead researcher"},
                {"name": "Maya Chen", "role": "validation engineer"},
            ],
        },
        "products": [
            {
                "name": "AtlasVision X1",
                "year": 2026,
                "sensors": [
                    {"color": "blue", "type": "optical", "count": 3},
                    {"color": "amber", "type": "status light", "count": 1},
                ],
                "metrics": {"samples": 500, "accuracy": 0.942, "notes": None},
            }
        ],
        "events": [
            {
                "type": "pilot_deployment",
                "participants": ["AtlasVision X1", "Harbor Laboratory"],
                "date": "2026-05-14",
            }
        ],
    }
    write_json(path, payload)


def _expected(root: Path, image_regions: dict[str, list[int]], locations: dict[str, Any]) -> None:
    expected = {
        "seed": SEED,
        "fictional": True,
        "entities": [
            {"name": "Nebula Technology", "type": "Organization"},
            {"name": "AtlasVision X1", "type": "Product"},
            {"name": "Lin Yue", "type": "Person"},
            {"name": "Harbor Laboratory", "type": "Facility"},
            {"name": "Shanghai", "type": "Location"},
        ],
        "relations": [
            ["AtlasVision X1", "developed_by", "Nebula Technology"],
            ["Lin Yue", "works_for", "Nebula Technology"],
            ["AtlasVision X1", "deployed_at", "Harbor Laboratory"],
            ["Harbor Laboratory", "located_in", "Shanghai"],
        ],
        "visual_assertions_requiring_review": [
            {"subject": "AtlasVision X1", "predicate": "blue_sensor_count", "value": 3},
            {"subject": "AtlasVision X1", "predicate": "status_light_color", "value": "amber"},
        ],
        "image_regions": image_regions,
        "locations": locations,
        "json_paths": [
            "$.organization.name",
            "$.organization.researchers[0].name",
            "$.products[0].metrics.accuracy",
            "$.products[0].metrics.notes",
            "$.events[0].participants[1]",
        ],
        "graph_policy": {
            "text_supported_relations_may_enter_commit": True,
            "visual_only_assertions_require_review": True,
        },
    }
    write_json(root / "expected" / "expected-results.json", expected)


def generate(output: Path) -> dict[str, Any]:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prismke-synthetic-", dir=output.parent) as temporary:
        staging = Path(temporary) / "synthetic"
        _text_variants(staging)
        png_path = staging / "images" / "atlasvision-x1.png"
        jpeg_path = staging / "images" / "atlasvision-x1.jpg"
        image_regions = _product_image(png_path, jpeg=False)
        _product_image(jpeg_path, jpeg=True)
        locations: dict[str, Any] = {}
        locations["native_pdf"] = _native_pdf(staging / "native" / "research-brief.pdf")
        locations["scanned_pdf"] = _scanned_pdf(staging / "scanned" / "bilingual-scan.pdf")
        locations["complex_pdf"] = _complex_pdf(
            staging / "complex" / "multimodal-evaluation.pdf", png_path
        )
        _docx(staging / "native" / "research-brief.docx", png_path)
        _nested_json(staging / "json" / "nested-research-data.json")
        _expected(staging, image_regions, locations)
        generated = [
            path
            for path in staging.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        ]
        manifest = {
            "schema_version": 1,
            "generator_seed": SEED,
            "fictional": True,
            "files": records(generated, staging),
        }
        write_json(staging / "manifest.json", manifest)
        if output.exists():
            shutil.rmtree(output)
        shutil.move(str(staging), output)
    return json.loads((output / "manifest.json").read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate deterministic PrismKE synthetic fixtures"
    )
    parser.add_argument("--output", type=Path, default=SYNTHETIC_ROOT)
    arguments = parser.parse_args()
    manifest = generate(arguments.output)
    print(f"Generated {len(manifest['files'])} synthetic files in {arguments.output}")


if __name__ == "__main__":
    main()
