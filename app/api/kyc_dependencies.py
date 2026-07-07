"""Combined KYC worker dependency wiring."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import httpx

from app.config.llm_settings import LlmSettings, get_llm_settings
from app.config.settings import Settings, get_settings
from app.models.llm_manager import LlmManager
from app.models.model_manager import ModelManager
from app.services.health_service import HealthService
from app.services.image_loader import ImageLoaderService
from app.services.kyc_normalizer_service import KycNormalizerService
from app.services.kyc_pipeline_service import KycPipelineService
from app.services.llm_health_service import LlmHealthService
from app.services.mrz_parser_service import MrzParserService
from app.services.ocr_service import OCRService
from app.services.pdf_loader import PdfLoaderService
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class KycWorkerContext:
    """Shared dependencies for combined KYC worker."""

    settings: Settings
    llm_settings: LlmSettings
    pipeline_service: KycPipelineService
    ocr_service: OCRService
    ocr_health_service: HealthService
    llm_health_service: LlmHealthService
    image_loader: ImageLoaderService

    def shutdown(self) -> None:
        self.image_loader.close()


def build_kyc_worker_context() -> KycWorkerContext:
    ocr_settings = get_settings()
    llm_settings = get_llm_settings()
    configure_logging(ocr_settings.log_level)
    logger.info("KYC worker start")

    model_manager = ModelManager.get_instance(ocr_settings)
    llm_manager = LlmManager.get_instance(llm_settings)

    http_client = httpx.Client(
        timeout=ocr_settings.request_timeout_seconds,
        follow_redirects=True,
    )
    image_loader = ImageLoaderService(ocr_settings, http_client=http_client)
    pdf_loader = PdfLoaderService(ocr_settings)

    ocr_service = OCRService(
        settings=ocr_settings,
        model_manager=model_manager,
        image_loader=image_loader,
        pdf_loader=pdf_loader,
    )
    pipeline_service = KycPipelineService(
        settings=llm_settings,
        ocr_service=ocr_service,
        mrz_parser=MrzParserService(),
        kyc_normalizer=KycNormalizerService(settings=llm_settings, llm_manager=llm_manager),
    )

    started_at = perf_counter()
    ocr_health_service = HealthService(
        settings=ocr_settings,
        model_manager=model_manager,
        started_at=started_at,
    )
    llm_health_service = LlmHealthService(
        settings=llm_settings,
        llm_manager=llm_manager,
        started_at=started_at,
    )

    return KycWorkerContext(
        settings=ocr_settings,
        llm_settings=llm_settings,
        pipeline_service=pipeline_service,
        ocr_service=ocr_service,
        ocr_health_service=ocr_health_service,
        llm_health_service=llm_health_service,
        image_loader=image_loader,
    )
