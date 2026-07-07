"""Tests for PDF conversion utilities."""

from io import BytesIO

import fitz
import pytest
from PIL import Image

from app.core.exceptions import PdfException
from app.schemas.errors import ErrorCode
from app.utils.pdf_utils import count_pdf_pages, render_pdf_pages


def _make_pdf(page_count: int = 1) -> bytes:
    document = fitz.open()
    for index in range(page_count):
        page = document.new_page()
        page.insert_text((72, 72), f"Page {index + 1}")
    buffer = BytesIO()
    document.save(buffer)
    document.close()
    return buffer.getvalue()


def test_count_pdf_pages() -> None:
    assert count_pdf_pages(_make_pdf(3)) == 3


def test_count_pdf_pages_invalid_data_raises() -> None:
    with pytest.raises(PdfException, match="open PDF"):
        count_pdf_pages(b"not-a-pdf")


def test_render_pdf_pages_single_page() -> None:
    pages = render_pdf_pages(_make_pdf(1), max_pages=5, max_dimension=1024)
    assert len(pages) == 1
    assert isinstance(pages[0], Image.Image)
    assert pages[0].width > 0
    assert pages[0].height > 0


def test_render_pdf_pages_multiple_pages() -> None:
    pages = render_pdf_pages(_make_pdf(3), max_pages=5, max_dimension=1024)
    assert len(pages) == 3


def test_render_pdf_pages_too_many_pages_raises() -> None:
    with pytest.raises(PdfException) as exc_info:
        render_pdf_pages(_make_pdf(4), max_pages=2, max_dimension=1024)
    assert exc_info.value.code == ErrorCode.TOO_MANY_PAGES


def test_render_pdf_pages_empty_document_raises() -> None:
    from unittest import mock

    pdf_bytes = _make_pdf(1)
    mock_document = mock.Mock()
    mock_document.is_encrypted = False
    mock_document.page_count = 0

    with (
        mock.patch("app.utils.pdf_utils.fitz.open", return_value=mock_document),
        pytest.raises(PdfException, match="no pages"),
    ):
        render_pdf_pages(pdf_bytes, max_pages=5, max_dimension=1024)

    mock_document.close.assert_called_once()
