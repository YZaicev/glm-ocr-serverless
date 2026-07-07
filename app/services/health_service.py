"""Internal worker health reporting."""

from __future__ import annotations

from time import perf_counter

import torch

from app.config.settings import Settings
from app.models.model_manager import ModelManager
from app.schemas.health import HealthResponse


class HealthService:
    """Expose runtime health information for the worker."""

    def __init__(
        self,
        settings: Settings,
        model_manager: ModelManager,
        *,
        started_at: float,
    ) -> None:
        self._settings = settings
        self._model_manager = model_manager
        self._started_at = started_at

    def get_status(self) -> HealthResponse:
        """Return current worker health snapshot."""
        cuda_version: str | None = None
        if torch.cuda.is_available():
            cuda_version = torch.version.cuda

        return HealthResponse(
            model_loaded=self._model_manager.is_loaded,
            gpu_available=torch.cuda.is_available(),
            cuda_version=cuda_version,
            torch_version=torch.__version__,
            model_id=self._settings.model_id,
            uptime_seconds=perf_counter() - self._started_at,
        )
