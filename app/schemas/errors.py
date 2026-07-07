"""Error code enumeration for API responses."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Machine-readable error codes returned by the OCR service."""

    INVALID_IMAGE = "INVALID_IMAGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    TOO_MANY_PAGES = "TOO_MANY_PAGES"
    UNSUPPORTED_MIME = "UNSUPPORTED_MIME"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PDF_ERROR = "PDF_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
