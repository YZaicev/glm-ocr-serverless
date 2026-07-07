"""LLM worker configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.settings import TorchDtypeName


class LlmSettings(BaseSettings):
    """Settings for GLM text LLM worker."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    model_id: str = Field(default="zai-org/glm-4-9b-chat-hf", alias="LLM_MODEL_ID")
    hf_home: str = Field(default="/models/hf", alias="HF_HOME")
    transformers_cache: str = Field(default="/models/hf", alias="TRANSFORMERS_CACHE")
    device: str = Field(default="cuda", alias="DEVICE")
    torch_dtype: TorchDtypeName = Field(default="bfloat16", alias="TORCH_DTYPE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_new_tokens: int = Field(default=1024, alias="LLM_MAX_NEW_TOKENS", ge=128, le=4096)
    temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE", ge=0.0, le=1.0)
    request_timeout_seconds: float = Field(default=120.0, alias="REQUEST_TIMEOUT_SECONDS", gt=0)
    worker_mode: Literal["llm"] = "llm"


@lru_cache(maxsize=1)
def get_llm_settings() -> LlmSettings:
    """Return cached LLM settings singleton."""
    return LlmSettings()
