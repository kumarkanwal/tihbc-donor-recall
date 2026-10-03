# Frontend Screens Specification

All pages follow AGENTS.md sections 8 and 9 and `docs/brand.md`. Every data view has loading, empty,
error, and success states. Dates display in `Asia/Karachi` as `03 Oct 2026, 10:30 AM`.

---

## 1. App Shell

**Sidebar (left, collapsible):** TIHBC logo at top, then:
Dashboard, Donor Batches, Content Series, Campaigns, Follow-up Inbox, Reports, Settings.
Coordinators do not see admin-only actions (buttons are hidden, not disabled).

**Top bar:** page title and breadcrumb (left); demo clock and "Skip time" control (admin only),
notifications for new follow-ups, user menu with role and logout (right).

**Skip time control:** shows current demo date and time. Dropdown with "+1 hour", "+1 day", "+3 days",
"+7 days", and "Reset clock". Shows a confirmation toast with the new time.

**Simulator button:** fixed bottom-right button labeled "Donor Phone". Opens the simulator panel
(`docs/simulator.md`). Available on every page.

---

## 2. Login `/login`
Centered card: logo, email, password, "Sign in" button. Inline error on invalid credentials.
Redirect to Dashboard after login.

---

## 3. Dashboard `/`
- **Filters row:** campaign selector (default "All campaigns"), date range.
- **KPI cards (row of 6):** Donors reached, Delivery rate, Read rate, Response rate, Confirmed, Needs call.
  Each shows value and the count behind it.
- **Chart 1:** daily sent / delivered / read / responded (line chart).
- **Chart 2:** response outcome breakdown: confirmed, rescheduled, declined, no response, escalated (bar chart).
- **Active campaigns table:** name, batch, status, progress bar (responded / enrolled), response rate, link.
- **Recent follow-ups:** latest 5 open items with type badge and "Open inbox" link.
- **Batch insight panel:** plain-text summary generated from metrics (e.g. "Response rate is highest among
  regular donors. Most declines are due to travel."). Styled as a normal card, no AI styling.

---

## 4. Donor Batches

### 4.1 List `/batches`
Table: name, file name, valid / total rows, invalid rows, uploaded by, uploaded at, used in campaigns.
Primary action (admin): "Upload batch".

### 4.2 Upload `/batches/new` (3-step wizard)
1. **Upload:** drag-and-drop area (CSV/XLSX), "Download sample file" link, batch name field.
2. **Review:** summary cards (total, valid, invalid), segment and language breakdown, table of the first
   10 valid rows, errors table (row, field, value, reason) with "Download error report".
3. **Confirm:** "Import 240 valid donors" button. Success screen with links to the batch and "Create campaign".

### 4.3 Detail `/batches/[id]`
Header with name and stats. Tabs: **Donors** (table with phone masked, segment, language, city,
blood group, last donation; filters and search) and **Validation report**.

---

## 5. Content Series

### 5.1 Library `/series`
Grid or table toggle. Each series shows name, kind badge (Primary / Secondary), status, languages,
step count, tags. Filters: kind, status, tag, language. Search. Actions: Open, Duplicate, Archive.
Primary action (admin): "New series".

### 5.2 Editor `/series/[id]`
Two-column layout:
- **Left:** series settings (name, description, kind, languages, response window, tags), then an ordered
  list of steps as cards showing "Step 2 · Day 3 · Utility". Drag to reorder. "Add step" button.
- **Step editor (opens in a drawer):** delay days, category, media (upload or none), language tabs
  (English / Urdu) each with body textarea, character counter (1024), variable insert buttons
  (`Donor name`, `Center name`, `Appointment date`), and up to 3 buttons with intent and labels per language.
- **Right:** live phone preview of the selected step in the selected language, styled like the simulator.

Header actions: "Activate series" (shows missing-content errors if invalid), "Duplicate", "Archive".

---

## 6. Campaigns

### 6.1 List `/campaigns`
Table: name, batch, primary series, status, start date, enrolled, response rate, progress bar.
Status filter tabs: All, Running, Scheduled, Paused, Completed, Draft. Primary action (admin): "New campaign".

### 6.2 Create `/campaigns/new` (single form with summary)
Fields: name, donor batch, primary series, secondary series, start (now or date-time).
Right side summary: donor count, languages covered (warning if a donor language is missing from a series),
message schedule timeline (Day 0, Day 3, Day 7, then secondary steps, then escalation).
Actions: "Save as draft", "Launch campaign" (confirmation dialog).

### 6.3 Detail `/campaigns/[id]`
- Header: name, status badge, Pause / Resume.
- **Status counters:** one card per enrollment status (clickable to filter the table).
- **Sequence timeline:** steps with sent / delivered / read / responded per step.
- **Enrollments table:** donor, phone (masked), language, status, current step, last activity,
  "View chat" (opens the simulator on that donor), "View details".
- **Enrollment drawer:** donor info, message and response timeline, detected intent, decline reason,
  appointment, linked follow-up.

---

## 7. Follow-up Inbox `/inbox`
The coordinator's main work screen.
- **Tabs with counts:** Needs call, Reschedule, Declined, Confirmed, All. Secondary filter: Open,
  In progress, Done. Toggle "Assigned to me". Campaign filter. Search.
- **List (left):** donor name, type badge, priority, campaign, latest reply snippet, time, assignee.
  New items appear live at the top with a subtle highlight.
- **Detail panel (right):** donor details with full phone and "Copy number", reply history, detected intent,
  requested date or booked slot, decline reason, activity log, notes input.
  Actions: "Assign to me", "Start", "Resolve" (outcome dropdown + optional note), "View chat".
- **Export CSV** button with current filters.

---

## 8. Reports `/reports`
Tabs:
- **Delivery and engagement:** funnel (sent → delivered → read → responded) per campaign; table per campaign.
- **Responses:** breakdown by intent, segment, and language (bar charts and table); decline reasons chart.
- **Inactive numbers:** table of invalid (upload) and undeliverable (sending) numbers with reason, batch,
  campaign. Summary cards at top.
Each tab has campaign and date filters and "Export CSV".

---

## 9. Settings `/settings`
Tabs:
- **WhatsApp integration (mocked):** status rows for Business verification, Phone number, Display name,
  Quality rating, Messaging limit; templates table (name, category, status). Note: "Demo environment".
- **Users:** read-only list of users and roles.
- **Demo controls (admin):** clock status, skip time buttons, "Reset demo data" (confirmation dialog).

---

## 10. Shared Components
`PageHeader`, `DataTable` (sorting, search, filters, pagination), `StatusBadge` (single color map for all
enums), `KpiCard`, `EmptyState`, `ErrorState`, `ConfirmDialog`, `FileDropzone`, `MaskedPhone`,
`DateTime`, `ChartCard`, `LanguageTabs`, `PhonePreview` (shared with the simulator bubble components).
