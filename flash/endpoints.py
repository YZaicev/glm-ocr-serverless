"""RunPod Flash endpoint definitions for OCR and LLM Docker workers."""

from runpod_flash import Endpoint, PodTemplate

from flash.settings import FlashSettings

_settings = FlashSettings()

ocr = Endpoint(
    name="glm-ocr",
    image=_settings.ocr_image,
    gpu=_settings.ocr_gpu,
    workers=_settings.ocr_workers,
    idle_timeout=_settings.idle_timeout_seconds,
    env=_settings.worker_env,
    template=PodTemplate(containerDiskInGb=_settings.ocr_container_disk_gb),
    execution_timeout_ms=_settings.ocr_timeout_ms,
    min_cuda_version="12.6",
)

llm = Endpoint(
    name="glm-llm",
    image=_settings.llm_image,
    gpu=_settings.llm_gpu,
    workers=_settings.llm_workers,
    idle_timeout=_settings.idle_timeout_seconds,
    env=_settings.worker_env,
    template=PodTemplate(containerDiskInGb=_settings.llm_container_disk_gb),
    execution_timeout_ms=_settings.llm_timeout_ms,
    min_cuda_version="12.6",
)
