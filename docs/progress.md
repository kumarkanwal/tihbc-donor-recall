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
| 2.4 | Messaging provider (simulator) | In progress | Building provider injection, appointment booking, step sending, deterministic delivery progression, events, CLI tools, and coverage. |
| 2.5 | Scheduler: dispatcher and escalation | Not started | |
| 2.6 | WebSockets and Redis events | Not started | |
| 2.7 | Simulator API | Not started | |
| 2.8 | Reply service flows | Not started | |
| 2.9 | LangGraph agent, fallback, LangSmith | Not started | |
| 2.10 | Follow-up inbox API | Not started | |
| 2.11 | Metrics and reports API | Not started | |
| 2.12 | Settings and demo clock API | Not started | |
| 2.13 | Seed data | Not started | |
| 2.14 | Backend tests | Not started | |

## Phase 3: Frontend
| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Setup, tokens, generated API client | Not started | |
| 3.2 | App shell and skip-time control | Not started | |
| 3.3 | Login | Not started | |
| 3.4 | Shared components | Not started | |
| 3.5 | Donor batches | Not started | |
| 3.6 | Content series library and editor | Done | Added the searchable/filterable table and grid library, administrator lifecycle actions, bilingual settings and step editor, accessible reordering, media upload, server-rendered simulator preview, activation problem groups, and coordinator/archived read-only states. API generation, lint, strict typecheck, 29 tests, and the production build pass. |
| 3.7 | Campaigns | Not started | |
| 3.8 | WhatsApp simulator | Done | Added the persistent slide-in donor phone, searchable mock conversation picker, localized live chats, reply flows, typing, ticks, media, formatting, RTL support, direct-open helper, and mock/API source boundary. Lint, strict typecheck, 35 tests, and the production build pass. |
| 3.9 | Follow-up inbox | Not started | |
| 3.10 | Dashboard | Not started | |
| 3.11 | Reports | Not started | |
| 3.12 | Settings | Not started | |
| 3.13 | WebSocket live updates | Not started | |

## Phase 4: Integration and deployment
| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | End-to-end Playwright flow | Not started | |
| 4.2 | Agent test with real LLM (EN, UR, Roman Urdu) | Not started | |
| 4.3 | Deploy to VPS | Not started | |
| 4.4 | Bug fixes and polish | Not started | |

## Phase 5: Demo preparation (human)
| # | Task | Status | Notes |
|---|---|---|---|
| 5.1 | Demo script | Not started | |
| 5.2 | Two full rehearsals | Not started | |
| 5.3 | Reset demo data before meeting | Not started | |
| 5.4 | Backup screen recording | Not started | |

DNS A record tihbc.kanwalkumar.com → 2.25.189.195 added. Deploy in 4.3.
