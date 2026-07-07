"""Tests for custom OCR exceptions."""

from app.core.exceptions import (
    InvalidImageException,
    ModelException,
    OCRException,
    PdfException,
    TimeoutException,
    ValidationException,
)
from app.schemas.errors import ErrorCode


def test_base_exception_to_dict() -> None:
    exc = OCRException("unexpected failure")
    payload = exc.to_dict()
    assert payload == {
        "success": False,
        "error": {"code": ErrorCode.INTERNAL_ERROR, "message": "unexpected failure"},
    }


def test_invalid_image_exception_code() -> None:
    exc = InvalidImageException("corrupt image")
    response = exc.to_error_response()
    assert response.error.code == ErrorCode.INVALID_IMAGE
    assert response.success is False


def test_pdf_exception_code() -> None:
    exc = PdfException("failed to read PDF")
    assert exc.code == ErrorCode.PDF_ERROR


def test_validation_exception_code() -> None:
    exc = ValidationException("missing input")
    assert exc.code == ErrorCode.VALIDATION_ERROR


def test_model_exception_code() -> None:
    exc = ModelException("inference failed")
    assert exc.code == ErrorCode.MODEL_ERROR


def test_timeout_exception_code() -> None:
    exc = TimeoutException("processing timed out")
    assert exc.code == ErrorCode.TIMEOUT
