#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}/flash"

export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if ! command -v flash >/dev/null 2>&1; then
  echo "runpod-flash CLI not found. Install: pip install runpod-flash" >&2
  exit 1
fi

exec flash dev --auto-provision "$@"
