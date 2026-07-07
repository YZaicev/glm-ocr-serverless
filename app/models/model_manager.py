"""Singleton GLM-OCR model loader and inference gateway.

This module is the only place allowed to interact with Transformers directly.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Final

import torch
from PIL import Image
from transformers import AutoProcessor, GlmOcrForConditionalGeneration

from app.config.settings import Settings
from app.core.exceptions import ModelException
from app.utils.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_PROMPT: Final[str] = "Text Recognition:"


@dataclass(frozen=True, slots=True)
class ModelArtifacts:
    """Loaded model artifacts required for inference."""

    processor: Any
    model: Any
    device: torch.device
    dtype: torch.dtype


class ModelManager:
    """Process-wide singleton responsible for loading and running GLM-OCR."""

    _instance: ModelManager | None = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._artifacts: ModelArtifacts | None = None

    @classmethod
    def get_instance(cls, settings: Settings) -> ModelManager:
        """Return a singleton instance for the worker process."""
        if cls._instance is not None:
            return cls._instance

        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(settings)
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._artifacts is not None

    def load(self) -> None:
        """Load processor and model exactly once."""
        if self._artifacts is not None:
            return

        start = perf_counter()
        logger.info("Model loading started (model_id=%s)", self._settings.model_id)

        try:
            self._apply_hf_cache_env()
            dtype = _parse_torch_dtype(self._settings.torch_dtype)
            device = _resolve_device(self._settings.device)

            processor = AutoProcessor.from_pretrained(self._settings.model_id)
            model = GlmOcrForConditionalGeneration.from_pretrained(
                self._settings.model_id,
                torch_dtype=dtype,
                device_map=None,
            )
            model.eval()
            model.to(device)

            self._artifacts = ModelArtifacts(
                processor=processor,
                model=model,
                device=device,
                dtype=dtype,
            )
        except ModelException:
            logger.exception("Model loading failed")
            raise
        except Exception as exc:
            logger.exception("Model loading failed")
            raise ModelException("Failed to load OCR model.") from exc
        finally:
            elapsed_ms = int((perf_counter() - start) * 1000)
            if self._artifacts is not None:
                logger.info("Model loaded (%d ms)", elapsed_ms)

    def recognize(self, image: Image.Image, *, prompt: str | None = None) -> str:
        """Run OCR on a single image and return plain text."""
        if self._artifacts is None:
            self.load()
        assert self._artifacts is not None  # for type checkers

        prompt_text = (prompt or _DEFAULT_PROMPT).strip() or _DEFAULT_PROMPT

        processor = self._artifacts.processor
        model = self._artifacts.model

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt_text},
                ],
            }
        ]

        try:
            inputs = processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            )
            inputs = {k: v.to(self._artifacts.device) for k, v in inputs.items()}

            with (
                torch.inference_mode(),
                _autocast_if_available(self._artifacts.device, self._artifacts.dtype),
            ):
                output = model.generate(**inputs, max_new_tokens=self._settings.max_new_tokens)

            decoded = processor.decode(output[0], skip_special_tokens=True)
            return decoded.strip()
        except Exception as exc:
            logger.exception("Model inference failed")
            raise ModelException("OCR inference failed.") from exc

    def _apply_hf_cache_env(self) -> None:
        # Ensure HF cache paths are consistent for transformers + hf_hub.
        os.environ.setdefault("HF_HOME", self._settings.hf_home)
        os.environ.setdefault("TRANSFORMERS_CACHE", self._settings.transformers_cache)


def _parse_torch_dtype(value: str) -> torch.dtype:
    normalized = value.strip().lower()
    if normalized == "float16":
        return torch.float16
    if normalized == "bfloat16":
        return torch.bfloat16
    if normalized == "float32":
        return torch.float32
    raise ValueError(f"Unsupported TORCH_DTYPE: {value!r}")


def _resolve_device(value: str) -> torch.device:
    normalized = value.strip().lower()
    if normalized.startswith("cuda") and not torch.cuda.is_available():
        raise ModelException("CUDA requested but not available.")
    return torch.device(normalized)


class _autocast_if_available:
    def __init__(self, device: torch.device, dtype: torch.dtype) -> None:
        self._device = device
        self._dtype = dtype
        self._ctx = None

    def __enter__(self) -> None:
        if self._device.type == "cuda" and self._dtype in {torch.float16, torch.bfloat16}:
            self._ctx = torch.autocast(device_type="cuda", dtype=self._dtype)
            self._ctx.__enter__()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._ctx is not None:
            self._ctx.__exit__(exc_type, exc, tb)
