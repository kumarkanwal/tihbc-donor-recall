# Decision Log

Append-only. Never renumber or delete. Format:
ID, Date, Status (Proposed / Accepted / Superseded), Decision, Reason, Consequences.

## D-001: Build a demo MVP with a WhatsApp simulator
Date: 2026-10-03 | Status: Accepted
Decision: No real WhatsApp API in the MVP. Messages go to an in-app simulator that looks like WhatsApp.
Reason: Client wants to experience the full flow before signing; avoids Meta verification delays.
Consequences: Messaging must sit behind a provider interface (see D-006).

## D-002: Monorepo with separate backend and frontend apps
Date: 2026-10-03 | Status: Accepted
Decision: One repo, `backend/` and `frontend/` developed and deployed independently.
Reason: Professional separation while giving Codex full-system context.

## D-003: Backend stack
Date: 2026-10-03 | Status: Accepted
Decision: FastAPI, async SQLAlchemy 2, PostgreSQL 16, Redis 7, Alembic, uv.
Reason: Team expertise; async suits WebSockets and the scheduler.

## D-004: Frontend stack
Date: 2026-10-03 | Status: Accepted
Decision: Next.js App Router, TypeScript strict, Tailwind, shadcn/ui, TanStack Query, pnpm.

## D-005: Contract-first API
Date: 2026-10-03 | Status: Accepted
Decision: Frontend types and client are generated from the backend OpenAPI spec.
Reason: Prevents backend and frontend from drifting apart and avoids duplicated types.

## D-006: Messaging provider abstraction
Date: 2026-10-03 | Status: Accepted
Decision: `MessagingProvider` interface; `SimulatorProvider` for the MVP.
Consequences: A `WhatsAppCloudProvider` can be added later without changing business logic.

## D-007: Demo clock and DB-polling dispatcher
Date: 2026-10-03 | Status: Accepted
Decision: All time comes from `core/clock.py` with a stored offset. The dispatcher polls due messages
from the DB. A time-skip endpoint advances the clock.
Reason: Lets the presenter show Day 3 / Day 7 and escalation in minutes; no extra broker.
Consequences: Fine for demo scale; revisit for production volume.

## D-008: Buttons are deterministic, AI only for free text
Date: 2026-10-03 | Status: Accepted
Decision: Button replies map directly to intents. The LangGraph agent handles free text only and never
writes to the DB or sends messages.
Reason: Lower cost, predictable demo, clean separation of concerns.

## D-009: Agent fallback
Date: 2026-10-03 | Status: Accepted
Decision: Low confidence, error, or timeout → intent `unknown` → `needs_call` follow-up.
If `LLM_ENABLED=false`, a keyword classifier is used.
Reason: The demo must never break because of the LLM.

## D-010: Observability with LangSmith and structlog
Date: 2026-10-03 | Status: Accepted
Decision: LangSmith traces every agent run; structlog JSON logs with request IDs.
No names or phone numbers are sent to the LLM or LangSmith.

## D-011: Two-step batch upload
Date: 2026-10-03 | Status: Accepted
Decision: Upload → preview (stored in Redis with a token, 30 min) → confirm import.
Reason: Nothing is saved until the admin reviews validation results.

## D-012: Reschedule via appointment slots
Date: 2026-10-03 | Status: Accepted
Decision: The bot offers up to 3 available slots as buttons; donors may also reply in free text.

## D-013: Decline reason capture
Date: 2026-10-03 | Status: Accepted
Decision: One follow-up question asks for the reason (Travelling, Health reason, Other).
Reason: Gives TIHBC useful reporting without pressuring the donor.

## D-014: Simulator shows the donor's perspective
Date: 2026-10-03 | Status: Accepted
Decision: TIHBC messages are incoming (left, white); donor replies are outgoing (right, green).
No WhatsApp logo or trademarked assets.

## D-015: UI style
Date: 2026-10-03 | Status: Accepted
Decision: Clean healthcare UI, no emojis, no AI-style visuals. Brand colors provisional until TIHBC
assets are received (`docs/brand.md`).

## D-016: Codex is the only coding agent
Date: 2026-10-03 | Status: Accepted
Decision: All code is written with Codex. Planning happens outside the repo.

## D-017: MVP scope
Date: 2026-10-03 | Status: Accepted
Decision: Phase 1 scope + AI reply agent + demo time-skip.
Deferred: donor eligibility check, opt-out (STOP) handling, campaign cost estimator, real WhatsApp API.

## D-018: Brand colors from client logo
Date: 2026-10-03 | Status: Accepted
Decision: Indus Blue #1F4799 is the primary color; Indus Red #E8202A is accent only.
Reason: Blue meets contrast for button text; red is reserved for emphasis so it is not confused
with errors. Full tokens in docs/brand.md.

## D-019: Light and dark mode
Date: 2026-10-03 | Status: Accepted
Decision: Light mode is default; Light / Dark / System switch using next-themes (class strategy).
All colors via tokens defined in docs/brand.md.
Consequences: Every screen must be checked in both themes.

## D-020: Simulator always uses light WhatsApp theme
Date: 2026-10-03 | Status: Accepted
Decision: The WhatsApp simulator ignores the app theme and uses its own WhatsApp tokens
(docs/simulator.md section 4) in both light and dark mode.
Reason: It represents a real donor phone screen.

## D-021: Local-first development, VPS at the end
Date: 2026-10-03 | Status: Accepted
Decision: Build and test everything locally with docker compose; deploy to the VPS in Phase 4.

## D-022: Multi-provider LLM routing with fallback
Date: 2026-10-03 | Status: Accepted
Decision: Router tries providers in LLM_PROVIDER_ORDER (default Groq first) with per-provider
timeout, total budget, and a Redis circuit breaker. Only API keys are required; default models
live in agents/llm/providers.py. Nodes never know which provider answered.
Reason: Speed (Groq) plus reliability; free tiers hit rate limits.
Consequences: Each provider's model must support structured output.

## D-023, D-024: Not used
Date: 2026-10-03 | Status: Skipped
Note: IDs reserved during the S-002 renumbering but never assigned. Do not reuse.

## D-025 — TIHBC business name with IHHN brand mark

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** Use `TIHBC` as the business name everywhere in the product. Use the IHHN logo as the brand mark.
- **Reason:** This keeps the operating identity consistent while retaining the approved parent-network visual identity.

## D-026 — Application-owned infrastructure lifecycles

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** Create the async SQLAlchemy engine/session factory and Redis client during the FastAPI lifespan, store typed resource objects on application state, and close them during shutdown. Request dependencies retrieve those lifecycle-owned resources.
- **Reason:** This avoids import-time network access, gives each process one managed connection pool/client, and keeps dependencies straightforward to override in tests.

## D-027 — Safe readiness failure details

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** A failed readiness probe returns HTTP 503 with `status: not_ready` and only the names of failed dependencies. It does not expose connection exception text.
- **Reason:** Operators can identify the unavailable service without leaking connection strings, hosts, credentials, or driver details.

## D-028 — Deterministic database identity and constraint naming

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** Generate UUID v4 primary keys in application code and apply one SQLAlchemy naming convention to primary keys, foreign keys, unique constraints, checks, and indexes. Keep the initial Alembic migration self-contained rather than importing live model definitions.
- **Reason:** Application-generated identifiers avoid requiring a PostgreSQL UUID extension, while deterministic names and a self-contained migration make upgrades, downgrades, and future schema comparisons stable.

## D-029 — Migration-owned foundational reference rows

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** Seed the `regular`, `lapsed`, and `first_time` segments with stable UUIDs, and seed the singleton demo-clock row, in revision `0002_reference_data`. Clock reads remain cache-only after startup; offset changes use short row-locked database transactions.
- **Reason:** Migration ownership guarantees every upgraded environment has the same required reference keys and clock singleton before application startup, while stable identifiers keep seed data repeatable.

## D-030 — Authentication primitives and authorization source

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** Hash passwords with Argon2id through `argon2-cffi` defaults and sign access tokens with PyJWT using HS256. Verify token expiry against the application clock, but load the current active user and role from PostgreSQL for every authenticated request. Use FastAPI's bearer security scheme only for token extraction and OpenAPI authorization support; domain exceptions retain the shared error response shape.
- **Reason:** This follows the approved security stack, makes demo-clock expiry deterministic, invalidates disabled accounts immediately, prevents stale token roles from granting access, and keeps API errors consistent.

## D-031 — Shared backend container lifecycle

- **Date:** 2026-10-03
- **Status:** Superseded by D-032
- **Decision:** Build one non-root production backend image for both API and worker processes. Its entrypoint waits for PostgreSQL and applies Alembic migrations before executing the supplied process command; Compose starts the worker only after the API is healthy so initial migrations are serialized.
- **Reason:** A shared image prevents dependency drift between processes, automatic migrations make startup reproducible, and API-gated worker startup avoids concurrent first-run migration races.

## D-032 — API-owned container migrations

- **Date:** 2026-10-03
- **Status:** Accepted
- **Supersedes:** D-031
- **Decision:** Keep one backend image and one entrypoint for API and worker, but gate Alembic with typed `RUN_MIGRATIONS` configuration. Compose sets it to `true` only for the API and explicitly to `false` for the worker; both processes still wait for PostgreSQL.
- **Reason:** A single migration owner eliminates cross-container Alembic races while preserving identical dependencies, readiness behavior, and startup scripts for both backend processes.

## D-033 — Cross-batch donor phone warnings

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** Enforce donor phone uniqueness only within a batch. During preview, a valid phone found in an earlier batch remains importable and produces a warning containing the source row, masked phone, and most recently created matching batch name.
- **Reason:** Repeat donor participation across recall batches is expected, while a visible warning gives staff context without blocking legitimate imports or exposing full phone numbers.

## D-034 — Deterministic duplicate rows and non-empty batch imports

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** For phones duplicated within one upload, accept the first normalized occurrence and reject each later occurrence with `Duplicate of row N`, referencing the first source row. Continue applying cross-batch warnings to the retained first row. Permit previews with zero valid donors for validation feedback, but reject their import with `VALIDATION_ERROR`. Trim batch names and require 1–120 characters at the API boundary.
- **Reason:** Staff should be able to import the first usable donor row while receiving an actionable pointer for every duplicate, and the system should not persist batches that cannot enroll any donors.

## D-035: Shared bilingual template-rendering boundary
Date: 2026-10-03 | Status: Accepted
Decision: Validate and render all message variables through `services/templates/renderer.py`. Support
only `donor_name`, `center_name`, and `appointment_date`; render appointment dates through
`TIMEZONE_DISPLAY` using the documented English and Urdu slot styles; and localize quick-reply labels
in the same boundary.
Reason: The series preview, messaging engine, simulator, and future automatic replies need identical
substitution, timezone, date, and button-label behavior without depending on series persistence.

## D-036: Active-series edits preserve activation validity
Date: 2026-10-03 | Status: Accepted
Decision: Permit edits to an active series only when it is not referenced by a scheduled, running, or
paused campaign. Keep its status active and reject any edit that would leave it incomplete under the
activation rules. Archived series remain immutable and cannot be reactivated.
Reason: This follows the specified campaign edit guard while preventing an active, selectable series
from becoming structurally invalid.

## D-037: Content-derived random-name media storage
Date: 2026-10-03 | Status: Accepted
Decision: Identify JPG, PNG, WebP, and MP4 uploads from binary signatures, enforce limits by detected
type, infer the stored extension, and write each asset atomically under a UUID-based random filename in
`MEDIA_STORAGE_DIR`. Serve the directory at `/media` and return URLs beneath `MEDIA_PUBLIC_URL`.
Reason: Request MIME types and filenames are untrusted, while inferred extensions and random names
prevent type confusion and filename collisions without adding a dependency.

## D-038: Backend-owned deterministic OpenAPI export
Date: 2026-10-03 | Status: Accepted
Decision: Export the live FastAPI contract with `python -m app.export_openapi` to the repository's
`frontend/openapi.json`, using sorted JSON keys, fixed two-space indentation, UTF-8, and one trailing
newline. Resolve the output from the module location so the command does not depend on the shell's
working directory beyond running the backend package.
Reason: A committed, reproducible contract keeps frontend client generation reviewable and prevents
the checked-in OpenAPI file from drifting behind backend route changes.

## D-039 — Frontend foundation versions and generated API contract

- **Date:** 2026-10-03
- **Status:** Accepted
- **Decision:** Use pnpm 12.4.2, Next.js 16.3.8, React 19.3.0, Tailwind CSS 4.3.3, and TypeScript 5.9.3 for the frontend foundation. Generate and commit API types from `frontend/openapi.json` with openapi-typescript 7.13.0, and call them through openapi-fetch 0.17.0. TypeScript 5.9.3 is the newest stable release compatible with openapi-typescript and the approved ESLint TypeScript tooling.
- **Reason:** Pinning the verified current-compatible foundation makes local and CI behavior reproducible while keeping the API contract generated rather than duplicated by hand.

## D-100 — Demo browser session persistence

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Store the access token and confirmed current user in a Zustand session store backed by browser `localStorage`. Keep all access behind the shared session module and clear the store, persisted value, and TanStack Query cache on logout. A 401 performs an intentional full navigation to clear in-memory authenticated state globally.
- **Reason:** The MVP needs sessions to survive navigation and reloads without adding an unavailable server-side cookie flow. Centralizing access keeps the demo-only persistence replaceable when production authentication is designed.
- **Consequences:** Browser storage is acceptable only for this demo and must not be treated as the production security model.

## D-101 — Headless shared-component foundations

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Build the server-driven `DataTable` on TanStack React Table 9.2.4 and use the shadcn-compatible Radix Alert Dialog and Tabs primitives for confirmation and bilingual content. Keep application styling and state presentation in repository-owned shared components.
- **Reason:** These approved headless foundations provide typed table state and accessible interaction behavior without imposing visual styles that conflict with the TIHBC tokens.
- **Consequences:** Feature pages supply server pagination, sorting, filters, and data while the shared components remain free of domain business logic.

## D-040 — Automatically provisioned isolated PostgreSQL tests

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** PostgreSQL tests replace the application database URL with `TEST_DATABASE_URL`. When it is unset, derive a `tihbc_test` database on the `DATABASE_URL` server. Refuse an identical development target, create the test database when absent, migrate it to Alembic head at session start, and keep each test rollback-isolated. Tests identify only records they create. Normal local pytest runs use the operating-system temporary directory; Codex alone uses `.pytest_tmp_codex`, and the cache provider stays disabled.
- **Reason:** Automated tests must never observe or mutate development data, must remain repeatable when a test database contains prior records, and must not create cross-user Windows permission conflicts in repository-owned temp/cache directories.

## D-041 — Redacted framework validation details

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Framework request-validation responses expose only `loc`, `msg`, and `type` for each error. The original submitted `input` value is removed globally before serialization.
- **Reason:** Validation metadata remains actionable without reflecting donor names, phone numbers, or other personal data in API responses.

## D-102 — Shared simulator presentation and dependency-free step ordering

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Keep simulator-only visual tokens in the shared theme token file and implement the phone frame and message bubble under `components/simulator/` for reuse by series previews and Task 3.8. Series steps use native pointer drag behavior plus explicit Move up/Move down buttons for keyboard operation, without adding a drag-and-drop dependency.
- **Reason:** The series preview and future simulator must remain visually identical, while explicit movement controls make ordering reliable and accessible without expanding the dependency surface.
- **Consequences:** Future simulator work should extend the shared simulator primitives instead of creating separate bubble styles, and step order changes continue to submit the complete backend-defined ID sequence.

## D-103 — Source-agnostic simulator boundary

- **Date:** 2026-10-04
- **Status:** Superseded by D-109
- **Decision:** Put all donor conversation reads, opens, replies, and live-event subscriptions behind one `SimulatorDataSource` interface selected by `NEXT_PUBLIC_SIMULATOR_SOURCE=mock|api`, defaulting to the in-memory mock. Keep the UI and TanStack Query hooks unaware of the selected source. Until backend Task 2.7 exports the documented simulator routes, the API adapter uses a narrow compatibility type bridge around the shared authenticated generated client and the documented WebSocket envelope.
- **Reason:** The complete demo interaction can be built and tested against deterministic mock data now, while the same UI can switch to REST and WebSocket delivery without component changes when the generated contract lands.
- **Consequences:** Task 2.7 must export the section-7 routes, after which the compatibility bridge is removed and the adapter compiles directly against generated path types; KI-005 tracks this handoff.

## D-104 — Reused Vitest worker with explicit DOM cleanup

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Run the frontend Vitest suite with one reused thread (`isolate: false`, `maxWorkers: 1`) and perform Testing Library cleanup explicitly after every test.
- **Reason:** Reusing the worker substantially reduces repeated jsdom startup cost while explicit cleanup preserves deterministic component isolation. The complete suite passed repeatedly before and after the change.
- **Consequences:** Tests must reset other module-level mutable state they introduce; DOM state is cleared centrally in `test/setup.ts`.

## D-042 — One live campaign per donor batch

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** On launch, lock the donor batch and reject the campaign when another campaign for that batch is `scheduled`, `running`, or `paused`. Draft and completed campaigns do not block launch.
- **Reason:** A donor batch represents one messaging audience; allowing two live campaigns to enroll it would double-message the same donors. The batch lock also prevents concurrent launches from bypassing the check.

## D-043 — Clock-anchored appointments with non-blocking fallback

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Calculate the default appointment from the later of campaign start and demo-clock time, then add two local calendar days and target 10:00 Asia/Karachi. Search the donor's city-selected center through the following 14 days before searching either demo center over the same window, locking the selected row before incrementing capacity. If no slot is available, send the message without an appointment, render `at your earliest convenience` in English or `اپنی جلد از جلد سہولت کے مطابق` in Urdu, and log a warning without donor personal data. Map Nazimabad cities to North Nazimabad Donor Center and default all other or missing cities to Korangi Campus Blood Center.
- **Reason:** Running campaigns may have historical start dates or temporarily exhausted slots. Appointment inventory must remain capacity-safe without stopping donor outreach or crashing the messaging worker.
- **Consequences:** Enrollment appointment data may remain null for a successfully sent message; downstream reply and rescheduling flows must support that state.

## D-105 — Complete campaign catalog for frontend search and sorting

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Load every page of the status-filtered campaign collection through the generated API client, then apply campaign search, sorting, and UI pagination to the complete result in the frontend. Keep enrollment search and pagination server-driven because that endpoint already exposes those query parameters.
- **Reason:** The campaign API currently filters only by status and page. The required campaign-wide search and sortable columns must remain correct beyond the backend's 100-row maximum page size without bypassing the generated client or adding an undocumented API contract.
- **Consequences:** Campaign catalog reads may make multiple paginated requests when there are more than 100 campaigns; a future backend search/sort contract can replace this aggregation without changing the table component.

## D-106 — One centralized realtime client and cache router

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Own one authenticated WebSocket client at the application-provider boundary per browser tab, and route every documented event through one cache-mapping module. API-backed simulator subscriptions share this client. Gate the connection with `NEXT_PUBLIC_REALTIME=on|off`, defaulting to `off` until the backend WebSocket task is complete.
- **Reason:** A single connection prevents duplicate events and reconnect loops, while centralized cache effects keep feature components independent of transport details and make reconnect-wide active-query refresh reliable.
- **Consequences:** New event types must be added to the typed event union and central router; they must not introduce component-level WebSocket connections or event handlers.

## D-044 — Bounded row-claimed scheduler transactions

- **Date:** 2026-10-04
- **Status:** Accepted
- **Decision:** Run scheduler phases in a fixed order and process each claimed campaign or enrollment in its own transaction. Claim work with PostgreSQL `FOR UPDATE SKIP LOCKED`, exclude a processed or failed record for the remainder of that tick, and cap each phase with `DISPATCHER_BATCH_SIZE`.
- **Reason:** Separate transactions isolate failures, skip-locked claims allow concurrent workers without duplicate sends, per-tick exclusion prevents an idempotent no-op from starving later records, and bounded phases keep polling responsive.
- **Consequences:** A failed record is retried on a later tick, while other due work continues during the current tick. Campaign completion and delivery progression run after enrollment dispatch in the same ordered tick.

## D-107 — Single pending frontend contract boundary

- **Date:** 2026-10-04
- **Status:** Superseded by D-108
- **Decision:** Define every temporary request and response type for the unimplemented follow-up, metrics, and reports endpoints in `frontend/lib/api/pending-contracts.ts`, alongside one narrow compatibility view of the normal authenticated API client. Feature hooks consume this boundary and expose a specific backend-update state for HTTP 404.
- **Reason:** Tasks 3.9–3.11 must implement the documented UI before backend Tasks 2.10/2.11 export OpenAPI types, while keeping temporary contracts easy to find, review, and delete without introducing component-level requests.
- **Consequences:** After backend Tasks 2.10/2.11, regenerate the API client, replace all pending-contract imports with generated types, remove the compatibility file, and close KI-008.

## D-108 — Extend the pending frontend contract boundary through Settings

- **Date:** 2026-10-05
- **Status:** Accepted
- **Supersedes:** D-107
- **Decision:** Keep the temporary integration-status and demo-data-reset shapes for Task 3.12 in the existing `frontend/lib/api/pending-contracts.ts` boundary, alongside the follow-up and metrics contracts. Continue using the normal authenticated API client and surface HTTP 404 as an explicit backend-update state. Remove each domain from the boundary independently when its generated OpenAPI contract lands.
- **Reason:** Backend Task 2.12 is not implemented, while the Settings UI must follow the documented contract now. Extending the one compatibility boundary avoids a second handwritten API-type module and keeps every temporary frontend contract easy to locate and retire.
- **Consequences:** Backend Tasks 2.10/2.11 close KI-008 and remove their types without waiting for Settings. Backend Task 2.12 closes KI-009 and allows the remaining compatibility types and reset call to use the generated client directly.

## D-045 — Lifecycle-owned Redis event fan-out and public payload boundary

- **Date:** 2026-10-05
- **Status:** Accepted
- **Decision:** Define domain event names and allow-listed payload models once in `ws/events.py`. Inject a Redis publisher into API, scheduler, and demo tools; own one subscriber and connection manager per API process. Coalesce metrics by campaign into the latest notification within a two-second window. Use Uvicorn's native ping/pong heartbeat and revalidate the active user every 20 seconds; check token expiry before every broadcast. Validate payloads at publication and reception and discard internal fields.
- **Reason:** Worker events must reach every API process without duplicate local broadcast paths, clients must receive only the shared staff REST fields, and burst invalidations should not cause repeated metric queries. Native control frames preserve the documented event union.
- **Consequences:** Redis outages are logged and subscribers retry; an outage cannot undo committed domain writes. Pub/sub has no replay guarantee, so clients refetch after reconnect. Real Redis tests use unique temporary channels and do not flush server data. The listener omits message bodies from logs.

## D-046 — Unclassified simulator replies and stable history cursors

- **Date:** 2026-10-05
- **Status:** Superseded by D-047
- **Decision:** Store button/text replies as delivered inbound messages under the enrollment row lock, clear `next_action_at`, and preserve the first `responded_at` without changing enrollment status or creating intent/follow-up records. Link text replies to the latest sent outbound message and button replies to their validated source; reject repeated button replies after either reply form. Publish public message/enrollment/metrics events only after commit. Limit simulated delivery progression and conversation-open read updates to outbound messages. Use exclusive message-UUID cursors resolved to `(created_at, id)` for history; return each latest slice chronologically with `next_before` and `limit`, excluding failed messages while retaining failed conversation previews for unreachable donors.
- **Reason:** Task 2.7 must stop outreach immediately without implementing Task 2.8 classification. Shared enrollment locks serialize replies against dispatch. UUID tie-breaking prevents missing or repeated messages when demo-clock timestamps match, and outbound-only receipts avoid treating incoming replies as simulated TIHBC deliveries.
- **Consequences:** The API specification now documents the previously unspecified pagination and donor-preview fields. Frontend generated-client regeneration and compatibility-bridge removal remain a frontend handoff (KI-005); live database acceptance is pending (KI-011).

## D-047 — Deterministic reply context in simulator messages

- **Date:** 2026-10-05
- **Status:** Accepted
- **Supersedes:** D-046 reply-classification behavior only; its cursor and receipt rules remain accepted.
- **Decision:** Route simulator replies through `services/reply_service.py`. Infer the pending deterministic context from the latest outbound message's internal button definitions: `slot_<uuid>` identifies offered appointment rows and the documented reason IDs identify decline-reason capture. Store free-text fallback classifications with the existing `agent` response source because the database contract intentionally exposes only `button` and `agent`; Task 2.9 can replace the classifier without changing persistence. Keep exact automatic reply text in language-specific modules under `services/replies/` and publish typing followed by both committed messages, enrollment, follow-up, and metrics events.
- **Reason:** Persisting conversation state in a second table is unnecessary for the bounded slot/reason flows because the sent message already records the offered choices. Stable internal IDs keep selection capacity-safe, preserve the documented public button shape, and leave the Task 2.9 agent as a drop-in classification replacement.
- **Consequences:** Button IDs are part of deterministic reply context and must remain stable after send. Repeated final-status intents add a system note to the open follow-up; changed intents use the enrollment reply state machine. D-046's temporary no-classification behavior no longer applies.

## D-109 — Generated simulator contract with exclusive refresh modes

- **Date:** 2026-10-05
- **Status:** Accepted
- **Supersedes:** D-103's default-source and temporary compatibility choices; its source-agnostic boundary remains.
- **Decision:** Default the simulator to `api`, alias its REST types directly from generated OpenAPI, and keep the offline `mock` source. Aggregate paginated conversation rows for the donor picker and derive campaign options from real rows. Use TanStack infinite message pages with exclusive `next_before` cursors and chronological presentation. While the phone is open, poll API messages every three seconds and conversations every ten seconds only when realtime is off; realtime uses the existing shared tab connection and event router without polling. Reconcile optimistic donor bubbles with server messages and never fabricate automatic replies in API mode.
- **Reason:** The backend simulator contract is now available, and the user explicitly requested live API mode with an offline fallback. Exclusive refresh modes avoid duplicate transport activity, while generated types catch nullable fields and pagination drift.
- **Consequences:** Restart the frontend after changing public source/realtime environment values. Closed phones and mock mode do not poll. KI-005 is resolved; browser/PostgreSQL/Redis acceptance remains tracked separately under KI-006/KI-010/KI-011.
