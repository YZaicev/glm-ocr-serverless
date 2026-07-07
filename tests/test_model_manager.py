"""Tests for ModelManager singleton behavior and inference wiring."""

from __future__ import annotations

from unittest import mock

import pytest
import torch
from PIL import Image

from app.config.settings import Settings
from app.core.exceptions import ModelException
from app.models.model_manager import ModelManager


@pytest.fixture(autouse=True)
def reset_model_manager_singleton() -> None:
    ModelManager._instance = None  # type: ignore[attr-defined]
    yield
    ModelManager._instance = None  # type: ignore[attr-defined]


def test_get_instance_is_singleton() -> None:
    settings = Settings()
    first = ModelManager.get_instance(settings)
    second = ModelManager.get_instance(settings)
    assert first is second


def test_load_only_happens_once() -> None:
    settings = Settings(device="cpu", torch_dtype="float32")
    manager = ModelManager.get_instance(settings)

    processor = mock.Mock()
    processor.apply_chat_template.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
    processor.decode.return_value = "ok"

    model = mock.Mock()
    model.generate.return_value = torch.tensor([[1, 2, 3]])

    with (
        mock.patch(
            "app.models.model_manager.AutoProcessor.from_pretrained",
            return_value=processor,
        ) as ap,
        mock.patch(
            "app.models.model_manager.GlmOcrForConditionalGeneration.from_pretrained",
            return_value=model,
        ) as mp,
    ):
        manager.load()
        manager.load()
        assert ap.call_count == 1
        assert mp.call_count == 1


def test_recognize_calls_processor_and_model() -> None:
    settings = Settings(device="cpu", torch_dtype="float32", max_new_tokens=64)
    manager = ModelManager.get_instance(settings)

    processor = mock.Mock()
    processor.apply_chat_template.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
    processor.decode.return_value = "hello"

    model = mock.Mock()
    model.generate.return_value = torch.tensor([[1, 2, 3]])

    with (
        mock.patch(
            "app.models.model_manager.AutoProcessor.from_pretrained",
            return_value=processor,
        ),
        mock.patch(
            "app.models.model_manager.GlmOcrForConditionalGeneration.from_pretrained",
            return_value=model,
        ),
    ):
        manager.load()
        text = manager.recognize(Image.new("RGB", (10, 10)))
        assert text == "hello"
        assert processor.apply_chat_template.called
        assert model.generate.called


def test_cuda_requested_but_unavailable_raises() -> None:
    settings = Settings(device="cuda", torch_dtype="float16")
    manager = ModelManager.get_instance(settings)
    with (
        mock.patch("app.models.model_manager.torch.cuda.is_available", return_value=False),
        pytest.raises(ModelException, match="CUDA"),
    ):
        manager.load()
