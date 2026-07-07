"""Tests for HealthService."""

from unittest import mock

from app.config.settings import Settings
from app.models.model_manager import ModelManager
from app.services.health_service import HealthService


def test_get_status() -> None:
    settings = Settings(model_id="zai-org/GLM-OCR")
    model_manager = mock.Mock(spec=ModelManager)
    model_manager.is_loaded = True

    service = HealthService(settings, model_manager, started_at=0.0)
    status = service.get_status()

    assert status.model_loaded is True
    assert isinstance(status.gpu_available, bool)
    assert status.model_id == "zai-org/GLM-OCR"
    assert status.torch_version
    assert status.uptime_seconds >= 0
