"""Fixed KYC document schemas."""

from app.schemas.kyc.document import (
    REQUIRED_FIELDS_BY_TYPE,
    KycDocumentType,
    KycFields,
    KycNormalizeInput,
    KycNormalizeResponse,
    KycValidation,
)

__all__ = [
    "KycDocumentType",
    "KycFields",
    "KycValidation",
    "KycNormalizeInput",
    "KycNormalizeResponse",
    "REQUIRED_FIELDS_BY_TYPE",
]
