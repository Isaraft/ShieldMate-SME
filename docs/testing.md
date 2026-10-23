# Verification through Phase 01

Run the exact automated commands in README. Backend tests use temporary or in-memory
SQLite, not the user's local database. Frontend tests mock only the health transport;
mock values never appear in the shipped API or interface.

Tests cover health shape, absent future endpoints, method restrictions, CORS defaults,
host rejection, non-leaking errors, configuration validation and migration upgrade,
repeat upgrade, drift check, downgrade and re-upgrade. Frontend tests cover each planned
route, navigation/focus, disabled registration, 404 recovery, loading, success, invalid
response, network failure and retry. Later-phase workflows are intentionally not tested
as if they existed.

## Manual/local browser checklist

1. Start both services. Load `/` and inspect the landing page. Open `/app`; the local API should show Responding.
2. Tab from the top: the first focus target is Skip to content. Activate it, then check
   visible focus through navigation. The disabled Create workspace button cannot submit.
3. Open Workspace preview. Navigate to every route; each says Coming in a later phase.
   Navigation changes focus to the main content. Refresh `/app/assets` directly.
4. Visit `/not-a-page`; use Return to home.
5. Stop the backend, reload `/app`, observe Unavailable, restart it and choose Retry connection.
6. At widths 360, 768, 1280 and 1920 CSS px, inspect text wrapping and absence of horizontal
   overflow. Check reduced motion and readable contrast. No metrics or fake findings appear.
7. In Compose, verify `/api/v1/health` through port 5173, security headers, non-root users
   and the persistent migration revision after a restart. No business record exists yet.

Dependency audits require internet access. A passing audit is a time-limited package
advisory check, not proof of application security or a penetration test. Keep observed
failures, unavailable checks and untested accessibility work explicit in the results.

## Phase 01 additions

Frontend tests cover public section destinations, mobile menu expansion/Escape/focus,
preview labels, health-only requests, empty findings, unique input associations,
validation/error/success/reset, and disabled/pending tab order. Browser QA covers 16
route/viewport combinations plus 16 interactions using the production container.
The mobile menu and FAQ must work by keyboard; UI examples never send input.
See [the exact commands and evidence](phase-01-results.md). The QA script uses optional
Playwright/axe tooling installed outside the application dependency tree.
