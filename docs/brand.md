# Brand and Design Tokens

Colors are taken from the client logo (Indus Hospital & Health Network): **red** and **blue**.
The app supports **light mode (default)** and **dark mode**. All colors are defined as tokens; components
never use raw hex values.

## 1. Identity
- Client: **Team Indus Health & Blood Center (TIHBC)**, part of the Indus Hospital & Health Network brand.
- Product name in UI: **Donor Recall**
- Logo file: `frontend/public/images/IHHN-Logo-02-150x150.webp` (150 x 150 px, raster).
  - Use at 40 px (sidebar collapsed), 48 px (sidebar), 96 px (login). Do not display larger than 150 px.
  - Never stretch, recolor, crop, or add effects.
  - **Dark mode:** always place the logo on a white rounded tile (8 px radius, 6 px padding) so the blue
    text stays readable.
  - In the simulator, the logo is the TIHBC profile picture (circular crop of the full logo on white).

## 2. Brand Colors (from logo)

| Name | Hex | Notes |
|---|---|---|
| Indus Red | `#E8202A` | Logo red. Accent only: brand mark, active nav indicator, small highlights |
| Indus Blue | `#1F4799` | Logo blue. Primary color for buttons, links, selected states |

Blue is the primary action color because it meets contrast requirements for text on buttons and keeps
red free for emphasis. Red is never used for large fills.

## 3. Theme Tokens

Defined once in `frontend/styles/tokens.css` under `:root` (light) and `.dark` (dark), mapped into the
Tailwind theme (shadcn/ui variable convention). Theme switching via `next-themes` with `class` strategy.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--background` | `#F6F8FB` | `#0E1525` | App background |
| `--surface` | `#FFFFFF` | `#151E31` | Cards, tables, panels, sidebar |
| `--surface-muted` | `#F1F4F9` | `#1B2640` | Table headers, hover rows |
| `--border` | `#E3E8EF` | `#26324A` | Borders and dividers |
| `--foreground` | `#0F1B33` | `#E7ECF5` | Main text |
| `--muted-foreground` | `#5F6B80` | `#97A3B8` | Secondary text |
| `--primary` | `#1F4799` | `#4A79E0` | Primary buttons, links, focus ring |
| `--primary-foreground` | `#FFFFFF` | `#FFFFFF` | Text on primary |
| `--primary-soft` | `#E8EEFA` | `#1C2B4D` | Selected rows, active nav background |
| `--accent` | `#E8202A` | `#F0464D` | Brand accent (active nav bar, logo areas) |
| `--accent-soft` | `#FDECEC` | `#3A1A1E` | Subtle accent backgrounds |
| `--success` | `#127A52` | `#3CCB8B` | Confirmed, delivered |
| `--warning` | `#B25E09` | `#F2A541` | Pending, reschedule |
| `--danger` | `#B42318` | `#F97066` | Errors, failed, declined |
| `--info` | `#0B6BCB` | `#5EA8F5` | In progress, informational |
| `--ring` | `#1F4799` | `#4A79E0` | Focus outline |

Rules:
- `--danger` is used together with a text label or icon, never color alone, so it is not confused with
  the brand red.
- Every text/background pair must meet WCAG AA (4.5:1 for body text).

## 4. Status Color Map (used by `StatusBadge` only)

| Status group | Token |
|---|---|
| `confirmed`, `rescheduled`, `delivered`, `read`, `done`, `completed` | success |
| `pending`, `reschedule_requested`, `scheduled`, `queued`, `open` | warning |
| `in_primary`, `in_secondary`, `running`, `sent`, `in_progress` | info |
| `declined`, `failed`, `invalid_number`, `undeliverable` | danger |
| `escalated`, `needs_call` | accent |
| `draft`, `paused`, `archived` | muted (border + muted text) |

Badges: soft tinted background (token at ~12% opacity), full-color text, no icons inside.

## 5. Theme Switching
- Default: light. Options: Light, Dark, System. Control in the top bar (sun/moon icon with label in menu).
- Preference stored per browser (next-themes handles storage). No flash of wrong theme on load.
- Charts read colors from tokens so they adapt to the theme.
- The **WhatsApp simulator always uses its own light WhatsApp tokens** (`docs/simulator.md`) in both
  themes, because it represents a real phone screen.

## 6. Typography
- UI font: **Inter** (fallback: system sans-serif).
- Urdu font: **Noto Nastaliq Urdu** (fallback: **Noto Naskh Arabic**) for elements with `lang="ur"`,
  line-height 1.9.
- Scale: page title 24 px semibold; section title 18 px semibold; body 14 px; small/meta 12 px.
- KPI numbers: 28 px semibold, tabular numerals.

## 7. Layout and Components
- Spacing scale: 4 px base (4, 8, 12, 16, 24, 32).
- Radius: 8 px cards and inputs, 6 px buttons and badges.
- Shadows: one subtle elevation in light mode; in dark mode use borders instead of shadows.
- Sidebar width 240 px (collapsed 64 px). Active item: `--primary-soft` background with a 3 px
  `--accent` bar on the left.
- Content max width 1440 px.
- Buttons: one primary per screen area; secondary as outline; destructive uses `--danger`.
- Icons: lucide-react, 16–20 px, stroke 1.75, with a text label for every action.
- Chart series order: `--primary`, `--accent`, `--success`, `--warning`, `--info`, `--muted-foreground`.

## 8. Not Allowed
Emojis, gradients, glow effects, sparkle or "magic" AI icons, decorative illustrations, large red fills,
raw hex values in components.
