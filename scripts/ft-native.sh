#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

FREQTRADE_DIR="${FREQTRADE_DIR:-/opt/freqtrade}"
FREQTRADE_BIN="${FREQTRADE_BIN:-$FREQTRADE_DIR/.venv/bin/freqtrade}"

if [[ ! -x "$FREQTRADE_BIN" ]]; then
  echo "Freqtrade binary not found or not executable: $FREQTRADE_BIN" >&2
  echo "Set FREQTRADE_DIR or FREQTRADE_BIN, or install Freqtrade under /opt/freqtrade." >&2
  exit 127
fi

cd "$ROOT_DIR/freqtrade"
exec "$FREQTRADE_BIN" "$@"
