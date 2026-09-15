"""PrismKE-specific exceptions."""


class PrismKEError(Exception):
    """Base error for recoverable PrismKE failures."""


class UnsupportedDocumentError(PrismKEError):
    """Raised when no parser supports an input document."""


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

    def __init__(self, message: str, *, call_records: list[object] | None = None) -> None:
        super().__init__(message)
        self.call_records = call_records or []


class LegacyCheckpointError(PrismKEError):
    """Raised when a run predates the current checkpoint format."""
