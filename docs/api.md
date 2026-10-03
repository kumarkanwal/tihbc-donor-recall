# API Specification

Base path: `/api/v1`. JSON only (except file uploads). Auth: `Authorization: Bearer <access_token>`.
Timestamps are ISO 8601 UTC. IDs are UUIDs. Field names are `snake_case`.

Roles: **A** = admin only, **C** = admin and coordinator, **P** = public.

---

## 1. Shared Conventions

**Paginated list response**
```json
{ "items": [], "total": 0, "page": 1, "page_size": 20 }
```
Query params for lists: `page`, `page_size` (max 100), `search`, `sort` (e.g. `-created_at`).

**Error response**
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Human readable", "details": {} } }
```

| Code | HTTP |
|---|---|
| `VALIDATION_ERROR` | 422 |
| `UNAUTHORIZED` | 401 |
| `FORBIDDEN` | 403 |
| `NOT_FOUND` | 404 |
| `CONFLICT` | 409 |
| `INVALID_STATE_TRANSITION` | 409 |
| `UPLOAD_INVALID` | 400 |
| `PREVIEW_EXPIRED` | 410 |
| `SLOT_FULL` | 409 |
| `INTERNAL_ERROR` | 500 |

---

## 2. Auth

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/auth/login` | P | Body `{email, password}` → `{access_token, token_type, user}` |
| GET | `/auth/me` | C | Current `User` |

`User`: `{id, email, full_name, role, is_active}`

## 3. Users and Lookups

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/users` | C | List active users (for assignment). Filter `role` |
| GET | `/segments` | C | `[{id, key, label}]` |
| GET | `/tags` | C | `[{id, name}]` |
| GET | `/appointment-slots` | C | Query `from`, `to`, `center_name`. Returns slots with `available` count |

## 4. Donor Batches

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/donor-batches/sample-file` | A | Download sample CSV with correct columns |
| POST | `/donor-batches/preview` | A | Multipart `file` (CSV/XLSX). Validates, returns `BatchPreview`. Nothing saved to DB |
| POST | `/donor-batches` | A | Body `{name, preview_token}` → imports valid rows, returns `DonorBatch` |
| GET | `/donor-batches` | C | Paginated `DonorBatch` list |
| GET | `/donor-batches/{id}` | C | `DonorBatchDetail` (includes segment and language breakdown) |
| GET | `/donor-batches/{id}/donors` | C | Paginated donors. Filters `segment`, `language`, `search` |
| GET | `/donor-batches/{id}/validation-report` | C | Invalid rows list |

`BatchPreview`
```json
{
  "preview_token": "string",          // stored in Redis, expires in 30 min
  "original_filename": "donors.xlsx",
  "total_rows": 250, "valid_rows": 240, "invalid_rows": 10,
  "segment_breakdown": [{"segment": "regular", "count": 120}],
  "language_breakdown": [{"language": "ur", "count": 140}],
  "sample_valid_rows": [ /* first 10 normalized rows */ ],
  "errors": [{"row": 12, "field": "phone", "value": "0300-12", "reason": "Invalid Pakistani mobile number"}]
}
```
Validation rules: required columns present; phone normalized to `+923XXXXXXXXX`; segment matches a
`segments.key`; language in `en`/`ur` (also accept `English`/`Urdu`, case-insensitive); no duplicate phone
in file; optional blood group in allowed list; `last_donation_date` parseable and not in the future.

`DonorBatch`: `{id, name, original_filename, total_rows, valid_rows, invalid_rows, uploaded_by, created_at, campaign_count}`

## 5. Content Series

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/content-series` | C | Paginated. Filters `kind`, `status`, `tag`, `language` |
| POST | `/content-series` | A | Create `{name, description, kind, languages, response_window_hours, tag_names}` |
| GET | `/content-series/{id}` | C | `SeriesDetail` with steps and contents |
| PATCH | `/content-series/{id}` | A | Update fields. Blocked if used by a running campaign |
| POST | `/content-series/{id}/actions/activate` | A | Validates every step has content for every language |
| POST | `/content-series/{id}/actions/archive` | A | |
| POST | `/content-series/{id}/actions/duplicate` | A | Copies series and steps as new `draft` |
| POST | `/content-series/{id}/steps` | A | Create `SeriesStepInput` |
| PATCH | `/content-series/{id}/steps/{step_id}` | A | Update step |
| DELETE | `/content-series/{id}/steps/{step_id}` | A | Re-numbers remaining steps |
| POST | `/content-series/{id}/steps/actions/reorder` | A | Body `{step_ids: [...]}` in new order |
| POST | `/content-series/{id}/preview` | C | Body `{step_id, language, donor_id?}` → rendered message for the simulator preview |
| POST | `/media` | A | Multipart image/video upload (video MP4 ≤ 16 MB, image ≤ 5 MB) → `{url, media_type}` |

`SeriesStepInput`
```json
{
  "delay_days": 3, "category": "utility",
  "media_type": "video", "media_url": "https://...",
  "contents": [{"language": "en", "body": "..."}, {"language": "ur", "body": "..."}],
  "buttons": [{"id": "btn_confirm", "intent": "confirm", "labels": {"en": "Confirm", "ur": "تصدیق"}}]
}
```

## 6. Campaigns

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/campaigns` | C | Paginated. Filter `status` |
| POST | `/campaigns` | A | `{name, batch_id, primary_series_id, secondary_series_id, start_at}` → `draft` |
| GET | `/campaigns/{id}` | C | `CampaignDetail` with status counts per `enrollment_status` |
| PATCH | `/campaigns/{id}` | A | Draft only |
| POST | `/campaigns/{id}/actions/launch` | A | `draft` → `scheduled` (future start) or `running` |
| POST | `/campaigns/{id}/actions/pause` | A | `running` → `paused` |
| POST | `/campaigns/{id}/actions/resume` | A | `paused` → `running` |
| GET | `/campaigns/{id}/enrollments` | C | Paginated. Filters `status`, `search` |
| GET | `/enrollments/{id}` | C | Enrollment with donor, timeline of messages and responses, follow-up |

Launch validation: both series `active`, series languages cover all donor languages in the batch,
batch has at least one valid donor.

## 7. Simulator

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/simulator/conversations` | C | Donors with messages. Filters `campaign_id`, `search`. Each item: `{donor, last_message, unread_count}` |
| GET | `/simulator/conversations/{donor_id}/messages` | C | Chronological messages (cursor pagination: `before`, `limit`) |
| POST | `/simulator/conversations/{donor_id}/actions/open` | C | Marks delivered outbound messages as `read` (if donor has read receipts on) |
| POST | `/simulator/conversations/{donor_id}/replies` | C | Donor reply: `{type: "button", button_id, reply_to_message_id}` or `{type: "text", text}` → created inbound `Message` |

`Message`
```json
{
  "id": "uuid", "donor_id": "uuid", "direction": "outbound", "kind": "template",
  "body": "string", "media_type": "video", "media_url": "string|null",
  "buttons": [{"id": "btn_confirm", "label": "Confirm"}],
  "button_id": null, "reply_to_message_id": null,
  "status": "delivered", "created_at": "...", "sent_at": "...", "delivered_at": "...", "read_at": null
}
```
Buttons are returned already localized to the donor's language. Buttons on a message become disabled
in the UI once the donor has replied to that message.

## 8. Follow-up Inbox

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/follow-ups` | C | Paginated. Filters `type`, `status`, `priority`, `campaign_id`, `assigned_to` (`me` allowed), `search` |
| GET | `/follow-ups/summary` | C | Counts by `type` and `status` (for tabs) |
| GET | `/follow-ups/{id}` | C | Detail: donor, enrollment, latest response, activities |
| PATCH | `/follow-ups/{id}` | C | `{status?, assigned_to_id?, priority?}` |
| POST | `/follow-ups/{id}/notes` | C | `{note}` |
| POST | `/follow-ups/{id}/actions/resolve` | C | `{outcome, note?}` → status `done` |
| GET | `/follow-ups/export` | C | CSV with current filters |

## 9. Metrics and Reports

All accept `campaign_id` (optional), `from`, `to`.

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/metrics/overview` | C | `{donors, sent, delivered, read, responded, delivery_rate, read_rate, response_rate, confirmed, rescheduled, declined, escalated, invalid_numbers, undeliverable}` |
| GET | `/metrics/timeseries` | C | Daily `{date, sent, delivered, read, responded}` |
| GET | `/metrics/response-breakdown` | C | Counts per intent, per segment, per language |
| GET | `/metrics/decline-reasons` | C | Counts per `decline_reason` |
| GET | `/metrics/campaigns` | C | Per-campaign comparison rows |
| GET | `/reports/inactive-numbers` | C | Paginated invalid (upload) and undeliverable (sending) numbers with reason |
| GET | `/reports/{report}/export` | C | CSV for `inactive-numbers`, `response-breakdown`, `campaigns` |

## 10. Settings and Demo

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/settings/integration` | C | Mocked: `{business_verified, phone_number, display_name, quality_rating, messaging_limit, templates: [{name, status, category}]}` |
| GET | `/demo/clock` | C | `{now, offset_seconds}` |
| POST | `/demo/clock/actions/advance` | A | `{days?, hours?}` → advances clock, runs dispatcher once, returns new clock |
| POST | `/demo/clock/actions/reset` | A | Offset to 0 |
| POST | `/demo/actions/reset-data` | A | Re-runs seed (only when `DEMO_MODE=true`) |

## 11. Health
`GET /health/live`, `GET /health/ready` (outside `/api/v1`, no auth).

## 12. WebSocket
`GET /ws?token=<access_token>`. Events are defined in `docs/websocket.md`.
