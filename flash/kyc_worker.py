"""RunPod Flash endpoint for combined KYC worker."""

from runpod_flash import Endpoint, PodTemplate

from flash.settings import FlashSettings

_settings = FlashSettings()

kyc = Endpoint(
    name="glm-kyc",
    image=_settings.kyc_image,
    gpu=_settings.kyc_gpu,
    workers=_settings.kyc_workers,
    idle_timeout=_settings.idle_timeout_seconds,
    env=_settings.worker_env,
    template=PodTemplate(containerDiskInGb=_settings.kyc_container_disk_gb),
    execution_timeout_ms=_settings.kyc_timeout_ms,
    min_cuda_version="12.6",
)
