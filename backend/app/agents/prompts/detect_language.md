You classify a donor's short reply as English (`en`) or Roman Urdu (`roman_ur`).
Return only the bound structured output. Urdu script is handled before this prompt.

Examples:
- `Yes I will come` -> `en`
- `Ji main aaunga` -> `roman_ur`
- `Kal nahi, Monday ko aa sakta hoon` -> `roman_ur`
- `Where is the center?` -> `en`
- `Tabiyat theek nahi` -> `roman_ur`

Reply JSON:
{reply}
