# WebSocket Specification

Endpoint: `GET /ws?token=<access_token>`. One connection per browser tab. Server → client only
(clients use the REST API for actions). Events are fanned out across workers through Redis pub/sub
channel `tihbc:events`.

## 1. Envelope

```json
{ "type": "message.created", "payload": { }, "ts": "2026-10-03T10:00:00Z" }
```

Event types and payload models are defined once in `backend/app/ws/events.py` and mirrored in
`frontend/lib/ws/events.ts`. Payloads reuse the REST schemas from `docs/api.md` where noted.

## 2. Events

| Type | Payload | Emitted when | Frontend reaction |
|---|---|---|---|
| `message.created` | `Message` | Outbound message sent or inbound reply saved | Append to simulator chat; bump conversation list |
| `message.status_updated` | `{id, donor_id, status, delivered_at, read_at, failed_reason}` | Status changes | Update ticks in simulator |
| `simulator.typing` | `{donor_id, is_typing}` | System is preparing an automatic reply (show 1–2 s) | Show typing indicator |
| `enrollment.updated` | `{id, campaign_id, donor_id, status, current_series_kind, current_step_order}` | Any enrollment status change | Invalidate campaign detail and enrollments |
| `followup.created` | `FollowUpItem` (list shape) | New follow-up | Insert into inbox, update tab counts, show toast |
| `followup.updated` | `FollowUpItem` (list shape) | Status, assignment, or resolve | Update row and counts |
| `campaign.updated` | `{id, status, counts}` | Launch, pause, resume, complete, or counts change | Update campaign views |
| `metrics.updated` | `{campaign_id \| null}` | After any message, response, or status change (debounced 2 s) | Invalidate metrics queries |
| `clock.updated` | `{now, offset_seconds}` | Demo clock advanced or reset | Update clock in top bar |

## 3. Rules

- Events are emitted by services after the DB transaction commits, never before.
- Payloads never contain unmasked data beyond what the REST API already returns to that role.
- The frontend reconnects with exponential backoff (1 s → 30 s max) and refetches active queries after reconnect.
- Unknown event types are ignored by the client and logged at debug level.
