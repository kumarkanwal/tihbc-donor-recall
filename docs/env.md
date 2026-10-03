# Environment Variables

All variables are read only through `backend/app/core/config.py` (pydantic-settings) or
`frontend/lib/env.ts` (zod-validated). The app fails at startup if a required variable is missing.
`.env.example` must always match this file.

## 1. Backend

| Variable | Required | Example | Description |
|---|---|---|---|
| `APP_ENV` | yes | `development` | `development`, `staging`, `production` |
| `DEMO_MODE` | yes | `true` | Enables demo clock controls and data reset |
| `API_BASE_PATH` | no | `/api/v1` | |
| `CORS_ORIGINS` | yes | `https://demo.example.com` | Comma-separated |
| `DATABASE_URL` | yes | `postgresql+asyncpg://tihbc:secret@db:5432/tihbc` | |
| `REDIS_URL` | yes | `redis://redis:6379/0` | |
| `JWT_SECRET` | yes | `change-me` | Long random string |
| `JWT_EXPIRES_MINUTES` | no | `720` | |
| `LOG_LEVEL` | no | `INFO` | |
| `TIMEZONE_DISPLAY` | no | `Asia/Karachi` | Used for rendered message dates |
| `UPLOAD_MAX_MB` | no | `10` | Donor file size limit |
| `UPLOAD_MAX_ROWS` | no | `5000` | |
| `PREVIEW_TTL_MINUTES` | no | `30` | Batch preview token lifetime |
| `MEDIA_STORAGE_DIR` | yes | `/data/media` | Uploaded images and videos |
| `MEDIA_PUBLIC_URL` | yes | `https://api.example.com/media` | |
| `MESSAGING_PROVIDER` | yes | `simulator` | Only `simulator` in the MVP |
| `DISPATCHER_INTERVAL_SECONDS` | no | `5` | Scheduler polling interval |
| `SIM_DELIVERY_DELAY_SECONDS` | no | `2` | Delay before `delivered` |
| `SIM_AUTO_READ_RATE` | no | `0.6` | Share of delivered messages auto-marked read for metrics realism |
| `SIM_AUTO_READ_DELAY_SECONDS` | no | `10` | |
| `SIM_TYPING_SECONDS` | no | `1.5` | Typing indicator before automatic replies |
| `LLM_ENABLED` | no | `true` | `false` uses keyword fallback |
| `LLM_PROVIDER` | if LLM on | `openai` | `openai` or `anthropic` |
| `LLM_MODEL` | if LLM on | `gpt-4o-mini` | |
| `LLM_API_KEY` | if LLM on | `sk-...` | |
| `LLM_TIMEOUT_SECONDS` | no | `8` | |
| `AGENT_CONFIDENCE_THRESHOLD` | no | `0.7` | |
| `LANGSMITH_TRACING` | no | `true` | |
| `LANGSMITH_API_KEY` | if tracing | `lsv2_...` | |
| `LANGSMITH_PROJECT` | if tracing | `tihbc-donor-recall-demo` | |
| `LANGSMITH_ENDPOINT` | no | `https://api.smith.langchain.com` | |
| `SEED_ADMIN_EMAIL` | demo | `admin@tihbc.demo` | |
| `SEED_ADMIN_PASSWORD` | demo | `ChangeMe123!` | |
| `SEED_COORDINATOR_EMAIL` | demo | `coordinator@tihbc.demo` | |
| `SEED_COORDINATOR_PASSWORD` | demo | `ChangeMe123!` | |

## 2. Frontend

| Variable | Required | Example | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | yes | `https://api.example.com/api/v1` | |
| `NEXT_PUBLIC_WS_URL` | yes | `wss://api.example.com/ws` | |
| `NEXT_PUBLIC_APP_NAME` | no | `TIHBC Donor Recall` | |
| `NEXT_PUBLIC_DEMO_MODE` | no | `true` | Shows demo controls |

## 3. Rules
- Never commit `.env`. Secrets only in the VPS environment or Docker secrets.
- `NEXT_PUBLIC_*` values are visible in the browser: never put secrets there.
- Adding a variable requires updating this file, `.env.example`, and the config module in the same change.
