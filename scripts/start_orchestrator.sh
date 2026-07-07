#!/usr/bin/env bash
set -euo pipefail

exec "$(dirname "$0")/start_flash_dev.sh" "$@"
