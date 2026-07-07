"""Full KYC pipeline: OCR → MRZ → LLM → merged JSON."""

from __future__ import annotations

from time import perf_counter

from app.config.llm_settings import LlmSettings
from app.schemas.kyc.document import KycNormalizeInput, build_validation
from app.schemas.kyc.pipeline import KycParseJobInput, KycPipelineResponse
from app.schemas.request import OCRJobInput
from app.services.kyc_field_merge import merge_kyc_fields
from app.services.kyc_normalizer_service import KycNormalizerService
from app.services.mrz_parser_service import MrzParserService
from app.services.ocr_service import OCRService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class KycPipelineService:
    """Run OCR, MRZ parsing, and LLM normalization in one worker."""

    def __init__(
        self,
        settings: LlmSettings,
        ocr_service: OCRService,
        mrz_parser: MrzParserService,
        kyc_normalizer: KycNormalizerService,
    ) -> None:
        self._settings = settings
        self._ocr_service = ocr_service
        self._mrz_parser = mrz_parser
        self._kyc_normalizer = kyc_normalizer

    def parse(self, job_input: KycParseJobInput) -> KycPipelineResponse:
        logger.info("KYC pipeline started (document_type=%s)", job_input.document_type)
        start = perf_counter()

        ocr_input = OCRJobInput(
            image=job_input.image,
            image_url=job_input.image_url,
            pdf=job_input.pdf,
            prompt=job_input.prompt,
        )
        ocr = self._ocr_service.process(ocr_input)
        ocr_pages = [page.model_dump() for page in ocr.pages]

        mrz = self._mrz_parser.parse_from_pages(ocr_pages)

        llm_result = self._kyc_normalizer.normalize(
            KycNormalizeInput(
                document_type=job_input.document_type,
                country=job_input.country,
                locale=job_input.locale,
                ocr_pages=ocr_pages,
                mrz_fields=mrz.fields if mrz.valid else None,
            )
        )

        merged_fields = merge_kyc_fields(
            llm_result.fields,
            mrz.fields if mrz.valid else None,
        )
        validation = build_validation(merged_fields, job_input.document_type)
        if mrz.valid:
            validation = validation.model_copy(
                update={"confidence": min(1.0, round(validation.confidence + 0.1, 2))}
            )

        elapsed_ms = int((perf_counter() - start) * 1000)
        logger.info("KYC pipeline completed (%d ms)", elapsed_ms)

        return KycPipelineResponse(
            processing_time_ms=elapsed_ms,
            document_type=job_input.document_type,
            ocr=ocr,
            mrz=mrz,
            fields=merged_fields,
            validation=validation,
            llm_model_id=self._settings.model_id,
        )
