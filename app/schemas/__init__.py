"""Pydantic request/response schemas."""

from app.schemas.errors import ErrorCode
from app.schemas.request import OCRJobInput, OCRRequest
from app.schemas.response import (
    ErrorDetail,
    ErrorResponse,
    OCRPageResult,
    OCRSuccessResponse,
)

__all__ = [
    "ErrorCode",
    "OCRJobInput",
    "OCRRequest",
    "ErrorDetail",
    "ErrorResponse",
    "OCRPageResult",
    "OCRSuccessResponse",
]
