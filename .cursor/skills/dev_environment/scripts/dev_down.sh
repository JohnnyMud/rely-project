#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${SCRIPT_DIR}/../.runtime"
STOP_DOCKER_DB_ON_DOWN="${STOP_DOCKER_DB_ON_DOWN:-0}"

stop_pid() {
  local pid="$1"
  local name="$2"

  if ! kill -0 "${pid}" 2>/dev/null; then
    return 0
  fi

  echo "Stopping ${name} (pid ${pid})"
  kill "${pid}" 2>/dev/null || true
  sleep 1
  if kill -0 "${pid}" 2>/dev/null; then
    echo "${name} still running; sending SIGKILL"
    kill -9 "${pid}" 2>/dev/null || true
  fi
}

stop_from_pid_file() {
  local pid_file="$1"
  local name="$2"
  if [[ ! -f "${pid_file}" ]]; then
    echo "${name}: no pid file"
    return 0
  fi

  local pid
  pid="$(cat "${pid_file}")"
  if [[ -z "${pid}" ]] || ! [[ "${pid}" =~ ^[0-9]+$ ]]; then
    echo "${name}: invalid pid file value (${pid})"
  elif ! kill -0 "${pid}" 2>/dev/null; then
    echo "${name}: process ${pid} not running"
  else
    stop_pid "${pid}" "${name}"
  fi
  rm -f "${pid_file}"
}

stop_if_matches_port() {
  local port="$1"
  local name="$2"
  local cmd_pattern="$3"
  local stopped_any=0

  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi

  local pids
  pids="$(lsof -t -nP -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null | sort -u || true)"
  if [[ -z "${pids}" ]]; then
    return 0
  fi

  while IFS= read -r pid; do
    [[ -z "${pid}" ]] && continue
    local cmd
    cmd="$(ps -p "${pid}" -o command= 2>/dev/null || true)"
    if [[ -n "${cmd}" ]] && [[ "${cmd}" =~ ${cmd_pattern} ]]; then
      stop_pid "${pid}" "${name}"
      stopped_any=1
    fi
  done <<< "${pids}"

  if [[ "${stopped_any}" -eq 1 ]]; then
    echo "${name}: stopped fallback process(es) via port ${port}"
  fi
}

stop_by_pattern() {
  local name="$1"
  local pattern="$2"
  if ! command -v pkill >/dev/null 2>&1; then
    return 0
  fi
  if pkill -f "${pattern}" 2>/dev/null; then
    echo "${name}: stopped fallback process(es) via pattern"
  fi
}

maybe_stop_docker_db() {
  if [[ "${STOP_DOCKER_DB_ON_DOWN}" != "1" ]]; then
    return 0
  fi
  if ! command -v docker >/dev/null 2>&1; then
    return 0
  fi
  if docker compose config --services >/dev/null 2>&1 && docker compose config --services | awk '/^db$/{found=1} END{exit !found}'; then
    echo "Stopping docker compose service: db"
    docker compose stop db >/dev/null 2>&1 || true
  fi
}

stop_from_pid_file "${RUNTIME_DIR}/backend.pid" "Backend"
stop_from_pid_file "${RUNTIME_DIR}/frontend.pid" "Frontend"
stop_from_pid_file "${RUNTIME_DIR}/tunnel.pid" "Tunnel"

# Fall back when pid files are missing or stale.
stop_if_matches_port 8000 "Backend" "uvicorn|python"
stop_if_matches_port 5173 "Frontend" "vite|node"
stop_if_matches_port 20241 "Tunnel" "cloudflared"
stop_by_pattern "Backend" "uvicorn main:app"
stop_by_pattern "Frontend" "vite"
stop_by_pattern "Tunnel" "cloudflared tunnel --url"
maybe_stop_docker_db

echo "Environment stopped."
