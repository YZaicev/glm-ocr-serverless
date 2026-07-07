"""Download GLM-OCR model weights during Docker image build."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from transformers import AutoProcessor, GlmOcrForConditionalGeneration

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


def main() -> None:
    settings = Settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)

    os.environ.setdefault("HF_HOME", settings.hf_home)
    os.environ.setdefault("TRANSFORMERS_CACHE", settings.transformers_cache)
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    logger.info("Downloading model (model_id=%s)", settings.model_id)

    token = _get_hf_token()
    logger.info("HF token provided: %s", "yes" if token else "no")
    AutoProcessor.from_pretrained(settings.model_id, token=token)
    GlmOcrForConditionalGeneration.from_pretrained(settings.model_id, token=token)

    logger.info("Model download completed")


if __name__ == "__main__":
    logger = get_logger(__name__)
    try:
        main()
    except Exception:
        logger.exception("Model download failed")
        sys.exit(1)
