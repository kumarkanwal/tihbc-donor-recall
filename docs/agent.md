# Reply Handling and LangGraph Agent Specification

This document defines how donor replies are processed: the deterministic conversation flow (owned by
`services/reply_service.py`) and the LangGraph agent used only for free-text messages.

---

## 1. Reply Routing

```
Inbound message
 ├─ button reply → intent from button definition (no LLM)
 └─ free text    → LangGraph reply agent → AgentResult
                    ↓
          reply_service.apply(result)
           ├─ update enrollment status (state machine)
           ├─ cancel remaining scheduled steps for the enrollment
           ├─ create or update follow-up item
           ├─ send acknowledgement / next question to donor
           └─ emit WebSocket events (after commit)
```

Free text sent while the system is waiting for a specific answer (slot choice, decline reason) is
passed to the agent with that context in `awaiting`.

## 2. Conversation Flows (deterministic)

All bot messages are stored as templates in `backend/app/services/replies/` per language (`en`, `ur`).
The donor's stored language is used unless the agent detects a different language in their message.

### 2.1 Confirm
- Enrollment → `confirmed`. Follow-up `confirmed` (normal priority) so the field team can plan.
- Bot: thank-you message with center name and date if available.

### 2.2 Reschedule
1. Enrollment → `reschedule_requested`.
2. If a date was given (agent) → offer up to 3 available slots nearest to that date.
   Otherwise → ask "Which day suits you?" and offer the next 3 available slots as buttons.
3. Donor picks a slot (button or text like "the second one", "Saturday wala") → book the slot
   (row-locked), enrollment → `rescheduled`, bot confirms date, time, and center.
4. Follow-up `reschedule` (normal priority) for the field team to note the new date.
5. If no slots are available or the request is unclear twice → follow-up `needs_call` (high priority),
   bot: "Our coordinator will call you to find a suitable time."

### 2.3 Decline
1. Enrollment → `declined`.
2. If the reason is unknown → bot asks for a reason with buttons: "Travelling", "Health reason", "Other".
   One question only; no further reminders.
3. Store `decline_reason`. Follow-up `declined` (normal priority).
4. Bot: polite closing message.

### 2.4 Question or Unknown
- Enrollment status unchanged (scheduled steps stop).
- Follow-up `needs_call` (high priority).
- Bot: "Thank you. A coordinator from Team Indus will contact you shortly."

### 2.5 After Final Status
Messages from donors already `confirmed`, `rescheduled`, or `declined` are classified again; a changed
intent (e.g. confirmed → decline) is applied, otherwise the open follow-up gets a system note with the text.

## 3. LangGraph Agent

Location: `backend/app/agents/`. The agent never writes to the DB and never sends messages.

### 3.1 State (`state.py`)
```python
class ReplyState(TypedDict):
    text: str
    donor_language: Literal["en", "ur"]
    awaiting: Literal["none", "slot_choice", "decline_reason"]
    offered_slots: list[OfferedSlot]        # id, starts_at, center_name, label
    today: date                             # from demo clock
    detected_language: str | None
    intent: str | None
    confidence: float | None
    requested_date: date | None
    selected_slot_id: str | None
    decline_reason: str | None
```

### 3.2 Nodes (`nodes/`, one file each)
1. `detect_language` → `en`, `ur` (Urdu script), or `roman_ur`. Rule-based first (Urdu Unicode range),
   LLM only to separate English from Roman Urdu when unclear.
2. `classify_intent` → `confirm`, `reschedule`, `decline`, `question`, `unknown` with confidence.
   When `awaiting` is set, classify against that context first (e.g. a date or number → slot choice).
3. `extract_details` (conditional):
   - reschedule → `requested_date` resolved relative to `today` ("kal" = tomorrow, "next Friday",
     "15 tareekh") or `selected_slot_id` from `offered_slots`.
   - decline → `decline_reason` mapped to the enum.
4. `build_result` → returns `AgentResult`.

Edges: `detect_language` → `classify_intent` → (`extract_details` if intent is reschedule or decline)
→ `build_result`.

### 3.3 Output (`AgentResult`, Pydantic)
```python
class AgentResult(BaseModel):
    intent: ResponseIntent
    confidence: float          # 0.0–1.0
    detected_language: str
    requested_date: date | None
    selected_slot_id: UUID | None
    decline_reason: DeclineReason | None
    trace_id: str | None
```

### 3.4 LLM Usage
- Every LLM call uses structured output bound to a Pydantic model. No regex parsing of LLM text.
- Model, temperature (0), and timeout come from config (`docs/env.md`).
- Prompts are files in `agents/prompts/`: `classify_intent.md`, `extract_date.md`, `extract_decline_reason.md`,
  `detect_language.md`. Prompts include few-shot examples in English, Urdu, and Roman Urdu.

### 3.5 Fallback
- If confidence < `AGENT_CONFIDENCE_THRESHOLD` (default 0.7), the LLM errors, or it times out
  → return intent `unknown`. The flow in 2.4 applies. The demo never breaks because of the LLM.
- If `LLM_ENABLED=false`, a keyword classifier is used (`agents/fallback.py`) with a small keyword list
  per intent in English and Roman Urdu.

## 4. Observability (LangSmith)
- Tracing enabled via env. Run name: `donor_reply`.
- Metadata on every run: `campaign_id`, `enrollment_id`, `donor_language`, `awaiting`, `environment`.
- Tags: `intent:<value>`, `source:agent`, `fallback:true|false`.
- The run id is saved as `donor_responses.trace_id`.
- Phone numbers and names are never sent to the LLM or LangSmith; only the message text and context.

## 5. Test Examples (must pass with the LLM mocked and in an evaluation set with the real LLM)

| Text | awaiting | Expected |
|---|---|---|
| "Yes I will come" | none | confirm |
| "Ji main aaunga" | none | confirm |
| "میں آؤں گا" | none | confirm |
| "Kal nahi, Monday ko aa sakta hoon" | none | reschedule, date = next Monday |
| "Can we do next week?" | none | reschedule, date = today + 7 (start of next week) |
| "Main shehar se bahar hoon" | none | decline, travelling |
| "Tabiyat theek nahi" | none | decline, health |
| "Abhi 1 mahina pehle diya tha" | none | decline, recently_donated |
| "Where is the center?" | none | question |
| "2nd wala" | slot_choice | reschedule, second offered slot |
| "asdfgh" | none | unknown |
