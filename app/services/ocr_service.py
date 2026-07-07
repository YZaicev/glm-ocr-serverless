"""OCR orchestration service."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from time import perf_counter

from PIL import Image

from app.config.settings import Settings
from app.core.exceptions import TimeoutException, ValidationException
from app.models.model_manager import ModelManager
from app.schemas.request import OCRJobInput
from app.schemas.response import OCRPageResult, OCRSuccessResponse
from app.services.image_loader import ImageLoaderService
from app.services.pdf_loader import PdfLoaderService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class OCRService:
    """Validate input, prepare images, run OCR, and return structured results."""

    def __init__(
        self,
        settings: Settings,
        model_manager: ModelManager,
        image_loader: ImageLoaderService,
        pdf_loader: PdfLoaderService,
    ) -> None:
        self._settings = settings
        self._model_manager = model_manager
        self._image_loader = image_loader
        self._pdf_loader = pdf_loader

    def process(self, job_input: OCRJobInput) -> OCRSuccessResponse:
        """Process a validated OCR job input."""
        logger.info("Processing started")
        start = perf_counter()

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._process_images, job_input)
                response = future.result(timeout=self._settings.request_timeout_seconds)
        except FuturesTimeoutError as exc:
            timeout = self._settings.request_timeout_seconds
            logger.error("Processing failed: timeout after %.1fs", timeout)
            raise TimeoutException("OCR processing timed out.") from exc

        elapsed_ms = int((perf_counter() - start) * 1000)
        logger.info("Processing completed (%d ms)", elapsed_ms)
        return OCRSuccessResponse(processing_time_ms=elapsed_ms, pages=response)

    def _process_images(self, job_input: OCRJobInput) -> list[OCRPageResult]:
        images = self._load_images(job_input)
        pages: list[OCRPageResult] = []

        for page_number, image in enumerate(images, start=1):
            text = self._model_manager.recognize(image, prompt=job_input.prompt)
            pages.append(OCRPageResult(page=page_number, text=text))

        return pages

    def _load_images(self, job_input: OCRJobInput) -> list[Image.Image]:
        if job_input.image is not None:
            return [self._image_loader.load_from_base64(job_input.image)]
        if job_input.image_url is not None:
            return [self._image_loader.load_from_url(job_input.image_url)]
        if job_input.pdf is not None:
            return self._pdf_loader.load_from_base64(job_input.pdf)

        msg = "No supported input source provided."
        raise ValidationException(msg)
