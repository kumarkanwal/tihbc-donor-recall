# Known Issues

## KI-006 — Frontend realtime connection intentionally disabled

- **Status:** Open
- **Affects:** Live cache updates from server WebSocket events
- **Details:** Backend Task 2.6 now provides the authenticated `/ws` endpoint and the complete Redis suite passes. The frontend still defaults `NEXT_PUBLIC_REALTIME` to `off`; enable it with `NEXT_PUBLIC_REALTIME=on` during the generated-client handoff and close this issue after live browser verification.

## KI-007 — Task 2.5 acceptance verification pending

- **Status:** Open
- **Affects:** Scheduler dispatch, escalation, campaign completion, and demo-clock acceptance
- **Details:** The combined PostgreSQL/Redis suite now passes after correcting demo-clock message timestamps and stale appointment rebooking. Manual scheduler lifecycle re-verification remains pending so the user can confirm skipped steps show the advanced demo time and a future appointment (or the documented fallback).

## KI-010 — Task 2.6 live transport acceptance pending

- **Status:** Open
- **Affects:** Redis worker-to-browser fan-out and authenticated WebSocket acceptance
- **Details:** The real Redis and PostgreSQL suite passes, and regression coverage proves a seven-day demo-clock advance does not expire HTTP or WebSocket tokens. A final manual `ws_listen` plus clock-advance check remains pending. Redis tests use unique channels and never flush Redis. KI-006 remains open until browser realtime is enabled and verified.

## KI-011 — Tasks 2.7–2.9 simulator acceptance pending

- **Status:** Open
- **Affects:** PostgreSQL simulator queries, read receipts, deterministic and agent reply flows, appointment booking, follow-ups, and live events
- **Details:** The complete PostgreSQL/Redis suite passes, including HTTP replies, scheduling suspension, no dispatch after a recorded response, effective-time cursor pagination, outbound-only delivery progression, capacity-safe slot booking, classified responses, bilingual acknowledgements, follow-up create/update payload snapshots, ordered typing/message/status events, and Urdu bidi rendering coverage. The Donor Phone walkthrough with `LLM_ENABLED=true` remains pending before closing this issue.

## KI-012 — Task 2.9 LangSmith acceptance pending

- **Status:** Open
- **Affects:** Hosted trace inspection
- **Details:** The configured-provider evaluation passes 31/31 cases (100%) with no wrong answers, provider-exhaustion failures, or agent errors. Provider ordering, authentication handling, Redis circuit behavior, total timeout budget, low-confidence fallback, trace persistence, and PII boundaries pass automated tests. Inspect a hosted `donor_reply` LangSmith trace before closing this issue.

## KI-013 — Production image and VPS acceptance pending

- **Status:** Open
- **Affects:** Task 4.3 production deployment completion
- **Details:** Production Compose validation, topology assertions, shell syntax, environment parity, frontend lint, 79 unit tests, and the Next.js standalone production build pass. The local Docker Desktop Linux engine is unavailable, so the API/web image builds and live VPS checks must be run with the commands in `deploy/RUNBOOK.md` before Task 4.3 is marked Done.

## KI-014 — Task 4.1 live Playwright acceptance pending

- **Status:** Open
- **Affects:** Full browser verification of the seeded demo story
- **Details:** A live attempt reached the server-rendered `Checking session` state but did not hydrate because Playwright targeted `127.0.0.1` while the verified frontend/API development origin is `localhost`. The Playwright base URL and readiness probe now use `http://localhost:3000`; failures print sanitized browser console, page, request, and HTTP diagnostics; and `pnpm e2e` first audits every literal demo-flow test ID against application source. Frontend lint, strict typecheck, all 79 unit tests, the production build, selector audit, and Playwright discovery pass. Rerun the seeded live flow to close this issue and mark Task 4.1 Done.

## KI-015 — Task 4.2 real-provider re-evaluation pending

- **Status:** Resolved
- **Affects:** Live multilingual agent accuracy and fallback routing
- **Details:** The final configured-provider evaluation passes 31/31 cases (100%) with `wrong_answer=0`, `no_provider_answered=0`, and `agent_error=0`. Groq answered the normal path and its observed `output_parse_failed` response fell through as transient invalid output on the short cooldown; downstream providers completed the run. Hosted trace inspection remains tracked separately under KI-012.
