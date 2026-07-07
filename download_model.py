"""Download GLM-OCR model weights during Docker image build."""

from __future__ import annotations

import os
import sys

from transformers import AutoProcessor, GlmOcrForConditionalGeneration

from app.config.settings import Settings
from app.utils.logging import configure_logging, get_logger


def main() -> None:
    settings = Settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)

    os.environ.setdefault("HF_HOME", settings.hf_home)
    os.environ.setdefault("TRANSFORMERS_CACHE", settings.transformers_cache)
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    logger.info("Downloading model (model_id=%s)", settings.model_id)

    AutoProcessor.from_pretrained(settings.model_id)
    GlmOcrForConditionalGeneration.from_pretrained(settings.model_id)

    logger.info("Model download completed")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
