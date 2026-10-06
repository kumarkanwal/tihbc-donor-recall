Map a donor's decline reason to one of `travelling`, `health`, `recently_donated`, `not_interested`,
or `other`. Return only the bound structured output.

Examples:
- English: `I am travelling` -> travelling
- Urdu: `میں شہر سے باہر ہوں` -> travelling
- Roman Urdu: `Tabiyat theek nahi` -> health
- Roman Urdu: `Abhi 1 mahina pehle diya tha` -> recently_donated
- English: `Not interested` -> not_interested
- Urdu: `کوئی اور وجہ` -> other

Reply JSON:
{reply}
