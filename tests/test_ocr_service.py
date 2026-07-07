"""Tests for OCRService."""

import base64
from io import BytesIO
from unittest import mock

import pytest
from PIL import Image

from app.config.settings import Settings
from app.core.exceptions import TimeoutException, ValidationException
from app.models.model_manager import ModelManager
from app.schemas.request import OCRJobInput
from app.services.image_loader import ImageLoaderService
from app.services.ocr_service import OCRService
from app.services.pdf_loader import PdfLoaderService


@pytest.fixture(autouse=True)
def reset_model_manager_singleton() -> None:
    ModelManager._instance = None  # type: ignore[attr-defined]
    yield
    ModelManager._instance = None  # type: ignore[attr-defined]


def _png_base64() -> str:
    image = Image.new("RGB", (32, 32), color="green")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _build_service() -> tuple[OCRService, mock.Mock]:
    settings = Settings(device="cpu", torch_dtype="float32", request_timeout_seconds=5.0)
    model_manager = mock.Mock(spec=ModelManager)
    model_manager.recognize.return_value = "recognized text"

    image_loader = mock.Mock(spec=ImageLoaderService)
    image_loader.load_from_base64.return_value = Image.new("RGB", (32, 32))

    pdf_loader = mock.Mock(spec=PdfLoaderService)

    service = OCRService(
        settings=settings,
        model_manager=model_manager,
        image_loader=image_loader,
        pdf_loader=pdf_loader,
    )
    return service, model_manager


def test_process_base64_image() -> None:
    service, model_manager = _build_service()
    result = service.process(OCRJobInput(image=_png_base64()))

    assert result.success is True
    assert len(result.pages) == 1
    assert result.pages[0].page == 1
    assert result.pages[0].text == "recognized text"
    assert result.processing_time_ms >= 0
    model_manager.recognize.assert_called_once()


def test_process_pdf_multiple_pages() -> None:
    settings = Settings(device="cpu", torch_dtype="float32")
    model_manager = mock.Mock(spec=ModelManager)
    model_manager.recognize.side_effect = ["page one", "page two"]

    image_loader = mock.Mock(spec=ImageLoaderService)
    pdf_loader = mock.Mock(spec=PdfLoaderService)
    pdf_loader.load_from_base64.return_value = [
        Image.new("RGB", (10, 10)),
        Image.new("RGB", (10, 10)),
    ]

    service = OCRService(settings, model_manager, image_loader, pdf_loader)
    result = service.process(OCRJobInput(pdf="dGVzdA=="))

    assert len(result.pages) == 2
    assert result.pages[0].text == "page one"
    assert result.pages[1].text == "page two"


def test_process_timeout() -> None:
    settings = Settings(device="cpu", torch_dtype="float32", request_timeout_seconds=0.001)
    model_manager = mock.Mock(spec=ModelManager)

    def slow_recognize(*_args: object, **_kwargs: object) -> str:
        import time

        time.sleep(0.05)
        return "late"

    model_manager.recognize.side_effect = slow_recognize

    image_loader = mock.Mock(spec=ImageLoaderService)
    image_loader.load_from_base64.return_value = Image.new("RGB", (8, 8))
    pdf_loader = mock.Mock(spec=PdfLoaderService)

    service = OCRService(settings, model_manager, image_loader, pdf_loader)
    with pytest.raises(TimeoutException):
        service.process(OCRJobInput(image=_png_base64()))


def test_process_no_input_raises() -> None:
    service, _ = _build_service()
    job_input = OCRJobInput.model_construct(image=None, image_url=None, pdf=None)
    with pytest.raises(ValidationException):
        service._load_images(job_input)
