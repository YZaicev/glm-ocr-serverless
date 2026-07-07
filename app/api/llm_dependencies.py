"""LLM worker dependency wiring."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from app.config.llm_settings import LlmSettings, get_llm_settings
from app.models.llm_manager import LlmManager
from app.services.kyc_normalizer_service import KycNormalizerService
from app.services.llm_health_service import LlmHealthService
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class LlmWorkerContext:
    """Shared LLM worker dependencies."""

    settings: LlmSettings
    kyc_normalizer: KycNormalizerService
    health_service: LlmHealthService


def build_llm_worker_context() -> LlmWorkerContext:
    settings = get_llm_settings()
    configure_logging(settings.log_level)
    logger.info("LLM worker start")

    llm_manager = LlmManager.get_instance(settings)
    llm_manager.load()

    kyc_normalizer = KycNormalizerService(settings=settings, llm_manager=llm_manager)
    health_service = LlmHealthService(
        settings=settings,
        llm_manager=llm_manager,
        started_at=perf_counter(),
    )

    return LlmWorkerContext(
        settings=settings,
        kyc_normalizer=kyc_normalizer,
        health_service=health_service,
    )
