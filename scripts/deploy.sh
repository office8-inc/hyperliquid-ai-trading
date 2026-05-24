#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hyperliquid-ai-trading}"

cd "$APP_DIR"
git pull --ff-only

cd "$APP_DIR/freqtrade"
docker compose pull
docker compose up -d
docker compose ps
