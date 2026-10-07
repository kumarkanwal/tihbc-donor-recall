Extract the donor's exact date or offered-slot expression from the supplied context. Do not resolve it
to a calendar date and never return a slot UUID. Copy only the shortest meaningful expression, or return
the string `none` when unclear. Ignore an expression the donor rejects and extract the affirmative
alternative.

Examples:
- English: `Can I come next week?` -> expression `next week`
- Roman Urdu: `Kal nahi, Monday ko aa sakta hoon` -> expression `Monday`
- Roman Urdu: `Parson aa sakta hoon` -> expression `Parson`
- Urdu: `اگلے ہفتے آ سکتا ہوں` -> expression `اگلے ہفتے`
- Awaiting slot: `2nd wala` -> expression `2nd wala`

Context JSON:
{context}
