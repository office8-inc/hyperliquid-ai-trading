#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <freqtrade-command> [args...]" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COMMAND="$1"
shift

exec "$SCRIPT_DIR/ft-native.sh" "$COMMAND" \
  --config user_data/config.json \
  --config user_data/config-private.json \
  "$@"
