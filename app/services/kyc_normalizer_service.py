"""KYC normalization using GLM LLM."""

from __future__ import annotations

import json
from time import perf_counter

from app.config.llm_settings import LlmSettings
from app.core.exceptions import ValidationException
from app.models.llm_manager import LlmManager
from app.schemas.kyc.document import (
    KycFields,
    KycNormalizeInput,
    KycNormalizeResponse,
    build_validation,
)
from app.utils.json_utils import extract_json_object
from app.utils.logging import get_logger

logger = get_logger(__name__)


class KycNormalizerService:
    """Convert OCR text into fixed KYC JSON using GLM LLM."""

    def __init__(self, settings: LlmSettings, llm_manager: LlmManager) -> None:
        self._settings = settings
        self._llm_manager = llm_manager

    def normalize(self, job_input: KycNormalizeInput) -> KycNormalizeResponse:
        if job_input.task != "kyc_normalize":
            msg = f"Unsupported task: {job_input.task}"
            raise ValidationException(msg)

        logger.info("KYC normalization started (document_type=%s)", job_input.document_type)
        start = perf_counter()

        prompt = self._build_prompt(job_input)
        raw_output = self._llm_manager.generate_json(user_prompt=prompt)
        fields = self._parse_fields(raw_output)

        validation = build_validation(fields, job_input.document_type)
        elapsed_ms = int((perf_counter() - start) * 1000)
        logger.info("KYC normalization completed (%d ms)", elapsed_ms)

        return KycNormalizeResponse(
            processing_time_ms=elapsed_ms,
            document_type=job_input.document_type,
            fields=fields,
            validation=validation,
            model_id=self._settings.model_id,
        )

    def _build_prompt(self, job_input: KycNormalizeInput) -> str:
        ocr_text = self._join_ocr_pages(job_input.ocr_pages)
        schema = KycFields.model_json_schema()

        return (
            "Extract KYC fields from OCR text and return ONLY JSON.\n"
            f"document_type: {job_input.document_type.value}\n"
            f"country: {job_input.country or 'unknown'}\n"
            f"locale: {job_input.locale or 'en'}\n"
            "Rules:\n"
            "- dates must be YYYY-MM-DD or null\n"
            "- country/nationality should be ISO 3166-1 alpha-3 when possible\n"
            "- do not add extra keys\n"
            "- use null when value is missing\n"
            f"JSON schema:\n{json.dumps(schema, ensure_ascii=True)}\n"
            "OCR text:\n"
            f"{ocr_text}"
        )

    @staticmethod
    def _join_ocr_pages(pages: list[dict[str, object]]) -> str:
        chunks: list[str] = []
        for index, page in enumerate(pages, start=1):
            page_no = page.get("page", index)
            text = str(page.get("text", "")).strip()
            chunks.append(f"[PAGE {page_no}]\n{text}")
        return "\n\n".join(chunks)

    def _parse_fields(self, raw_output: str) -> KycFields:
        try:
            payload = extract_json_object(raw_output)
            return KycFields.model_validate(payload)
        except Exception:
            logger.warning("First JSON parse failed, retrying with repair prompt")
            repair_prompt = (
                "Fix this into valid JSON only, matching the same schema:\n"
                f"{raw_output}"
            )
            repaired = self._llm_manager.generate_json(user_prompt=repair_prompt)
            try:
                payload = extract_json_object(repaired)
                return KycFields.model_validate(payload)
            except Exception as second_error:
                msg = "Failed to parse KYC JSON from LLM output."
                raise ValidationException(msg) from second_error
