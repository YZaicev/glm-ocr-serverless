"""Service for loading images from PDF documents."""

from __future__ import annotations

from PIL import Image

from app.config.settings import Settings
from app.core.exceptions import ValidationException
from app.utils.base64_utils import decode_base64_payload
from app.utils.logging import get_logger
from app.utils.pdf_utils import render_pdf_pages

logger = get_logger(__name__)


class PdfLoaderService:
    """Decode PDF input and render pages as images."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def load_from_base64(self, encoded: str) -> list[Image.Image]:
        """Decode a base64 PDF and render each page as an image."""
        if not self._settings.allow_pdf:
            msg = "PDF input is disabled."
            raise ValidationException(msg)

        raw_bytes = decode_base64_payload(encoded)
        logger.debug("Loaded base64 PDF (%d bytes)", len(raw_bytes))
        pages = render_pdf_pages(
            raw_bytes,
            max_pages=self._settings.max_pages,
            max_dimension=self._settings.max_image_size,
        )
        logger.debug("Rendered %d PDF page(s)", len(pages))
        return pages
