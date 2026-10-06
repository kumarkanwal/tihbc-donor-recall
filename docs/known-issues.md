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
- **Details:** The complete PostgreSQL/Redis suite passes, including HTTP replies, scheduling suspension, outbound-only delivery progression, stable cursor pagination, capacity-safe slot booking, classified responses, bilingual acknowledgements, follow-up create/update payload snapshots, and ordered typing/message/status events. The Donor Phone walkthrough with `LLM_ENABLED=true` remains pending before closing this issue.

## KI-012 — Task 2.9 real-provider and LangSmith acceptance pending

- **Status:** Open
- **Affects:** Live multilingual LLM accuracy, provider fallback latency, and hosted trace inspection
- **Details:** All documented agent examples, provider ordering, authentication handling, Redis circuit behavior, total timeout budget, low-confidence fallback, trace persistence, and PII boundaries pass with mocked LLMs. Real provider keys and LangSmith credentials are not available in this session; run `python -m app.agents.evaluate` with the configured environment and inspect a `donor_reply` trace before closing this issue.
