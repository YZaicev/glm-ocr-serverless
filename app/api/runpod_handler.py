"""RunPod request handling (kept out of handler.py)."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.api.dependencies import WorkerContext
from app.core.exceptions import OCRException
from app.schemas.errors import ErrorCode
from app.schemas.request import OCRRequest
from app.schemas.response import ErrorDetail, ErrorResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RunPodHandler:
    """Translate RunPod events into OCR or health responses."""

    def __init__(self, context: WorkerContext) -> None:
        self._context = context

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        """Process a RunPod serverless event."""
        job_id = event.get("id")
        logger.info("Job received (id=%s)", job_id)

        raw_input = event.get("input")
        if isinstance(raw_input, dict) and raw_input.get("health") is True:
            return self._context.health_service.get_status().model_dump()

        try:
            request = OCRRequest.from_runpod_event(event)
            response = self._context.ocr_service.process(request.input)
            return response.model_dump()
        except OCRException as exc:
            logger.error("Processing failed: %s", exc.message)
            return exc.to_dict()
        except ValidationError as exc:
            message = "; ".join(error["msg"] for error in exc.errors())
            logger.error("Processing failed: validation error")
            return ErrorResponse(
                success=False,
                error=ErrorDetail(code=ErrorCode.VALIDATION_ERROR, message=message),
            ).model_dump()
        except ValueError as exc:
            logger.error("Processing failed: %s", exc)
            return ErrorResponse(
                success=False,
                error=ErrorDetail(code=ErrorCode.VALIDATION_ERROR, message=str(exc)),
            ).model_dump()
        except Exception:
            logger.exception("Processing failed: unexpected error")
            return ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="An unexpected error occurred.",
                ),
            ).model_dump()
