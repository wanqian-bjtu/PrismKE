"""Parser selection by media type."""

from pathlib import Path

from src.core.errors import UnsupportedDocumentError
from src.domain import DocumentIR, SourceDocument
from src.parsing.adapters import (
    DOCXParser,
    HTMLParser,
    ImageParser,
    JSONParser,
    LegacyDOCParser,
    MarkdownParser,
    PDFParser,
    TextParser,
    detect_media_type,
)
from src.parsing.base import ParserAdapter


class ParserRegistry:
    def __init__(
        self,
        parsers: list[ParserAdapter] | None = None,
        asset_dir: Path | None = None,
        allow_remote_assets: bool = False,
        derived_dir: Path | None = None,
        libreoffice_bin: Path | None = None,
        conversion_timeout_seconds: int = 120,
    ) -> None:
        self._parsers = parsers or [
            TextParser(),
            MarkdownParser(asset_dir, allow_remote_assets),
            HTMLParser(asset_dir, allow_remote_assets),
            JSONParser(),
            LegacyDOCParser(
                asset_dir,
                derived_dir,
                libreoffice_bin,
                conversion_timeout_seconds,
            ),
            DOCXParser(asset_dir),
            PDFParser(asset_dir),
            ImageParser(asset_dir),
        ]

    async def parse(self, source: SourceDocument) -> DocumentIR:
        media_type = detect_media_type(source.path, source.media_type)
        for parser in self._parsers:
            if parser.supports(media_type):
                document = await parser.parse(source)
                if document.source_filename is None:
                    name = source.path.name
                    prefix, separator, original = name.partition("--")
                    document.source_filename = (
                        original
                        if separator
                        and len(prefix) == 32
                        and all(c in "0123456789abcdef" for c in prefix)
                        else name
                    )
                return document
        raise UnsupportedDocumentError(f"unsupported media type: {media_type or 'unknown'}")
