"""PrismKE-specific exceptions."""

from collections.abc import Sequence


class PrismKEError(Exception):
    """Base error for recoverable PrismKE failures."""


class UnsupportedDocumentError(PrismKEError):
    """Raised when no parser supports an input document."""


class DocumentConversionError(PrismKEError):
    """Raised when a legacy document cannot be converted safely."""


class PDFParserBlockedError(PrismKEError):
    """Raised when a selected high-precision parser cannot safely finish."""

    def __init__(self, code: str, message: str, *, decision: object | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.decision = decision


class MinerUUnavailableError(PDFParserBlockedError):
    def __init__(
        self, message: str = "MinerU service is unavailable", *, decision: object | None = None
    ) -> None:
        super().__init__("MINERU_UNAVAILABLE", message, decision=decision)


class MinerUParseError(PDFParserBlockedError):
    def __init__(
        self, message: str = "MinerU parsing failed", *, decision: object | None = None
    ) -> None:
        super().__init__("MINERU_PARSE_FAILED", message, decision=decision)


class MinerUEvidenceError(PDFParserBlockedError):
    def __init__(
        self,
        message: str = "MinerU evidence package is invalid",
        *,
        decision: object | None = None,
    ) -> None:
        super().__init__("MINERU_EVIDENCE_INVALID", message, decision=decision)


class TaskModeCommitError(PrismKEError):
    """Raised when an extraction-only task attempts a graph commit."""

    code = "TASK_MODE_NO_GRAPH_COMMIT"


class SchemaValidationError(PrismKEError):
    """Raised when extracted knowledge violates a schema."""


class EvidenceRequiredError(PrismKEError):
    """Raised when a claim without evidence reaches persistence."""


class EvidenceIntegrityError(PrismKEError):
    """Raised when stored evidence is missing, changed, or inconsistent."""


class GraphIntegrityError(PrismKEError):
    """Raised when a graph transaction violates referential integrity."""


class ProviderConfigurationError(PrismKEError):
    """Raised when an explicitly selected provider is not configured."""


class ProviderRequestError(PrismKEError):
    """Raised for a sanitized external provider request failure."""

    def __init__(self, message: str, *, call_record: object | None = None) -> None:
        super().__init__(message)
        self.call_record = call_record


class ProviderResponseError(PrismKEError):
    """Raised when a provider returns an unusable response payload."""

    def __init__(self, message: str, *, call_records: Sequence[object] | None = None) -> None:
        super().__init__(message)
        self.call_records = list(call_records or [])


class LegacyCheckpointError(PrismKEError):
    """Raised when a run predates the current checkpoint format."""
