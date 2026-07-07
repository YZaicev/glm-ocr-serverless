"""Tests for PDF loader service."""

import base64
from io import BytesIO

import fitz
import pytest

from app.config.settings import Settings
from app.core.exceptions import PdfException, ValidationException
from app.services.pdf_loader import PdfLoaderService


def _pdf_base64(page_count: int = 2) -> str:
    document = fitz.open()
    for index in range(page_count):
        page = document.new_page()
        page.insert_text((72, 72), f"Page {index + 1}")
    buffer = BytesIO()
    document.save(buffer)
    document.close()
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_load_from_base64_success() -> None:
    service = PdfLoaderService(Settings())
    pages = service.load_from_base64(_pdf_base64(2))
    assert len(pages) == 2


def test_load_from_base64_disabled() -> None:
    service = PdfLoaderService(Settings(allow_pdf=False))
    with pytest.raises(ValidationException, match="PDF"):
        service.load_from_base64(_pdf_base64())


def test_load_from_base64_too_many_pages() -> None:
    service = PdfLoaderService(Settings(max_pages=1))
    with pytest.raises(PdfException):
        service.load_from_base64(_pdf_base64(2))
