"""MRZ parsing result schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.kyc.document import KycFields


class MrzParseResult(BaseModel):
    """Result of machine-readable zone extraction."""

    model_config = ConfigDict(extra="forbid")

    parsed: bool = False
    valid: bool = False
    format: str | None = Field(default=None, description="TD1, TD2, or TD3")
    fields: KycFields | None = None
    raw_lines: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
