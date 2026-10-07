Extract rescheduling details relative to `today` from the supplied context.
Return a requested calendar date, a selected offered-slot UUID, or both as null when unclear.
Never invent a slot UUID. `kal` means tomorrow. `next week` means today plus 7 days. Resolve weekday
phrases to the next occurrence after today unless the reply clearly says otherwise.
Ignore a date phrase when the donor explicitly rejects it, and extract the affirmative alternative.

Examples:
- English: today 2026-10-05, `next week` -> requested_date 2026-10-12
- Roman Urdu: today 2026-10-05, `kal` -> requested_date 2026-10-06
- Roman Urdu: today 2026-10-05, `Kal nahi, Monday ko aa sakta hoon` -> requested_date 2026-10-12
- Roman Urdu: today 2026-10-05, `agley haftay` -> requested_date 2026-10-12
- Urdu: today 2026-10-05, `اگلے پیر` -> requested_date 2026-10-12
- Urdu: today 2026-10-05, `اگلے ہفتے` -> requested_date 2026-10-12
- Awaiting slot with three offers: `2nd wala` -> the second offered slot UUID

Context JSON:
{context}
