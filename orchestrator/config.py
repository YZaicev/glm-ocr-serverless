"""Orchestrator configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    """Local orchestrator settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    runpod_api_key: str = Field(alias="RUNPOD_API_KEY")
    runpod_ocr_endpoint_id: str = Field(alias="RUNPOD_OCR_ENDPOINT_ID")
    runpod_llm_endpoint_id: str = Field(alias="RUNPOD_LLM_ENDPOINT_ID")
    runpod_base_url: str = Field(default="https://api.runpod.ai/v2", alias="RUNPOD_BASE_URL")
    request_timeout_seconds: float = Field(default=300.0, alias="REQUEST_TIMEOUT_SECONDS", gt=0)
    host: str = Field(default="0.0.0.0", alias="ORCHESTRATOR_HOST")
    port: int = Field(default=8080, alias="ORCHESTRATOR_PORT", ge=1, le=65535)
