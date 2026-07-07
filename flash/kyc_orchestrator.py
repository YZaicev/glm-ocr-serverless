"""Local KYC orchestrator exposed via Flash load-balanced routes."""

from __future__ import annotations

from runpod_flash import Endpoint

from flash.endpoints import llm, ocr
from flash.kyc_service import parse_kyc_document
from flash.settings import FlashSettings
from orchestrator.schemas import KycParseRequest

_settings = FlashSettings()

api = Endpoint(
    name="glm-kyc-orchestrator",
    cpu="cpu5c-4-8",
    workers=_settings.orchestrator_workers,
    execution_timeout_ms=_settings.orchestrator_timeout_ms,
)


@api.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@api.post("/v1/kyc/parse")
async def parse_kyc(body: dict) -> dict:
    request = KycParseRequest.model_validate(body)
    response = await parse_kyc_document(
        ocr,
        llm,
        request,
        ocr_timeout_seconds=_settings.ocr_timeout_ms / 1000,
        llm_timeout_seconds=_settings.llm_timeout_ms / 1000,
    )
    return response.model_dump()
