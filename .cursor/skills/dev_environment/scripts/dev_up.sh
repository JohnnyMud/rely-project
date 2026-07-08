#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${SCRIPT_DIR}/../.runtime"
mkdir -p "${RUNTIME_DIR}"

BACKEND_LOG="${RUNTIME_DIR}/backend.log"
FRONTEND_LOG="${RUNTIME_DIR}/frontend.log"
TUNNEL_LOG="${RUNTIME_DIR}/tunnel.log"

BACKEND_PID_FILE="${RUNTIME_DIR}/backend.pid"
FRONTEND_PID_FILE="${RUNTIME_DIR}/frontend.pid"
TUNNEL_PID_FILE="${RUNTIME_DIR}/tunnel.pid"

AUTOSTART_POSTGRES="${AUTOSTART_POSTGRES:-1}"
AUTO_UPDATE_RETELL_WEBHOOK="${AUTO_UPDATE_RETELL_WEBHOOK:-0}"
BACKEND_HEALTH_URL="${BACKEND_HEALTH_URL:-http://127.0.0.1:8000/}"

ensure_not_running() {
  local pid_file="$1"
  local name="$2"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}")"
    if kill -0 "${pid}" 2>/dev/null; then
      echo "${name} appears to already be running (pid ${pid})."
      echo "Run dev_down.sh first or remove stale pid files."
      exit 1
    fi
    rm -f "${pid_file}"
  fi
}

extract_trycloudflare_url() {
  local log_file="$1"
  awk 'match($0,/https:\/\/[-a-zA-Z0-9.]*trycloudflare.com/) {print substr($0, RSTART, RLENGTH); exit}' "${log_file}"
}

wait_for_health() {
  local attempts=30
  local wait_seconds=1
  for ((i=1; i<=attempts; i++)); do
    if curl -fsS "${BACKEND_HEALTH_URL}" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${wait_seconds}"
  done
  return 1
}

start_postgres_if_configured() {
  if [[ "${AUTOSTART_POSTGRES}" != "1" ]]; then
    return 0
  fi
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found; skipping PostgreSQL autostart."
    return 0
  fi

  if docker compose config --services >/dev/null 2>&1; then
    if docker compose config --services | awk '/^postgres$/{found=1} END{exit !found}'; then
      echo "Starting docker compose service: db"
      docker compose up -d db
      return 0
    fi
  fi
  echo "No docker compose db service detected; skipping PostgreSQL autostart."
}

ensure_not_running "${BACKEND_PID_FILE}" "Backend"
ensure_not_running "${FRONTEND_PID_FILE}" "Frontend"
ensure_not_running "${TUNNEL_PID_FILE}" "Tunnel"

start_postgres_if_configured

echo "Starting backend..."
"${SCRIPT_DIR}/run_backend.sh" >"${BACKEND_LOG}" 2>&1 &
echo $! >"${BACKEND_PID_FILE}"

if ! wait_for_health; then
  echo "Backend health check failed at ${BACKEND_HEALTH_URL}."
  echo "See ${BACKEND_LOG} for details."
  exit 1
fi

echo "Starting frontend..."
"${SCRIPT_DIR}/run_frontend.sh" >"${FRONTEND_LOG}" 2>&1 &
echo $! >"${FRONTEND_PID_FILE}"

echo "Starting tunnel..."
"${SCRIPT_DIR}/run_tunnel.sh" >"${TUNNEL_LOG}" 2>&1 &
echo $! >"${TUNNEL_PID_FILE}"

echo "Waiting for Cloudflare URL..."
TUNNEL_URL=""
for _ in $(seq 1 60); do
  if [[ -f "${TUNNEL_LOG}" ]]; then
    TUNNEL_URL="$(extract_trycloudflare_url "${TUNNEL_LOG}" || true)"
    if [[ -n "${TUNNEL_URL}" ]]; then
      break
    fi
  fi
  sleep 1
done

if [[ -z "${TUNNEL_URL}" ]]; then
  echo "Tunnel URL not found yet. Check ${TUNNEL_LOG}."
  exit 1
fi

echo "Tunnel URL: ${TUNNEL_URL}"

if [[ "${AUTO_UPDATE_RETELL_WEBHOOK}" == "1" ]]; then
  echo "Updating Retell webhook..."
  "${SCRIPT_DIR}/update_retell_webhook.py" --tunnel-url "${TUNNEL_URL}" --apply || true
else
  echo "Retell update skipped (AUTO_UPDATE_RETELL_WEBHOOK=0)."
  echo "Run manually:"
  echo "  ${SCRIPT_DIR}/update_retell_webhook.py --tunnel-url ${TUNNEL_URL} --apply"
fi

echo "Environment ready."
echo "Logs:"
echo "  backend:  ${BACKEND_LOG}"
echo "  frontend: ${FRONTEND_LOG}"
echo "  tunnel:   ${TUNNEL_LOG}"
