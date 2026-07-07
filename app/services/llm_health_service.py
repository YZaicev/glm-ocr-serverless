"""Health reporting for LLM worker."""

from __future__ import annotations

from time import perf_counter

import torch

from app.config.llm_settings import LlmSettings
from app.models.llm_manager import LlmManager
from app.schemas.health import HealthResponse


class LlmHealthService:
    """Expose runtime health for LLM worker."""

    def __init__(
        self,
        settings: LlmSettings,
        llm_manager: LlmManager,
        *,
        started_at: float,
    ) -> None:
        self._settings = settings
        self._llm_manager = llm_manager
        self._started_at = started_at

    def get_status(self) -> HealthResponse:
        cuda_version: str | None = None
        if torch.cuda.is_available():
            cuda_version = torch.version.cuda

        return HealthResponse(
            model_loaded=self._llm_manager.is_loaded,
            gpu_available=torch.cuda.is_available(),
            cuda_version=cuda_version,
            torch_version=torch.__version__,
            model_id=self._settings.model_id,
            uptime_seconds=perf_counter() - self._started_at,
        )
