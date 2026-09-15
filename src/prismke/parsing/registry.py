"""Parser selection by media type."""

from prismke.core.errors import UnsupportedDocumentError
from prismke.domain import DocumentIR, SourceDocument
from prismke.parsing.adapters import ImageParser, PDFParser, TextParser, detect_media_type
from prismke.parsing.base import ParserAdapter


class ParserRegistry:
    def __init__(self, parsers: list[ParserAdapter] | None = None) -> None:
        self._parsers = parsers or [TextParser(), PDFParser(), ImageParser()]

    async def parse(self, source: SourceDocument) -> DocumentIR:
        media_type = detect_media_type(source.path, source.media_type)
        for parser in self._parsers:
            if parser.supports(media_type):
                return await parser.parse(source)
        raise UnsupportedDocumentError(f"unsupported media type: {media_type or 'unknown'}")
