#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:."

if [ -f orchestrator/.env ]; then
  set -a
  # shellcheck disable=SC1091
  source orchestrator/.env
  set +a
fi

exec uvicorn orchestrator.main:app --host "${ORCHESTRATOR_HOST:-0.0.0.0}" --port "${ORCHESTRATOR_PORT:-8080}"
