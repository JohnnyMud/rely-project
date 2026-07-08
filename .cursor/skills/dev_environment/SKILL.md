---
name: dev-environment
description: Start and verify the local development environment for this project, including PostgreSQL, FastAPI, React frontend, Cloudflare tunnel, Retell webhook URL updates, and health checks. Use when the user asks to set up, boot, or verify the local stack end-to-end.
disable-model-invocation: true
---

# Dev Environment

Use this skill to bring the full local environment to a ready state and verify it is working.

## Script Entry Points

Skill scripts live in `scripts/`:

- `scripts/dev_up.sh`: Full startup orchestration (optional Postgres autostart, backend, frontend, tunnel, health check, optional Retell webhook update).
- `scripts/dev_down.sh`: Stop processes started by `dev_up.sh` using PID files.
- `scripts/run_backend.sh`: Start FastAPI backend only.
- `scripts/run_frontend.sh`: Start React frontend only.
- `scripts/run_tunnel.sh`: Start Cloudflare tunnel only.
- `scripts/update_retell_webhook.py`: Update Retell webhook URL from tunnel URL.

Use `dev_up.sh`/`dev_down.sh` for normal day-to-day flow. Use individual `run_*` scripts when debugging a specific service.

## Canonical Workflow

Follow this sequence:

1. Start PostgreSQL (if using Docker).
2. Start the FastAPI backend with uvicorn.
3. Start the React frontend with npm run dev.
4. Start a Cloudflare tunnel pointing to the backend.
5. Wait for the tunnel URL.
6. Update your webhook provider (Retell) with the new public URL if necessary.
7. Verify the health endpoint responds before considering the environment ready.

Do not skip verification steps.

## Fast Paths

### Full environment up/down

```bash
# From .cursor/skills/dev_environment/
./scripts/dev_up.sh
./scripts/dev_down.sh
```

### Component-only entry points

```bash
./scripts/run_backend.sh
./scripts/run_frontend.sh
./scripts/run_tunnel.sh
./scripts/update_retell_webhook.py --tunnel-url "https://<id>.trycloudflare.com" --apply
```

## Project Defaults

- Backend command: `uvicorn main:app --reload`
- Backend URL: `http://127.0.0.1:8000`
- Health endpoint: `GET /` (expects JSON with `"status": "healthy"`)
- Frontend command: `npm run dev` from `frontend/`
- Cloudflare tunnel command: `cloudflared tunnel --url http://localhost:8000`
- Retell webhook endpoint path: `/webhooks/retell`

## Setup Procedure

### 1) Start PostgreSQL

- If PostgreSQL is managed by Docker, start it first.
- If it is already running, do not start a duplicate instance.
- Confirm DB availability before moving on.

### 2) Start FastAPI backend

- Run from project root:
  - `uvicorn main:app --reload`
- Wait until uvicorn reports it is serving on port `8000`.
- If startup fails, stop and fix backend errors before continuing.

### 3) Start React frontend

- Run from `frontend/`:
  - `npm run dev`
- Wait until Vite reports the local URL (typically `http://localhost:5173`).

### 4) Start Cloudflare tunnel to backend

- Run:
  - `cloudflared tunnel --url http://localhost:8000`
- Wait for an `https://...trycloudflare.com` URL.
- Treat this URL as ephemeral per run.

### 5) Update Retell webhook URL (if changed)

- Build webhook URL as:
  - `<tunnel-url>/webhooks/retell`
- Compare with currently configured Retell webhook.
- If different, update Retell to the new URL.
- If unchanged, no update is needed.

### 6) Verify environment readiness

- Confirm backend health check:
  - `curl http://127.0.0.1:8000/`
- Only mark environment as ready when:
  - PostgreSQL is reachable
  - Backend is running
  - Frontend is running
  - Cloudflare tunnel is active with a public URL
  - Retell webhook is correctly configured (or confirmed unchanged)
  - Health endpoint returns expected response

## Quick Command Checklist

Run these in separate terminals:

```bash
# Terminal 1: database (example only; use your project's docker command)
docker compose up -d db

# Terminal 2: backend
uvicorn main:app --reload

# Terminal 3: frontend
cd frontend
npm run dev

# Terminal 4: tunnel
cloudflared tunnel --url http://localhost:8000

# Terminal 5: health check
curl http://127.0.0.1:8000/
```

## Script Configuration

`scripts/dev_up.sh` supports:

- `AUTOSTART_POSTGRES` (default `1`): Start `docker compose` postgres service if present.
- `AUTO_UPDATE_RETELL_WEBHOOK` (default `0`): Run webhook updater automatically once tunnel URL is detected.
- `BACKEND_HEALTH_URL` (default `http://127.0.0.1:8000/`): Health-check URL used for readiness.

Backend/tunnel scripts also support:

- `BACKEND_HOST` (default `127.0.0.1`)
- `BACKEND_PORT` (default `8000`)
- `BACKEND_APP` (default `main:app`)
- `TUNNEL_TARGET_URL` (default `http://localhost:${BACKEND_PORT}`)
- `FRONTEND_DIR` (default `frontend`)

`scripts/update_retell_webhook.py` supports:

- `--tunnel-url` or `--webhook-url`
- `--apply` (without it, runs dry-run)
- `RETELL_API_KEY` and `RETELL_AGENT_ID` for SDK-based updates
- Optional HTTP fallback env vars:
  - `RETELL_WEBHOOK_UPDATE_URL`
  - `RETELL_WEBHOOK_UPDATE_METHOD` (default `PATCH`)
  - `RETELL_WEBHOOK_UPDATE_TOKEN`
  - `RETELL_WEBHOOK_UPDATE_AUTH_HEADER` (default `Authorization`)
  - `RETELL_WEBHOOK_PATH` (default `/webhooks/retell`)

## Failure Handling

- If backend health check fails, resolve backend/DB issues first.
- If tunnel starts before backend is healthy, restart tunnel after backend is healthy.
- If Retell still cannot deliver events, re-check exact webhook URL, path, and HTTPS accessibility.
