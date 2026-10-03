# Brand and Design Tokens

> **Status: provisional.** Final TIHBC logo files and brand colors will replace the values marked
> `TBC`. Until then, use the provisional values below exactly, through tokens only, so they can be
> swapped in one place.

## 1. Identity
- Full name: **Team Indus Health & Blood Center**
- Short name: **TIHBC**
- Product name in UI: **Donor Recall**
- Logo files: `frontend/public/brand/logo.svg` (full), `logo-mark.svg` (icon only), `logo-white.svg`.
  Never stretch, recolor, or add effects. Minimum clear space equal to the mark's height on all sides.

## 2. Color Tokens

Defined once as CSS variables in `frontend/styles/tokens.css` and mapped into the Tailwind theme.
Components use token names (`bg-primary`, `text-muted-foreground`), never raw hex values.

| Token | Provisional value | Use |
|---|---|---|
| `--primary` | `#B4232A` (TBC) | Primary buttons, active nav, key highlights |
| `--primary-foreground` | `#FFFFFF` | Text on primary |
| `--primary-soft` | `#FBEAEA` (TBC) | Selected rows, subtle highlights |
| `--background` | `#F7F8FA` | App background |
| `--surface` | `#FFFFFF` | Cards, tables, panels |
| `--border` | `#E4E7EC` | Borders and dividers |
| `--foreground` | `#101828` | Main text |
| `--muted-foreground` | `#667085` | Secondary text |
| `--success` | `#12805C` | Confirmed, delivered |
| `--warning` | `#B54708` | Pending, reschedule |
| `--danger` | `#C01048` | Errors, failed, declined |
| `--info` | `#175CD3` | Informational, in progress |

`--danger` must stay visually distinct from `--primary`.

## 3. Status Color Map (used by `StatusBadge` only)

| Status group | Token |
|---|---|
| `confirmed`, `rescheduled`, `delivered`, `read`, `done`, `completed` | success |
| `pending`, `reschedule_requested`, `scheduled`, `queued`, `open` | warning |
| `in_primary`, `in_secondary`, `running`, `sent`, `in_progress` | info |
| `declined`, `failed`, `invalid_number`, `undeliverable` | danger |
| `escalated`, `needs_call` | primary |
| `draft`, `paused`, `archived` | muted (border + muted text) |

Badges: light tinted background, darker text, no icons inside.

## 4. Typography
- UI font: **Inter** (fallback: system sans-serif).
- Urdu font: **Noto Nastaliq Urdu** (fallback: **Noto Naskh Arabic**), applied to elements with `lang="ur"`,
  line-height 1.9.
- Scale: page title 24 px semibold; section title 18 px semibold; body 14 px; small/meta 12 px.
- Numbers in KPI cards: 28 px semibold, tabular numerals.

## 5. Layout and Components
- Spacing scale: 4 px base (4, 8, 12, 16, 24, 32).
- Radius: 8 px cards and inputs, 6 px buttons and badges.
- Shadows: one subtle elevation for cards and dropdowns only. No glows.
- Sidebar width 240 px (collapsed 64 px). Content max width 1440 px.
- Buttons: one primary per screen area; secondary as outline; destructive uses `--danger`.
- Icons: lucide-react, 16–20 px, stroke 1.75, with a text label for every action.
- Charts: use `--primary`, `--info`, `--success`, `--warning`, `--muted-foreground` in that order.

## 6. Not Allowed
Emojis, gradients, glow effects, sparkle or "magic" AI icons, decorative illustrations, more than one
accent color per component, raw hex values in components.
