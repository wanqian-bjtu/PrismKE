from __future__ import annotations

import argparse
import html
import io
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageOps

from data.tools.common import PUBLIC_ROOT, atomic_write, sha256_file, write_json

FONT_PATH = Path(__file__).resolve().parent / "assets" / "DejaVuSans.ttf"
ALLOWED_IMAGE_HOSTS = {"i.abcnewsfe.com"}
MAX_IMAGE_BYTES = 12 * 1024 * 1024
ImageFetcher = Callable[[str], tuple[bytes, str]]


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not normalized:
        raise ValueError("source id must contain at least one letter or digit")
    return normalized


def _meta(soup: BeautifulSoup, name: str) -> str:
    node = soup.find("meta", attrs={"name": name})
    return str(node.get("content", "")).strip() if node else ""


def _canonical_url(soup: BeautifulSoup) -> str:
    node = soup.find("link", rel="canonical")
    return str(node.get("href", "")).strip() if node else ""


def _text(node: object | None) -> str:
    if node is None or not hasattr(node, "get_text"):
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def _article_parts(soup: BeautifulSoup) -> tuple[str, str, str, list[str]]:
    headline = _text(soup.select_one('[data-testid="prism-headline"] h1'))
    if not headline:
        headline = _text(soup.find("h1"))
    if not headline:
        headline = _text(soup.find("title"))
    description = _meta(soup, "description")
    byline = _text(soup.select_one('[data-testid="prism-byline"]'))
    body = soup.select_one('[data-testid="prism-article-body"]')
    if body is None:
        body = soup.find("article") or soup.find("main") or soup.find("body")
    paragraphs: list[str] = []
    seen: set[str] = set()
    if body is not None:
        for node in body.select("p"):
            value = _text(node)
            if len(value) < 30 or value in seen:
                continue
            seen.add(value)
            paragraphs.append(value)
    if not headline or not paragraphs:
        raise ValueError("could not locate a headline and article paragraphs")
    return headline, description, byline, paragraphs


def _article_figures(soup: BeautifulSoup) -> list[dict[str, str]]:
    body = soup.select_one('[data-testid="prism-article-body"]')
    if body is None:
        return []
    figures: list[dict[str, str]] = []
    for node in body.select("figure"):
        image = node.find("img")
        source_url = str(image.get("src", "")).strip() if image else ""
        if not source_url:
            continue
        figures.append(
            {
                "source_url": source_url,
                "caption": _text(node),
            }
        )
    return figures[:6]


def _fetch_image(url: str) -> tuple[bytes, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS:
        raise ValueError(f"image host is not allowed: {parsed.hostname or 'missing'}")
    with (
        httpx.Client(
            follow_redirects=True,
            timeout=httpx.Timeout(45.0),
            headers={"User-Agent": "PrismKE-Private-Research-Fixture/1.0"},
        ) as client,
        client.stream("GET", url) as response,
    ):
        response.raise_for_status()
        final = urlparse(str(response.url))
        if final.scheme != "https" or final.hostname not in ALLOWED_IMAGE_HOSTS:
            raise ValueError("image redirect left the allowed host")
        content_type = response.headers.get("content-type", "").split(";", 1)[0]
        if content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise ValueError(f"unsupported image content type: {content_type}")
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_bytes():
            size += len(chunk)
            if size > MAX_IMAGE_BYTES:
                raise ValueError("image exceeds the private fixture size limit")
            chunks.append(chunk)
    return b"".join(chunks), content_type


def _prepare_images(
    figures: list[dict[str, str]],
    *,
    safe_id: str,
    public_root: Path,
    fetcher: ImageFetcher,
) -> list[dict[str, str | int]]:
    original_assets = public_root / "originals" / "local-user-provided" / f"{safe_id}-assets"
    sanitized_assets = public_root / "sanitized" / "local-user-provided" / f"{safe_id}-assets"
    smoke_assets = public_root / "smoke" / "local-user-provided" / f"{safe_id}-assets"
    for directory in (original_assets, sanitized_assets, smoke_assets):
        directory.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, str | int]] = []
    for index, figure in enumerate(figures, 1):
        source_url = figure["source_url"]
        raw, content_type = fetcher(source_url)
        original_suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }[content_type]
        original = original_assets / f"image-{index:02d}{original_suffix}"
        atomic_write(original, raw)
        with Image.open(io.BytesIO(raw)) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            width, height = image.size
            if width < 200 or height < 150 or width * height > 50_000_000:
                raise ValueError("image dimensions are outside the private fixture limits")
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=90, optimize=False, progressive=False)
        filename = f"image-{index:02d}.jpg"
        sanitized = sanitized_assets / filename
        smoke = smoke_assets / filename
        atomic_write(sanitized, output.getvalue())
        atomic_write(smoke, output.getvalue())
        records.append(
            {
                "index": index,
                "source_url": source_url,
                "caption": figure["caption"],
                "filename": filename,
                "width": width,
                "height": height,
                "original_sha256": sha256_file(original),
                "sanitized_sha256": sha256_file(sanitized),
            }
        )
    return records


def _wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if current and width > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _render_multimodal_pdf(
    target: Path,
    *,
    headline: str,
    description: str,
    byline: str,
    paragraphs: list[str],
    image_records: list[dict[str, str | int]],
    asset_root: Path,
    canonical_url: str,
    copyright_notice: str,
) -> None:
    width, height = 1240, 1754
    margin, bottom = 90, 110
    title_font = ImageFont.truetype(str(FONT_PATH), 45)
    subtitle_font = ImageFont.truetype(str(FONT_PATH), 25)
    body_font = ImageFont.truetype(str(FONT_PATH), 23)
    small_font = ImageFont.truetype(str(FONT_PATH), 18)
    pages: list[Image.Image] = []
    page = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(page)
    y = 90

    def new_page() -> None:
        nonlocal page, draw, y
        pages.append(page)
        page = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(page)
        y = 90

    def add_text(text: str, font: ImageFont.FreeTypeFont, *, gap: int = 26) -> None:
        nonlocal y
        lines = _wrapped_lines(draw, text, font, width - 2 * margin)
        line_height = font.size + 11
        required = len(lines) * line_height + gap
        if y + required > height - bottom:
            new_page()
        for line in lines:
            draw.text((margin, y), line, fill="#172033", font=font)
            y += line_height
        y += gap

    def add_image(record: dict[str, str | int]) -> None:
        nonlocal y
        source = asset_root / str(record["filename"])
        with Image.open(source) as opened:
            image = opened.convert("RGB")
            scale = min((width - 2 * margin) / image.width, 570 / image.height, 1.0)
            rendered = image.resize(
                (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                Image.Resampling.LANCZOS,
            )
        caption_lines = _wrapped_lines(
            draw,
            str(record["caption"]),
            small_font,
            width - 2 * margin,
        )
        required = rendered.height + len(caption_lines) * 27 + 45
        if y + required > height - bottom:
            new_page()
        x = (width - rendered.width) // 2
        page.paste(rendered, (x, y))
        y += rendered.height + 14
        for line in caption_lines:
            draw.text((margin, y), line, fill="#4b5565", font=small_font)
            y += 27
        y += 32

    add_text(headline, title_font, gap=30)
    add_text(description, subtitle_font, gap=20)
    add_text(byline, small_font, gap=18)
    add_text(
        "Private research fixture. Copyrighted source text and photographs; do not redistribute.",
        small_font,
        gap=34,
    )
    image_slots = {0: 0, 6: 1, 12: 2}
    for index, paragraph in enumerate(paragraphs):
        image_index = image_slots.get(index)
        if image_index is not None and image_index < len(image_records):
            add_image(image_records[image_index])
        add_text(paragraph, body_font)
    add_text(f"Source: {canonical_url}", small_font, gap=12)
    add_text(f"Copyright: {copyright_notice}", small_font, gap=12)
    pages.append(page)
    for page_number, item in enumerate(pages, 1):
        footer = ImageDraw.Draw(item)
        footer.text(
            (width // 2 - 35, height - 65),
            f"Page {page_number}",
            fill="#667085",
            font=small_font,
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(
        target,
        format="PDF",
        save_all=True,
        append_images=pages[1:],
        resolution=150.0,
    )


def _render_html(
    *,
    headline: str,
    description: str,
    byline: str,
    paragraphs: list[str],
    canonical_url: str,
    copyright_notice: str,
    image_records: list[dict[str, str | int]],
    asset_directory: str,
) -> bytes:
    body_parts: list[str] = []
    image_slots = {0: 0, 6: 1, 12: 2}
    for index, paragraph in enumerate(paragraphs):
        image_index = image_slots.get(index)
        if image_index is not None and image_index < len(image_records):
            record = image_records[image_index]
            body_parts.append(
                "    <figure>"
                f'<img src="{html.escape(asset_directory)}/{html.escape(str(record["filename"]))}" '
                f'alt="{html.escape(str(record["caption"]))}">'
                f"<figcaption>{html.escape(str(record['caption']))}</figcaption>"
                "</figure>"
            )
        body_parts.append(f"    <p>{html.escape(paragraph)}</p>")
    paragraph_html = "\n".join(body_parts)
    source_note = (
        f'<p class="source">Source: <span>{html.escape(canonical_url)}</span></p>'
        if canonical_url
        else ""
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src 'unsafe-inline'; img-src 'self'">
  <meta name="robots" content="noindex,nofollow">
  <meta name="copyright" content="{html.escape(copyright_notice)}">
  <title>{html.escape(headline)}</title>
  <style>
    body {{ max-width: 760px; margin: 48px auto; padding: 0 24px;
            font: 18px/1.65 Georgia, serif; color: #172033; }}
    h1 {{ font: 700 38px/1.2 Arial, sans-serif; }}
    .description {{ color: #44506a; font-size: 20px; }}
    .byline, .source, .notice {{ color: #667085; font: 14px/1.5 Arial, sans-serif; }}
    .notice {{ border-left: 4px solid #d69e2e; padding: 10px 14px; background: #fff8e6; }}
    figure {{ margin: 32px 0; }}
    img {{ width: 100%; height: auto; display: block; }}
    figcaption {{ margin-top: 8px; color: #667085; font: 14px/1.5 Arial, sans-serif; }}
  </style>
</head>
<body>
  <main>
    <p class="notice">Private research fixture. Copyrighted source text; do not redistribute.</p>
    <h1>{html.escape(headline)}</h1>
    <p class="description">{html.escape(description)}</p>
    <p class="byline">{html.escape(byline)}</p>
{paragraph_html}
    {source_note}
  </main>
</body>
</html>
"""
    return document.encode("utf-8")


def import_local_html(
    source: Path,
    *,
    source_id: str,
    public_root: Path = PUBLIC_ROOT,
    include_images: bool = False,
    image_fetcher: ImageFetcher | None = None,
) -> dict[str, object]:
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("source must be an HTML file")
    safe_id = _safe_name(source_id)
    soup = BeautifulSoup(source.read_bytes(), "html.parser")
    headline, description, byline, paragraphs = _article_parts(soup)
    figures = _article_figures(soup) if include_images else []
    canonical_url = _canonical_url(soup)
    copyright_notice = _meta(soup, "copyright") or "Copyright status not supplied"

    original_dir = public_root / "originals" / "local-user-provided"
    sanitized_dir = public_root / "sanitized" / "local-user-provided"
    smoke_dir = public_root / "smoke" / "local-user-provided"
    provenance_dir = public_root / "provenance" / "local"
    for directory in (original_dir, sanitized_dir, smoke_dir, provenance_dir):
        directory.mkdir(parents=True, exist_ok=True)

    original = original_dir / f"{safe_id}.html"
    sanitized = sanitized_dir / f"{safe_id}-sanitized.html"
    smoke = smoke_dir / sanitized.name
    shutil.copyfile(source, original)
    image_records = _prepare_images(
        figures,
        safe_id=safe_id,
        public_root=public_root,
        fetcher=image_fetcher or _fetch_image,
    )
    payload = _render_html(
        headline=headline,
        description=description,
        byline=byline,
        paragraphs=paragraphs,
        canonical_url=canonical_url,
        copyright_notice=copyright_notice,
        image_records=image_records,
        asset_directory=f"{safe_id}-assets",
    )
    atomic_write(sanitized, payload)
    atomic_write(smoke, payload)
    sanitized_pdf = sanitized_dir / f"{safe_id}-multimodal.pdf"
    smoke_pdf = smoke_dir / sanitized_pdf.name
    if image_records:
        _render_multimodal_pdf(
            sanitized_pdf,
            headline=headline,
            description=description,
            byline=byline,
            paragraphs=paragraphs,
            image_records=image_records,
            asset_root=sanitized_dir / f"{safe_id}-assets",
            canonical_url=canonical_url,
            copyright_notice=copyright_notice,
        )
        shutil.copyfile(sanitized_pdf, smoke_pdf)
    result: dict[str, object] = {
        "schema_version": 1,
        "source_id": safe_id,
        "classification": "private-research-use-only",
        "redistribution_allowed": False,
        "source_filename": source.name,
        "canonical_url": canonical_url,
        "title": headline,
        "copyright": copyright_notice,
        "paragraph_count": len(paragraphs),
        "image_count": len(image_records),
        "images": image_records,
        "original_relative_path": original.relative_to(public_root).as_posix(),
        "original_sha256": sha256_file(original),
        "sanitized_relative_path": sanitized.relative_to(public_root).as_posix(),
        "sanitized_sha256": sha256_file(sanitized),
        "multimodal_pdf_relative_path": (
            sanitized_pdf.relative_to(public_root).as_posix() if image_records else None
        ),
        "multimodal_pdf_sha256": sha256_file(sanitized_pdf) if image_records else None,
        "transforms": [
            "retained headline, description, public byline, article paragraphs, and canonical URL",
            "removed scripts, stylesheets, forms, embeds, advertisements, analytics, "
            "cookies, and application state",
            "removed remote images and other third-party media",
            "added restrictive Content-Security-Policy and noindex metadata",
        ],
    }
    write_json(provenance_dir / f"{safe_id}.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a user-provided copyrighted HTML page for private research testing"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--id", required=True, dest="source_id")
    parser.add_argument(
        "--private-research-use",
        action="store_true",
        help="confirm that the local copy will not be redistributed",
    )
    parser.add_argument(
        "--include-images",
        action="store_true",
        help="download allowlisted article images into the private fixture",
    )
    args = parser.parse_args()
    if not args.private_research_use:
        parser.error("--private-research-use is required")
    result = import_local_html(
        args.source,
        source_id=args.source_id,
        include_images=args.include_images,
    )
    print(
        f"Imported {result['paragraph_count']} paragraphs and {result['image_count']} images to "
        f"{result['sanitized_relative_path']}"
    )


if __name__ == "__main__":
    main()
