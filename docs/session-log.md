# Session Log

## S-002 — 2026-10-03 — Backend skeleton

- **Done:** Created the Python 3.12 `uv` backend project; FastAPI factory; typed root `.env` settings; structured JSON logging, request IDs, and phone masking; shared API errors; async PostgreSQL and Redis lifecycle dependencies; demo clock; health and empty v1 routers; PostgreSQL/Redis Compose services; complete `.env.example`; and 22 focused tests.
- **Verification:** `uv sync`, Ruff lint, Ruff format check, strict mypy, and pytest all pass. Uvicorn starts successfully with the required environment, `/health/live` returns 200, and request IDs are returned. All authored source/test files are below 300 lines.
- **Next:** Install or provide Docker, run `docker compose up -d`, verify both containers are healthy, and confirm `/health/ready` returns 200 against the real services. Then mark task 1.1 Done and proceed to task 1.2.
- **Blockers:** Docker/Compose is unavailable on the current machine, so container and real PostgreSQL readiness checks could not be completed. Redis was reachable locally, but PostgreSQL was not.

## S-003 — 2026-10-03 — Backend skeleton verification and config hardening

- **Done:** Confirmed production settings resolve the repository-root `.env` through an absolute path derived from `config.py`; extracted the path calculation into a tested helper; added coverage for loading from a `backend/` working directory and for OS environment precedence; corrected Compose host mappings to PostgreSQL 5432 and Redis 6380; rebuilt `.env.example` with all 53 documented names, local host URLs, and placeholders only.
- **Verification:** Ruff lint and format checks pass, strict mypy passes, and all 24 tests pass. The resolved production path is absolute and points to the existing repository-root `.env`. `.env.example` has exact name parity with `docs/env.md`.
- **Next:** Add the 42 missing documented names to the ignored root `.env`, run the reported Docker/Uvicorn commands locally, and mark task 1.1 Done only after both containers and both health endpoints report healthy/200.
- **Blockers:** Docker is unavailable to this execution session. The current root `.env` is incomplete, so Uvicorn cannot start from it without external environment overrides.

## S-004 — 2026-10-03 — Test artifact isolation and brand identity decision

- **Done:** Configured pytest to keep its base temp directory and cache under `backend/.pytest_tmp`; added that directory to `.gitignore`; limited the documented Uvicorn reload watcher to `backend/app`; confirmed the existing HTTPX TestClient deprecation warning remains tracked as KI-002; and recorded accepted decision D-025 to use TIHBC as the business name with the IHHN logo as the brand mark.
- **Verification:** Ruff lint and format checks pass, strict mypy passes, and all 24 tests pass. Pytest reports the one already-documented HTTPX/Starlette deprecation warning.
- **Next:** Continue task 1.1 runtime verification when the required local-service results are available, using PostgreSQL on `localhost:5433` and Redis on `localhost:6380` as configured in the ignored `.env`.
- **Blockers:** Docker remains unavailable to this execution session; no Docker operation was required for this setup change.

## S-005 — 2026-10-03 — Database models and initial migration

- **Done:** Renumbered the S-002 decisions from conflicting IDs D-001/D-002 to D-026/D-027; added the complete SQLAlchemy model registry for all 17 tables and 18 PostgreSQL enums in `docs/database.md`; added deterministic constraint naming, application-generated UUID v4 identifiers, relationships, required indexes, cascades, checks, and defaults; configured async Alembic; created the self-contained initial migration; and added enum, metadata, constraint, revision-chain, and offline SQL tests. Also completed missing type annotations in existing backend tests so the full test tree passes strict mypy.
- **Verification:** Ruff lint and format checks pass; strict mypy passes across all 38 application and test source files; all 51 tests pass with only the already-recorded KI-002 warning; offline upgrade and downgrade SQL compile; and the user successfully ran PostgreSQL upgrade, `alembic check`, downgrade to base, upgrade to head, and a second `alembic check` against `localhost:5433`. The database is restored at `0001_initial_schema (head)` with no pending schema operations.
- **Next:** Proceed to the next explicitly requested MVP task using the completed model and migration foundation.
- **Blockers:** None for Task 1.2. Docker remains unavailable to this execution session but did not block the user-run PostgreSQL verification.

## S-006 — 2026-10-03 — Database persistence acceptance completion

- **Done:** Completed the remaining Task 1.2 acceptance work: added a typed generic base repository with get, paginated list, and add operations; made the demo clock load its persisted offset during application startup while keeping `now()` cache-only; made advance/reset persist through row-locked transactions; added migration `0002_reference_data` for the three required segments and singleton clock row without modifying `0001`; and added opt-in, reachability-guarded PostgreSQL tests for batch phone uniqueness, open follow-up uniqueness, appointment capacity, clock restart persistence, and reference segments. Isolated configuration tests from the real environment, changed pytest to a directly creatable `.pytest_tmp` base path, removed SQLAlchemy test warnings, and cleaned the sandbox-owned temporary directory with user assistance.
- **Verification:** The unchanged `0001` migration retains SHA-256 `80677123C2FB26C36C74449A7313AEE63B6621F00A6FE81D7FD63578747A4A89`. Ruff lint and format checks pass, strict mypy passes across all 46 application and test source files, offline upgrade/downgrade SQL compiles, and user-run Alembic downgrade/upgrade/current/check commands pass at `0002_reference_data` with no schema drift. The final live PostgreSQL suite reports 60 passed with only the already-recorded KI-002 warning. Integration data is contained by nested savepoints and an outer transaction rolled back in fixture cleanup.
- **Next:** Proceed to the next explicitly requested MVP task.
- **Blockers:** None. Task 1.1 and Task 1.2 are complete.

## S-007 — 2026-10-03 — Codex pytest directory isolation

- **Done:** Reserved `backend/.pytest_tmp` for human local test runs and added the Section 14 rule requiring Codex to route both pytest temporary output and cache data through `backend/.pytest_tmp_codex`. Added `.pytest_tmp_codex/` to `.gitignore`.
- **Verification:** Confirmed both pytest runtime paths are Git-ignored and the documented Codex command overrides both `basetemp` and `cache_dir`, so Codex runs cannot create or modify the human-owned `.pytest_tmp` path.
- **Next:** Use the isolated Codex pytest command for every future backend test run.
- **Blockers:** None.

## S-008 — 2026-10-03 — Authentication and role access

- **Done:** Added Argon2id password hashing, HS256 access-token creation and application-clock verification, case-insensitive authentication with generic credential failures, active-user database resolution, reusable role dependencies, paginated active-user lookup, auth/user schemas and routes, masked login logging, and an idempotent `app.seed.users` command. Completed `.env.example` with all documented settings and retained Codex-only pytest isolation.
- **Verification:** Ruff lint and format checks pass; strict mypy passes across application and tests; the user-run PostgreSQL suite reports 80 passed with only KI-002; two seed command runs returned the same admin/coordinator IDs; admin login succeeded; and authenticated `/api/v1/auth/me` returned HTTP 200 with no password hash.
- **Next:** Build and verify Task 1.4 backend containers and placeholder scheduler worker.
- **Blockers:** None.

## S-009 — 2026-10-03 — Backend containerization

- **Done:** Added a multi-stage Python 3.12 slim image that installs only locked runtime dependencies, runs as a non-root user, and defaults to production Uvicorn; added a shared entrypoint and typed PostgreSQL wait/migration helpers; expanded Compose with healthy API and worker services, internal database/Redis URLs, startup ordering, and persistent media storage; added a signal-aware placeholder scheduler with configurable heartbeats; and documented setup, local mode, Docker mode, seeding, and tests. After verification exposed duplicate migration attempts, added typed `RUN_MIGRATIONS` ownership so only the API applies Alembic while the worker waits and skips it.
- **Verification:** User-run Docker checks confirmed successful image build, healthy database/Redis/API/worker containers, HTTP 200 readiness from host and container, migration head `0002_reference_data`, containerized demo-user seeding, worker heartbeats, clean worker stop/start, and stack shutdown. After the migration-ownership correction, Ruff lint and format checks pass, strict mypy passes across 74 source files, and 80 non-PostgreSQL tests pass with 6 opt-in PostgreSQL tests skipped and only KI-002. Tests explicitly cover `RUN_MIGRATIONS` parsing/defaults and the API-run/worker-skip branches.
- **Next:** Begin the next explicitly requested implementation phase; do not add the frontend container before Task 3.1.
- **Blockers:** None. Phase 1 backend foundation tasks 1.1–1.4 are complete.

## S-010 — 2026-10-03 — Campaign-free donor batch query regression

- **Done:** Changed donor batch list and detail campaign aggregation to a left outer join grouped by batch and uploader, keeping the pagination total independent of campaigns. Audited every Task 2.1 list/detail query: joins to uploader and segment are backed by required foreign keys, while optional campaigns are now explicitly outer-joined. Added a rollback-isolated PostgreSQL HTTP regression that imports a three-donor batch with no campaigns and verifies list, detail, and donor endpoints, including `campaign_count: 0`. Updated result-row iteration for the covered repositories to remain compatible with current SQLAlchemy behavior.
- **Verification:** Ruff lint and format checks pass, strict mypy passes across application and tests, and the complete live PostgreSQL suite passes all 125 tests with only the already-recorded KI-002 warning.
- **Next:** Rebuild/restart the API container and repeat the `/docs` list/detail checks against the manually imported batch. Mark Task 2.1 Done after that runtime verification succeeds.
- **Blockers:** Docker is unavailable to this execution session, so container rebuild and `/docs` verification must be run by the user. No code or automated-test blocker remains.

## S-011 — 2026-10-03 — Donor batch validation completion

- **Done:** Changed within-file duplicate handling so the first normalized phone occurrence remains valid and every later occurrence reports `Duplicate of row N`; retained cross-batch warnings on the accepted first row; rejected imports whose preview has zero valid donors before any database write; and locked batch-name trimming with a 1–120 character limit at the API boundary. Added validator, service, and API coverage for these behaviors; documented the contract in `docs/api.md`; recorded accepted decision D-034; and retained the campaign-free outer-join regression. After confirming it had zero donors and campaigns, deleted the user-identified empty local batch `755c6fbb-e596-4396-9138-1dd941ed617c`.
- **Verification:** User `/docs` verification passed for sample upload, preview, import, list, and detail. Ruff lint and format checks pass, strict mypy passes across application and tests, and the complete live PostgreSQL suite passes all 130 tests with only the already-recorded KI-002 warning.
- **Next:** Proceed to the next explicitly requested MVP task.
- **Blockers:** None. Task 2.1 is complete.

## S-012 — 2026-10-03 — [FE] Task 3.1 specification review

- **Done:** Completed the required project-memory review, read the frontend brand, screen, and environment specifications, confirmed the requested logo is present, and marked Task 3.1 In progress. Checked the working tree, committed history, and full repository for the required D-018, D-019, and D-020 entries.
- **Verification:** Confirmed `docs/decisions.md` currently starts at D-025 and ends at D-034; Git history contains no recoverable text for D-018 through D-020. Confirmed `frontend/.env.local` and `frontend/package.json` do not yet exist.
- **Next:** Restore or provide D-018, D-019, and D-020, then scaffold and verify Task 3.1 without modifying backend code or `docs/api.md`.
- **Blockers:** Required frontend decisions D-018, D-019, and D-020 are missing, so the project rules prohibit guessing and starting implementation.

## S-013 — 2026-10-03 — Content series, templates, and media implementation

- **Done:** Implemented the independent bilingual template renderer with approved-variable validation, display-timezone date formatting, and localized buttons; content-signature JPG/PNG/WebP/MP4 validation, size limits, atomic random-name storage, and `/media` serving; complete content-series list/create/detail/update/activate/archive/duplicate APIs; ordered step create/update/delete/reorder operations; case-insensitive on-demand tags; aggregate activation error reporting; active-campaign and archived-series guards; deep duplication; and simulator-shaped sample/real-donor previews. Added focused renderer, media, schema, validation, role, static-serving, and rollback-isolated PostgreSQL HTTP tests.
- **Verification:** Ruff lint and format checks pass, strict mypy passes across application and tests, OpenAPI generation includes the content-series and media paths, and the complete live PostgreSQL suite passes all 164 tests with only the already-recorded KI-002 warning. All new source and test files remain below 300 lines.
- **Next:** Run the provided Docker `/docs` acceptance flow for the three-step Regular Donor Recall series, Urdu preview, duplicate, and archive; then report the results so Task 2.2 can be marked Done.
- **Blockers:** Docker is unavailable to this execution session. Task 2.2 remains In progress only for the requested user-run container and `/docs` verification.

## S-014 — 2026-10-03 — Deterministic OpenAPI export

- **Done:** Added `python -m app.export_openapi` to export the live FastAPI schema to `frontend/openapi.json` with sorted keys, fixed formatting, UTF-8, and a trailing newline; replaced the frontend placeholder with the current API contract; documented the command and mandatory post-API-change workflow in AGENTS.md; and added repeatability and contract-path tests.
- **Verification:** Two consecutive exports produced identical SHA-256 `0A6A5D8604688BF516CFD91CE652B8483571D478B7A478A11738301F4A595302`. Ruff lint and format checks pass, strict mypy passes across application and tests, and the complete live PostgreSQL suite passes with only the already-recorded KI-002 warning.
- **Next:** Complete the requested Docker `/docs` acceptance flow for Task 2.2 and report the results so the task can be marked Done. Run the exporter and commit `frontend/openapi.json` after every future API change.
- **Blockers:** Docker remains unavailable to this execution session; no exporter or automated-test blocker remains.

## S-015 — 2026-10-03 — [FE] Frontend foundation verification

- **Done:** Completed the Task 3.1 Next.js frontend foundation with strict TypeScript, Tailwind and shadcn-style primitives, exact light/dark brand tokens, next-themes switching, Inter and Noto Nastaliq Urdu fonts, validated public environment config, TanStack Query defaults, Zustand dependency, generated OpenAPI types, authenticated openapi-fetch middleware, typed API errors, global 401 handling, Vitest and Playwright configuration, required folder structure, and the temporary visual-check page. Replaced the theme mount effect with `useSyncExternalStore`, documented and narrowly suppressed the intentional full-reload 401 navigation warning, excluded the backend-owned OpenAPI export from Prettier, removed the generated root pnpm cache, and placed the frontend version decision at D-039 after the backend decisions.
- **Verification:** The official backend exporter restored `frontend/openapi.json` to SHA-256 `0A6A5D8604688BF516CFD91CE652B8483571D478B7A478A11738301F4A595302`; `pnpm gen:api`, lint, strict typecheck, 2 Vitest tests, and the Next.js production build pass. The temporary page was visually checked in light and dark modes at `http://localhost:3000`; no authored source file exceeds 400 lines and components contain no raw hex colors.
- **Next:** Restore the original D-023 and D-024 text, close KI-004, mark Task 3.1 Done, then begin Tasks 3.2–3.4 from their supplied briefs.
- **Blockers:** D-023 and D-024 have no recoverable source text. The detailed Task 3.2–3.4 prompt referenced by the user is also unavailable in the repository and current thread context.

## S-016 — 2026-10-03 — [FE] Task 3.1 closure

- **Done:** Recorded D-023 and D-024 as intentionally skipped during the S-002 renumbering, closed KI-004, added the parallel-session decision namespace rule, and marked Task 3.1 Done. Preserved the backend D-035 and the frontend foundation decision at D-039 as directed.
- **Verification:** Decision IDs D-001 through D-039 are represented exactly once and remain in order, including the combined skipped entry for D-023/D-024. Task 3.1 retains passing API generation, lint, strict typecheck, 2 Vitest tests, production build, and light/dark visual checks.
- **Next:** Implement Task 3.2 app shell, followed by Task 3.3 login/session and Task 3.4 shared components.
- **Blockers:** None for Task 3.1.

## S-017 — 2026-10-03 — [FE] App shell

- **Done:** Replaced the temporary setup page with auth and dashboard route groups; added the shared dashboard layout, seven required navigation destinations, persistent 240/64 px sidebar, tablet collapse, active accent styling, page title and breadcrumb context, role-gated disabled demo-clock control, notification and user-menu placeholders, theme control, reusable page-header and empty states, and the navigation-persistent donor phone panel.
- **Verification:** `pnpm lint`, strict typecheck, 5 Vitest tests, and the Next.js production build pass. The shell, active navigation, light and dark themes, 240 px desktop sidebar, 64 px tablet sidebar, and 400 px donor panel were visually checked at `http://localhost:3000`.
- **Next:** Implement Task 3.3 login, session persistence, current-user query, route protection, logout, and global 401 behavior.
- **Blockers:** None.

## S-018 — 2026-10-04 — [FE] Login and session

- **Done:** Added the centered TIHBC login with React Hook Form and Zod validation, pending and inline error states, generic 401 messaging, typed login and `/auth/me` confirmation, safe requested-page redirects, Zustand memory plus localStorage session persistence, protected-route and logged-in login redirects without protected-content flash, the TanStack Query current-user hook, current-user-driven role visibility and top-bar identity, cache-clearing logout, and global 401 reset. Corrected the generated-client base so versioned OpenAPI paths are not duplicated.
- **Verification:** `pnpm lint`, strict typecheck, 12 Vitest tests, and the Next.js production build pass. Browser checks confirmed `/` redirects to `/login?next=%2F`, the light-theme login layout, 96 px logo, required copy, and inline empty-field validation. The local backend was not running, so credential acceptance was covered with the generated API contract and component-level 401 test rather than a live browser round-trip.
- **Next:** Implement Task 3.4 shared components from `docs/screens.md` section 10.
- **Blockers:** None for implementation; live API acceptance remains environment-dependent.

## S-019 — 2026-10-04 — [FE] Shared components

- **Done:** Completed the section-10 shared component set: PageHeader; TanStack Table v9 DataTable with server pagination and sorting, debounced search, filter slot, accessible row activation, responsive scrolling, and loading/empty/error/success states; every documented database enum in StatusBadge with muted unknown fallback; KpiCard; configurable EmptyState and ErrorState; accessible ConfirmDialog; validated keyboard and drag/drop FileDropzone; permission-aware MaskedPhone; absolute and relative Asia/Karachi DateTime; state-aware ChartCard; English/Urdu LanguageTabs; and a structural PhonePreview for later simulator bubble reuse. Added the destructive button variant required by ConfirmDialog.
- **Verification:** `pnpm lint`, strict typecheck, 18 Vitest tests, and the Next.js production build pass. Date/time formatting, every documented enum value, unknown status fallback, DataTable data/pagination/empty rendering, login errors, API errors, role visibility, safe redirects, and generated-client URL handling have automated coverage. All shared component files are at or below 196 lines and application components contain no raw hex colors.
- **Next:** Proceed to the next explicitly requested frontend task.
- **Blockers:** None.

## S-020 — 2026-10-04 — [FE] Donor Batches pages

- **Done:** Replaced the Donor Batches placeholder with the searchable, sortable, paginated batch list and admin-only upload action; added an admin-guarded three-step CSV/XLSX wizard with authenticated sample download, client-side name/file checks, preview metrics and breakdowns, normalized donor sample, downloadable error CSV, clearly separated cross-batch warnings, zero-valid protection, confirmation, expired-preview recovery, and success links; and added batch details with metrics, breakdowns, searchable/filterable donors, masked phones, and the persisted validation report. Added domain hooks around the generated client with documented donor-batch error handling and preserved API-masked phone values in the shared renderer.
- **Verification:** `pnpm gen:api`, ESLint, strict typecheck, all 24 Vitest tests, and the Next.js production build pass. Five new page-flow tests cover wizard completion, zero-valid blocking, `PREVIEW_EXPIRED`, warnings, and coordinator visibility; a shared regression covers API-masked phone rendering. The local API returned HTTP 200 from `/health/live`; the desktop browser surface failed to attach to localhost after two attempts, so the live upload walkthrough remains a short manual acceptance check rather than an observed automated browser run.
- **Next:** Log in as the demo admin, download and upload the sample CSV, then upload the locally supplied `bad-donors.csv` to visually confirm review/import/detail behavior in the running stack.
- **Blockers:** None in the implementation. `bad-donors.csv` is not stored in the repository, and the desktop browser surface was unavailable for the final interactive check.

## S-021 — 2026-10-04 — [BE] Task 2.2 closure

- **Done:** Closed Content Series Task 2.2 after the full manual `/docs` flow passed. Added a dedicated `TEST_DATABASE_URL` that defaults to `tihbc_test` on the development PostgreSQL server, refuses the development database itself, creates the test database when missing, and migrates it automatically at pytest session start. Made integration assertions select only records created by each test, removed repository-wide pytest temp/cache defaults that caused Windows ownership collisions, and globally removed submitted `input` values from framework validation-error details. Regenerated the deterministic OpenAPI contract.
- **Verification:** User-run isolated PostgreSQL suite passed all 170 tests with only KI-002. Codex-run Ruff lint and format checks pass, strict mypy passes across 120 source files, and the non-PostgreSQL suite reports 158 passed and 12 skipped with only KI-002. OpenAPI SHA-256 remains `0A6A5D8604688BF516CFD91CE652B8483571D478B7A478A11738301F4A595302`.
- **Next:** Proceed to Task 2.3, Campaigns: create, launch, pause, and resume.
- **Blockers:** None. Task 2.2 is complete.

## S-022 — 2026-10-04 — [FE] Content Series pages

- **Done:** Split the batch upload wizard and batch detail screen into focused components; replaced the Content Series placeholder with the paginated table/grid library, complete filters and actions, draft creation, two-column editor, bilingual settings, accessible ordered step cards, media upload, localized quick replies, variable insertion, structured activation feedback, and server-rendered phone preview. Added reusable simulator phone/bubble primitives and enforced archived/coordinator read-only behavior.
- **Verification:** `pnpm gen:api`, ESLint, strict TypeScript, all 29 Vitest tests, and the Next.js production build pass. Focused tests cover activation problem grouping, variable insertion, the three-button limit, archived read-only controls, and the coordinator editor view. The original batch flow tests continue to pass after the component split.
- **Next:** Manually verify the admin and coordinator flows against a running seeded API, then proceed to Task 3.7.
- **Blockers:** None.

## S-023 — 2026-10-04 — [FE] WhatsApp simulator UI

- **Done:** Confirmed Task 3.6 was committed and already closed in progress/session memory; enabled Vitest worker reuse with explicit per-test DOM cleanup; replaced the empty donor-phone panel with a persistent slide-in simulator; added a source-agnostic mock/API data boundary, documented WebSocket subscription, and direct-open helper; seeded four English/Urdu donor conversations including an unreachable number; and implemented search/campaign filtering, masked chat rows, localized bubbles and quick replies, reply lockout, media lightbox, formatting, grouping tails, status ticks, typing, text input, auto-scroll, new-message affordance, secure-business notice, Urdu typography, and mock automatic confirm/reschedule/decline/free-text flows.
- **Verification:** `pnpm lint`, strict TypeScript, all 35 Vitest tests, and the Next.js production build pass. The full pre-change suite passed twice with `isolate: false`, and the final suite passes with explicit cleanup. Focused coverage verifies formatting, sent/delivered/read ticks, disabled replied buttons, typing start/clear and confirm auto-reply timing, Urdu rendering, and unreachable-donor presentation. All simulator components remain below 125 lines and every authored source module remains below 300 lines.
- **Next:** Manually open Donor Phone, select Aisha Khan, tap Confirm, send a free-text reply, and switch to فاطمہ علی to verify the presentation; after backend Task 2.7, export OpenAPI, regenerate the client, remove the KI-005 compatibility bridge, and test `NEXT_PUBLIC_SIMULATOR_SOURCE=api`.
- **Blockers:** None for Task 3.8 mock mode. API-backed mode intentionally awaits backend Task 2.7.

## S-024 — 2026-10-04 — [BE] Campaign lifecycle and enrollments

- **Done:** Completed Task 2.3 with paginated campaign creation, draft updates, detail and status filtering; centralized launch, scheduled-start, pause, resume, and completion transitions; aggregate launch validation; transactional donor enrollment creation without messages; grouped enrollment-status counts; filtered enrollment list/detail views; coordinator read-only access; real donor-batch campaign counts; and end-to-end content-series edit protection. Split campaign and enrollment persistence into focused repositories, removed deprecated SQLAlchemy result conversions, and regenerated the deterministic OpenAPI contract.
- **Verification:** User-run isolated PostgreSQL suite passed all 203 tests; the 13 campaign-query deprecation warnings it exposed were removed afterward, leaving only KI-002 in the Codex-run suite. User `/docs` verification passed archived-series validation, draft repair, launch with three pending enrollments, complete zero-filled counts, masked list/full detail phones, empty timeline/follow-up/appointment, pause/resume, live-series edit blocking, same-batch double-launch blocking, and coordinator read/write roles. Ruff lint and format checks pass, strict mypy passes across 81 application files, and the non-PostgreSQL suite reports 189 passed and 14 skipped with only KI-002. OpenAPI SHA-256 is `FCE04042DE12801B0C183F745ADB03AFE84A38675E17C68FD56FE6C5CF1AFAE0`.
- **Next:** Proceed to Task 2.4, the simulator messaging provider.
- **Blockers:** None. Task 2.3 is complete.

## S-025 — 2026-10-04 — [BE] Simulator messaging and delivery

- **Done:** Completed Task 2.4 with a provider-neutral messaging contract and configured simulator provider; post-commit domain-event publishing; capacity-safe appointment selection and idempotent demo slot seeding; transactional, row-locked next-step sending with bilingual rendering, unreachable-donor handling, scheduling math, and duplicate prevention; deterministic sent-to-delivered-to-read progression; and demo-only send and delivery CLI tools. Corrected appointment selection for historical campaign starts, added a 14-day preferred/alternate-center search and localized no-slot fallback, aligned the `message.created` event with the documented public message shape, narrowed delivery row locks to messages, and added non-sensitive send/failure logging.
- **Verification:** User-run isolated PostgreSQL suite passed all 221 tests with only KI-002. User CLI/API verification confirmed idempotent slot seeding, successful image message send, post-commit events, a 10:00 Asia/Karachi appointment based on current demo time, primary-step scheduling three days later, delivered/read progression, a complete enrollment timeline, and a second-send no-op. Codex-run Ruff lint and format checks pass, strict mypy passes across 106 application files, and the non-PostgreSQL suite reports 197 passed and 24 skipped with only KI-002. The deterministic OpenAPI export is current and unchanged.
- **Next:** Proceed to Task 2.5, scheduler dispatch and escalation.
- **Blockers:** None. Task 2.4 is complete.

## S-026 — 2026-10-04 — [FE] Campaign pages

- **Done:** Regenerated the frontend API types from the committed campaign contract; added the complete campaign library with status tabs, full-catalog search/sorting, pagination, progress, and administrator-only creation; built draft creation/editing with searchable batch and active-series choices, Asia/Karachi scheduling, language coverage warnings, and a projected primary-to-secondary escalation timeline; added confirmed launch plus structured backend problem rendering; and completed campaign detail lifecycle actions, enrollment status filters, sequence placeholders, enrollment details, and direct donor-phone chat opening. Coordinators and non-draft campaigns are read-only. While running the full suite, corrected two simulator hook warnings exposed by the shared lint gate without changing simulator behavior.
- **Verification:** `pnpm gen:api`, ESLint, strict TypeScript, all 41 Vitest tests, and the Next.js production build pass. Six focused tests cover launch-problem rendering, language coverage warnings, status-tab filtering, pause/resume controls, coordinator read-only behavior, and the View chat helper. Campaign components remain below the repository's component-size limit.
- **Next:** Manually open the existing `Task 2.3 Manual Test` campaign to verify lifecycle, enrollments, and donor chat, then open `Duplicate Batch Test` and confirm its launch is rejected with the same-batch conflict from D-042.
- **Blockers:** None.

## S-027 — 2026-10-04 — [FE] Live updates infrastructure and Skip time

- **Done:** Completed Task 3.13 part 1 with one authenticated WebSocket client per browser tab, bounded exponential reconnect, active-query refresh after reconnect, strict documented event types, unknown-event filtering, and one centralized cache/notification router. Moved API-backed simulator events onto the shared client and retained mock events through the same cache router. Added an accessible toast viewport plus the administrator-only Asia/Karachi demo clock and Skip time menu for one hour, one/three/seven days, and reset; successful changes refresh campaign, enrollment, simulator, and metrics data and show the new time. Added `NEXT_PUBLIC_REALTIME`, defaulting off pending backend Task 2.6.
- **Verification:** `pnpm gen:api` was run against the current backend working-copy contract; because those demo routes are not yet committed in `frontend/openapi.json`, the generated drift was not retained and the documented compatibility shapes are used. ESLint, strict TypeScript, all 49 Vitest tests, and the Next.js production build pass. New coverage verifies reconnect backoff, unknown-event handling, centralized cache mapping, follow-up toast behavior, clock API requests and invalidations, Skip time selection, and coordinator hiding.
- **Requests for backend:** Complete Task 2.6 and expose authenticated `/ws` before enabling `NEXT_PUBLIC_REALTIME=on`. Commit and export the Task 2.5 demo-clock routes currently present in the shared working copy; then regenerate the client and remove the narrow clock compatibility bridge.
- **Next:** Complete the remaining Task 3.13 live-update integration after the WebSocket and outstanding feature APIs are committed, then enable and verify realtime against the running stack.
- **Blockers:** None for part 1; live WebSocket acceptance intentionally waits for backend Task 2.6.
