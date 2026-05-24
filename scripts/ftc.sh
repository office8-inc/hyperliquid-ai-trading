#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <freqtrade-command> [args...]" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

COMMAND="$1"
shift

cd "$ROOT_DIR/freqtrade"
exec docker compose run --rm freqtrade "$COMMAND" \
  --config /freqtrade/user_data/config.json \
  --config /freqtrade/user_data/config-private.json \
  "$@"
