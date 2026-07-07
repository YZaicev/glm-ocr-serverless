"""Service for loading images from base64 payloads and URLs."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from PIL import Image

from app.config.settings import Settings
from app.core.exceptions import InvalidImageException, ValidationException
from app.utils.base64_utils import decode_base64_payload, parse_data_uri
from app.utils.image_utils import prepare_image
from app.utils.logging import get_logger

logger = get_logger(__name__)

_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


class ImageLoaderService:
    """Load and validate images from supported input sources."""

    def __init__(self, settings: Settings, http_client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._http_client = http_client or httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
        )
        self._owns_client = http_client is None

    def load_from_base64(self, encoded: str) -> Image.Image:
        """Decode and validate a base64-encoded image."""
        if not self._settings.allow_base64_images:
            msg = "Base64 image input is disabled."
            raise ValidationException(msg)

        declared_mime, _ = parse_data_uri(encoded)
        raw_bytes = decode_base64_payload(encoded)
        logger.debug("Loaded base64 image (%d bytes)", len(raw_bytes))
        return prepare_image(
            raw_bytes,
            max_dimension=self._settings.max_image_size,
            declared_mime=declared_mime,
            allow_oversized=True,
        )

    def load_from_url(self, url: str) -> Image.Image:
        """Download and validate an image from a public URL."""
        if not self._settings.allow_url_images:
            msg = "URL image input is disabled."
            raise ValidationException(msg)

        normalized_url = url.strip()
        self._validate_url(normalized_url)

        try:
            response = self._http_client.get(normalized_url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            msg = f"Failed to download image from URL: {exc}"
            raise InvalidImageException(msg) from exc

        content_type = response.headers.get("content-type", "").split(";")[0].strip() or None
        raw_bytes = response.content
        logger.debug("Downloaded image from URL (%d bytes)", len(raw_bytes))
        return prepare_image(
            raw_bytes,
            max_dimension=self._settings.max_image_size,
            declared_mime=content_type,
            allow_oversized=True,
        )

    def close(self) -> None:
        """Close the owned HTTP client."""
        if self._owns_client:
            self._http_client.close()

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_URL_SCHEMES:
            msg = f"Unsupported URL scheme: {parsed.scheme or 'missing'}."
            raise ValidationException(msg)
        if not parsed.netloc:
            msg = "Image URL must include a host."
            raise ValidationException(msg)
