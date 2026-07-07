"""Download OCR and LLM model weights during Docker image build."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from transformers import (
    AutoModelForCausalLM,
    AutoProcessor,
    AutoTokenizer,
    GlmOcrForConditionalGeneration,
)

from app.config.llm_settings import LlmSettings
from app.config.settings import Settings
from app.utils.logging import configure_logging, get_logger


def _get_hf_token() -> str | None:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if token:
        return token.strip() or None

    secret_path = Path("/run/secrets/HF_TOKEN")
    if secret_path.exists():
        value = secret_path.read_text(encoding="utf-8").strip()
        return value or None

    return None


def _download_ocr(settings: Settings, token: str | None, logger) -> None:
    logger.info("Downloading OCR model (model_id=%s)", settings.model_id)
    AutoProcessor.from_pretrained(settings.model_id, token=token)
    GlmOcrForConditionalGeneration.from_pretrained(settings.model_id, token=token)


def _download_llm(settings: LlmSettings, token: str | None, logger) -> None:
    logger.info("Downloading LLM (model_id=%s)", settings.model_id)
    AutoTokenizer.from_pretrained(settings.model_id, token=token, trust_remote_code=True)
    AutoModelForCausalLM.from_pretrained(
        settings.model_id,
        token=token,
        trust_remote_code=True,
    )


def main() -> None:
    ocr_settings = Settings()
    llm_settings = LlmSettings()
    configure_logging(ocr_settings.log_level)
    logger = get_logger(__name__)

    os.environ.setdefault("HF_HOME", ocr_settings.hf_home)
    os.environ.setdefault("TRANSFORMERS_CACHE", ocr_settings.transformers_cache)
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    token = _get_hf_token()
    logger.info("HF token provided: %s", "yes" if token else "no")

    _download_ocr(ocr_settings, token, logger)
    _download_llm(llm_settings, token, logger)
    logger.info("All models downloaded")


if __name__ == "__main__":
    logger = get_logger(__name__)
    try:
        main()
    except Exception:
        logger.exception("Model download failed")
        sys.exit(1)
