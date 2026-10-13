"""Auditable routing between PyMuPDF and MinerU PDF parsing."""

from __future__ import annotations

import pymupdf

from src.core.errors import MinerUEvidenceError, MinerUParseError, MinerUUnavailableError
from src.core.ids import canonical_hash
from src.domain import (
    DocumentIR,
    PDFComplexityThresholds,
    PDFParseDecision,
    PDFParseMode,
    PDFParserName,
    SourceDocument,
)
from src.parsing.adapters import PDFParser
from src.parsing.mineru import MinerUV1Client, convert_mineru_document
from src.parsing.pdf_complexity import complexity_fingerprint, inspect_pdf


class RoutedPDFParser:
    def __init__(
        self,
        lightweight: PDFParser,
        mineru: MinerUV1Client,
        *,
        mode: PDFParseMode = PDFParseMode.AUTO,
        thresholds: PDFComplexityThresholds | None = None,
        fallback_approved: bool = False,
    ) -> None:
        self.lightweight = lightweight
        self.mineru = mineru
        self.mode = mode
        self.thresholds = thresholds or PDFComplexityThresholds()
        self.fallback_approved = fallback_approved

    def supports(self, media_type: str) -> bool:
        return media_type == "application/pdf"

    async def parse(self, source: SourceDocument) -> DocumentIR:
        report = inspect_pdf(source.path, self.thresholds)
        reasons = list(report.reason_codes)
        if self.fallback_approved:
            parser = PDFParserName.PYMUPDF
            reasons = ["OPERATOR_CONFIRMED_FALLBACK", *reasons]
        elif self.mode == PDFParseMode.PYMUPDF:
            parser = PDFParserName.PYMUPDF
            reasons = ["USER_FORCED_PYMUPDF"]
        elif self.mode == PDFParseMode.MINERU:
            parser = PDFParserName.MINERU
            reasons = ["USER_FORCED_MINERU", *reasons]
        elif report.requires_mineru:
            parser = PDFParserName.MINERU
        else:
            parser = PDFParserName.PYMUPDF
            reasons = ["LIGHTWEIGHT_PDF"]
        config_fingerprint = canonical_hash(
            {
                "thresholds": complexity_fingerprint(self.thresholds),
                "mode": self.mode,
                "fallback_approved": self.fallback_approved,
                "mineru": self.mineru.fingerprint(),
            }
        )
        if parser == PDFParserName.PYMUPDF:
            version = str(pymupdf.version[0])
            decision = PDFParseDecision(
                requested_mode=self.mode,
                actual_parser=parser,
                reason_codes=reasons,
                complexity=report,
                parser_version=version,
                parser_fingerprint=canonical_hash(
                    {"parser": "pymupdf", "version": version, "config": config_fingerprint}
                ),
                config_fingerprint=config_fingerprint,
            )
            document = await self.lightweight.parse(source)
            document.pdf_parse_decision = decision
            return document
        decision = PDFParseDecision(
            requested_mode=self.mode,
            actual_parser=parser,
            reason_codes=reasons,
            complexity=report,
            parser_version=self.mineru.version,
            parser_fingerprint=self.mineru.fingerprint(),
            config_fingerprint=config_fingerprint,
            mineru_status="running",
        )
        status = await self.mineru.status()
        if not status.get("available"):
            decision.mineru_status = "unavailable"
            raise MinerUUnavailableError(decision=decision)
        try:
            artifacts = await self.mineru.parse(source)
        except (MinerUUnavailableError, MinerUParseError, MinerUEvidenceError) as exc:
            exc.decision = decision
            raise
        decision.mineru_job_id = artifacts.job_id
        decision.mineru_status = artifacts.status
        decision.artifact_manifest_hash = artifacts.manifest_hash
        try:
            return convert_mineru_document(source, artifacts, decision)
        except MinerUEvidenceError as exc:
            exc.decision = decision
            raise
        except Exception as exc:
            raise MinerUEvidenceError(str(exc), decision=decision) from exc
