import pytest
from PIL import Image

from prismke.domain import SourceDocument
from prismke.parsing.adapters import MarkdownParser


@pytest.mark.asyncio
async def test_markdown_inline_html_images_keep_occurrences_and_text_positions(tmp_path):
    Image.new("RGB", (128, 128), "white").save(tmp_path / "image.png")
    source = tmp_path / "README.md"
    source.write_text(
        'Title\n<div><img src="image.png" alt="method"></div>\n'
        '<table><td><img src="image.png"></td></table>\n'
    )
    document = await MarkdownParser(tmp_path / "assets").parse(SourceDocument(path=source))
    assert len(document.media_assets) == 2
    assert document.media_assets[0].id != document.media_assets[1].id
    assert document.media_assets[0].blob_hash == document.media_assets[1].blob_hash
    raw = source.read_text()
    for block in document.text_blocks:
        assert raw[block.char_start : block.char_end] == block.text


@pytest.mark.asyncio
async def test_markdown_html_remote_image_respects_blocking_policy(tmp_path):
    source = tmp_path / "README.md"
    source.write_text('<img src="https://example.invalid/image.png">')
    document = await MarkdownParser().parse(SourceDocument(path=source))
    assert not document.media_assets
    assert any(w.startswith("remote_asset_blocked") for w in document.warnings)
