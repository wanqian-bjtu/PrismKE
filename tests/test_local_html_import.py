from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup

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
