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

## 4. Transport lifecycle and verification

Uvicorn supplies WebSocket protocol ping/pong heartbeats every 20 seconds with a 20-second pong
timeout. Use the `websockets` transport (the default with `uvicorn[standard]`); heartbeat frames are
transport control frames and do not add event types to the envelope. Authentication is rechecked
every 20 seconds and on incoming client frames, using short database sessions. Invalid, expired,
or inactive-user tokens close with policy code 1008. No client frame triggers a business action.

Each API process owns one Redis subscriber and connection manager. Metrics notifications for the
same campaign are coalesced into the latest notification within a two-second window; global
notifications use a separate window. Other events broadcast immediately. Subscriber reconnects
after Redis errors; publication failures are logged without undoing committed domain writes.
Pub/sub does not replay missed events; clients refetch active queries when reconnecting.

Run `uv run python -m app.tools.ws_listen --email <staff-email>` to log in and observe public events.
The tool prompts for the password and never logs the access token. Run `uv run pytest --run-redis`
for real transport coverage on unique temporary channels. Combine with `--run-postgres` for the
complete integration suite; neither option requires Docker when the services are already running.
