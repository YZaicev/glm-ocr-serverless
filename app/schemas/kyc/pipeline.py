"""Combined KYC pipeline request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.kyc.document import KycDocumentType, KycFields, KycValidation
from app.schemas.kyc.mrz import MrzParseResult
from app.schemas.response import OCRSuccessResponse


class KycParseJobInput(BaseModel):
    """RunPod input for full KYC pipeline (OCR + MRZ + LLM)."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(default="kyc_parse")
    image: str | None = Field(default=None, description="Base64 image (data-URI allowed).")
    image_url: str | None = None
    pdf: str | None = None
    document_type: KycDocumentType
    country: str | None = None
    locale: str = "en"
    prompt: str | None = None

    @model_validator(mode="after")
    def validate_single_input_source(self) -> KycParseJobInput:
        sources = [self.image, self.image_url, self.pdf]
        provided = sum(1 for value in sources if value)
        if provided != 1:
            msg = "Exactly one of 'image', 'image_url', or 'pdf' must be provided."
            raise ValueError(msg)
        return self


class KycPipelineResponse(BaseModel):
    """Full KYC pipeline response."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    processing_time_ms: int = Field(ge=0)
    document_type: KycDocumentType
    ocr: OCRSuccessResponse
    mrz: MrzParseResult
    fields: KycFields
    validation: KycValidation
    llm_model_id: str
