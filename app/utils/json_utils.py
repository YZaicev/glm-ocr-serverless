"""JSON parsing helpers for LLM outputs."""

from __future__ import annotations

import json
import re
from typing import Any

_JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract and parse the first JSON object from model output."""
    normalized = text.strip()
    if not normalized:
        msg = "LLM returned empty response."
        raise ValueError(msg)

    candidates: list[str] = [normalized]
    block_match = _JSON_BLOCK_PATTERN.search(normalized)
    if block_match:
        candidates.insert(0, block_match.group(1))

    start = normalized.find("{")
    end = normalized.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(normalized[start : end + 1])

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if not isinstance(parsed, dict):
            msg = "LLM JSON root must be an object."
            raise ValueError(msg)
        return parsed

    msg = "Unable to parse JSON object from LLM response."
    raise ValueError(msg) from last_error
