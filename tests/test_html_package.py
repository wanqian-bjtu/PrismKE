from __future__ import annotations

import io
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from PIL import Image

from src.core.ids import file_sha256
from src.domain import DocumentIR, SourceDocument
from src.parsing.adapters import HTMLPackageParser
from src.parsing.registry import ParserRegistry


def _png(color: str = "navy") -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (96, 96), color).save(stream, format="PNG")
    return stream.getvalue()


def _package(path: Path, entries: dict[str, bytes]) -> Path:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return path


@pytest.mark.asyncio
async def test_html_package_preserves_relative_images_and_package_identity(
    tmp_path: Path,
) -> None:
    package = _package(
        tmp_path / "research-package.zip",
        {
            "site/pages/research.html": (
                b"<html><body><h1>Research</h1>"
                b'<img src="../images/chart.png" alt="Result chart">'
                b"</body></html>"
            ),
            "site/images/chart.png": _png(),
        },
    )
    document = await ParserRegistry(
        asset_dir=tmp_path / "assets",
        derived_dir=tmp_path / "derived",
    ).parse(SourceDocument(path=package))

    assert document.source_path == str(package.resolve())
    assert document.source_hash == file_sha256(package)
    assert document.source_filename == "research.html"
    assert document.source_package_filename == "research-package.zip"
    assert document.source_entry_path == "site/pages/research.html"
    assert document.media_type == "text/html"
    assert len(document.media_assets) == 1
    assert document.media_assets[0].source_ref.endswith("site/images/chart.png")
    assert document.warnings == []


@pytest.mark.asyncio
async def test_html_package_hash_changes_when_only_an_image_changes(tmp_path: Path) -> None:
    html = b'<html><body><img src="images/chart.png"></body></html>'
    first = _package(
        tmp_path / "first.zip",
        {"index.html": html, "images/chart.png": _png("navy")},
    )
    second = _package(
        tmp_path / "second.zip",
        {"index.html": html, "images/chart.png": _png("red")},
    )
    parser = ParserRegistry(
        asset_dir=tmp_path / "assets",
        derived_dir=tmp_path / "derived",
    )

    first_document = await parser.parse(SourceDocument(path=first))
    second_document = await parser.parse(SourceDocument(path=second))

    assert first_document.source_hash != second_document.source_hash
    assert first_document.id != second_document.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("entries", "code"),
    [
        ({"../escape.html": b"<p>unsafe</p>"}, "HTML_PACKAGE_UNSAFE_PATH"),
        (
            {"one.html": b"<p>one</p>", "two.htm": b"<p>two</p>"},
            "HTML_PACKAGE_HTML_AMBIGUOUS",
        ),
    ],
)
async def test_html_package_rejects_unsafe_or_ambiguous_archives(
    tmp_path: Path,
    entries: dict[str, bytes],
    code: str,
) -> None:
    package = _package(tmp_path / "invalid.zip", entries)
    parser = HTMLPackageParser(package_dir=tmp_path / "derived")

    with pytest.raises(ValueError, match=code):
        await parser.parse(SourceDocument(path=package))


@pytest.mark.asyncio
async def test_html_package_rejects_excessive_compression_ratio(tmp_path: Path) -> None:
    package = _package(
        tmp_path / "bomb.zip",
        {"index.html": b"<p>" + (b"0" * (2 * 1024 * 1024)) + b"</p>"},
    )
    parser = HTMLPackageParser(
        package_dir=tmp_path / "derived",
        max_compression_ratio=20.0,
    )

    with pytest.raises(ValueError, match="HTML_PACKAGE_COMPRESSION_RATIO_EXCEEDED"):
        await parser.parse(SourceDocument(path=package))


def test_document_ir_package_fields_are_backward_compatible() -> None:
    document = DocumentIR.model_validate(
        {
            "id": "doc:test",
            "source_path": "document.html",
            "source_hash": "0" * 64,
            "media_type": "text/html",
        }
    )

    assert document.source_package_filename is None
    assert document.source_entry_path is None
