"""Orchestrator API schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.kyc.document import KycDocumentType, KycNormalizeResponse
from app.schemas.response import OCRSuccessResponse


class KycParseRequest(BaseModel):
    """Incoming local orchestrator request."""

    model_config = ConfigDict(extra="forbid")

    image_base64: str
    document_type: KycDocumentType
    country: str | None = None
    locale: str = "en"
    prompt: str | None = None


class KycParseResponse(BaseModel):
    """Combined OCR + KYC response."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    processing_time_ms: int = Field(ge=0)
    ocr: OCRSuccessResponse
    kyc: KycNormalizeResponse
