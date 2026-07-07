"""Flash app settings (Docker images, GPU, scaling)."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from runpod_flash import GpuType


class FlashSettings(BaseSettings):
    """Configuration for Flash-managed OCR/LLM endpoints."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    ocr_image: str = Field(
        default="ghcr.io/yzaicev/glm-ocr-serverless:main",
        alias="FLASH_OCR_IMAGE",
    )
    llm_image: str = Field(
        default="ghcr.io/yzaicev/glm-ocr-serverless-llm:main",
        alias="FLASH_LLM_IMAGE",
    )
    ocr_container_disk_gb: int = Field(default=30, alias="FLASH_OCR_CONTAINER_DISK_GB", ge=10)
    llm_container_disk_gb: int = Field(default=40, alias="FLASH_LLM_CONTAINER_DISK_GB", ge=20)
    ocr_timeout_ms: int = Field(default=120_000, alias="FLASH_OCR_TIMEOUT_MS", ge=1_000)
    llm_timeout_ms: int = Field(default=300_000, alias="FLASH_LLM_TIMEOUT_MS", ge=1_000)
    workers_min: int = Field(default=0, alias="FLASH_WORKERS_MIN", ge=0)
    workers_max: int = Field(default=3, alias="FLASH_WORKERS_MAX", ge=1)
    idle_timeout_seconds: int = Field(default=60, alias="FLASH_IDLE_TIMEOUT_SECONDS", ge=1)

    @property
    def workers(self) -> tuple[int, int]:
        return (self.workers_min, self.workers_max)

    @property
    def ocr_gpu(self) -> list[GpuType]:
        return [
            GpuType.NVIDIA_GEFORCE_RTX_4090,
            GpuType.NVIDIA_RTX_A6000,
        ]

    @property
    def llm_gpu(self) -> list[GpuType]:
        return [
            GpuType.NVIDIA_GEFORCE_RTX_4090,
            GpuType.NVIDIA_RTX_A6000,
        ]
