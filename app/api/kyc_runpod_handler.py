"""RunPod handler for combined KYC worker."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.api.kyc_dependencies import KycWorkerContext
from app.core.exceptions import OCRException
from app.schemas.errors import ErrorCode
from app.schemas.kyc.pipeline import KycParseJobInput
from app.schemas.request import OCRRequest
from app.schemas.response import ErrorDetail, ErrorResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)


class KycRunPodHandler:
    """OCR-only, KYC pipeline, and health on a single GPU worker."""

    def __init__(self, context: KycWorkerContext) -> None:
        self._context = context

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        job_id = event.get("id")
        logger.info("KYC worker job received (id=%s)", job_id)

        raw_input = event.get("input")
        if isinstance(raw_input, dict) and raw_input.get("health") is True:
            return self._health_payload()

        if not isinstance(raw_input, dict):
            return self._validation_error("Missing or invalid 'input' field in request.")

        task = str(raw_input.get("task", "ocr")).strip().lower()
        try:
            if task in {"kyc_parse", "kyc"}:
                request = KycParseJobInput.model_validate(raw_input)
                response = self._context.pipeline_service.parse(request)
                return response.model_dump()

            request = OCRRequest.from_runpod_event(event)
            response = self._context.ocr_service.process(request.input)
            return response.model_dump()
        except OCRException as exc:
            logger.error("Processing failed: %s", exc.message)
            return exc.to_dict()
        except ValidationError as exc:
            message = "; ".join(error["msg"] for error in exc.errors())
            return self._validation_error(message)
        except ValueError as exc:
            return self._validation_error(str(exc))
        except Exception:
            logger.exception("Processing failed: unexpected error")
            return ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="An unexpected error occurred.",
                ),
            ).model_dump()

    def _health_payload(self) -> dict[str, Any]:
        ocr = self._context.ocr_health_service.get_status().model_dump()
        llm = self._context.llm_health_service.get_status().model_dump()
        return {
            "status": "ok",
            "ocr": ocr,
            "llm": llm,
            "llm_model_id": self._context.llm_settings.model_id,
        }

    @staticmethod
    def _validation_error(message: str) -> dict[str, Any]:
        return ErrorResponse(
            success=False,
            error=ErrorDetail(code=ErrorCode.VALIDATION_ERROR, message=message),
        ).model_dump()
