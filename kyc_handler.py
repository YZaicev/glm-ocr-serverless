"""RunPod Serverless entrypoint for combined KYC worker."""

from __future__ import annotations

import runpod

from app.api.kyc_dependencies import KycWorkerContext, build_kyc_worker_context
from app.api.kyc_runpod_handler import KycRunPodHandler

_CONTEXT: KycWorkerContext | None = None


def _ensure_context() -> KycWorkerContext:
    global _CONTEXT
    if _CONTEXT is None:
        _CONTEXT = build_kyc_worker_context()
    return _CONTEXT


def handler(event: dict) -> dict:
    return KycRunPodHandler(_ensure_context()).handle(event)


if __name__ == "__main__":
    _ensure_context()
    runpod.serverless.start({"handler": handler})
