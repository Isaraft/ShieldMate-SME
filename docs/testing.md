# Verification through Phase 06

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

## Phase 05 finding verification

The full backend suite includes deterministic saved-observation rule cases and migrated
SQLite integration tests for authorization, lifecycle, retention, source ordering, concurrent
reconciliation/read snapshots, crash rollback and backfill. No external probes are used.
Frontend tests mock API responses only in test files; production pages always request the
backend. See [Phase 05 results](phase-05-results.md) for exact commands and counts.

`scripts/qa/phase05.compose.yaml` is a separate local stack with an isolated volume. It
injects DNS ownership verification and explicitly synthetic saved scanner observations;
its worker runs the real offline reconciliation loop. `phase05_seed.py` refuses workspaces
without the LOCAL QA prefix. The QA modules are mounted only for tests and are absent
from production images. Never present these snapshots as a live security assessment.

`scripts/verify-phase-05.cjs` checks real registration/session/organization/asset routes,
worker processing, source links, exact API/UI totals and priorities, partial/clean/reopened
history, container restart, idempotent backfill, stale and error states. It captures four
widths and runs axe. Earlier browser scripts support `EVIDENCE_DIR` so regression evidence
can be retained without overwriting historical phase screenshots. Live owned-domain E2E,
physical assistive devices and non-Chromium browsers require separate manual checks.

## Phase 06 dashboard and tasks

The backend suite adds task create/open idempotency, status/owner/note persistence, version
conflicts, CSRF/Origin/session/tenant checks, bounded history and persistent abuse budget,
atomic rollback/concurrent mutations, composite foreign keys, preserved migrations, honest
dashboard states and absence of evaluator/network writes. Frontend tests cover exact
projections, truthful states, task filtering, secure creation, saved edits, escaped notes,
recurrence, conflicts, draft navigation and session expiry.

`scripts/qa/phase06.compose.yaml` uses its own volume/ports and mounted injected TXT/saved
observation fixtures. The worker runs real reconciliation; production images contain no QA
modules. `scripts/verify-phase-06.cjs` exercises actual account → asset → observations →
priority → task → edit → reload → done/unverified → conflict → evidence resolution/recurrence
→ container restart → source navigation. Four widths and axe are recorded. See
[Phase 06 results](phase-06-results.md) for exact commands and actual evidence. A live
team-owned DNS/provider scan, real assistive technology and SME beta users remain separate
manual work; fixture QA does not establish those outcomes.

## Phase 07 report, demo and language verification

`backend/tests/test_reports.py` covers evidence scope, immutable bytes, PDF extraction and
font glyphs, renderer limits/failure, report quotas/concurrency, tenant/CSRF/session guards,
logout during rendering, recovery, migration and synthetic-demo isolation. Frontend tests
extend the existing suites with reports/demo/language interactions. Run the regular full
backend/frontend commands plus `npm run i18n:check --prefix frontend`.

The isolated `scripts/qa/phase07.compose.yaml` stack and
`scripts/verify-phase-07.cjs` verify actual Docker-backed APIs/downloads/restarts, EN/RU,
100 responsive/axe views and synthetic-demo separation. They inject DNS proof and saved
observations; they never establish live owned-domain E2E. `scripts/verify-pdfs.py` extracts
and rasterizes all four downloaded QA/demo PDFs; visual inspection is still required.
See [the Phase 07 results](phase-07-results.md) for actual commands/counts and limitations.

## Phase 08 release-candidate checks

Run the unchanged backend/frontend commands above. New tests cover cross-tab stable CSRF, raw ASGI body bounds, sanitized unexpected errors, bootstrap limits, missing/stale readiness, strict local configuration, cookie separation, actual SQLite-full rollback, consistent committed-WAL backups, exclusive/no-partial publication and a real owned-loopback HTTP parser service. Existing DNS/SSRF/rebinding/TLS/SNI/peer, authorization/expiry/concurrency, finding/task/report tenant and lifecycle regressions remain enabled.

The local fixture profile is `compose.local.yaml` plus `scripts/qa/phase08.override.yaml`, project `shieldmate-phase08-qa`, port 15873. `scripts/verify-phase-08.cjs` expects a fresh disposable QA DB; it exercises the browser product journey, 399 populated/public/empty responsive/axe views, real queue around injected DNS/socket responses, two-tab account transitions, immutable EN/RU/KK snapshots, actual worker SIGKILL/90-second lease recovery and backend restart. The harness polls readiness through expected transient 502/503 and waits for asynchronous finding evaluation explicitly. No live domain is scanned. Private auth state is stored outside the repository.

After it completes, run `scripts/verify-phase08-interactions.cjs` for all-width screenshots, filters, keyboard dialog/menu focus and controlled report failure; `scripts/verify-phase08-operations.cjs` for online backup, isolated Docker restore, private report hashes, compiled-runtime headers/Host/body/deep links, permissions and failed migration startup. `scripts/verify-phase08-report-ui.cjs` additionally checks the actual localized generate/download/retry controls and all demo steps in a separate synthetic workspace. The operations script requires unused backup/restore destinations. Use optional installed Playwright/Chromium and axe-core paths via `PLAYWRIGHT_MODULE`, `PLAYWRIGHT_BROWSERS_PATH`, `AXE_MODULE`; they are QA tools, not new app dependencies.

`scripts/verify-phase-08-pdfs.py` uses Poppler on all 12 real API-generated PDF samples; `scripts/phase08-contact-sheets.py` uses Pillow for review sheets. Inspect actual rendered pages as well as extraction/bounds assertions. `scripts/check-secrets.py` scans high-confidence signatures in working-tree text, including untracked files, without printing matched values; it does not inspect Git history or binary artifacts. Dependency audit and secret scan results do not certify the application or base image. Exact results and honest NOT TESTED items are in `phase-08-results.md`.

## Phase 09 evidence/research tooling

The application suites remain unchanged. Run `backend/.venv/bin/pytest scripts/tests -q` for the independent standard-library evidence validator tests, `backend/.venv/bin/mypy --strict scripts/research scripts/research_evidence.py`, Ruff/format with backend config, and `node --test --test-reporter=tap scripts/tests/qa-runtime.test.cjs`. Internal fixtures are explicitly INTERNAL TEST DATA in temporary directories, not participants or reported beta results. The CLI rejects synthetic rows in real mode, validates declared consent/evidence/retention/denominators and scenario/build drift, and handles empty templates without a success percentage.

`SHIELDMATE_QA_PHASE=09` runs the existing browser/interactions/operations/report-UI scripts using new fixed localhost QA projects and raw output under `../../work/phase09/engineering`. Normal defaults remain Phase08. `scripts/verify-phase09-demo-isolation.cjs` independently checks fresh guest demo resets in EN/RU/KK at360/768/1280/1920, allows only local public-demo requests, and verifies no cookies or customer state. These are developer/automated QA, never human alpha/beta sessions. Selected actual screenshots/PDF review pages are classified in `docs/evidence/phase-09/`; follow `docs/testing/README.md` for consented human evidence outside Git.
