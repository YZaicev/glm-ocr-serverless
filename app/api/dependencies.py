"""Worker dependency wiring and lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import httpx

from app.config.settings import Settings, get_settings
from app.models.model_manager import ModelManager
from app.services.health_service import HealthService
from app.services.image_loader import ImageLoaderService
from app.services.ocr_service import OCRService
from app.services.pdf_loader import PdfLoaderService
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class WorkerContext:
    """Shared worker dependencies."""

    settings: Settings
    ocr_service: OCRService
    health_service: HealthService
    image_loader: ImageLoaderService

    def shutdown(self) -> None:
        self.image_loader.close()


def build_worker_context() -> WorkerContext:
    """Initialize logging, preload model, and wire services."""
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Worker start")

    model_manager = ModelManager.get_instance(settings)
    model_manager.load()

    http_client = httpx.Client(
        timeout=settings.request_timeout_seconds,
        follow_redirects=True,
    )
    image_loader = ImageLoaderService(settings, http_client=http_client)
    pdf_loader = PdfLoaderService(settings)

    ocr_service = OCRService(
        settings=settings,
        model_manager=model_manager,
        image_loader=image_loader,
        pdf_loader=pdf_loader,
    )
    health_service = HealthService(
        settings=settings,
        model_manager=model_manager,
        started_at=perf_counter(),
    )

    return WorkerContext(
        settings=settings,
        ocr_service=ocr_service,
        health_service=health_service,
        image_loader=image_loader,
    )
