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
1. `detect_language` → `en`, `ur` (Urdu script), or `roman_ur`. Rule-based first (Urdu Unicode range
   and deterministic reschedule phrases), LLM only to separate English from Roman Urdu when unclear.
2. `classify_intent` → `confirm`, `reschedule`, `decline`, `question`, `unknown` with confidence.
   Before an LLM call, known relative dates and weekdays classify as reschedules, offered-slot ordinals
   and weekday names resolve against the supplied slots, and deliberately ambiguous replies remain unknown.
3. `extract_details` (conditional):
   - reschedule → the LLM can extract only the original date/slot expression. Application code resolves
     weekday names, today/tomorrow/day-after-tomorrow, next-week phrases, and their Urdu/Roman Urdu
     equivalents against demo-clock `today`; slot choices resolve only against `offered_slots`.
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

### 3.4 LLM Usage and Provider Routing
- Every LLM call uses a closed, all-fields-required structured output bound to a Pydantic model. Optional
  wire values use explicit sentinel enum/string values instead of nullable unions; application code maps
  sentinels back to domain `None`. No regex parsing of LLM text.
- Temperature 0 where the provider model supports explicit sampling controls; fixed-sampling Gemini models
  use their native default. Prompts are files in `agents/prompts/`: `classify_intent.md`, `extract_date.md`,
  `extract_decline_reason.md`, `detect_language.md`, with few-shot examples in English, Urdu, and Roman Urdu.

**Routing (`agents/llm/`)**
- `providers.py`: one registry entry per provider (name, base URL, key setting, client type, and a
  **default free model** that supports structured output). `<PROVIDER>_MODEL` in env overrides the default.
  Only the API key is required to enable a provider. Gemini defaults to the stable
  `gemini-3.5-flash-lite` model.
- Startup check: list each enabled provider's models; if the configured model is missing, log a warning
  containing the configured model and returned catalog, then skip that provider (never crash).
  Groq, Cerebras, Together, and OpenRouter use the OpenAI-compatible chat client with their base URL;
  Gemini and Mistral use their LangChain integrations. Adding a provider means adding one registry entry.
- `router.py`: builds the chain in `LLM_PROVIDER_ORDER`, skipping providers without a key. Implemented with
  LangChain `with_fallbacks`, plus:
  - per-provider timeout (`LLM_TIMEOUT_SECONDS`) and total budget (`LLM_TOTAL_BUDGET_SECONDS`);
  - fall back to the next provider for every provider-local failure, including timeout, invalid structured
    output, connection errors, 4xx responses, rate limits (429), and server errors (5xx);
  - open the failing provider's shared circuit immediately for 400/401/402/403 responses. Groq
    `output_parse_failed` responses are transient invalid output and use the normal cooldown; true 400
    schema/request errors and 401/402/403 responses use ten times the normal cooldown;
  - log sanitized error details for all provider failures without credentials or full phone numbers. Groq
    GPT-OSS models use strict JSON Schema mode with compatible closed schemas;
  - use Gemini native JSON Schema structured output, explicitly disable SDK automatic function calling,
    and advertise the SDK's 10-second minimum request deadline while retaining the router's shorter outer timeout;
  - circuit breaker in Redis: after `LLM_CIRCUIT_FAILURES` consecutive failures a provider is skipped for
    `LLM_CIRCUIT_COOLDOWN_SECONDS` (shared across workers).
- Nodes call only `get_structured_llm(schema)` from the router; they never know which provider answered.
- Each result records the provider and model used (saved in LangSmith metadata and logs).
- Startup logs which providers are active (names only, never keys).
- `RoutingUnavailable` is raised only after every available provider is exhausted or the total routing
  budget is spent.

### 3.5 Fallback
- If confidence < `AGENT_CONFIDENCE_THRESHOLD` (default 0.7), or **all** providers fail or the total
  budget runs out → return intent `unknown`. The flow in 2.4 applies. The demo never breaks because of the LLM.
- If `LLM_ENABLED=false`, a keyword classifier is used (`agents/fallback.py`) with a small keyword list
  per intent in English and Roman Urdu.

### 3.6 Real-provider evaluation
- `uv run python -m app.agents.evaluate` runs all evaluation cases with a 1500 ms delay between cases.
- `--delay-ms N` changes the inter-case delay; `--provider NAME` restricts the run to one configured
  provider.
- Each case prints expected and actual intent/date/reason/slot values plus every provider attempt and its
  status. The summary separates wrong answers, provider exhaustion, and unexpected agent errors.

## 4. Observability (LangSmith)
- Tracing enabled via env. Run name: `donor_reply`.
- Metadata on every run: `campaign_id`, `enrollment_id`, `donor_language`, `awaiting`, `environment`,
  `llm_provider`, `llm_model`, `fallback_count`.
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
