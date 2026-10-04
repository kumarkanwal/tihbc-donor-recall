# AGENTS.md — TIHBC Donor Recall Demo (MVP)

This file is the single source of truth for Codex and every human
working in this repository. Read it fully before writing any code. If a rule here conflicts with your
defaults, this file wins. If something is unclear or missing, stop and ask; do not guess.

---

## 1. Project Context

**Client:** Team Indus Health & Blood Center (TIHBC)
**Vendor:** Innoventix360
**What we are building:** A working demo (MVP) of the Phase 1 "WhatsApp-Based Donor Recall & Rescheduling
System". It is shown to the client before contract signing, so it must look and behave like a real product.

**Core idea:** TIHBC staff upload donor batches, attach a content series (scheduled messages), launch a
campaign, and donors receive recall messages on WhatsApp. Donors confirm, reschedule, or decline in-chat.
Responses flow into a live follow-up list for coordinators. Non-responders get a secondary sequence, then
are escalated to a human coordinator. A dashboard reports delivery, engagement, and inactive numbers.

**Important:** There is NO real WhatsApp API in this MVP. Messages are delivered to a built-in
**WhatsApp Simulator** (a side popup in the web app that looks exactly like WhatsApp). The messaging layer
MUST be built behind a provider interface so the real WhatsApp Cloud API can be plugged in later without
changing business logic.

### 1.1 Phase 1 Scope (must all be demonstrable)
1. Donor batch upload (CSV/XLSX) with validation: phone format, segment, language, duplicates.
2. Content Series Library: multiple series, multiple languages (English, Urdu), tagging.
3. Batch → Series assignment as Campaigns; multiple campaigns can run concurrently.
4. Scheduled, interval-based recall messaging engine.
5. In-chat response capture: Confirm / Reschedule / Decline → live follow-up list.
6. Non-responder escalation: automated secondary sequence → human coordinator hand-off.
7. Metrics dashboard: sent, delivered, read, responded, response-rate breakdown,
   invalid and inactive number report.
8. User accounts with role-based access (Admin, Coordinator).
9. Settings page showing WhatsApp integration status (mocked for the demo).

### 1.2 Additional (approved)
- AI reply agent (LangGraph) that understands free-text replies in English, Urdu, and Roman Urdu,
  classifies intent, extracts reschedule dates, and captures decline reasons.
- Demo time-skip control to fast-forward the schedule during a live presentation.

### 1.3 Out of Scope
Do not build anything not listed above (no CRM/EMR integration, no real WhatsApp sending, no billing,
no content creation tools beyond the series builder). Propose ideas in the PR description instead.

---

## 1A. Reference Documents (read before coding)

Detailed specifications live in `docs/`. AGENTS.md defines the rules; these files define exactly what to
build. Always check the relevant file before starting a task, and follow it exactly.

| File | Contains | Read when |
|---|---|---|
| `docs/api.md` | Every endpoint: method, path, auth/role, request and response schemas, error codes | Building or calling any API |
| `docs/database.md` | All tables, columns, types, constraints, indexes, and relations | Writing models, migrations, repositories |
| `docs/screens.md` | Every frontend page: purpose, layout, columns, filters, actions, states | Building any frontend page or component |
| `docs/websocket.md` | Every WebSocket event type and its exact payload | Emitting or consuming realtime events |
| `docs/simulator.md` | WhatsApp simulator behavior and visual details | Building the simulator |
| `docs/agent.md` | LangGraph reply agent: nodes, state, outputs, prompts, fallback | Building the reply agent |
| `docs/env.md` | All environment variables with descriptions and example values | Adding or reading config |
| `docs/brand.md` | Logo usage, light and dark theme tokens, fonts | Any UI work |
| `docs/demo-content.md` | Exact message texts (EN/UR), bot replies, buttons, seed settings | Seed data, reply service, series features |

Rules for these documents:
- If code and a spec disagree, the spec wins. Do not silently diverge.
- If a spec is missing, incomplete, or contradicts AGENTS.md, stop and ask; do not invent details.
- When a change requires updating a spec (e.g. a new endpoint or column), update the doc in the same change.

---

## 1B. Project Memory Files (read and update every session)

Codex has no memory between sessions. These files are the project's memory. Keeping them accurate is
part of every task, not optional.

| File | Purpose | Codex must |
|---|---|---|
| `docs/session-log.md` | Short entry per session: done, next, blockers | Read the latest entry first; add a new entry at the end of every session |
| `docs/progress.md` | Task tracker for the whole MVP | Read before choosing work; update status after every task |
| `docs/decisions.md` | Append-only log of technical and product decisions | Read before coding; add an entry for every new decision |
| `docs/known-issues.md` | Bugs, shortcuts, TODOs not fixed in the current task | Add anything found but not fixed; remove entries when fixed |
| `CHANGELOG.md` | Feature-level changes for the client | Add a line when a user-visible feature is completed |

### 1B.1 Start-of-Session Checklist
1. Read the latest entry in `docs/session-log.md`.
2. Read `docs/progress.md` and confirm which task you are working on.
3. Read `docs/decisions.md` (at minimum all `Accepted` entries).
4. Read `docs/known-issues.md` for anything affecting the task.
5. Read the relevant spec files from section 1A.

### 1B.2 End-of-Session Checklist
1. Update task status in `docs/progress.md` (`Not started`, `In progress`, `Done`, `Blocked`).
2. Add new decisions to `docs/decisions.md`.
3. Add or remove items in `docs/known-issues.md`.
4. Add an entry to `docs/session-log.md`.
5. Update `CHANGELOG.md` if a user-visible feature was completed.

### 1B.3 Decision Rules
- Record a decision whenever you choose a library, pattern, structure, or naming approach that is not
  already defined, or when you deviate from a spec.
- Use the next number (`D-018`, `D-019`, ...). Never renumber or delete entries.
- Parallel sessions: backend sessions use the next free ID below D-100; frontend sessions use D-100 and up.
  Always re-read `docs/decisions.md` immediately before appending.
- Never change an accepted decision silently. Add a new entry with `Supersedes: D-0XX` and mark the old
  entry `Superseded by D-0YY`.
- Decisions that change scope, UX, or the client-facing flow need human approval: record them as
  `Proposed` and stop until approved.

---

## 2. Repository Structure

Monorepo, two independent apps. They are developed, tested, and deployed separately and communicate only
through the HTTP API and WebSocket contract.

```
tihbc-donor-recall/
├── AGENTS.md
├── CHANGELOG.md
├── docs/                      # specs (section 1A) and project memory (section 1B)
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── app/
│   │   ├── main.py            # app factory only
│   │   ├── core/              # config, logging, security, clock, errors, db session
│   │   ├── models/            # SQLAlchemy ORM models (one file per aggregate)
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── repositories/      # DB access only
│   │   ├── services/          # business logic (one service per domain)
│   │   ├── api/
│   │   │   ├── deps.py        # shared dependencies (db, current user, role guards)
│   │   │   └── v1/            # one router file per resource
│   │   ├── messaging/         # provider interface + simulator provider
│   │   ├── scheduler/         # dispatcher, escalation checks
│   │   ├── agents/            # LangGraph reply agent
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   ├── nodes/         # one node per file
│   │   │   └── prompts/       # prompt templates as files, never inline strings
│   │   ├── ws/                # WebSocket manager and event definitions
│   │   └── seed/              # demo seed data
│   └── tests/                 # mirrors app/ structure
└── frontend/
    ├── package.json
    ├── app/                   # Next.js App Router pages
    │   ├── (auth)/login/
    │   └── (dashboard)/       # dashboard, batches, series, campaigns, inbox, reports, settings
    ├── components/
    │   ├── ui/                # shadcn/ui primitives (do not edit generated logic)
    │   ├── shared/            # reusable app components (tables, page header, status badge)
    │   ├── features/          # feature components grouped by domain
    │   └── simulator/         # WhatsApp simulator popup
    ├── hooks/                 # data hooks (TanStack Query) per domain
    ├── lib/
    │   ├── api/               # generated OpenAPI client + thin wrappers
    │   ├── ws/                # WebSocket client
    │   └── utils/
    ├── types/
    └── styles/
```

---

## 3. Tech Stack (do not substitute without approval)

### Backend
- Python 3.12, dependency management with `uv`
- FastAPI, Pydantic v2, pydantic-settings
- SQLAlchemy 2.x (async) + asyncpg, Alembic migrations
- PostgreSQL 16, Redis 7 (pub/sub for WebSocket fan-out, locks)
- pandas + openpyxl for file parsing, `phonenumbers` for phone validation
- LangGraph + LangChain; LLM provider configurable via env
- LangSmith for agent tracing
- structlog for structured JSON logging
- pytest, pytest-asyncio, httpx; ruff (lint + format); mypy (strict)

### Frontend
- Next.js (App Router), React, TypeScript (strict), `pnpm`
- next-themes for light/dark mode
- Tailwind CSS, shadcn/ui, lucide-react icons
- TanStack Query for server state; Zustand only for small client UI state (e.g. simulator open/closed)
- react-hook-form + zod for forms
- openapi-typescript + openapi-fetch for the typed API client
- Recharts for charts
- ESLint + Prettier; Vitest + Testing Library; Playwright for the main demo flow

### Infrastructure
- Docker + docker-compose, Nginx reverse proxy, SSL
- `api.<domain>` → backend, `demo.<domain>` → frontend

---

## 4. Domain Model and Glossary

Use these names exactly in code, DB, API, and UI. Do not invent synonyms.

| Entity | Meaning |
|---|---|
| `User` | Staff account. Role: `admin` or `coordinator`. |
| `Donor` | A person in a batch. Fields: name, phone (E.164), segment, language (`en`/`ur`), city, blood_group, last_donation_date. |
| `DonorBatch` | One uploaded file of donors, with validation report. |
| `Segment` | Donor grouping label (e.g. `regular`, `lapsed`, `first_time`). |
| `ContentSeries` | A named, tagged sequence of messages. Has a `kind`: `primary` or `secondary`. |
| `SeriesStep` | One message in a series: order, `delay_days`, per-language body, optional media (video/image), up to 3 quick-reply buttons, category (`utility`/`marketing`). |
| `Campaign` | Assignment of one batch to one primary series and one secondary series, with a start time. |
| `Enrollment` | One donor's progress through one campaign. Holds the recall status. |
| `Message` | One outbound or inbound message in the simulator chat. |
| `DonorResponse` | A classified reply: intent, extracted date, decline reason, confidence. |
| `FollowUpItem` | A task in the coordinator inbox. |

### 4.1 Status Enums (single definition, shared via OpenAPI)

- `CampaignStatus`: `draft`, `scheduled`, `running`, `paused`, `completed`
- `EnrollmentStatus`: `pending`, `in_primary`, `in_secondary`, `escalated`, `confirmed`,
  `reschedule_requested`, `rescheduled`, `declined`, `invalid_number`, `undeliverable`
- `MessageStatus`: `queued`, `sent`, `delivered`, `read`, `failed`
- `ResponseIntent`: `confirm`, `reschedule`, `decline`, `question`, `unknown`
- `FollowUpType`: `confirmed`, `reschedule`, `declined`, `needs_call`
- `FollowUpStatus`: `open`, `in_progress`, `done`

All state changes go through a service method that validates the transition. Never set a status field
directly from a route or another service.

---

## 5. Core Flows

### 5.1 Batch Upload
1. Admin uploads CSV/XLSX. Required columns: `name`, `phone`, `segment`, `language`.
   Optional: `city`, `blood_group`, `last_donation_date`.
2. Backend validates every row: Pakistani numbers normalized to E.164 (`+923XXXXXXXXX`), allowed segment
   and language values, duplicates within the file and against existing donors.
3. Response returns a preview: valid count, invalid rows with row number and reason.
4. Admin confirms import; only valid rows are saved. The validation report is stored on the batch.

### 5.2 Campaign Lifecycle
1. Admin creates a campaign: batch + primary series + secondary series + start time.
2. On launch, one `Enrollment` per valid donor is created, and the first step's messages are queued.
3. The dispatcher sends due messages through the messaging provider using the donor's language.
4. Multiple campaigns run concurrently and must never interfere with each other.

### 5.3 Reply Handling
1. Button replies map directly to intents; no LLM call.
2. Free-text replies go to the LangGraph reply agent.
3. The agent returns a structured `DonorResponse`. The service updates the enrollment, creates or updates
   a `FollowUpItem`, sends the appropriate in-chat acknowledgement, and emits WebSocket events.
4. A reply stops further scheduled steps for that enrollment.

### 5.4 Escalation
1. If the primary series finishes with no reply after the final step's wait window → enroll in secondary.
2. If the secondary series finishes with no reply → status `escalated`, create a `needs_call` follow-up.
3. Escalation checks run in the scheduler, are idempotent, and are safe to run repeatedly.

### 5.5 Simulated Delivery (demo realism)
- The simulator provider advances messages `sent` → `delivered` → `read` with short realistic delays.
- Donors flagged in seed data as inactive produce `failed` / `undeliverable` so the inactive-number report
  has real data.
- Read receipts are not guaranteed for all donors (some never reach `read`).

### 5.6 Demo Clock and Time-Skip
- All code gets the current time from `core/clock.py` (`clock.now()`). Never call `datetime.now()` or
  `datetime.utcnow()` anywhere else.
- The demo clock supports an offset. The time-skip endpoint (admin only) advances the offset and triggers
  a dispatcher run, so Day 3 and Day 7 steps fire immediately.
- Store all timestamps in UTC; convert to `Asia/Karachi` only in the UI.

---

## 6. Engineering Rules (apply everywhere)

### 6.1 File and Function Size
- Target under 300 lines per file. Hard limit 400. If a file approaches the limit, split it by
  responsibility before adding more.
- Functions do one thing. Aim for under 40 lines; refactor anything over 60.
- Max 3 levels of nesting. Use early returns and guard clauses.

### 6.2 Modularity and DRY
- One responsibility per module. One router per resource, one service per domain, one model per aggregate.
- Before writing new code, search the codebase for an existing helper, component, hook, or schema.
  Reuse or extend it. Duplicated logic is a bug.
- Shared logic belongs in `core/` (backend) or `lib/`, `hooks/`, `components/shared/` (frontend).
- No copy-paste between features. If two places need the same thing, extract it.

### 6.3 Code Quality
- Fully typed code. No `Any` in Python and no `any` in TypeScript unless justified in a comment.
- Clear, descriptive names. No abbreviations except well-known ones (`id`, `url`, `db`).
- No magic numbers or strings. Use constants or enums.
- No dead code, commented-out code, or unused imports.
- Comments explain *why*, not *what*. Public functions and classes get a short docstring.
- No `print` / `console.log`. Use the logger.
- Fail loudly: never swallow exceptions. Catch only what you can handle.

### 6.4 Configuration and Secrets
- All config via environment variables loaded through `core/config.py` (pydantic-settings) or the frontend
  env module. Never read `os.environ` or `process.env` directly elsewhere.
- Never commit secrets. Keep `.env.example` updated with every new variable.

### 6.5 Dependencies
- Do not add a dependency if the standard library or an existing dependency can do the job.
- Every new dependency must be justified in the PR description.

---

## 7. Backend Rules

### 7.1 Layering (strict)
```
api (routes) → services (business logic) → repositories (DB access) → models
```
- Routes: parse input, call one service method, return a schema. No business logic, no DB queries.
- Services: all business rules and state transitions. No HTTP concepts (no `Request`, no `HTTPException`).
- Repositories: queries only. No business rules.
- Models never leave the service layer; routes always return Pydantic schemas.

### 7.2 API Conventions
- All routes under `/api/v1`. Resource names plural and kebab-case: `/donor-batches`, `/content-series`.
- Standard methods: `GET` list/detail, `POST` create, `PATCH` update, `DELETE` remove,
  `POST /{id}/actions/<verb>` for state changes (e.g. `/campaigns/{id}/actions/launch`).
- List endpoints are paginated (`page`, `page_size`, default 20, max 100) and return
  `{ items, total, page, page_size }`.
- Consistent error shape: `{ "error": { "code": "STRING_CODE", "message": "Human readable", "details": {} } }`.
  Raise domain exceptions in services; a single exception handler maps them to HTTP status codes.
- Every endpoint has explicit `response_model`, `summary`, and tags so the OpenAPI client is clean.

### 7.3 Database
- All schema changes via Alembic migrations. Never edit an applied migration.
- UUID primary keys, `created_at` / `updated_at` on every table.
- Index foreign keys and every column used for filtering.
- Use transactions for multi-step writes. Avoid N+1 queries (use `selectinload` / joins).

### 7.4 Messaging Provider
- Define `MessagingProvider` (abstract) in `messaging/base.py` with methods for sending template messages,
  sending free-form messages, and reporting status updates.
- Implement `SimulatorProvider` for the demo. A future `WhatsAppCloudProvider` must be a drop-in
  replacement. Business logic must never import a concrete provider; inject it via dependency.

### 7.5 Scheduler
- The dispatcher runs as a separate process/worker, polling for due messages (`scheduled_at <= clock.now()`).
- Every job is idempotent: use DB row locks or Redis locks so a message is never sent twice.
- Escalation checks run on the same loop and follow section 5.4.

### 7.6 WebSockets
- Single endpoint: `/ws` (authenticated via token query param).
- Events have the shape `{ "type": "<event>", "payload": {...}, "ts": "<iso>" }`. Event types and payloads
  are defined in `docs/websocket.md` and implemented once in `ws/events.py`.
- Broadcast through Redis pub/sub so multiple workers stay in sync.

### 7.7 LangGraph Reply Agent
- Graph lives in `agents/graph.py`; each node in its own file under `agents/nodes/`.
- Nodes: `detect_language` → `classify_intent` → `extract_details` (date/slot or decline reason)
  → `build_result`.
- Use structured output (Pydantic models) for every LLM call. Never parse free text with regex.
- Prompts live in `agents/prompts/` as files. No prompt strings inline in code.
- If the LLM call fails or confidence is below the configured threshold, return intent `unknown` and
  create a `needs_call` follow-up. The system must keep working without the LLM.
- The agent does not write to the DB. It returns a result; the service applies it.

---

## 8. Frontend Rules

### 8.1 Structure
- Pages in `app/` are thin: they compose feature components and hooks only.
- All API calls go through the generated client in `lib/api/` and are wrapped in hooks in `hooks/`.
  Components never call `fetch` directly.
- Server state lives in TanStack Query. WebSocket events update or invalidate the relevant query cache.
- One component per file. Components over ~200 lines get split.
- Regenerate the API client whenever the backend OpenAPI spec changes. Never hand-write API types.

### 8.2 Required UI States
Every data view must handle: loading (skeletons), empty (clear message and primary action),
error (message and retry), and success. No blank screens.

### 8.3 Forms
- react-hook-form + zod. Validate on the client and show backend validation errors inline.
- Disable submit while pending; show success and error toasts.

### 8.4 Accessibility and Responsiveness
- Semantic HTML, labels on all inputs, keyboard navigable, visible focus states.
- Works on desktop first; must remain usable on tablet.

---

## 9. UI and Design Rules

The audience is hospital and blood-center staff, not engineers. The UI must be simple, calm, and obvious.

- Clean, professional healthcare look using the client's red and blue brand colors and logo
  (`frontend/public/images/`). Exact tokens and logo rules are in `docs/brand.md`.
- Light mode (default) and dark mode, switchable from the top bar. Every screen must look correct in both.
- **No emojis anywhere** in the admin UI, seed data, or system messages.
- **No "AI-style" visuals:** no gradients, glows, sparkles, or "magic" icons.
  AI-generated results are shown as normal data (e.g. "Decline reason: Travelling").
- Clear labels in plain language. Every screen has one obvious primary action.
- Consistent spacing, typography, and components across all pages (use the shared design tokens).
- Tables: sortable columns, search, filters by status, pagination.
- Status badges use one shared component with a fixed color map per status.
- Lucide icons only, used sparingly and always with a text label for actions.
- Support Urdu text correctly (right-to-left rendering where Urdu content is displayed).

### 9.1 WhatsApp Simulator (the only WhatsApp-styled area)
- Opened from a floating button; slides in as a side panel with a phone frame.
- Donor switcher at the top to view any enrolled donor's chat.
- Must look like WhatsApp: chat header with business name and profile image (TIHBC), wallpaper,
  outgoing/incoming bubble styles, timestamps, tick states (single, double, blue double),
  typing indicator, video/image media previews, quick-reply buttons, text input with send.
- Do not use the WhatsApp logo or trademarked assets.
- Updates live via WebSocket; no manual refresh.

---

## 10. Observability

- **LangSmith:** enabled through env vars (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`).
  Every agent run includes metadata: `campaign_id`, `enrollment_id`, `donor_language`, `environment`.
  Tag runs by node and intent.
- **Logging:** structlog JSON logs. Every request gets a `request_id` (middleware), propagated to services,
  scheduler jobs, and agent runs. Log key events: upload result, campaign launch, message sent/failed,
  reply classified, escalation, follow-up status change.
- Never log full phone numbers or personal data. Mask phones (`+92300*****67`).
- Health endpoints: `/health/live` and `/health/ready` (checks DB and Redis).

---

## 11. Security

- JWT auth with access token; passwords hashed with argon2 or bcrypt.
- Role guards as reusable dependencies (`require_role("admin")`). Coordinators cannot upload, create
  series, launch campaigns, or use time-skip.
- Validate uploads: file type, size limit (configurable), row limit.
- CORS restricted to the frontend domain. All inputs validated by Pydantic/zod.
- Donor data is personal health-related data: minimum exposure, masked in logs.

---

## 12. Testing

- Backend: unit tests for every service; API tests for every router; tests for state transitions,
  upload validation, escalation timing (using the demo clock), and agent fallback behavior.
  Mock the LLM in tests; never call a real LLM in CI.
- Frontend: component tests for shared components and the simulator; one Playwright test covering
  the full demo flow (upload → series → campaign → reply → follow-up → dashboard).
- New code must include tests. Do not delete or weaken a test to make it pass.

---

## 13. Seed Data (demo)

- Command: `uv run python -m app.seed`. Idempotent; can reset the demo to a clean state.
- About 200 donors with realistic Pakistani names, valid `+923` numbers, mixed segments and languages,
  including some invalid rows (sample upload file) and some inactive numbers.
- 3 content series (English and Urdu versions), 1 secondary series, 2 campaigns already running,
  and a realistic mix of confirmed, rescheduled, declined, and escalated donors.
- Users: one admin and one coordinator (credentials in `.env.example`, demo only).
- No emojis in any seed content.

---

## 14. Commands

```bash
# Backend
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --reload-dir app
uv run python -m app.scheduler     # dispatcher worker
uv run python -m app.seed
uv run python -m app.export_openapi # write the stable schema to frontend/openapi.json
uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest

# Frontend
cd frontend
pnpm install
pnpm gen:api                       # regenerate client from backend OpenAPI
pnpm dev
pnpm lint && pnpm typecheck && pnpm test

# Full stack
docker compose up --build
```

Run `uv run python -m app.export_openapi` after every API change and commit the updated
`frontend/openapi.json` file.

**Codex pytest isolation:** When Codex runs backend tests, it must use
`uv run pytest --basetemp=.pytest_tmp_codex -o cache_dir=.pytest_tmp_codex/cache` (plus any other
required pytest arguments). Codex must never create, use, modify, or delete `backend/.pytest_tmp`;
that path is reserved for human local test runs. Both paths remain Git-ignored.

---

## 15. Git Workflow

- Branches: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`.
- Conventional commits: `feat(campaigns): add launch action`.
- Small, focused PRs (one feature or fix). The PR description states what changed, why, and how it was tested.
- Never commit generated build output, `.env`, or local data.

---

## 16. Rules for Codex

1. Follow the start-of-session checklist (1B.1), then read the related existing code before making changes.
2. For any non-trivial task, write a short plan first (files to add/change), then implement.
3. Stay within the requested task. Do not refactor unrelated code or add unrequested features.
4. Reuse before creating: search for existing helpers, schemas, hooks, and components first.
5. Respect the layering, file-size limits, and naming in this file.
6. If you change an API schema, regenerate the frontend client and update the affected hooks in the same change.
7. If you add an env variable, update `.env.example` and `core/config.py`.
8. Run lint, type checks, and tests before declaring a task done. Fix failures; do not skip them.
9. Never use `datetime.now()` outside the clock module, never call a concrete messaging provider directly,
   never put prompts inline.
10. If requirements are ambiguous or a rule blocks you, stop and ask instead of guessing.
11. Finish every session with the end-of-session checklist (1B.2).

---

## 17. Definition of Done

A task is done only when:
- It works end-to-end in the running app (backend + frontend + simulator where relevant).
- All UI states (loading, empty, error, success) are handled.
- Lint, type checks, and tests pass; new logic has tests.
- No file exceeds 400 lines; no duplicated logic was introduced.
- Logs and LangSmith traces (for agent work) are present and free of personal data.
- `.env.example`, migrations, and the API client are up to date.
- `docs/progress.md`, `docs/decisions.md`, `docs/known-issues.md`, `docs/session-log.md`, and `CHANGELOG.md` are updated.
