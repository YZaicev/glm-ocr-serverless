"""Tests for Flash KYC orchestration service."""

import asyncio
from unittest import mock

import pytest
from fastapi import HTTPException

from app.schemas.kyc.document import (
    KycDocumentType,
    KycFields,
    KycValidation,
)
from flash.kyc_service import parse_kyc_document
from orchestrator.schemas import KycParseRequest


class _FakeJob:
    def __init__(self, output: object) -> None:
        self.output = output


def test_parse_kyc_document_success() -> None:
    async def _run() -> None:
        ocr_endpoint = mock.AsyncMock()
        llm_endpoint = mock.AsyncMock()
        ocr_endpoint.runsync.return_value = _FakeJob(
            {
                "success": True,
                "processing_time_ms": 100,
                "pages": [{"page": 1, "text": "PASSPORT IVAN IVANOV"}],
            }
        )
        llm_endpoint.runsync.return_value = _FakeJob(
            {
                "success": True,
                "processing_time_ms": 200,
                "document_type": "passport",
                "fields": {"full_name": "IVAN IVANOV"},
                "validation": {
                    "is_complete": False,
                    "missing_fields": ["document_number"],
                    "confidence": 0.2,
                },
                "model_id": "zai-org/glm-4-9b-chat-hf",
            }
        )

        request = KycParseRequest(
            image_base64="data:image/png;base64,abc",
            document_type=KycDocumentType.PASSPORT,
            country="RU",
        )
        response = await parse_kyc_document(ocr_endpoint, llm_endpoint, request)

        assert response.ocr.pages[0].text == "PASSPORT IVAN IVANOV"
        assert response.kyc.fields == KycFields(full_name="IVAN IVANOV")
        assert response.kyc.validation == KycValidation(
            is_complete=False,
            missing_fields=["document_number"],
            confidence=0.2,
        )
        ocr_endpoint.runsync.assert_awaited_once()
        llm_endpoint.runsync.assert_awaited_once()

    asyncio.run(_run())


def test_parse_kyc_document_ocr_failure() -> None:
    async def _run() -> None:
        ocr_endpoint = mock.AsyncMock()
        llm_endpoint = mock.AsyncMock()
        ocr_endpoint.runsync.return_value = _FakeJob(
            {
                "success": False,
                "error": {"code": "INVALID_IMAGE", "message": "bad image"},
            }
        )

        request = KycParseRequest(
            image_base64="bad",
            document_type=KycDocumentType.PASSPORT,
        )

        with pytest.raises(HTTPException) as exc_info:
            await parse_kyc_document(ocr_endpoint, llm_endpoint, request)

        assert exc_info.value.status_code == 502
        llm_endpoint.runsync.assert_not_awaited()

    asyncio.run(_run())
