Classify a blood donor's reply as `confirm`, `reschedule`, `decline`, `question`, or `unknown`.
Respect the `awaiting` context first. A slot number/date while awaiting a slot is `reschedule`.
Return only the bound structured output with a calibrated confidence from 0 to 1.

Examples:
- English: `Yes I will come` -> confirm, 0.98
- Urdu: `میں آؤں گا` -> confirm, 0.98
- Roman Urdu: `Kal nahi, Monday ko aa sakta hoon` -> reschedule, 0.98
- English: `Where is the center?` -> question, 0.98
- Roman Urdu: `Main shehar se bahar hoon` -> decline, 0.96
- Urdu: `طبیعت ٹھیک نہیں` -> decline, 0.96
- English: `asdfgh` -> unknown, 0.1
- Awaiting slot: `2nd wala` -> reschedule, 0.99

Context JSON:
{context}
