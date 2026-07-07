"""Environment-based application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TorchDtypeName = Literal["float16", "bfloat16", "float32"]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    model_id: str = Field(default="zai-org/GLM-OCR", alias="MODEL_ID")
    hf_home: str = Field(default="/models/hf", alias="HF_HOME")
    transformers_cache: str = Field(default="/models/hf", alias="TRANSFORMERS_CACHE")
    device: str = Field(default="cuda", alias="DEVICE")
    torch_dtype: TorchDtypeName = Field(default="bfloat16", alias="TORCH_DTYPE")
    max_image_size: int = Field(default=4096, alias="MAX_IMAGE_SIZE", ge=256, le=16384)
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    allow_url_images: bool = Field(default=True, alias="ALLOW_URL_IMAGES")
    allow_base64_images: bool = Field(default=True, alias="ALLOW_BASE64_IMAGES")
    allow_pdf: bool = Field(default=True, alias="ALLOW_PDF")
    max_pages: int = Field(default=50, alias="MAX_PAGES", ge=1, le=500)
    max_new_tokens: int = Field(default=512, alias="MAX_NEW_TOKENS", ge=64, le=4096)
    request_timeout_seconds: float = Field(default=120.0, alias="REQUEST_TIMEOUT_SECONDS", gt=0)

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in valid_levels:
            msg = f"LOG_LEVEL must be one of {sorted(valid_levels)}, got {value!r}"
            raise ValueError(msg)
        return normalized

    @field_validator("device")
    @classmethod
    def normalize_device(cls, value: str) -> str:
        return value.strip().lower()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
