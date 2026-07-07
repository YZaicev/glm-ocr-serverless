"""Flash app settings (single combined KYC worker)."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from runpod_flash import GpuType


class FlashSettings(BaseSettings):
    """Configuration for Flash-managed KYC worker."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    kyc_image: str = Field(
        default="ghcr.io/yzaicev/glm-ocr-serverless:main",
        alias="FLASH_KYC_IMAGE",
    )
    kyc_container_disk_gb: int = Field(default=40, alias="FLASH_KYC_CONTAINER_DISK_GB", ge=20)
    kyc_timeout_ms: int = Field(default=300_000, alias="FLASH_KYC_TIMEOUT_MS", ge=1_000)
    kyc_workers_min: int = Field(default=0, alias="FLASH_KYC_WORKERS_MIN", ge=0)
    kyc_workers_max: int = Field(default=1, alias="FLASH_KYC_WORKERS_MAX", ge=1)
    idle_timeout_seconds: int = Field(default=60, alias="FLASH_IDLE_TIMEOUT_SECONDS", ge=1)
    worker_torch_dtype: str = Field(default="float16", alias="FLASH_WORKER_TORCH_DTYPE")
    llm_model_id: str = Field(
        default="Qwen/Qwen2.5-3B-Instruct",
        alias="FLASH_LLM_MODEL_ID",
    )

    @property
    def kyc_workers(self) -> tuple[int, int]:
        return (self.kyc_workers_min, self.kyc_workers_max)

    @property
    def worker_env(self) -> dict[str, str]:
        return {
            "DEVICE": "cuda",
            "TORCH_DTYPE": self.worker_torch_dtype,
            "LLM_MODEL_ID": self.llm_model_id,
            "LOG_LEVEL": "INFO",
        }

    @property
    def kyc_gpu(self) -> list[GpuType]:
        return [
            GpuType.NVIDIA_GEFORCE_RTX_4090,
            GpuType.NVIDIA_RTX_A6000,
        ]
