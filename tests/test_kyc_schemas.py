"""Tests for KYC schemas."""

from app.schemas.kyc.document import (
    KycDocumentType,
    KycFields,
    KycNormalizeInput,
    build_validation,
)


def test_build_validation_complete_passport() -> None:
    fields = KycFields(
        full_name="IVAN IVANOV",
        date_of_birth="1990-01-15",
        document_number="123456789",
        nationality="RUS",
        expiry_date="2030-01-14",
    )
    validation = build_validation(fields, KycDocumentType.PASSPORT)
    assert validation.is_complete is True
    assert validation.missing_fields == []


def test_build_validation_missing_fields() -> None:
    fields = KycFields(full_name="IVAN IVANOV")
    validation = build_validation(fields, KycDocumentType.PASSPORT)
    assert validation.is_complete is False
    assert "document_number" in validation.missing_fields


def test_kyc_normalize_input_schema() -> None:
    payload = KycNormalizeInput(
        document_type=KycDocumentType.ID_CARD,
        country="RU",
        ocr_pages=[{"page": 1, "text": "sample"}],
    )
    assert payload.task == "kyc_normalize"
