"""RunPod Serverless entrypoint for GLM LLM KYC worker."""

from __future__ import annotations

import runpod

from app.api.llm_dependencies import LlmWorkerContext, build_llm_worker_context
from app.api.llm_runpod_handler import LlmRunPodHandler

_CONTEXT: LlmWorkerContext | None = None


def _ensure_context() -> LlmWorkerContext:
    global _CONTEXT
    if _CONTEXT is None:
        _CONTEXT = build_llm_worker_context()
    return _CONTEXT


def handler(event: dict) -> dict:
    """Thin RunPod handler for LLM normalization."""
    return LlmRunPodHandler(_ensure_context()).handle(event)


if __name__ == "__main__":
    _ensure_context()
    runpod.serverless.start({"handler": handler})
