#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export FREQTRADE_IMAGE="${FREQTRADE_IMAGE:-freqtradeorg/freqtrade:2026.4_freqai}"

exec "$SCRIPT_DIR/ftc.sh" "$@"
