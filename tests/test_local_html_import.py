from __future__ import annotations

import io
import json
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image

from data.tools.import_local_html import import_local_html


def test_import_local_html_creates_inert_private_fixture(tmp_path: Path) -> None:
    source = tmp_path / "source.html"
    source.write_text(
        """<!doctype html><html><head>
        <link rel="canonical" href="https://example.test/article">
        <meta name="copyright" content="Copyright Example Publisher">
        <meta name="description" content="A fictional test description.">
        <script src="https://tracker.test/a.js"></script></head><body>
        <div data-testid="prism-headline"><h1>Example news report</h1></div>
        <div data-testid="prism-byline">By Example Author</div>
        <div data-testid="prism-article-body">
          <p>This first paragraph contains enough words to represent normal article prose.</p>
          <p>The second paragraph names an organization and describes a dated event.</p>
          <form action="https://tracker.test"><input name="email"></form>
          <iframe src="https://tracker.test/embed"></iframe>
        </div></body></html>""",
        encoding="utf-8",
    )

    public_root = tmp_path / "public"
    result = import_local_html(source, source_id="Example News", public_root=public_root)
    sanitized = public_root / str(result["sanitized_relative_path"])
    soup = BeautifulSoup(sanitized.read_bytes(), "html.parser")

    assert result["redistribution_allowed"] is False
    assert result["paragraph_count"] == 2
    assert soup.find("script") is None
    assert soup.find("form") is None
    assert soup.find("iframe") is None
    assert "tracker.test" not in sanitized.read_text(encoding="utf-8")
    provenance = json.loads(
        (public_root / "provenance/local/example-news.json").read_text(encoding="utf-8")
    )
    assert provenance["classification"] == "private-research-use-only"


def test_import_local_html_can_bundle_allowlisted_images(tmp_path: Path) -> None:
    source = tmp_path / "source.html"
    source.write_text(
        """<!doctype html><html><head>
        <link rel="canonical" href="https://example.test/article">
        <meta name="copyright" content="Copyright Example Publisher">
        <meta name="description" content="A fictional test description."></head><body>
        <div data-testid="prism-headline"><h1>Example illustrated report</h1></div>
        <div data-testid="prism-byline">By Example Author</div>
        <div data-testid="prism-article-body">
          <p>This paragraph contains enough words to represent normal article prose.</p>
          <figure><img src="https://i.abcnewsfe.com/example.jpg">
          <figcaption>Example caption and photo credit.</figcaption></figure>
          <p>The second paragraph describes an event illustrated by the photograph.</p>
        </div></body></html>""",
        encoding="utf-8",
    )
    image = Image.new("RGB", (640, 360), "#2f6fbd")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    public_root = tmp_path / "public"
    result = import_local_html(
        source,
        source_id="Example Illustrated News",
        public_root=public_root,
        include_images=True,
        image_fetcher=lambda _url: (buffer.getvalue(), "image/png"),
    )

    sanitized = public_root / str(result["sanitized_relative_path"])
    soup = BeautifulSoup(sanitized.read_bytes(), "html.parser")
    image_node = soup.find("img")
    assert result["image_count"] == 1
    assert image_node is not None
    assert image_node["src"] == "example-illustrated-news-assets/image-01.jpg"
    assert (public_root / str(result["multimodal_pdf_relative_path"])).is_file()
    assert "data:image" not in sanitized.read_text(encoding="utf-8")
