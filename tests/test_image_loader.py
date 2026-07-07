"""Tests for image loader service."""

import base64
from io import BytesIO
from unittest import mock

import httpx
import pytest
from PIL import Image

from app.config.settings import Settings
from app.core.exceptions import InvalidImageException, ValidationException
from app.services.image_loader import ImageLoaderService


def _png_base64(width: int = 64, height: int = 64) -> str:
    image = Image.new("RGB", (width, height), color="blue")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _settings(**overrides: object) -> Settings:
    return Settings(**overrides)


def test_load_from_base64_success() -> None:
    service = ImageLoaderService(_settings())
    try:
        image = service.load_from_base64(_png_base64())
        assert image.size == (64, 64)
    finally:
        service.close()


def test_load_from_base64_disabled() -> None:
    service = ImageLoaderService(_settings(allow_base64_images=False))
    try:
        with pytest.raises(ValidationException, match="Base64"):
            service.load_from_base64(_png_base64())
    finally:
        service.close()


def test_load_from_base64_resizes_large_image() -> None:
    service = ImageLoaderService(_settings(max_image_size=256))
    try:
        image = service.load_from_base64(_png_base64(800, 400))
        assert image.size == (256, 128)
    finally:
        service.close()


def test_load_from_url_success() -> None:
    png_bytes = base64.b64decode(_png_base64())
    request = httpx.Request("GET", "https://example.com/image.png")
    response = httpx.Response(
        200,
        content=png_bytes,
        headers={"content-type": "image/png"},
        request=request,
    )
    client = mock.Mock(spec=httpx.Client)
    client.get.return_value = response

    service = ImageLoaderService(_settings(), http_client=client)
    image = service.load_from_url("https://example.com/image.png")
    assert image.size == (64, 64)
    client.get.assert_called_once_with("https://example.com/image.png")


def test_load_from_url_disabled() -> None:
    service = ImageLoaderService(_settings(allow_url_images=False))
    try:
        with pytest.raises(ValidationException, match="URL"):
            service.load_from_url("https://example.com/image.png")
    finally:
        service.close()


def test_load_from_url_rejects_invalid_scheme() -> None:
    service = ImageLoaderService(_settings())
    try:
        with pytest.raises(ValidationException, match="scheme"):
            service.load_from_url("ftp://example.com/image.png")
    finally:
        service.close()


def test_load_from_url_http_error() -> None:
    client = mock.Mock(spec=httpx.Client)
    client.get.side_effect = httpx.HTTPError("network failure")

    service = ImageLoaderService(_settings(), http_client=client)
    with pytest.raises(InvalidImageException, match="download"):
        service.load_from_url("https://example.com/missing.png")
