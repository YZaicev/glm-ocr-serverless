"""Tests for LLM RunPod handler."""

from unittest import mock

from app.api.llm_dependencies import LlmWorkerContext
from app.api.llm_runpod_handler import LlmRunPodHandler
from app.schemas.health import HealthResponse
from app.schemas.kyc.document import (
    KycDocumentType,
    KycFields,
    KycNormalizeResponse,
    KycValidation,
)


def test_llm_health_request() -> None:
    health_service = mock.Mock()
    health_service.get_status.return_value = HealthResponse(
        model_loaded=True,
        gpu_available=True,
        cuda_version="12.6",
        torch_version="2.12.1",
        model_id="zai-org/glm-4-9b-chat-hf",
        uptime_seconds=1.0,
    )
    context = LlmWorkerContext(
        settings=mock.Mock(),
        kyc_normalizer=mock.Mock(),
        health_service=health_service,
    )
    handler = LlmRunPodHandler(context)
    result = handler.handle({"input": {"health": True}})
    assert result["model_loaded"] is True


def test_llm_kyc_request() -> None:
    kyc_normalizer = mock.Mock()
    kyc_normalizer.normalize.return_value = KycNormalizeResponse(
        processing_time_ms=100,
        document_type=KycDocumentType.PASSPORT,
        fields=KycFields(full_name="IVAN IVANOV"),
        validation=KycValidation(
            is_complete=False,
            missing_fields=["document_number"],
            confidence=0.2,
        ),
        model_id="zai-org/glm-4-9b-chat-hf",
    )
    context = LlmWorkerContext(
        settings=mock.Mock(),
        kyc_normalizer=kyc_normalizer,
        health_service=mock.Mock(),
    )
    handler = LlmRunPodHandler(context)
    result = handler.handle(
        {
            "input": {
                "task": "kyc_normalize",
                "document_type": "passport",
                "ocr_pages": [{"page": 1, "text": "IVAN IVANOV"}],
            }
        }
    )
    assert result["success"] is True
    assert result["fields"]["full_name"] == "IVAN IVANOV"
