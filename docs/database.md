# Database Specification

PostgreSQL 16. All tables use UUID primary keys (`id`), and `created_at` / `updated_at` (timestamptz, UTC)
unless stated otherwise. All timestamps are UTC. Enums are PostgreSQL enums created via Alembic.
Every foreign key is indexed.

---

## 1. Enums

| Enum | Values |
|---|---|
| `user_role` | `admin`, `coordinator` |
| `language_code` | `en`, `ur` |
| `series_kind` | `primary`, `secondary` |
| `series_status` | `draft`, `active`, `archived` |
| `message_category` | `utility`, `marketing` |
| `media_type` | `none`, `image`, `video` |
| `campaign_status` | `draft`, `scheduled`, `running`, `paused`, `completed` |
| `enrollment_status` | `pending`, `in_primary`, `in_secondary`, `escalated`, `confirmed`, `reschedule_requested`, `rescheduled`, `declined`, `invalid_number`, `undeliverable` |
| `message_direction` | `outbound` (TIHBC → donor), `inbound` (donor → TIHBC) |
| `message_kind` | `template`, `text`, `interactive`, `button_reply` |
| `message_status` | `queued`, `sent`, `delivered`, `read`, `failed` |
| `response_intent` | `confirm`, `reschedule`, `decline`, `question`, `unknown` |
| `response_source` | `button`, `agent` |
| `decline_reason` | `travelling`, `health`, `recently_donated`, `not_interested`, `other` |
| `follow_up_type` | `confirmed`, `reschedule`, `declined`, `needs_call` |
| `follow_up_status` | `open`, `in_progress`, `done` |
| `follow_up_priority` | `normal`, `high` |
| `follow_up_outcome` | `attended`, `rebooked`, `not_reachable`, `declined`, `other` |

---

## 2. Tables

### 2.1 `users`
| Column | Type | Notes |
|---|---|---|
| email | varchar(255) | unique, lowercase |
| full_name | varchar(120) | |
| password_hash | varchar(255) | argon2 |
| role | user_role | |
| is_active | boolean | default true |

### 2.2 `segments`
| Column | Type | Notes |
|---|---|---|
| key | varchar(40) | unique, e.g. `regular`, `lapsed`, `first_time` |
| label | varchar(80) | display name |

### 2.3 `donor_batches`
| Column | Type | Notes |
|---|---|---|
| name | varchar(120) | |
| original_filename | varchar(255) | |
| uploaded_by_id | FK users | |
| total_rows | int | |
| valid_rows | int | |
| invalid_rows | int | |
| validation_report | jsonb | list of `{row, field, value, reason}` |

### 2.4 `donors`
| Column | Type | Notes |
|---|---|---|
| batch_id | FK donor_batches | on delete cascade |
| full_name | varchar(120) | |
| phone_e164 | varchar(16) | `+923XXXXXXXXX` |
| segment_id | FK segments | |
| language | language_code | |
| city | varchar(80) | nullable |
| blood_group | varchar(3) | nullable; `A+ A- B+ B- AB+ AB- O+ O-` |
| last_donation_date | date | nullable |
| sim_reachable | boolean | default true; simulator only. false → messages fail (inactive number) |
| sim_read_receipts | boolean | default true; simulator only. false → never reaches `read` |

Constraints: unique (`batch_id`, `phone_e164`). Index on `phone_e164`.

### 2.5 `tags` and `series_tags`
`tags`: `name` varchar(40) unique.
`series_tags`: `series_id` FK, `tag_id` FK, composite primary key. No timestamps.

### 2.6 `content_series`
| Column | Type | Notes |
|---|---|---|
| name | varchar(120) | |
| description | text | nullable |
| kind | series_kind | |
| status | series_status | default `draft` |
| languages | language_code[] | languages every step must have content for |
| response_window_hours | int | wait after the last step before escalating; default 48 |
| created_by_id | FK users | |

### 2.7 `series_steps`
| Column | Type | Notes |
|---|---|---|
| series_id | FK content_series | on delete cascade |
| step_order | int | 1-based |
| delay_days | int | days after previous step (step 1 relative to campaign start; usually 0) |
| category | message_category | |
| media_type | media_type | default `none` |
| media_url | varchar(500) | nullable |
| buttons | jsonb | up to 3: `{id, intent, labels: {en, ur}}`; intent is `confirm`/`reschedule`/`decline` |

Constraints: unique (`series_id`, `step_order`).

### 2.8 `series_step_contents`
| Column | Type | Notes |
|---|---|---|
| step_id | FK series_steps | on delete cascade |
| language | language_code | |
| body | text | max 1024 chars; supports variables `{{donor_name}}`, `{{center_name}}`, `{{appointment_date}}` |

Constraints: unique (`step_id`, `language`).

### 2.9 `appointment_slots`
| Column | Type | Notes |
|---|---|---|
| center_name | varchar(120) | |
| starts_at | timestamptz | |
| capacity | int | |
| booked_count | int | default 0; must never exceed capacity |

Index on `starts_at`.

### 2.10 `campaigns`
| Column | Type | Notes |
|---|---|---|
| name | varchar(120) | |
| batch_id | FK donor_batches | |
| primary_series_id | FK content_series | kind must be `primary` |
| secondary_series_id | FK content_series | kind must be `secondary` |
| status | campaign_status | default `draft` |
| start_at | timestamptz | |
| launched_at | timestamptz | nullable |
| completed_at | timestamptz | nullable |
| created_by_id | FK users | |

### 2.11 `enrollments`
| Column | Type | Notes |
|---|---|---|
| campaign_id | FK campaigns | |
| donor_id | FK donors | |
| status | enrollment_status | |
| current_series_kind | series_kind | nullable |
| current_step_order | int | nullable |
| next_action_at | timestamptz | nullable; next scheduled step or escalation check |
| responded_at | timestamptz | nullable |
| appointment_slot_id | FK appointment_slots | nullable |
| decline_reason | decline_reason | nullable |

Constraints: unique (`campaign_id`, `donor_id`). Indexes on `status`, `next_action_at`.

### 2.12 `messages`
| Column | Type | Notes |
|---|---|---|
| donor_id | FK donors | chat thread key |
| enrollment_id | FK enrollments | nullable |
| step_id | FK series_steps | nullable |
| direction | message_direction | |
| kind | message_kind | |
| body | text | rendered text (variables already filled) |
| media_type | media_type | |
| media_url | varchar(500) | nullable |
| buttons | jsonb | nullable; buttons shown with this message |
| reply_to_message_id | FK messages | nullable |
| button_id | varchar(40) | nullable; for `button_reply` |
| status | message_status | |
| scheduled_at | timestamptz | |
| sent_at / delivered_at / read_at | timestamptz | nullable |
| failed_reason | varchar(120) | nullable |
| provider_message_id | varchar(120) | nullable |

Indexes: (`donor_id`, `created_at`), (`status`, `scheduled_at`).

### 2.13 `donor_responses`
| Column | Type | Notes |
|---|---|---|
| enrollment_id | FK enrollments | |
| message_id | FK messages | the inbound message |
| intent | response_intent | |
| source | response_source | |
| detected_language | varchar(8) | `en`, `ur`, `roman_ur` |
| requested_date | date | nullable |
| decline_reason | decline_reason | nullable |
| confidence | numeric(3,2) | 1.00 for button replies |
| trace_id | varchar(120) | nullable; LangSmith run id |

### 2.14 `follow_up_items`
| Column | Type | Notes |
|---|---|---|
| enrollment_id | FK enrollments | |
| type | follow_up_type | |
| status | follow_up_status | default `open` |
| priority | follow_up_priority | `high` for `needs_call` |
| assigned_to_id | FK users | nullable |
| outcome | follow_up_outcome | nullable; set on resolve |
| resolved_at | timestamptz | nullable |
| resolved_by_id | FK users | nullable |

Only one open item per enrollment: partial unique index on `enrollment_id` where `status <> 'done'`.

### 2.15 `follow_up_activities`
| Column | Type | Notes |
|---|---|---|
| follow_up_id | FK follow_up_items | |
| user_id | FK users | nullable for system entries |
| action | varchar(40) | `created`, `assigned`, `status_changed`, `note`, `resolved` |
| note | text | nullable |

### 2.16 `demo_clock`
Single-row table (`id` = 1). `offset_seconds` bigint default 0. Read by `core/clock.py`.
The singleton row is inserted by migration. Application startup loads its value into the process-local
clock cache so `clock.now()` performs no database I/O. Advancing or resetting the clock persists the
row transactionally before updating the cache.

---

## 3. Relations Summary

```
users ─┬─< donor_batches ─< donors ─< enrollments >─ campaigns
       ├─< content_series ─< series_steps ─< series_step_contents
       └─< follow_up_items (assigned)
campaigns >─ donor_batches, content_series (primary, secondary)
enrollments ─< messages, donor_responses, follow_up_items
follow_up_items ─< follow_up_activities
enrollments >─ appointment_slots
```

---

## 4. Rules

- Deleting is restricted (no cascade) for anything referenced by a running campaign.
- `booked_count` is incremented inside a transaction with a row lock on the slot.
- Metrics are computed by query from `messages`, `enrollments`, and `donor_responses`; no counter columns.
