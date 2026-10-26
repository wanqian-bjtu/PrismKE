from __future__ import annotations

import argparse
import html
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

from data.tools.common import SYNTHETIC_ROOT, atomic_write, canonicalize_zip, records, write_json

# Long prose fixtures remain readable as complete Python string literals.
# ruff: noqa: E501

SEED = 140013
FONT_PATH = Path(__file__).resolve().parent / "assets" / "DejaVuSans.ttf"
FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)
TITLE = "AtlasVision X1 Pilot Evaluation Report"
SUBTITLE = "Automated inspection at Harbor Laboratory"

SECTIONS: list[tuple[str, list[str]]] = [
    (
        "Executive summary",
        [
            "Nebula Technology conducted a six-week pilot of the AtlasVision X1 inspection system at Harbor Laboratory in Shanghai. The study examined whether a compact multimodal device could identify surface defects while preserving enough evidence for a human reviewer to reproduce each finding. The evaluation covered 500 fictional manufactured samples and compared a native-text baseline, an OCR-assisted workflow, and a vision-language workflow.",
            "The vision-language workflow achieved an inspection accuracy of 94.2 percent, compared with 91.0 percent for OCR-assisted review and 88.0 percent for the native-text baseline. The result supports continued prototyping, but it does not justify autonomous acceptance of safety-critical parts. Every visual-only quantity, identity claim, and spatial relation remains subject to human review.",
        ],
    ),
    (
        "Operational context",
        [
            "Harbor Laboratory operates a small validation line used to test optical sensors under controlled lighting. Before the pilot, technicians recorded observations in free-text notes and attached photographs to separate folders. This process made it difficult to connect a reported defect to the exact image region, device configuration, and inspection step that produced the observation.",
            "AtlasVision X1 was installed above the second conveyor station on 14 May 2026. The device uses three blue optical sensors to capture overlapping views and one amber status light to show that a sample is awaiting review. Lead researcher Lin Yue coordinated the pilot with validation engineer Maya Chen and the laboratory operations team.",
        ],
    ),
    (
        "System design and evidence capture",
        [
            "Each sample passed through an illuminated inspection zone before reaching the manual review desk. The device produced a product image, a cropped defect region, and a short observation record. The record included the sample identifier, capture time, sensor channel, predicted defect class, confidence score, and a reference to the original image rather than an embedded copy.",
            "The pilot treated the original image as evidence and the extracted statement as a candidate assertion. A candidate could enter the knowledge graph only after its source hash, page or image coordinates, schema type, and review state were validated. This separation allowed the team to correct a conclusion without rewriting the source evidence or losing the earlier decision history.",
        ],
    ),
    (
        "Evaluation method",
        [
            "The team created 500 synthetic samples distributed across scratches, coating gaps, alignment errors, and control cases with no defect. Samples were assigned to five balanced batches and evaluated under the same lighting and conveyor speed. Ground-truth labels were agreed by two reviewers before model output was examined, and disagreements were resolved in a separate adjudication pass.",
            "Three processing modes were compared. The native-text baseline used only the technician note, the OCR-assisted mode added text recovered from labels and screens, and the vision-language mode examined the image together with the note. Accuracy was calculated over the final defect classification. Region-level evidence was checked to confirm that each observation could be traced to the relevant part of the image.",
        ],
    ),
    (
        "Results and interpretation",
        [
            "The native-text baseline classified 440 of 500 samples correctly. OCR-assisted review increased the correct total to 455, mainly because printed batch labels and equipment messages became available to the extraction process. The vision-language workflow classified 471 samples correctly and was strongest on alignment errors that required comparison between the sample edge and a fixture.",
            "Performance gains were not uniform. Reflections on glossy surfaces produced several false positives, and small coating gaps near the image boundary were occasionally missed. The team therefore recommended retaining region previews and review tasks for high-risk observations. The reported 94.2 percent accuracy describes this fictional pilot only and must not be interpreted as a production benchmark.",
        ],
    ),
    (
        "Governance limitations and conclusion",
        [
            "This evaluation used synthetic samples, a controlled laboratory layout, and a single device configuration. It did not test long-term drift, adversarial inputs, worker privacy, or performance across independent sites. The media files and measurements in this report are fictional and exist only to exercise document parsing, evidence linking, entity resolution, visual review, and graph commit controls.",
            "The pilot shows how multimodal evidence can improve defect classification while remaining auditable. Nebula Technology will use the findings to refine the prototype and test additional lighting conditions. Any future deployment should preserve the same rule used here: models may propose knowledge, but deterministic validation and accountable human review decide what becomes part of the governed graph.",
        ],
    ),
]
RESULTS = [
    ("Native text", 500, 440, "88.0%"),
    ("OCR assisted", 500, 455, "91.0%"),
    ("Vision language", 500, 471, "94.2%"),
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Bundled font is missing: {FONT_PATH}")
    return ImageFont.truetype(str(FONT_PATH), size=size)


def _save_image(image: Image.Image, path: Path, *, jpeg: bool) -> None:
    image.info.clear()
    path.parent.mkdir(parents=True, exist_ok=True)
    if jpeg:
        image.save(path, format="JPEG", quality=92, optimize=False, progressive=False, exif=b"")
    else:
        image.save(path, format="PNG", optimize=False, compress_level=0)


def _product_image(path: Path, *, jpeg: bool) -> dict[str, list[int]]:
    image = Image.new("RGB", (1200, 800), "#EEF3F8")
    draw = ImageDraw.Draw(image)
    draw.text((90, 50), "AtlasVision X1 inspection unit", fill="#10233F", font=_font(48))
    draw.text((92, 112), "Fictional equipment reference image", fill="#52647A", font=_font(23))
    draw.rounded_rectangle((120, 180, 1080, 680), 34, "#FFFFFF", "#153B73", 7)
    draw.rounded_rectangle((255, 255, 945, 565), 28, "#DCEBFF", "#245EAA", 7)
    draw.rectangle((300, 285, 900, 350), fill="#153B73")
    draw.text((468, 300), "ATLASVISION X1", fill="#FFFFFF", font=_font(30))
    regions: dict[str, list[int]] = {}
    for index, x in enumerate((370, 555, 740), 1):
        box = (x, 390, x + 90, 480)
        draw.ellipse(box, fill="#1769C2", outline="#0C2E5D", width=6)
        draw.text((x + 26, 492), f"S{index}", fill="#0C2E5D", font=_font(23))
        regions[f"blue_sensor_{index}"] = list(box)
    light = (840, 492, 904, 556)
    draw.ellipse(light, fill="#F2A900", outline="#9A5B00", width=5)
    draw.text((718, 588), "review status light", fill="#6A4A00", font=_font(21))
    draw.text((160, 605), "three overlapping optical views", fill="#33445C", font=_font(21))
    draw.text((92, 730), "NEBULA TECHNOLOGY | PILOT CONFIGURATION", fill="#153B73", font=_font(21))
    _save_image(image, path, jpeg=jpeg)
    return {**regions, "amber_light": list(light), "product": [255, 255, 945, 565]}


def _deployment_image(path: Path) -> dict[str, list[int]]:
    image = Image.new("RGB", (1400, 850), "#F5F7FA")
    draw = ImageDraw.Draw(image)
    draw.text((70, 45), "Harbor Laboratory pilot layout", fill="#10233F", font=_font(42))
    draw.text(
        (72, 102), "Material flow and evidence capture points", fill="#52647A", font=_font(20)
    )
    draw.rounded_rectangle((70, 165, 1330, 760), 26, "#FFFFFF", "#9AA8B8", 4)
    conveyor = (150, 375, 1210, 530)
    draw.rounded_rectangle(conveyor, 22, "#D9E0E8", "#66788D", 5)
    for x in range(190, 1180, 95):
        draw.ellipse((x, 420, x + 48, 468), fill="#AAB6C3", outline="#66788D", width=3)
    boxes = {
        "sample_intake": (120, 235, 350, 325),
        "inspection_station": (485, 210, 820, 340),
        "human_review_desk": (925, 210, 1245, 340),
        "camera_region": (560, 355, 750, 555),
    }
    styles = [
        ("sample_intake", "#E8F1FC", "Sample intake"),
        ("inspection_station", "#DDEFE5", "AtlasVision X1 station"),
        ("human_review_desk", "#FFF0D2", "Human review desk"),
    ]
    for key, fill, label in styles:
        box = boxes[key]
        draw.rounded_rectangle(box, 18, fill, "#40546B", 4)
        draw.text((box[0] + 20, box[1] + 30), label, fill="#20344D", font=_font(24))
    camera = boxes["camera_region"]
    draw.rounded_rectangle(camera, 20, "#CFE2FA", "#1769C2", 6)
    draw.text((588, 390), "CAMERA", fill="#0C2E5D", font=_font(24))
    draw.text((584, 455), "region image", fill="#0C2E5D", font=_font(20))
    for start, end, color in [
        ((350, 280), (485, 280), "#245EAA"),
        ((820, 280), (925, 280), "#D08A00"),
    ]:
        draw.line((*start, *end), fill=color, width=5)
    draw.text((140, 645), "1  Register sample", fill="#33445C", font=_font(20))
    draw.text((500, 645), "2  Capture image and bbox", fill="#33445C", font=_font(20))
    draw.text((930, 645), "3  Confirm or reject", fill="#33445C", font=_font(20))
    draw.text((72, 790), "FICTIONAL LABORATORY LAYOUT", fill="#8A1C1C", font=_font(20))
    _save_image(image, path, jpeg=True)
    return {key: list(value) for key, value in boxes.items()} | {"conveyor": list(conveyor)}


def _chart(path: Path) -> dict[str, list[int]]:
    image = Image.new("RGB", (1400, 850), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.text((70, 45), "Inspection accuracy by processing mode", fill="#10233F", font=_font(42))
    draw.text((72, 102), "500 fictional samples per mode", fill="#52647A", font=_font(20))
    left, top, right, bottom = 150, 190, 1300, 700
    draw.line((left, top, left, bottom), fill="#40546B", width=4)
    draw.line((left, bottom, right, bottom), fill="#40546B", width=4)
    for value in range(0, 101, 20):
        y = bottom - int(value / 100 * (bottom - top))
        draw.line((left, y, right, y), fill="#D9E0E8", width=2)
        draw.text((80, y - 13), f"{value}%", fill="#52647A", font=_font(20))
    regions: dict[str, list[int]] = {}
    for index, ((mode, _, _, accuracy), color) in enumerate(
        zip(RESULTS, ("#3478C9", "#52A675", "#E3A72F"), strict=True)
    ):
        value = float(accuracy.rstrip("%"))
        x0, x1 = 255 + index * 345, 425 + index * 345
        y0 = bottom - int(value / 100 * (bottom - top))
        draw.rectangle((x0, y0, x1, bottom), fill=color, outline="#20344D", width=3)
        draw.text((x0 + 38, y0 - 42), accuracy, fill="#10233F", font=_font(25))
        draw.text((x0 - 10, bottom + 25), mode, fill="#20344D", font=_font(20))
        regions[mode.lower().replace(" ", "_")] = [x0, y0, x1, bottom]
    draw.text(
        (70, 795),
        "Higher values indicate more correct final classifications.",
        fill="#52647A",
        font=_font(20),
    )
    _save_image(image, path, jpeg=True)
    return regions


def _insert(
    page: pymupdf.Page,
    rect: pymupdf.Rect,
    text: str,
    size: float,
    *,
    font: str = "helv",
    align: int = 0,
) -> None:
    spare = page.insert_textbox(
        rect,
        text,
        fontsize=size,
        fontname=font,
        color=(0.07, 0.14, 0.25),
        lineheight=1.28,
        align=align,
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


def _native_pdf(path: Path, product: Path) -> dict[str, Any]:
    document = pymupdf.open()
    blocks: list[dict[str, Any]] = []
    first = document.new_page(width=595, height=842)
    _insert(first, pymupdf.Rect(54, 55, 541, 95), TITLE, 20, align=1)
    _insert(first, pymupdf.Rect(54, 100, 541, 130), SUBTITLE, 12, align=1)
    first.insert_image(pymupdf.Rect(110, 155, 485, 405), filename=str(product))
    _insert(
        first,
        pymupdf.Rect(80, 412, 515, 435),
        "Figure 1. AtlasVision X1 pilot configuration",
        8.5,
        align=1,
    )
    _insert(first, pymupdf.Rect(58, 455, 537, 480), SECTIONS[0][0], 14)
    rect = pymupdf.Rect(58, 490, 537, 775)
    _insert(first, rect, "\n\n".join(SECTIONS[0][1]), 9.5)
    blocks.append({"section": SECTIONS[0][0], "page": 1, "bbox": list(rect)})
    for number, indexes in enumerate(((1, 2), (3, 4), (5,)), 2):
        page = document.new_page(width=595, height=842)
        y = 55
        for index in indexes:
            heading, paragraphs = SECTIONS[index]
            _insert(page, pymupdf.Rect(58, y, 537, y + 25), heading, 14)
            y += 34
            height = 150 if len(indexes) == 2 else 360
            rect = pymupdf.Rect(58, y, 537, y + height)
            _insert(page, rect, "\n\n".join(paragraphs), 10)
            blocks.append({"section": heading, "page": number, "bbox": list(rect)})
            y += height + 34
        page.insert_text((286, 815), str(number), fontsize=8)
    _save_pdf(document, path)
    return {"blocks": blocks, "expected_parser": "pymupdf", "pages": 4}


def _scanned_pdf(path: Path) -> dict[str, Any]:
    source = pymupdf.open()
    page = source.new_page(width=595, height=842)
    _insert(
        page,
        pymupdf.Rect(55, 60, 540, 105),
        "AtlasVision X1 试点评估摘要",
        20,
        font="china-s",
        align=1,
    )
    chinese = "星河科技在上海港湾实验室开展了为期六周的虚构试点，用于评估 AtlasVision X1 在受控光照条件下识别表面缺陷的能力。设备安装在第二条传送工位上方，通过三个蓝色光学传感器采集重叠视角，并使用一个琥珀色状态灯提示样品正在等待人工复核。\n\n试验共使用五百个合成样品，覆盖划痕、涂层缺口、位置偏移和无缺陷对照。原生文本、OCR 辅助和视觉语言三种流程分别获得百分之八十八、百分之九十一和百分之九十四点二的分类准确率。视觉语言流程在需要比较样品边缘和夹具位置的任务上表现更好，但反光表面仍然造成了若干误报。\n\n本次评估要求每条结论都能回溯到原始图片、页面或图像区域。仅由视觉信息支持的数量、身份和空间关系不得自动写入知识图谱，必须先经过证据校验和人工审核。报告中的公司、人员、设备、实验室和数据均为虚构内容，仅用于多模态解析测试。"
    _insert(page, pymupdf.Rect(65, 135, 530, 715), chinese, 14, font="china-s")
    page = source.new_page(width=595, height=842)
    _insert(page, pymupdf.Rect(55, 60, 540, 105), "Pilot review memorandum", 20, align=1)
    english = "Nebula Technology completed a six-week fictional pilot of AtlasVision X1 at Harbor Laboratory. The equipment was mounted above the second conveyor station and captured three overlapping optical views of each sample. An amber status light indicated when a candidate observation was waiting for human review.\n\nFive hundred synthetic samples were divided across scratches, coating gaps, alignment errors, and no-defect controls. The vision-language workflow classified 471 samples correctly, but glossy surfaces produced false positives and small boundary defects were sometimes missed. These limitations prevented the team from recommending autonomous acceptance of safety-critical parts.\n\nEvery observation retained a source hash and an image-region reference. Visual-only counts, identities, and spatial relations required explicit review before graph commit. All names, measurements, and operational details in this memorandum are fictional and exist solely to test OCR, evidence recovery, and multimodal extraction."
    _insert(page, pymupdf.Rect(65, 140, 530, 700), english, 13)
    scanned = pymupdf.open()
    for source_page in source:
        target = scanned.new_page(width=595, height=842)
        target.insert_image(
            target.rect,
            stream=source_page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).tobytes("png"),
        )
    source.close()
    _save_pdf(scanned, path)
    return {
        "pages": 2,
        "whole_page_bbox": [0, 0, 595, 842],
        "expected_parser": "mineru",
        "native_text_characters": 0,
    }


def _complex_pdf(path: Path, product: Path, deployment: Path, chart: Path) -> dict[str, Any]:
    document = pymupdf.open()
    page = document.new_page(width=842, height=595)
    _insert(
        page, pymupdf.Rect(40, 24, 802, 56), "AtlasVision X1 multimodal pilot dossier", 18, align=1
    )
    _insert(page, pymupdf.Rect(42, 76, 392, 100), "Research context", 13)
    _insert(
        page, pymupdf.Rect(42, 108, 392, 530), "\n\n".join(SECTIONS[1][1] + SECTIONS[2][1]), 9.1
    )
    page.draw_line((417, 78), (417, 535), color=(0.75, 0.78, 0.82), width=1)
    page.insert_image(pymupdf.Rect(455, 88, 795, 315), filename=str(product))
    _insert(
        page,
        pymupdf.Rect(455, 322, 795, 345),
        "Figure 1. Device configuration and visual regions",
        8.5,
        align=1,
    )
    _insert(
        page,
        pymupdf.Rect(455, 375, 795, 535),
        "The original image remains the evidence object. Extracted entities, properties, and spatial relations are candidates until source hashes, image coordinates, schema constraints, and review state have been verified.",
        10,
    )
    page = document.new_page(width=842, height=595)
    _insert(page, pymupdf.Rect(40, 24, 802, 56), "Evaluation results", 18, align=1)
    page.insert_image(pymupdf.Rect(42, 78, 472, 339), filename=str(chart))
    columns, rows = [510, 650, 725, 800], [105, 155, 205, 255, 305]
    for x in columns:
        page.draw_line((x, rows[0]), (x, rows[-1]), color=(0.4, 0.45, 0.5), width=1)
    for y in rows:
        page.draw_line((columns[0], y), (columns[-1], y), color=(0.4, 0.45, 0.5), width=1)
    labels = [
        (520, 136, "Mode"),
        (660, 136, "Correct"),
        (735, 136, "Accuracy"),
        (520, 186, "Native text"),
        (670, 186, "440"),
        (745, 186, "88.0%"),
        (520, 236, "OCR assisted"),
        (670, 236, "455"),
        (745, 236, "91.0%"),
        (520, 286, "Vision language"),
        (670, 286, "471"),
        (745, 286, "94.2%"),
    ]
    for x, y, label in labels:
        page.insert_text((x, y), label, fontsize=8.5)
    _insert(page, pymupdf.Rect(42, 385, 802, 548), "\n\n".join(SECTIONS[4][1]), 9.4)
    page = document.new_page(width=595, height=842)
    _insert(page, pymupdf.Rect(48, 38, 547, 72), "Deployment and governance", 18, align=1)
    page.insert_image(pymupdf.Rect(55, 95, 540, 389), filename=str(deployment))
    _insert(
        page,
        pymupdf.Rect(55, 395, 540, 420),
        "Figure 2. Harbor Laboratory pilot workflow",
        8.5,
        align=1,
    )
    page.draw_rect(pymupdf.Rect(75, 495, 520, 557), color=(0.25, 0.32, 0.4), width=1)
    _insert(
        page,
        pymupdf.Rect(85, 505, 510, 545),
        "F1 = 2 * precision * recall / (precision + recall)",
        14,
        align=1,
    )
    _insert(page, pymupdf.Rect(60, 600, 535, 770), SECTIONS[5][1][1], 10)
    _save_pdf(document, path)
    return {
        "expected_parser": "mineru",
        "pages": 3,
        "media": ["image", "chart", "table", "formula", "page_render"],
        "table_bbox": [510, 105, 800, 305],
        "formula_bbox": [75, 495, 520, 557],
    }


def _shade(cell: Any, fill: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shading)


def _docx(path: Path, product: Path, deployment: Path, chart: Path) -> None:
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.72)
    section.left_margin = section.right_margin = Inches(0.82)
    props = document.core_properties
    props.title, props.author, props.subject = (
        TITLE,
        "PrismKE synthetic fixture generator",
        "Fictional multimodal inspection report",
    )
    props.created = props.modified = props.last_printed = FIXED_TIME
    document.styles["Normal"].font.name, document.styles["Normal"].font.size = "Arial", Pt(10.5)
    document.styles["Normal"].paragraph_format.space_after = Pt(7)
    for name in ("Title", "Subtitle", "Heading 1", "Heading 2"):
        style = document.styles[name]
        style.font.color.rgb, style.font.name = RGBColor(0, 0, 0), "Arial"
        if name.startswith("Heading"):
            style.paragraph_format.space_after = Pt(8)
        ppr = style.element.find(qn("w:pPr"))
        if ppr is not None and (border := ppr.find(qn("w:pBdr"))) is not None:
            ppr.remove(border)
    for style_name, text in (("Title", TITLE), ("Subtitle", SUBTITLE)):
        paragraph = document.add_paragraph(style=style_name)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run(text)
    details = document.add_paragraph(
        "Nebula Technology | 30 June 2026 | Fictional evaluation material"
    )
    details.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_picture(str(product), width=Inches(5.8))
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption = document.add_paragraph("Figure 1  AtlasVision X1 pilot configuration")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for index, (heading, paragraphs) in enumerate(SECTIONS):
        heading_paragraph = document.add_heading(heading, level=1)
        if index in {1, 3, 5}:
            heading_paragraph.paragraph_format.page_break_before = True
        for text in paragraphs:
            document.add_paragraph(text)
        if index == 2:
            document.add_picture(str(deployment), width=Inches(6.2))
            document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            document.add_paragraph(
                "Figure 2  Harbor Laboratory pilot workflow"
            ).alignment = WD_ALIGN_PARAGRAPH.CENTER
        if index == 4:
            document.add_picture(str(chart), width=Inches(5.25))
            document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            document.add_paragraph(
                "Figure 3  Inspection accuracy by processing mode"
            ).alignment = WD_ALIGN_PARAGRAPH.CENTER
            table = document.add_table(rows=4, cols=4)
            table.style = "Table Grid"
            for cell, value in zip(
                table.rows[0].cells,
                ("Processing mode", "Samples", "Correct", "Accuracy"),
                strict=True,
            ):
                cell.text = value
            for row, values in zip(table.rows[1:], RESULTS, strict=True):
                for cell, value in zip(row.cells, values, strict=True):
                    cell.text = str(value)
            for row_index, row in enumerate(table.rows):
                for cell in row.cells:
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    _shade(
                        cell,
                        "1F4E78"
                        if row_index == 0
                        else ("EEF4FA" if row_index % 2 == 0 else "FFFFFF"),
                    )
                    for paragraph in cell.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for run in paragraph.runs:
                            run.font.size = Pt(9.5)
                            if row_index == 0:
                                run.bold, run.font.color.rgb = True, RGBColor(255, 255, 255)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("PrismKE fictional multimodal fixture | seed 140013")
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(path)
    canonicalize_zip(path)


def _text_variants(root: Path) -> None:
    parts = [TITLE, SUBTITLE, "Nebula Technology | 30 June 2026"]
    markdown = [f"# {TITLE}", "", f"*{SUBTITLE}*", "", "Nebula Technology | 30 June 2026"]
    html_sections: list[str] = []
    for heading, paragraphs in SECTIONS:
        parts += ["", heading, "", *paragraphs]
        markdown += ["", f"## {heading}", "", *paragraphs]
        html_sections.append(
            f"<section><h2>{html.escape(heading)}</h2>{''.join(f'<p>{html.escape(p)}</p>' for p in paragraphs)}</section>"
        )
    parts += [
        "",
        "Fictional data notice",
        "",
        "All organizations, people, products, facilities, measurements, and events are fictional.",
    ]
    markdown += [
        "",
        "## Figures",
        "",
        "![AtlasVision X1](../images/atlasvision-x1.png)",
        "",
        "![Pilot layout](../images/harbor-laboratory-deployment.jpg)",
        "",
        "![Performance chart](../images/inspection-performance-chart.jpg)",
    ]
    atomic_write(root / "native" / "research-brief.txt", ("\n".join(parts) + "\n").encode())
    atomic_write(root / "native" / "research-brief.md", ("\n".join(markdown) + "\n").encode())
    body = (
        "".join(html_sections)
        + '<h2>Figures</h2><img src="../images/atlasvision-x1.png" alt="AtlasVision X1"><img src="../images/harbor-laboratory-deployment.jpg" alt="Pilot layout"><img src="../images/inspection-performance-chart.jpg" alt="Performance chart">'
    )
    page = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{TITLE}</title><style>body{{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;line-height:1.6;color:#17263a}}img{{max-width:100%;height:auto}}h1,h2{{color:#000}}</style></head><body><main><h1>{TITLE}</h1><p><em>{SUBTITLE}</em></p>{body}</main></body></html>\n'
    atomic_write(root / "native" / "research-brief.html", page.encode())


def _nested_json(path: Path) -> None:
    payload = {
        "dataset": {"name": "AtlasVision X1 pilot evaluation", "fictional": True},
        "organization": {
            "name": "Nebula Technology",
            "name_zh": "星河科技",
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
                "evaluation": {
                    "samples": 500,
                    "modes": [
                        {"name": row[0], "correct": row[2], "accuracy": row[3]} for row in RESULTS
                    ],
                    "notes": None,
                },
            }
        ],
        "events": [
            {
                "type": "pilot_deployment",
                "participants": ["AtlasVision X1", "Harbor Laboratory"],
                "date": "2026-05-14",
                "status": "completed",
            }
        ],
    }
    write_json(path, payload)


def _expected(root: Path, regions: dict[str, Any], locations: dict[str, Any]) -> None:
    expected = {
        "seed": SEED,
        "fictional": True,
        "document_title": TITLE,
        "entities": [
            {"name": name, "type": kind}
            for name, kind in [
                ("Nebula Technology", "Organization"),
                ("AtlasVision X1", "Product"),
                ("Lin Yue", "Person"),
                ("Maya Chen", "Person"),
                ("Harbor Laboratory", "Facility"),
                ("Shanghai", "Location"),
            ]
        ],
        "relations": [
            ["AtlasVision X1", "developed_by", "Nebula Technology"],
            ["Lin Yue", "works_for", "Nebula Technology"],
            ["Maya Chen", "works_for", "Nebula Technology"],
            ["AtlasVision X1", "deployed_at", "Harbor Laboratory"],
            ["Harbor Laboratory", "located_in", "Shanghai"],
        ],
        "attributes": [
            {"subject": "AtlasVision X1", "predicate": "pilot_samples", "value": 500},
            {"subject": "AtlasVision X1", "predicate": "vision_language_accuracy", "value": 0.942},
        ],
        "visual_assertions_requiring_review": [
            {"subject": "AtlasVision X1", "predicate": "blue_sensor_count", "value": 3},
            {"subject": "AtlasVision X1", "predicate": "status_light_color", "value": "amber"},
        ],
        "image_regions": regions,
        "locations": locations,
        "json_paths": [
            "$.organization.name",
            "$.organization.researchers[0].name",
            "$.products[0].evaluation.modes[2].accuracy",
            "$.products[0].evaluation.notes",
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
        png, jpg = staging / "images/atlasvision-x1.png", staging / "images/atlasvision-x1.jpg"
        deployment, chart = (
            staging / "images/harbor-laboratory-deployment.jpg",
            staging / "images/inspection-performance-chart.jpg",
        )
        regions = {
            "product": _product_image(png, jpeg=False),
            "deployment": _deployment_image(deployment),
            "performance_chart": _chart(chart),
        }
        _product_image(jpg, jpeg=True)
        locations = {
            "native_pdf": _native_pdf(staging / "native/research-brief.pdf", png),
            "scanned_pdf": _scanned_pdf(staging / "scanned/bilingual-scan.pdf"),
            "complex_pdf": _complex_pdf(
                staging / "complex/multimodal-evaluation.pdf", jpg, deployment, chart
            ),
        }
        _docx(staging / "native/research-brief.docx", png, deployment, chart)
        _nested_json(staging / "json/nested-research-data.json")
        _expected(staging, regions, locations)
        readme = "# AtlasVision X1 fictional evaluation package\n\nA coherent fictional report is supplied as TXT, Markdown, HTML, DOCX, searchable PDF, raster-only bilingual PDF, complex PDF, images, and nested JSON. The product image tests visual parts, the deployment image tests spatial layout, and the chart tests numeric evidence. All names and measurements are fictional.\n"
        atomic_write(staging / "README.md", readme.encode())
        generated = [
            item for item in staging.rglob("*") if item.is_file() and item.name != "manifest.json"
        ]
        manifest = {
            "schema_version": 2,
            "generator_seed": SEED,
            "fictional": True,
            "document_title": TITLE,
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
    args = parser.parse_args()
    manifest = generate(args.output)
    print(f"Generated {len(manifest['files'])} synthetic files in {args.output}")


if __name__ == "__main__":
    main()
