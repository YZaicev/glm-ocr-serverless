"""PDF to image conversion utilities."""

from __future__ import annotations

import fitz
from PIL import Image

from app.core.exceptions import PdfException
from app.schemas.errors import ErrorCode
from app.utils.image_utils import prepare_image

_PDF_RENDER_DPI = 200


def count_pdf_pages(data: bytes) -> int:
    """Return the number of pages in a PDF document."""
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        msg = "Unable to open PDF document."
        raise PdfException(msg) from exc

    try:
        if document.is_encrypted and not document.authenticate(""):
            msg = "Encrypted PDF documents are not supported."
            raise PdfException(msg, code=ErrorCode.TOO_MANY_PAGES)
        return document.page_count
    finally:
        document.close()


def render_pdf_pages(
    data: bytes,
    *,
    max_pages: int,
    max_dimension: int,
) -> list[Image.Image]:
    """Render PDF pages into validated PIL images."""
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        msg = "Unable to open PDF document."
        raise PdfException(msg) from exc

    images: list[Image.Image] = []
    try:
        if document.is_encrypted and not document.authenticate(""):
            msg = "Encrypted PDF documents are not supported."
            raise PdfException(msg)

        page_count = document.page_count
        if page_count == 0:
            msg = "PDF document contains no pages."
            raise PdfException(msg)

        if page_count > max_pages:
            msg = f"PDF has {page_count} pages, exceeding the limit of {max_pages}."
            raise PdfException(msg, code=ErrorCode.TOO_MANY_PAGES)

        zoom = _PDF_RENDER_DPI / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for page_index in range(page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            prepared = prepare_image(
                _image_to_bytes(image),
                max_dimension=max_dimension,
                declared_mime="image/png",
                allow_oversized=True,
            )
            images.append(prepared)
    finally:
        document.close()

    return images


def _image_to_bytes(image: Image.Image) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
