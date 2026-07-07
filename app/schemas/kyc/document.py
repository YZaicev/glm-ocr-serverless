"""Fixed KYC JSON schema for document normalization."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KycDocumentType(StrEnum):
    """Supported KYC document categories."""

    PASSPORT = "passport"
    ID_CARD = "id_card"
    DRIVER_LICENSE = "driver_license"
    PROOF_OF_ADDRESS = "proof_of_address"


REQUIRED_FIELDS_BY_TYPE: Final[dict[KycDocumentType, tuple[str, ...]]] = {
    KycDocumentType.PASSPORT: (
        "full_name",
        "date_of_birth",
        "document_number",
        "nationality",
        "expiry_date",
    ),
    KycDocumentType.ID_CARD: (
        "full_name",
        "date_of_birth",
        "document_number",
        "issuing_country",
        "expiry_date",
    ),
    KycDocumentType.DRIVER_LICENSE: (
        "full_name",
        "date_of_birth",
        "document_number",
        "expiry_date",
    ),
    KycDocumentType.PROOF_OF_ADDRESS: (
        "full_name",
        "address_line",
        "city",
        "issue_date",
    ),
}


class KycFields(BaseModel):
    """Normalized KYC fields (fixed structure)."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = Field(default=None, description="YYYY-MM-DD")
    document_number: str | None = None
    issuing_country: str | None = Field(default=None, description="ISO 3166-1 alpha-3")
    nationality: str | None = Field(default=None, description="ISO 3166-1 alpha-3")
    expiry_date: str | None = Field(default=None, description="YYYY-MM-DD")
    issue_date: str | None = Field(default=None, description="YYYY-MM-DD")
    address_line: str | None = None
    city: str | None = None
    postal_code: str | None = None
    gender: str | None = None

    @field_validator(
        "date_of_birth",
        "expiry_date",
        "issue_date",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class KycValidation(BaseModel):
    """Validation metadata for extracted KYC data."""

    model_config = ConfigDict(extra="forbid")

    is_complete: bool
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class KycNormalizeInput(BaseModel):
    """LLM worker input for KYC normalization."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(default="kyc_normalize")
    document_type: KycDocumentType
    country: str | None = Field(default=None, description="ISO 3166-1 alpha-2/3")
    locale: str | None = Field(default="en")
    ocr_pages: list[dict[str, object]]
    mrz_fields: KycFields | None = None


class KycNormalizeResponse(BaseModel):
    """Fixed KYC normalization response."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    processing_time_ms: int = Field(ge=0)
    document_type: KycDocumentType
    fields: KycFields
    validation: KycValidation
    model_id: str


def build_validation(fields: KycFields, document_type: KycDocumentType) -> KycValidation:
    """Compute completeness based on required fields for document type."""
    required = REQUIRED_FIELDS_BY_TYPE[document_type]
    missing: list[str] = []
    payload = fields.model_dump()

    for field_name in required:
        value = payload.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field_name)

    filled_ratio = 1.0 - (len(missing) / len(required)) if required else 1.0
    confidence = round(max(0.0, min(1.0, filled_ratio)), 2)

    return KycValidation(
        is_complete=len(missing) == 0,
        missing_fields=missing,
        confidence=confidence,
    )
