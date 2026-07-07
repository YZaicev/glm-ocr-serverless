"""Download GLM text model during Docker image build."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer

from app.config.llm_settings import LlmSettings
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


def _get_hf_token() -> str | None:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if token:
        return token.strip() or None
    secret_path = Path("/run/secrets/HF_TOKEN")
    if secret_path.exists():
        return secret_path.read_text(encoding="utf-8").strip() or None
    return None


def main() -> None:
    settings = LlmSettings()
    configure_logging(settings.log_level)

    os.environ.setdefault("HF_HOME", settings.hf_home)
    os.environ.setdefault("TRANSFORMERS_CACHE", settings.transformers_cache)
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    token = _get_hf_token()
    logger.info("Downloading LLM (model_id=%s)", settings.model_id)
    logger.info("HF token provided: %s", "yes" if token else "no")

    AutoTokenizer.from_pretrained(settings.model_id, token=token, trust_remote_code=True)
    AutoModelForCausalLM.from_pretrained(settings.model_id, token=token, trust_remote_code=True)

    logger.info("LLM download completed")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("LLM download failed")
        sys.exit(1)
