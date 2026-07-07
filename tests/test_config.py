"""Tests for application configuration."""

import os
from unittest import mock

import pytest

from app.config.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_settings() -> None:
    settings = Settings()
    assert settings.model_id == "zai-org/GLM-OCR"
    assert settings.device == "cuda"
    assert settings.torch_dtype == "bfloat16"
    assert settings.max_image_size == 4096
    assert settings.allow_url_images is True
    assert settings.allow_base64_images is True
    assert settings.allow_pdf is True
    assert settings.max_pages == 50


def test_settings_from_environment() -> None:
    env = {
        "MODEL_ID": "custom/model",
        "DEVICE": "CPU",
        "TORCH_DTYPE": "float16",
        "MAX_IMAGE_SIZE": "2048",
        "LOG_LEVEL": "debug",
        "ALLOW_URL_IMAGES": "false",
        "ALLOW_BASE64_IMAGES": "0",
        "ALLOW_PDF": "no",
        "MAX_PAGES": "10",
    }
    with mock.patch.dict(os.environ, env, clear=False):
        settings = Settings()
    assert settings.model_id == "custom/model"
    assert settings.device == "cpu"
    assert settings.torch_dtype == "float16"
    assert settings.max_image_size == 2048
    assert settings.log_level == "DEBUG"
    assert settings.allow_url_images is False
    assert settings.allow_base64_images is False
    assert settings.allow_pdf is False
    assert settings.max_pages == 10


def test_invalid_log_level_raises() -> None:
    with (
        mock.patch.dict(os.environ, {"LOG_LEVEL": "VERBOSE"}, clear=False),
        pytest.raises(ValueError, match="LOG_LEVEL"),
    ):
        Settings()


def test_get_settings_is_singleton() -> None:
    first = get_settings()
    second = get_settings()
    assert first is second
