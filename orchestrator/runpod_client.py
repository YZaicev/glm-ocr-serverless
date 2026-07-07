"""RunPod Serverless API client."""

from __future__ import annotations

from typing import Any

import httpx

from orchestrator.config import OrchestratorSettings


class RunPodClient:
    """Client for RunPod /runsync endpoint calls."""

    def __init__(self, settings: OrchestratorSettings) -> None:
        self._settings = settings
        self._client = httpx.Client(
            timeout=settings.request_timeout_seconds,
            headers={
                "Authorization": f"Bearer {settings.runpod_api_key}",
                "Content-Type": "application/json",
            },
        )

    def runsync(self, endpoint_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._settings.runpod_base_url.rstrip('/')}/{endpoint_id}/runsync"
        response = self._client.post(url, json={"input": payload})
        response.raise_for_status()
        body = response.json()

        if isinstance(body, dict) and "output" in body:
            output = body["output"]
            if isinstance(output, dict):
                return output
            msg = "RunPod output is not a JSON object."
            raise ValueError(msg)

        if isinstance(body, dict):
            return body

        msg = "Unexpected RunPod response format."
        raise ValueError(msg)

    def close(self) -> None:
        self._client.close()
