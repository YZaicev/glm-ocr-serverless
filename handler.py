"""RunPod Serverless entrypoint."""

from __future__ import annotations

import runpod

from app.api.dependencies import WorkerContext, build_worker_context
from app.api.runpod_handler import RunPodHandler

_CONTEXT: WorkerContext | None = None


def _ensure_context() -> WorkerContext:
    global _CONTEXT
    if _CONTEXT is None:
        _CONTEXT = build_worker_context()
    return _CONTEXT


def handler(event: dict) -> dict:
    """Thin RunPod handler — delegates all logic to RunPodHandler."""
    return RunPodHandler(_ensure_context()).handle(event)


if __name__ == "__main__":
    _ensure_context()
    runpod.serverless.start({"handler": handler})
