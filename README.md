# Patient Calling System Quickstart

Patient appointment reminder application with:

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL
- Frontend: React + Vite
- Voice integration: Retell

## Prerequisites

- Python `3.12+`
- `[uv](https://docs.astral.sh/uv/getting-started/installation/)` for Python dependency management
- Node.js `18+` and npm
- Docker Desktop (for local PostgreSQL)
- `cloudflared` (for Retell webhook testing)
  - macOS: `brew install cloudflared`

## 1) Clone and install dependencies

```bash
git clone https://github.com/JohnnyMud/rely-project.git
cd rely-project
uv sync
cd frontend && npm install && cd ..
```

## 2) Configure environment variables

Create a `.env` file in the project root:

```bash
POSTGRES_USER="local"
POSTGRES_PASSWORD="rely123"
RETELL_API_KEY="your_retell_api_key"
RETELL_AGENT_ID="agent_xxxxxxxxxxxxxxxxxxxxxxxx"
```

Notes:

- `RETELL_AGENT_ID` should include the `agent_` prefix.
- Current project DB config defaults to:
  - `postgresql://local:rely123@localhost:5432/patient_calls`
  - If you change credentials, update both `app/db.py` and `alembic.ini`.

## 3) Start PostgreSQL

```bash
docker compose up -d db
```

## 4) Run database migrations

```bash
uv run alembic upgrade head
```

## 5) Start the app

### Option A (recommended): use dev environment scripts

```bash
set -a && source .env && set +a
PATH="$(pwd)/.venv/bin:$PATH" ./.cursor/skills/dev_environment/scripts/dev_up.sh
```

This starts backend, frontend, and tunnel, then waits for health checks.

### Option B: start services manually (separate terminals)

```bash
# Terminal 1 - backend
set -a && source .env && set +a
PATH="$(pwd)/.venv/bin:$PATH" uvicorn main:app --reload

# Terminal 2 - frontend
cd frontend
npm run dev

# Terminal 3 - cloudflare tunnel
cloudflared tunnel --url http://localhost:8000
```

## 6) Register/update Retell webhook (dev_up.sh should have already set this up, but just in case)

Use the tunnel URL from `cloudflared` and point Retell to:

`https://<your-tunnel>.trycloudflare.com/webhooks/retell`

Or use the helper script:

```bash
set -a && source .env && set +a
PATH="$(pwd)/.venv/bin:$PATH" ./.cursor/skills/dev_environment/scripts/update_retell_webhook.py --tunnel-url "https://<your-tunnel>.trycloudflare.com" --apply
```

## Verify everything is running

- Backend health: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Frontend: [http://localhost:5173/](http://localhost:5173/)

## Stop services

```bash
./.cursor/skills/dev_environment/scripts/dev_down.sh
docker compose stop db
```

## Troubleshooting

- `uvicorn: not found`
  - Use `PATH="$(pwd)/.venv/bin:$PATH"` or `uv run uvicorn ...`
- Backend fails with `RETELL_API_KEY` missing
  - Load env vars before startup: `set -a && source .env && set +a`
- Dev script says Postgres service not detected
  - Compose service name is `db` in `docker-compose.yml`

