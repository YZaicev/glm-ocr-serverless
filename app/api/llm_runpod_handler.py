"""RunPod handler for GLM LLM KYC normalization worker."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.api.llm_dependencies import LlmWorkerContext
from app.core.exceptions import OCRException
from app.schemas.errors import ErrorCode
from app.schemas.kyc.document import KycNormalizeInput
from app.schemas.response import ErrorDetail, ErrorResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)


class LlmRunPodHandler:
    """Handle KYC normalization jobs on LLM worker."""

    def __init__(self, context: LlmWorkerContext) -> None:
        self._context = context

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        job_id = event.get("id")
        logger.info("LLM job received (id=%s)", job_id)

        raw_input = event.get("input")
        if isinstance(raw_input, dict) and raw_input.get("health") is True:
            return self._context.health_service.get_status().model_dump()

        try:
            if not isinstance(raw_input, dict):
                msg = "Missing or invalid 'input' field in request."
                raise ValueError(msg)

            request = KycNormalizeInput.model_validate(raw_input)
            response = self._context.kyc_normalizer.normalize(request)
            return response.model_dump()
        except OCRException as exc:
            logger.error("LLM processing failed: %s", exc.message)
            return exc.to_dict()
        except ValidationError as exc:
            message = "; ".join(error["msg"] for error in exc.errors())
            return ErrorResponse(
                success=False,
                error=ErrorDetail(code=ErrorCode.VALIDATION_ERROR, message=message),
            ).model_dump()
        except ValueError as exc:
            return ErrorResponse(
                success=False,
                error=ErrorDetail(code=ErrorCode.VALIDATION_ERROR, message=str(exc)),
            ).model_dump()
        except Exception:
            logger.exception("LLM processing failed: unexpected error")
            return ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="An unexpected error occurred.",
                ),
            ).model_dump()
