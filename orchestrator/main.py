"""Local KYC orchestrator (OCR endpoint + LLM endpoint)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, HTTPException

from app.schemas.kyc.document import KycNormalizeInput, KycNormalizeResponse
from app.schemas.response import OCRSuccessResponse
from orchestrator.config import OrchestratorSettings
from orchestrator.runpod_client import RunPodClient
from orchestrator.schemas import KycParseRequest, KycParseResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = OrchestratorSettings()
    client = RunPodClient(settings)
    app.state.settings = settings
    app.state.runpod_client = client
    yield
    client.close()


app = FastAPI(title="GLM KYC Orchestrator", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/kyc/parse", response_model=KycParseResponse)
def parse_kyc(request: KycParseRequest) -> KycParseResponse:
    start = perf_counter()
    settings: OrchestratorSettings = app.state.settings
    client: RunPodClient = app.state.runpod_client

    ocr_payload: dict[str, object] = {"image": request.image_base64}
    if request.prompt:
        ocr_payload["prompt"] = request.prompt

    try:
        ocr_raw = client.runsync(settings.runpod_ocr_endpoint_id, ocr_payload)
        if not ocr_raw.get("success", False):
            raise HTTPException(status_code=502, detail=ocr_raw)
        ocr = OCRSuccessResponse.model_validate(ocr_raw)

        llm_payload = KycNormalizeInput(
            document_type=request.document_type,
            country=request.country,
            locale=request.locale,
            ocr_pages=[page.model_dump() for page in ocr.pages],
        ).model_dump()

        kyc_raw = client.runsync(settings.runpod_llm_endpoint_id, llm_payload)
        if not kyc_raw.get("success", False):
            raise HTTPException(status_code=502, detail=kyc_raw)

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
