# TIHBC Donor Recall Demo

The donor-phone simulator defaults to `NEXT_PUBLIC_SIMULATOR_SOURCE=api`. For offline demos,
set `NEXT_PUBLIC_SIMULATOR_SOURCE=mock` in the frontend environment and restart `pnpm dev`.
With `NEXT_PUBLIC_REALTIME=off`, the open phone polls messages every 3 seconds and conversations
every 10 seconds. Set it to `on` to use the shared authenticated WebSocket instead (no polling).

Backend-first MVP for TIHBC's donor recall and rescheduling workflow. The backend supports local `uv`
development and a Docker Compose stack using the same root environment file.

## Setup

Requirements for local mode are Python 3.12, `uv`, PostgreSQL 16 on `localhost:5433`, and Redis 7 on
`localhost:6380`. Docker mode requires Docker Compose.

Create the ignored root environment file, then replace placeholder secrets and credentials:

```powershell
Copy-Item .env.example .env
```

Keep `DATABASE_URL` and `REDIS_URL` set to the documented localhost ports. Compose overrides the
container-side connection URLs and media path, so the same `.env` remains valid outside Docker.

## Local mode

```powershell
Set-Location backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --reload-dir app
```

In a second terminal, start the scheduler worker:

```powershell
Set-Location backend
uv run python -m app.scheduler
```

The API is available at `http://localhost:8000`; OpenAPI docs are at
`http://localhost:8000/docs`.

## Docker mode

Run these commands from the repository root:

```powershell
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://localhost:8000/health/ready
docker compose logs --tail=50 api worker
```

Both backend entrypoints wait for PostgreSQL. Compose sets `RUN_MIGRATIONS=true` only on the API, so
the API applies `alembic upgrade head` while the worker skips migrations and starts after API health.

Stop the stack without deleting persistent database, Redis, or media volumes:

```powershell
docker compose down
```

## Seed demo data

Local mode:

```powershell
Set-Location backend
uv run python -m app.seed
```

Docker mode:

```powershell
docker compose exec api python -m app.seed
```

The command is safe to run repeatedly. It preserves staff accounts and the current demo-clock offset,
then transactionally rebuilds the full operational demo dataset: donors, slots, bilingual series,
campaigns, simulator history, responses, follow-ups, and appointments. It also generates
`backend/app/seed/assets/sample-donors.xlsx`. The same full reset is available to administrators from
Settings when `DEMO_MODE=true`.

Run one scheduler tick or exercise the lower-level messaging tools:

```powershell
Set-Location backend
uv run python -m app.tools.run_tick
uv run python -m app.tools.send_next_step --enrollment <enrollment-uuid>
uv run python -m app.tools.advance_delivery
```

Watch live events with `uv run python -m app.tools.ws_listen --email <staff-email>` (password is
prompted). Run `uv run pytest --run-postgres --run-redis` with PostgreSQL and Redis available to
verify the database flows and independent worker-to-WebSocket fan-out. Redis tests use unique
channels and never flush the server. Set `TEST_REDIS_URL` if the test connection differs from
`REDIS_URL`.

These commands require `DEMO_MODE=true`. Delivery progression follows the configured simulator
delivery and automatic-read delays, so run it again after the read delay to observe a read receipt.

## Tests and checks

From `backend/`:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
uv run pytest --run-postgres --run-redis
uv run python -m app.export_openapi
```

PostgreSQL tests run only with `--run-postgres`; Redis fan-out tests additionally require
`--run-redis`. Database tests never use `DATABASE_URL`: pytest selects
`TEST_DATABASE_URL`, or derives `tihbc_test` on the same server when that variable is unset. At session
start it creates the test database if needed and applies all Alembic migrations, then each test rolls
back its writes. The database user must be able to create `tihbc_test` on the first run; it does not
need `CREATEDB` after the database exists.

Pytest uses the operating system's per-user temporary directory for normal local runs and disables its
cache provider. Codex runs must override the base temp path as documented in `AGENTS.md`; they must
never access the legacy human-owned `backend/.pytest_tmp` directory.

## Playwright demo flow

The end-to-end suite uses the real local API and the generated
`backend/app/seed/assets/sample-donors.xlsx` workbook. Seed operational demo data before each manual
run, and do not point these commands at an environment whose data must be preserved. Keep the default
demo admin and coordinator credentials from `.env.example`; the suite signs in with both accounts.
The demo time-skip action runs the required dispatcher tick, so a separate scheduler worker is not
required for this test.

First-time setup from the repository root:

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env.local
docker compose up -d db redis
Set-Location frontend
pnpm install
pnpm exec playwright install chromium
```

Set `NEXT_PUBLIC_SIMULATOR_SOURCE=api` in `frontend/.env.local`. Then seed and start the backend in one
terminal:

```powershell
Set-Location backend
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --reload-dir app
```

Start the frontend in a second terminal:

```powershell
Set-Location frontend
pnpm dev
```

Run the complete demo story in a third terminal:

```powershell
Set-Location frontend
pnpm e2e
```

Playwright reuses the frontend at `http://127.0.0.1:3000` when it is already running. It verifies the
admin upload and campaign flow, donor confirmation and automatic reply, live staff counters and inbox,
dashboard KPIs, logout, and coordinator role restrictions without fixed sleeps.
