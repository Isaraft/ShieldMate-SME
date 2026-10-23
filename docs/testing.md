# Verification through Phase 03

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
   visible focus through navigation. The Create account link opens registration.
3. Open Workspace preview. Navigate to every route; each says Coming in a later phase.
   Navigation changes focus to the main content. Refresh `/app/assets` directly.
4. Visit `/not-a-page`; use Return to home.
5. Stop the backend, reload `/preview`, observe Unavailable, restart it and choose Retry connection.
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

## Phase 02 verification

See [Phase 02 commands and evidence](phase-02-results.md). The original public route tests
now target `/preview`; private `/app` routes use real session guards. Integration tests
use migrated temporary SQLite databases and never reset the user database. Browser
accounts are generated only during local QA, with random passwords kept in memory.

## Phase 03 domains

[Phase 03 results](phase-03-results.md) records the actual domain security tests and browser
checks. `scripts/qa/phase03_server.py` is an isolated test harness with injected DNS only;
never run it as the application server or present its verified fixtures as live DNS proof.
Production entry remains `app.main:app`. Live provider E2E requires an operator-controlled
domain and manual TXT publication; it is not part of automated CI.

## Phase 04 checks

Run the existing backend/frontend quality commands plus the scanner tests (included in
pytest/Vitest). Network tests use mocked DNS/socket transports and temporary migrated DBs.
They never probe external domains. See [scanner design](scanner.md) and the Phase 04 report.
Use the ordinary Compose stack for marketing/auth regressions; use the separate
`scripts/qa/phase04.compose.yaml` stack for deterministic scanning browser/restart checks.
It uses an isolated volume and mounted test-only modules, not production network results.
A real team-owned live scan remains a separate manual acceptance step.
