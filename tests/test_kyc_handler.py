"""Tests for combined KYC RunPod handler."""

from unittest import mock

from app.api.kyc_dependencies import KycWorkerContext
from app.api.kyc_runpod_handler import KycRunPodHandler
from app.schemas.health import HealthResponse
from app.schemas.kyc.document import KycDocumentType, KycFields, KycValidation
from app.schemas.kyc.mrz import MrzParseResult
from app.schemas.kyc.pipeline import KycPipelineResponse
from app.schemas.response import OCRPageResult, OCRSuccessResponse


def test_kyc_health_request() -> None:
    context = KycWorkerContext(
        settings=mock.Mock(),
        llm_settings=mock.Mock(model_id="Qwen/Qwen2.5-3B-Instruct"),
        pipeline_service=mock.Mock(),
        ocr_service=mock.Mock(),
        ocr_health_service=mock.Mock(
            get_status=mock.Mock(
                return_value=HealthResponse(
                    model_loaded=True,
                    gpu_available=True,
                    cuda_version="12.6",
                    torch_version="2.4.0",
                    model_id="zai-org/GLM-OCR",
                    uptime_seconds=1.0,
                )
            )
        ),
        llm_health_service=mock.Mock(
            get_status=mock.Mock(
                return_value=HealthResponse(
                    model_loaded=True,
                    gpu_available=True,
                    cuda_version="12.6",
                    torch_version="2.4.0",
                    model_id="Qwen/Qwen2.5-3B-Instruct",
                    uptime_seconds=1.0,
                )
            )
        ),
        image_loader=mock.Mock(),
    )
    handler = KycRunPodHandler(context)
    result = handler.handle({"input": {"health": True}})
    assert result["status"] == "ok"
    assert result["llm_model_id"] == "Qwen/Qwen2.5-3B-Instruct"


def test_kyc_parse_request() -> None:
    pipeline = mock.Mock()
    pipeline.parse.return_value = KycPipelineResponse(
        processing_time_ms=100,
        document_type=KycDocumentType.PASSPORT,
        ocr=OCRSuccessResponse(
            processing_time_ms=40,
            pages=[OCRPageResult(page=1, text="P<UTO...")],
        ),
        mrz=MrzParseResult(parsed=True, valid=True, format="TD3"),
        fields=KycFields(full_name="ANNA MARIA ERIKSSON"),
        validation=KycValidation(is_complete=False, missing_fields=["nationality"], confidence=0.5),
        llm_model_id="Qwen/Qwen2.5-3B-Instruct",
    )
    context = mock.Mock()
    context.pipeline_service = pipeline
    handler = KycRunPodHandler(context)
    result = handler.handle(
        {
            "input": {
                "task": "kyc_parse",
                "image": "abc",
                "document_type": "passport",
            }
        }
    )
    assert result["success"] is True
    assert result["fields"]["full_name"] == "ANNA MARIA ERIKSSON"
