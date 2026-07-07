"""Custom OCR exceptions with API response conversion."""

from __future__ import annotations

from typing import Any

from app.schemas.errors import ErrorCode
from app.schemas.response import ErrorDetail, ErrorResponse


class OCRException(Exception):
    """Base exception for all OCR service errors."""

    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    status_code: int = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_error_response(self) -> ErrorResponse:
        """Convert exception into a structured API error response."""
        return ErrorResponse(
            success=False,
            error=ErrorDetail(code=self.code, message=self.message),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception as a plain dictionary."""
        return self.to_error_response().model_dump()


class InvalidImageException(OCRException):
    """Raised when image data is corrupt, invalid, or unsupported."""

    code = ErrorCode.INVALID_IMAGE
    status_code = 400

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        if code is not None:
            self.code = code


class PdfException(OCRException):
    """Raised when PDF processing fails."""

    code = ErrorCode.PDF_ERROR
    status_code = 400

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        if code is not None:
            self.code = code


class ValidationException(OCRException):
    """Raised when request validation fails."""

    code = ErrorCode.VALIDATION_ERROR
    status_code = 400


class ModelException(OCRException):
    """Raised when model loading or inference fails."""

    code = ErrorCode.MODEL_ERROR
    status_code = 500


class TimeoutException(OCRException):
    """Raised when processing exceeds the allowed time."""

    code = ErrorCode.TIMEOUT
    status_code = 408
