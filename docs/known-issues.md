# Known Issues

## KI-002 — TestClient dependency deprecation warning

- **Status:** Open
- **Affects:** Backend test output
- **Details:** FastAPI's current `TestClient` import emits a Starlette warning that its HTTPX-based implementation is deprecated in favor of `httpx2`. The required test stack still passes; dependency substitution is outside task 1.1 and requires review before changing the approved stack.

## KI-005 — Simulator routes absent from generated frontend contract

- **Status:** Open
- **Affects:** Frontend API-backed simulator source only; mock mode is complete
- **Details:** Backend Task 2.7 has not yet exported the documented `/simulator` routes into `frontend/openapi.json`. The API adapter therefore uses a narrow compatibility type bridge around the authenticated generated client. After Task 2.7, regenerate the client, remove the bridge, and verify the final cursor-pagination response directly against the generated types.

## KI-006 — Frontend realtime connection intentionally disabled

- **Status:** Open
- **Affects:** Live cache updates from server WebSocket events
- **Details:** `NEXT_PUBLIC_REALTIME` defaults to `off` until backend Task 2.6 provides the authenticated `/ws` endpoint. The shared client, reconnect policy, event router, and API-simulator handoff are complete and tested. Enable it with `NEXT_PUBLIC_REALTIME=on` after Task 2.6 and close this issue after live verification.

## KI-007 — Task 2.5 acceptance verification pending

- **Status:** Open
- **Affects:** Scheduler dispatch, escalation, campaign completion, and demo-clock acceptance
- **Details:** Task 2.5 PostgreSQL suite (234 tests) and manual scheduler lifecycle have not yet been verified by the user. Codex verification passed Ruff, format, strict mypy, and 204 non-PostgreSQL tests with only KI-002.

## KI-008 — Follow-up and metrics frontend contracts pending generation

- **Status:** Open
- **Affects:** Frontend Tasks 3.9, 3.10, and 3.11
- **Details:** Backend Tasks 2.10/2.11 are not implemented, so the documented follow-up, metrics, and reports shapes temporarily live in `frontend/lib/api/pending-contracts.ts`. These pages show “Available after backend update” for HTTP 404. Regenerate OpenAPI and remove the pending contract boundary when those backend APIs land.

## KI-009 — Settings frontend contract pending generation

- **Status:** Open
- **Affects:** Frontend Task 3.12 integration status and demo-data reset
- **Details:** Backend Task 2.12 has not exported `/settings/integration` or `/demo/actions/reset-data`, so their documented shapes temporarily share `frontend/lib/api/pending-contracts.ts`. The Settings page shows “Available after backend update” when the integration endpoint returns HTTP 404. Regenerate OpenAPI, replace the compatibility calls, and verify reset behavior when Task 2.12 lands.

## KI-010 — Task 2.6 live transport acceptance pending

- **Status:** Open
- **Affects:** Redis worker-to-browser fan-out and authenticated WebSocket acceptance
- **Details:** The real Redis integration test, PostgreSQL suite, and manual `ws_listen` plus clock-advance check are deferred for combined user verification with Task 2.5. Local auth, broadcast, failure isolation, payload filtering, expiry, and metrics debounce tests pass. Run `uv run pytest --run-postgres --run-redis`; Redis tests use unique channels and never flush Redis. KI-006 remains open until browser realtime is enabled and verified.
