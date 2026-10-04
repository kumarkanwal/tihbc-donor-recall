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

## Phase status

**Phase 1 — Backend foundation (Tasks 1.1–1.4): Done.**

**Phase 2 — Donor and content management: Task 2.1 complete.**
