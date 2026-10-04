# MVP Progress

| Task | Status | Notes |
|---|---|---|
| 1.1 Backend skeleton | Done | Automated checks pass. User verification confirmed Docker Compose services healthy, `/health/ready` returned 200, and the complete test suite passed. Pytest artifacts are isolated under `backend/.pytest_tmp`, and Uvicorn reload watches only `backend/app`. |
| 1.2 Database models and migrations | Done | Implemented all specified models, constraints, relationships, generic repository operations, cached persistent demo clock, and migrations through `0002_reference_data`. Upgrade/downgrade and schema-parity checks pass; all 60 tests pass against PostgreSQL, and integration writes are rollback-isolated. |
| 1.3 Authentication and role access | Done | Added Argon2 password hashing, clock-aware HS256 access tokens, active-user and role enforcement, auth/user APIs, and idempotent demo-user seeding. All 80 tests pass against PostgreSQL; seed reruns retain user IDs; admin login and `/auth/me` were verified through OpenAPI docs. |
| 1.4 Docker compose for the backend | Done | Added a non-root multi-stage backend image, shared PostgreSQL-waiting entrypoint, API-owned migrations, healthy API/worker Compose services, persistent media storage, graceful placeholder worker heartbeats, and local/Docker documentation. User-run Docker build, health, migration, seed, log, restart, and shutdown checks passed. |
| 2.1 Donor batch upload | Done | CSV/XLSX preview, first-occurrence duplicate handling, cross-batch warnings, Redis preview storage, non-empty transactional import, protected batch/donor APIs, campaign-free list/detail behavior, and PostgreSQL HTTP coverage are complete. User `/docs` verification passed for sample upload, preview, import, list, and detail. |
| 2.2 Content series, steps, and media upload | In progress | Renderer, validated media storage/static serving, full content-series lifecycle, ordered step management, preview rendering, role guards, PostgreSQL HTTP coverage, and deterministic committed OpenAPI export are implemented. All automated checks pass; awaiting the requested user-run Docker `/docs` acceptance flow. |
| 3.1 Frontend setup, design tokens, and API client | Done | Next.js foundation, exact light/dark tokens, fonts, theme and query providers, validated environment, generated typed API client, global auth/error handling, tooling, temporary visual page, and required folder structure are complete. API generation, lint, typecheck, 2 tests, production build, and light/dark visual checks pass. |
| 3.2 App shell | Done | Added auth/dashboard route groups, persistent 240/64 px responsive navigation, active-route styling, page context and role-gated top-bar controls, light/dark theme access, placeholder routes, and a navigation-persistent donor phone panel. Lint, typecheck, 5 tests, production build, and responsive light/dark visual checks pass. |
| 3.3 Login and session | Done | Added the validated staff login, safe return paths, typed login plus `/auth/me` confirmation, demo-only memory/localStorage session persistence, protected-route and login redirects without content flash, current-user query, shared role visibility, cache-clearing logout, and global 401 reset. Lint, typecheck, 12 tests, production build, protected-route redirect, login layout, and inline validation checks pass. |
| 3.4 Shared components | Done | Added typed PageHeader, server-side DataTable, complete StatusBadge coverage, KpiCard, EmptyState, ErrorState, ConfirmDialog, FileDropzone, MaskedPhone, DateTime, ChartCard, LanguageTabs, and structural PhonePreview. All use design tokens, required view states, accessible controls, and responsive layouts. Lint, typecheck, 18 tests, and production build pass. |
| 3.5 Donor Batches pages | Done | Added the searchable/sortable batch list, role-gated three-step CSV/XLSX upload and import wizard, warning/error review, expired-preview recovery, authenticated downloads, batch detail metrics, filtered donor browsing, and validation reports. API generation, lint, strict typecheck, 24 tests, and the production build pass. |

## Phase status

**Phase 1 — Backend foundation (Tasks 1.1–1.4): Done.**

**Phase 2 — Donor and content management: Task 2.1 complete.**

**Phase 3 — Frontend application: Tasks 3.1–3.5 complete.**
