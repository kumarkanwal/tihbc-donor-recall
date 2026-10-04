# TIHBC Donor Recall Demo

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

In a second terminal, start the placeholder scheduler worker:

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

## Seed demo users

Local mode:

```powershell
Set-Location backend
uv run python -m app.seed.users
```

Docker mode:

```powershell
docker compose exec api python -m app.seed.users
```

The command creates or updates the configured admin and coordinator and is safe to run repeatedly.

## Tests and checks

From `backend/`:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest
uv run pytest --run-postgres
```

PostgreSQL tests run only with `--run-postgres`. They never use `DATABASE_URL`: pytest selects
`TEST_DATABASE_URL`, or derives `tihbc_test` on the same server when that variable is unset. At session
start it creates the test database if needed and applies all Alembic migrations, then each test rolls
back its writes. The database user must be able to create `tihbc_test` on the first run; it does not
need `CREATEDB` after the database exists.

Pytest uses the operating system's per-user temporary directory for normal local runs and disables its
cache provider. Codex runs must override the base temp path as documented in `AGENTS.md`; they must
never access the legacy human-owned `backend/.pytest_tmp` directory.
