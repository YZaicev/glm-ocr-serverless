"""KYC orchestration logic (OCR Flash endpoint → LLM Flash endpoint)."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Protocol

from fastapi import HTTPException

from app.schemas.kyc.document import KycNormalizeInput, KycNormalizeResponse
from app.schemas.response import OCRSuccessResponse
from orchestrator.schemas import KycParseRequest, KycParseResponse


class FlashQueueEndpoint(Protocol):
    """Subset of runpod_flash.Endpoint used by the KYC service."""

    async def runsync(self, input_data: Any, timeout: float = 60.0) -> Any: ...


def _require_success_payload(payload: object, *, step: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail={step: "invalid response type"})
    if not payload.get("success", False):
        raise HTTPException(status_code=502, detail={step: payload})
    return payload


async def parse_kyc_document(
    ocr_endpoint: FlashQueueEndpoint,
    llm_endpoint: FlashQueueEndpoint,
    request: KycParseRequest,
    *,
    ocr_timeout_seconds: float = 120.0,
    llm_timeout_seconds: float = 300.0,
) -> KycParseResponse:
    """Run OCR then LLM normalization via RunPod Flash endpoints."""
    start = perf_counter()

    ocr_payload: dict[str, object] = {"image": request.image_base64}
    if request.prompt:
        ocr_payload["prompt"] = request.prompt

    try:
        ocr_job = await ocr_endpoint.runsync(ocr_payload, timeout=ocr_timeout_seconds)
        ocr_raw = _require_success_payload(ocr_job.output, step="ocr")
        ocr = OCRSuccessResponse.model_validate(ocr_raw)

        llm_payload = KycNormalizeInput(
            document_type=request.document_type,
            country=request.country,
            locale=request.locale,
            ocr_pages=[page.model_dump() for page in ocr.pages],
        ).model_dump()

        llm_job = await llm_endpoint.runsync(llm_payload, timeout=llm_timeout_seconds)
        kyc_raw = _require_success_payload(llm_job.output, step="kyc")
        kyc = KycNormalizeResponse.model_validate(kyc_raw)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed_ms = int((perf_counter() - start) * 1000)
    return KycParseResponse(
        processing_time_ms=elapsed_ms,
        ocr=ocr,
        kyc=kyc,
    )
