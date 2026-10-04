# Known Issues

## KI-002 — TestClient dependency deprecation warning

- **Status:** Open
- **Affects:** Backend test output
- **Details:** FastAPI's current `TestClient` import emits a Starlette warning that its HTTPX-based implementation is deprecated in favor of `httpx2`. The required test stack still passes; dependency substitution is outside task 1.1 and requires review before changing the approved stack.

## KI-005 — Simulator routes absent from generated frontend contract

- **Status:** Open
- **Affects:** Frontend API-backed simulator source only; mock mode is complete
- **Details:** Backend Task 2.7 has not yet exported the documented `/simulator` routes into `frontend/openapi.json`. The API adapter therefore uses a narrow compatibility type bridge around the authenticated generated client. After Task 2.7, regenerate the client, remove the bridge, and verify the final cursor-pagination response directly against the generated types.
