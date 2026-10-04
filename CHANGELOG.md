# Changelog

## Unreleased

- Added the bilingual Content Series library and editor with table/grid browsing, filters, lifecycle actions, ordered message steps, media and quick replies, activation guidance, and live simulator-styled previews.
- Added complete Donor Batches screens for searchable batch browsing, role-gated CSV/XLSX validation and import, warning/error review, expired-preview recovery, donor filtering, and validation reports.
- Added the reusable table, state, KPI, dialog, upload, phone, date/time, chart, bilingual, and phone-preview component library for upcoming frontend screens.
- Added validated staff sign-in, persisted demo sessions, protected routes, role-aware current-user data, and complete logout and expired-session handling.
- Added the responsive application shell with persistent navigation, role-aware top-bar controls, light/dark theme access, placeholder pages, and the donor phone panel entry point.
- Added the frontend application foundation, light and dark brand themes, Urdu typography, typed API client, shared status styling, and temporary visual verification page.
- Added secure staff login, role-based API access, current-user lookup, active-user listing, and idempotent admin/coordinator demo-user seeding.
- Added production backend containers for the API and scheduler worker, automatic API-owned database migrations, dependency health checks, and persistent media storage.
- Added donor batch sample download, CSV/XLSX validation previews, first-occurrence duplicate handling, cross-batch warnings, transactional imports that reject empty batches, and searchable batch/donor browsing. Newly imported batches remain visible before campaign assignment.
- Added the bilingual content-series library API, ordered step operations, aggregate activation validation, localized simulator previews, duplication and archiving, and validated image/video uploads with static media serving.
- Prevented request-validation responses from echoing submitted personal data while retaining actionable field, message, and error-type details.
