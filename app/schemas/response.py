"""OCR API response schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.errors import ErrorCode


class OCRPageResult(BaseModel):
    """OCR result for a single page."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    text: str


class OCRSuccessResponse(BaseModel):
    """Successful OCR response."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    processing_time_ms: int = Field(ge=0)
    pages: list[OCRPageResult]


class ErrorDetail(BaseModel):
    """Structured error detail."""

    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str


class ErrorResponse(BaseModel):
    """Failed OCR response."""

    model_config = ConfigDict(extra="forbid")

    success: bool = False
    error: ErrorDetail
