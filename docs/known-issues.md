# Known Issues

## KI-002 — TestClient dependency deprecation warning

- **Status:** Open
- **Affects:** Backend test output
- **Details:** FastAPI's current `TestClient` import emits a Starlette warning that its HTTPX-based implementation is deprecated in favor of `httpx2`. The required test stack still passes; dependency substitution is outside task 1.1 and requires review before changing the approved stack.
