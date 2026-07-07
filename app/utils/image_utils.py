"""Image validation, format checks, and resizing."""

from __future__ import annotations

from io import BytesIO
from typing import Final

from PIL import Image, UnidentifiedImageError

from app.core.exceptions import InvalidImageException
from app.schemas.errors import ErrorCode

SUPPORTED_IMAGE_FORMATS: Final[frozenset[str]] = frozenset(
    {"JPEG", "PNG", "WEBP", "BMP", "TIFF", "GIF"}
)

SUPPORTED_MIME_TYPES: Final[frozenset[str]] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/tiff",
        "image/gif",
    }
)

_FORMAT_TO_MIME: Final[dict[str, str]] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "BMP": "image/bmp",
    "TIFF": "image/tiff",
    "GIF": "image/gif",
}


def resolve_mime_type(image_format: str | None, declared_mime: str | None) -> str | None:
    """Resolve MIME type from declared value or detected image format."""
    if declared_mime is not None:
        return declared_mime.lower()
    if image_format is None:
        return None
    return _FORMAT_TO_MIME.get(image_format.upper())


def open_image_from_bytes(data: bytes) -> Image.Image:
    """Open a PIL image from raw bytes."""
    if not data:
        msg = "Image data is empty."
        raise InvalidImageException(msg)

    try:
        image = Image.open(BytesIO(data))
        image.load()
    except UnidentifiedImageError as exc:
        msg = "Unable to identify image file."
        raise InvalidImageException(msg) from exc
    except OSError as exc:
        msg = "Corrupted or unreadable image data."
        raise InvalidImageException(msg) from exc

    return image


def validate_image_format(image: Image.Image) -> str:
    """Validate image format and return normalized format name."""
    image_format = (image.format or "").upper()
    if image_format not in SUPPORTED_IMAGE_FORMATS:
        msg = f"Unsupported image format: {image_format or 'unknown'}."
        raise InvalidImageException(msg, code=ErrorCode.UNSUPPORTED_FORMAT)
    return image_format


def validate_mime_type(mime_type: str | None) -> None:
    """Reject unsupported MIME types when explicitly declared."""
    if mime_type is None:
        return
    normalized = mime_type.lower()
    if normalized not in SUPPORTED_MIME_TYPES:
        msg = f"Unsupported MIME type: {mime_type}."
        raise InvalidImageException(msg, code=ErrorCode.UNSUPPORTED_MIME)


def validate_image_dimensions(image: Image.Image, *, max_dimension: int) -> None:
    """Reject images whose width or height exceeds the configured limit."""
    width, height = image.size
    if width > max_dimension or height > max_dimension:
        msg = f"Image dimensions {width}x{height} exceed maximum allowed size of {max_dimension}px."
        raise InvalidImageException(msg, code=ErrorCode.IMAGE_TOO_LARGE)


def resize_image_if_needed(image: Image.Image, max_dimension: int) -> Image.Image:
    """Downscale image in-place when either dimension exceeds the limit."""
    width, height = image.size
    if width <= max_dimension and height <= max_dimension:
        return image

    scale = min(max_dimension / width, max_dimension / height)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    if image.mode in {"RGBA", "LA"} and resized.mode not in {"RGBA", "LA"}:
        resized = resized.convert("RGB")
    return resized


def prepare_image(
    data: bytes,
    *,
    max_dimension: int,
    declared_mime: str | None = None,
    allow_oversized: bool = False,
) -> Image.Image:
    """Open, validate, and optionally resize an image from bytes."""
    image = open_image_from_bytes(data)
    image_format = validate_image_format(image)
    mime_type = resolve_mime_type(image_format, declared_mime)
    validate_mime_type(mime_type)

    if allow_oversized:
        return resize_image_if_needed(image, max_dimension)

    validate_image_dimensions(image, max_dimension=max_dimension)
    return image
