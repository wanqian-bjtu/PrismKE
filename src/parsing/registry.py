"""Parser selection by media type."""

from pathlib import Path

from src.core.errors import UnsupportedDocumentError
from src.domain import DocumentIR, PDFComplexityThresholds, PDFParseMode, SourceDocument
from src.parsing.adapters import (
    DOCXParser,
    HTMLPackageParser,
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
from src.parsing.mineru import MinerUV1Client
from src.parsing.pdf_router import RoutedPDFParser


class ParserRegistry:
    def __init__(
        self,
        parsers: list[ParserAdapter] | None = None,
        asset_dir: Path | None = None,
        allow_remote_assets: bool = False,
        derived_dir: Path | None = None,
        libreoffice_bin: Path | None = None,
        conversion_timeout_seconds: int = 120,
        pdf_parse_mode: PDFParseMode = PDFParseMode.AUTO,
        pdf_thresholds: PDFComplexityThresholds | None = None,
        mineru_client: MinerUV1Client | None = None,
        pdf_fallback_approved: bool = False,
        archive_max_entries: int = 1000,
        archive_max_entry_bytes: int = 200 * 1024 * 1024,
        archive_max_total_bytes: int = 500 * 1024 * 1024,
        archive_max_compression_ratio: float = 200.0,
    ) -> None:
        lightweight_pdf = PDFParser(asset_dir)
        routed_pdf = RoutedPDFParser(
            lightweight_pdf,
            mineru_client
            or MinerUV1Client("http://127.0.0.1:18020", Path("runtime/derived-documents")),
            mode=pdf_parse_mode,
            thresholds=pdf_thresholds,
            fallback_approved=pdf_fallback_approved,
        )
        self._parsers = parsers or [
            TextParser(),
            MarkdownParser(asset_dir, allow_remote_assets),
            HTMLPackageParser(
                asset_dir,
                allow_remote_assets,
                (derived_dir or Path("runtime/derived-documents")) / "html-packages",
                max_entries=archive_max_entries,
                max_entry_bytes=archive_max_entry_bytes,
                max_total_bytes=archive_max_total_bytes,
                max_compression_ratio=archive_max_compression_ratio,
            ),
            HTMLParser(asset_dir, allow_remote_assets),
            JSONParser(),
            LegacyDOCParser(
                asset_dir,
                derived_dir,
                libreoffice_bin,
                conversion_timeout_seconds,
            ),
            DOCXParser(asset_dir),
            routed_pdf,
            ImageParser(asset_dir),
        ]

    async def parse(self, source: SourceDocument) -> DocumentIR:
        media_type = detect_media_type(source.path, source.media_type)
        for parser in self._parsers:
            if parser.supports(media_type):
                document = await parser.parse(source)
                if document.source_filename is None:
                    name = source.source_filename or source.path.name
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
