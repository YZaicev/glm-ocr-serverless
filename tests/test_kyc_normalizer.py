"""Tests for KYC normalizer service."""

from unittest import mock

from app.config.llm_settings import LlmSettings
from app.schemas.kyc.document import KycDocumentType, KycNormalizeInput
from app.services.kyc_normalizer_service import KycNormalizerService


def test_normalize_success() -> None:
    settings = LlmSettings(device="cpu", torch_dtype="float32")
    llm_manager = mock.Mock()
    llm_manager.generate_json.return_value = (
        '{"full_name":"IVAN IVANOV","date_of_birth":"1990-01-15",'
        '"document_number":"123456789","nationality":"RUS","expiry_date":"2030-01-14"}'
    )

    service = KycNormalizerService(settings, llm_manager)
    result = service.normalize(
        KycNormalizeInput(
            document_type=KycDocumentType.PASSPORT,
            country="RU",
            ocr_pages=[{"page": 1, "text": "PASSPORT IVAN IVANOV"}],
        )
    )

    assert result.success is True
    assert result.fields.full_name == "IVAN IVANOV"
    assert result.validation.is_complete is True
