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
    ocr_workers_min: int = Field(default=0, alias="FLASH_OCR_WORKERS_MIN", ge=0)
    ocr_workers_max: int = Field(default=2, alias="FLASH_OCR_WORKERS_MAX", ge=1)
    llm_workers_min: int = Field(default=0, alias="FLASH_LLM_WORKERS_MIN", ge=0)
    llm_workers_max: int = Field(default=1, alias="FLASH_LLM_WORKERS_MAX", ge=1)
    orchestrator_workers_min: int = Field(
        default=0,
        alias="FLASH_ORCHESTRATOR_WORKERS_MIN",
        ge=0,
    )
    orchestrator_workers_max: int = Field(
        default=1,
        alias="FLASH_ORCHESTRATOR_WORKERS_MAX",
        ge=1,
    )
    orchestrator_timeout_ms: int = Field(
        default=600_000,
        alias="FLASH_ORCHESTRATOR_TIMEOUT_MS",
        ge=1_000,
    )
    worker_torch_dtype: str = Field(default="float16", alias="FLASH_WORKER_TORCH_DTYPE")
    idle_timeout_seconds: int = Field(default=60, alias="FLASH_IDLE_TIMEOUT_SECONDS", ge=1)

    @property
    def worker_env(self) -> dict[str, str]:
        """Environment passed to OCR/LLM Docker workers."""
        return {
            "DEVICE": "cuda",
            "TORCH_DTYPE": self.worker_torch_dtype,
            "LOG_LEVEL": "INFO",
        }

    @property
    def ocr_workers(self) -> tuple[int, int]:
        return (self.ocr_workers_min, self.ocr_workers_max)

    @property
    def llm_workers(self) -> tuple[int, int]:
        return (self.llm_workers_min, self.llm_workers_max)

    @property
    def orchestrator_workers(self) -> tuple[int, int]:
        return (self.orchestrator_workers_min, self.orchestrator_workers_max)

    @property
    def total_workers_max(self) -> int:
        """Sum of max workers across all Flash endpoints in this app."""
        return self.ocr_workers_max + self.llm_workers_max + self.orchestrator_workers_max

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
