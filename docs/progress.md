# Progress Tracker

Status values: Not started | In progress | Done | Blocked
Update after every task. Add a note for Blocked items.

## Phase 0: Preparation (human)
| # | Task | Status | Notes |
|---|---|---|---|
| 0.1 | TIHBC logo and brand colors → update brand.md | Not started | |
| 0.2 | Repo with AGENTS.md and docs/ | Done | |
| 0.3 | VPS: Docker, Nginx, subdomains, SSL | Not started | |
| 0.4 | LLM and LangSmith API keys | Not started | |
| 0.5 | Demo content: 3 series (EN/UR), 1 sample video | Not started | |

## Phase 1: Backend foundation
| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Skeleton: config, logging, clock, errors | Not started | |
| 1.2 | Models and Alembic migrations | Not started | |
| 1.3 | Auth: login, JWT, role guards | Not started | |
| 1.4 | Docker compose: API, Postgres, Redis | Not started | |

## Phase 2: Backend features
| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Batch upload: preview, validation, import | Not started | |
| 2.2 | Content series, steps, media upload | Done | Bilingual series lifecycle, ordered steps, previews, media validation/storage, role guards, and isolated PostgreSQL coverage are complete. Manual `/docs` acceptance and all 170 automated tests pass. |
| 2.3 | Campaigns: create, launch, pause, resume | Done | Added campaign CRUD and lifecycle actions, aggregate launch validation, isolated batch enrollment creation, status counts, enrollment browsing/detail, coordinator read access, and live-series protection. All 203 PostgreSQL tests and the complete `/docs` acceptance flow pass. |
| 2.4 | Messaging provider (simulator) | Done | Added provider-injected bilingual step sending, capacity-safe appointment booking with a non-blocking localized fallback, deterministic simulated delivery/read progression, post-commit events, demo CLI tools, and idempotency. All 221 PostgreSQL tests and the live CLI/API acceptance flow pass. |
| 2.5 | Scheduler: dispatcher and escalation | Done (pending user verification) | Added the idempotent worker tick, primary-to-secondary escalation, needs-call follow-ups, campaign completion, and admin demo-clock API. Automated PostgreSQL and manual lifecycle verification remain tracked in KI-007. |
| 2.6 | WebSockets and Redis events | Done (pending user verification) | Authenticated WebSockets, Redis cross-process event delivery, public payload filtering, metrics coalescing, worker/CLI integration, and local tests are complete. Live acceptance remains pending under KI-010. |
| 2.7 | Simulator API | Done (pending user verification) | Added conversation browsing, chronological UUID-cursor message pages, read receipts, and transactional inbound replies that stop scheduled outreach without intent handling. PostgreSQL/manual acceptance remains tracked in KI-011. |
| 2.8 | Reply service flows | Done (pending user verification) | Added deterministic button and fallback-text classification, enrollment transitions, bilingual acknowledgements, capacity-safe rescheduling, decline reasons, follow-up upserts, donor-response persistence, typing/live events, and final-status handling. Live PostgreSQL/simulator acceptance remains tracked in KI-011. |
| 2.9 | LangGraph agent, fallback, LangSmith | Done (pending real-provider re-evaluation) | Fixed provider-local 400/401/402/403 failures so they open only that provider's circuit and continue through the fallback chain; Groq GPT-OSS now uses strict JSON Schema output. The evaluator reports field-level and per-attempt diagnostics and supports pacing/provider isolation. A configured-provider rerun remains tracked in KI-015. |
| 2.10 | Follow-up inbox API | Done | Added filtered pagination, summary counts, donor/response/activity detail, audited coordinator actions, post-commit updates, and CSV export matching the frontend contract. |
| 2.11 | Metrics and reports API | Done | Added query-computed KPI, local-day timeseries, response/decline/campaign breakdowns, paginated invalid and undeliverable numbers, filters, and CSV exports matching the frontend contract. |
| 2.12 | Settings and demo clock API | Done | Added mocked verified integration settings sourced from active series steps plus an admin/demo-mode-only transactional reset that preserves staff users and demo-clock state, clears operational data, and restores configured users and slots. The complete 327-test PostgreSQL/Redis suite passes. |
| 2.13 | Seed data | Done | Added an idempotent transactional full seed with 195 realistic donors, the documented segment/language/simulator mixes, exact bilingual series, two running and one draft campaign, realistic messages/responses/follow-ups/appointments, and a 40-row sample workbook. Reset-data now runs the full seed; 330 PostgreSQL/Redis tests pass. |
| 2.14 | Backend tests | Done | Completed the backend audit: added architecture and reset-rollback coverage, removed stale dead code and a resolved warning issue, verified all application files are below 300 lines, refreshed README commands, and passed 333 PostgreSQL/Redis tests with deprecation warnings treated as errors. |

## Phase 3: Frontend
| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Setup, tokens, generated API client | Not started | |
| 3.2 | App shell and skip-time control | Not started | |
| 3.3 | Login | Not started | |
| 3.4 | Shared components | Not started | |
| 3.5 | Donor batches | Not started | |
| 3.6 | Content series library and editor | Done | Added the searchable/filterable table and grid library, administrator lifecycle actions, bilingual settings and step editor, accessible reordering, media upload, server-rendered simulator preview, activation problem groups, and coordinator/archived read-only states. API generation, lint, strict typecheck, 29 tests, and the production build pass. |
| 3.7 | Campaigns | Done | Added the searchable, sortable campaign library; role-aware draft creation and editing; launch, pause, and resume controls; audience and schedule summaries; enrollment counters, filtering, detail drawer, and donor-chat entry points. API generation, lint, strict typecheck, 41 tests, and the production build pass. |
| 3.8 | WhatsApp simulator | Done | Added the persistent donor phone and offline mock; API mode uses generated Task 2.7 types, real campaign filters, all conversation pages, chronological history, read receipts, and optimistic replies. The picker labels campaign context and defaults to the newest running campaign; the phone status bar follows demo time. Live acceptance remains KI-011. |
| 3.9 | Follow-up inbox | Done | Added the filtered coordinator queue, count tabs, detail workflow, assignment/start/resolve/note actions, CSV export, chat entry point, and realtime-compatible query keys. Now uses the generated Task 2.10 contract with normal retryable errors. |
| 3.10 | Dashboard | Done | Added campaign/date filters, six KPI cards, token-driven daily activity and outcome charts, active campaign progress, recent follow-ups, deterministic insights, and realtime-compatible metrics keys. Now uses the generated Task 2.11 contract. |
| 3.11 | Reports | Done | Added delivery/engagement, responses, and inactive-number tabs with shared filters, token-driven Recharts, aggregate tables and cards, pagination, and per-report CSV exports. Now uses the generated Task 2.11 contract. |
| 3.12 | Settings | Done | Added mocked integration status and template approval views, a read-only paginated user directory, administrator-only demo clock controls and confirmed data reset, and role/demo-mode gating. Settings, clock, and reset now use generated backend contracts. |
| 3.13 | WebSocket live updates | In progress | Part 1 complete: added the shared authenticated realtime client, centralized event-to-cache routing, reconnect refresh, API-simulator integration, and generated administrator demo-clock/Skip time controls. Relative timestamps now use one shared demo-time source. Realtime remains disabled by default pending live acceptance. |

## Phase 4: Integration and deployment
| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | End-to-end Playwright flow | In progress | One serial Chromium suite covers the complete seeded admin-to-donor-to-coordinator story with stable selectors and no fixed sleeps. Playwright now uses the canonical `localhost` frontend origin, audits every literal test ID before execution, and prints sanitized browser errors and failed requests on failure. Frontend checks and Playwright discovery pass; the live seeded rerun remains pending under KI-014. |
| 4.2 | Agent test with real LLM (EN, UR, Roman Urdu) | In progress | Initial run scored 6/31 because a Cerebras 402 terminated routing after Groq throttling. The fallback and evaluation tooling are fixed; rerun the 31-case evaluation and inspect LangSmith traces under KI-015. |
| 4.3 | Deploy to VPS | In progress | Production Compose, standalone web image, Caddy block, backup automation, environment template, and operations runbook are complete. Compose/static/standalone-build checks pass; Docker image builds and live VPS acceptance remain pending because the local Docker engine is unavailable. |
| 4.4 | Bug fixes and polish | In progress | Fixed generated-client multipart bodies for batch/media uploads and browser timer binding for WebSocket reconnects; frontend quality gate passes. |

## Phase 5: Demo preparation (human)
| # | Task | Status | Notes |
|---|---|---|---|
| 5.1 | Demo script | Not started | |
| 5.2 | Two full rehearsals | Not started | |
| 5.3 | Reset demo data before meeting | Not started | |
| 5.4 | Backup screen recording | Not started | |

DNS A record tihbc.kanwalkumar.com → 2.25.189.195 added. Deploy in 4.3.
