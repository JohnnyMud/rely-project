#!/usr/bin/env bash
set -euo pipefail

BACKEND_PORT="${BACKEND_PORT:-8000}"
TUNNEL_TARGET_URL="${TUNNEL_TARGET_URL:-http://localhost:${BACKEND_PORT}}"

echo "Starting Cloudflare tunnel -> ${TUNNEL_TARGET_URL}"
exec cloudflared tunnel --url "${TUNNEL_TARGET_URL}"
