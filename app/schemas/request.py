"""Incoming OCR request schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OCRJobInput(BaseModel):
    """RunPod job input payload."""

    model_config = ConfigDict(extra="forbid")

    image: str | None = Field(
        default=None,
        description="Base64-encoded image data (optionally with data-URI prefix).",
    )
    image_url: str | None = Field(default=None, description="Public URL of an image to process.")
    pdf: str | None = Field(
        default=None,
        description="Base64-encoded PDF data (optionally with data-URI prefix).",
    )
    prompt: str | None = Field(
        default=None,
        description="Optional OCR prompt override. Defaults to 'Text Recognition:'.",
    )

    @model_validator(mode="after")
    def validate_single_input_source(self) -> OCRJobInput:
        sources = [self.image, self.image_url, self.pdf]
        source_names = ("image", "image_url", "pdf")
        provided = [name for name, value in zip(source_names, sources, strict=True) if value]
        if len(provided) != 1:
            msg = "Exactly one of 'image', 'image_url', or 'pdf' must be provided."
            raise ValueError(msg)
        return self


class OCRRequest(BaseModel):
    """Top-level RunPod handler request wrapper."""

    model_config = ConfigDict(extra="allow")

    input: OCRJobInput
    id: str | None = None

    @classmethod
    def from_runpod_event(cls, event: dict[str, Any]) -> OCRRequest:
        """Parse a RunPod serverless event into a validated request."""
        raw_input = event.get("input")
        if not isinstance(raw_input, dict):
            msg = "Missing or invalid 'input' field in request."
            raise ValueError(msg)
        return cls(
            input=OCRJobInput.model_validate(raw_input),
            id=event.get("id"),
        )
