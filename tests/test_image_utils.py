"""Tests for image validation and resizing."""

from io import BytesIO

import pytest
from PIL import Image

from app.core.exceptions import InvalidImageException
from app.schemas.errors import ErrorCode
from app.utils.image_utils import (
    open_image_from_bytes,
    prepare_image,
    resize_image_if_needed,
    validate_image_dimensions,
    validate_image_format,
)


def _make_png_bytes(width: int, height: int) -> bytes:
    image = Image.new("RGB", (width, height), color="red")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_open_image_from_bytes_success() -> None:
    image = open_image_from_bytes(_make_png_bytes(32, 32))
    assert image.size == (32, 32)


def test_open_image_from_empty_bytes_raises() -> None:
    with pytest.raises(InvalidImageException, match="empty"):
        open_image_from_bytes(b"")


def test_open_image_from_corrupt_bytes_raises() -> None:
    with pytest.raises(InvalidImageException):
        open_image_from_bytes(b"not-an-image")


def test_validate_image_format_rejects_unknown() -> None:
    image = Image.new("RGB", (10, 10))
    image.format = "UNKNOWN"  # type: ignore[misc]
    with pytest.raises(InvalidImageException) as exc_info:
        validate_image_format(image)
    assert exc_info.value.code == ErrorCode.UNSUPPORTED_FORMAT


def test_validate_image_dimensions_rejects_oversized() -> None:
    image = Image.new("RGB", (500, 500))
    image.format = "PNG"
    with pytest.raises(InvalidImageException) as exc_info:
        validate_image_dimensions(image, max_dimension=400)
    assert exc_info.value.code == ErrorCode.IMAGE_TOO_LARGE


def test_resize_image_if_needed_downscales() -> None:
    image = Image.new("RGB", (800, 400))
    resized = resize_image_if_needed(image, max_dimension=400)
    assert resized.size == (400, 200)


def test_resize_image_if_needed_keeps_small_image() -> None:
    image = Image.new("RGB", (200, 100))
    resized = resize_image_if_needed(image, max_dimension=400)
    assert resized.size == (200, 100)


def test_prepare_image_with_declared_mime() -> None:
    image = prepare_image(
        _make_png_bytes(100, 100),
        max_dimension=512,
        declared_mime="image/png",
        allow_oversized=True,
    )
    assert image.size == (100, 100)


def test_prepare_image_rejects_unsupported_mime() -> None:
    with pytest.raises(InvalidImageException) as exc_info:
        prepare_image(
            _make_png_bytes(50, 50),
            max_dimension=512,
            declared_mime="image/svg+xml",
            allow_oversized=True,
        )
    assert exc_info.value.code == ErrorCode.UNSUPPORTED_MIME
