"""Base64 and data-URI decoding helpers."""

from __future__ import annotations

import base64
import binascii
import re
from typing import Final

from app.core.exceptions import InvalidImageException

_DATA_URI_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$",
    re.DOTALL,
)


def parse_data_uri(encoded: str) -> tuple[str | None, str]:
    """Extract MIME type and base64 payload from a data URI or raw base64 string."""
    normalized = encoded.strip()
    match = _DATA_URI_PATTERN.match(normalized)
    if match is None:
        return None, normalized
    return match.group("mime"), match.group("data")


def decode_base64_payload(encoded: str) -> bytes:
    """Decode a base64 string or data URI into raw bytes."""
    _, payload = parse_data_uri(encoded)
    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        msg = "Invalid base64 image data."
        raise InvalidImageException(msg) from exc
