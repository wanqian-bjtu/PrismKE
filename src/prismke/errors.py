"""Domain-specific exceptions."""


class PrismKEError(Exception):
    """Base error for recoverable PrismKE failures."""


class UnsupportedDocumentError(PrismKEError):
    """Raised when no parser supports an input document."""


class SchemaValidationError(PrismKEError):
    """Raised when extracted knowledge violates a strict schema."""


class EvidenceRequiredError(PrismKEError):
    """Raised when a claim without evidence reaches persistence."""
