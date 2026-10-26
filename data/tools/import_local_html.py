from __future__ import annotations

import argparse
import html
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

from data.tools.common import PUBLIC_ROOT, atomic_write, sha256_file, write_json


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


def _render_html(
    *,
    headline: str,
    description: str,
    byline: str,
    paragraphs: list[str],
    canonical_url: str,
    copyright_notice: str,
) -> bytes:
    paragraph_html = "\n".join(f"    <p>{html.escape(item)}</p>" for item in paragraphs)
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
        content="default-src 'none'; style-src 'unsafe-inline'">
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
) -> dict[str, object]:
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("source must be an HTML file")
    safe_id = _safe_name(source_id)
    soup = BeautifulSoup(source.read_bytes(), "html.parser")
    headline, description, byline, paragraphs = _article_parts(soup)
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
    payload = _render_html(
        headline=headline,
        description=description,
        byline=byline,
        paragraphs=paragraphs,
        canonical_url=canonical_url,
        copyright_notice=copyright_notice,
    )
    atomic_write(sanitized, payload)
    atomic_write(smoke, payload)
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
        "original_relative_path": original.relative_to(public_root).as_posix(),
        "original_sha256": sha256_file(original),
        "sanitized_relative_path": sanitized.relative_to(public_root).as_posix(),
        "sanitized_sha256": sha256_file(sanitized),
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
    args = parser.parse_args()
    if not args.private_research_use:
        parser.error("--private-research-use is required")
    result = import_local_html(args.source, source_id=args.source_id)
    print(
        f"Imported {result['paragraph_count']} paragraphs to "
        f"{result['sanitized_relative_path']}"
    )


if __name__ == "__main__":
    main()
