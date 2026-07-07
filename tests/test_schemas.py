"""Tests for request/response schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.request import OCRJobInput, OCRRequest
from app.schemas.response import OCRPageResult, OCRSuccessResponse


def test_ocr_job_input_requires_exactly_one_source() -> None:
    with pytest.raises(ValidationError):
        OCRJobInput()

    with pytest.raises(ValidationError):
        OCRJobInput(image="abc", image_url="https://example.com/a.png")

    payload = OCRJobInput(image="abc")
    assert payload.image == "abc"


def test_ocr_request_from_runpod_event() -> None:
    event = {"id": "job-1", "input": {"image": "base64data"}}
    request = OCRRequest.from_runpod_event(event)
    assert request.id == "job-1"
    assert request.input.image == "base64data"


def test_ocr_request_from_runpod_event_invalid_input() -> None:
    with pytest.raises(ValueError, match="input"):
        OCRRequest.from_runpod_event({"input": "not-a-dict"})


def test_success_response_schema() -> None:
    response = OCRSuccessResponse(
        processing_time_ms=100,
        pages=[OCRPageResult(page=1, text="hello")],
    )
    assert response.success is True
    assert response.pages[0].text == "hello"
