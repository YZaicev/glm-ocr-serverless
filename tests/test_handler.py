"""Tests for RunPod handler."""

from unittest import mock

import pytest

from app.api.dependencies import WorkerContext
from app.api.runpod_handler import RunPodHandler
from app.core.exceptions import InvalidImageException
from app.schemas.health import HealthResponse
from app.schemas.response import OCRPageResult, OCRSuccessResponse


@pytest.fixture
def handler() -> RunPodHandler:
    ocr_service = mock.Mock()
    health_service = mock.Mock()
    health_service.get_status.return_value = HealthResponse(
        model_loaded=True,
        gpu_available=False,
        cuda_version=None,
        torch_version="2.4.0",
        model_id="zai-org/GLM-OCR",
        uptime_seconds=12.5,
    )
    ocr_service.process.return_value = OCRSuccessResponse(
        processing_time_ms=50,
        pages=[OCRPageResult(page=1, text="hello")],
    )

    context = WorkerContext(
        settings=mock.Mock(),
        ocr_service=ocr_service,
        health_service=health_service,
        image_loader=mock.Mock(),
    )
    return RunPodHandler(context)


def test_health_request(handler: RunPodHandler) -> None:
    result = handler.handle({"id": "job-health", "input": {"health": True}})
    assert result["model_loaded"] is True
    assert result["model_id"] == "zai-org/GLM-OCR"


def test_ocr_success(handler: RunPodHandler) -> None:
    result = handler.handle({"id": "job-1", "input": {"image": "abc"}})
    assert result["success"] is True
    assert result["pages"][0]["text"] == "hello"


def test_ocr_exception(handler: RunPodHandler) -> None:
    handler._context.ocr_service.process.side_effect = InvalidImageException("bad image")
    result = handler.handle({"id": "job-2", "input": {"image": "abc"}})
    assert result["success"] is False
    assert result["error"]["code"] == "INVALID_IMAGE"


def test_validation_error(handler: RunPodHandler) -> None:
    result = handler.handle({"id": "job-3", "input": {}})
    assert result["success"] is False
    assert result["error"]["code"] == "VALIDATION_ERROR"
