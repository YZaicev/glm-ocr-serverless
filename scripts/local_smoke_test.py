"""Send a sample OCR request to a local RunPod handler function."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

from app.api.dependencies import build_worker_context
from app.api.runpod_handler import RunPodHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Local GLM-OCR smoke test")
    parser.add_argument("image", type=Path, help="Path to a local image file")
    args = parser.parse_args()

    image_bytes = args.image.read_bytes()
    encoded = base64.b64encode(image_bytes).decode("ascii")

    context = build_worker_context()
    handler = RunPodHandler(context)
    try:
        result = handler.handle({"id": "local-smoke", "input": {"image": encoded}})
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    finally:
        context.shutdown()


if __name__ == "__main__":
    main()
