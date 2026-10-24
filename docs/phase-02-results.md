# Phase: 02 — Authentication & Organization Workspace

Historical Phase 02 report. Phase 08 replaces per-read CSRF rotation with stable session-bound tokens and adds a separate local RC cookie; see [current architecture](architecture.md) and [Phase 08 results](phase-08-results.md). The original verification below records behavior at that phase.

## Design/architecture decisions

The existing burgundy/red identity, local fonts and typed UI controls are retained.
`/app` and its business destinations now require an authenticated session and organization.
The public design preview moved to `/preview` (including `/preview/ui-kit`); the old
`/app/ui-kit` address redirects there. No private account data is used by the preview.
Registration creates an account, then explicitly requires login before company onboarding.

Passwords use Argon2id through argon2-cffi (64 MiB, 3 iterations, parallelism 2), with
rehashing on successful login when parameters change. Passwords accept 12–128 Unicode
characters. Email is trimmed/lowercased, length-limited and practically validated without
provider-specific rewriting. Company names normalize whitespace and allow 1–120 characters.
Unknown payload fields are rejected. Database uniqueness handles concurrent duplicates.

## API routes and data/migration changes

Migration `6b5520d9fa5d` follows `0001_foundation` without altering the foundation revision.
It adds users, organizations and sessions, with UUID identity, unique normalized email,
unique organization owner, foreign keys and indexed session expiry. No later-phase tables.

| Method | `/api/v1` path         | Contract                                                                      |
| ------ | ---------------------- | ----------------------------------------------------------------------------- |
| GET    | /auth/csrf             | Establish anonymous cookie if needed; return a fresh session-bound CSRF value |
| POST   | /auth/register         | 201 account created; 409 duplicate; does not log in                           |
| POST   | /auth/login            | Generic 401 on wrong credentials; rotate session on success                   |
| POST   | /auth/logout           | Revoke server session and clear cookie                                        |
| GET    | /auth/me               | Authenticated account and owned organization, or 401                          |
| POST   | /organizations         | Create one owned company, or 409                                              |
| GET    | /organizations/current | Read only the current owner's company                                         |
| PATCH  | /organizations/current | Rename only the current owner's company                                       |

Sessions use random 256-bit bearer tokens stored only as SHA-256 hashes in SQLite. The
raw value exists only in a host-only HttpOnly cookie, scoped to `/api`, SameSite=Lax,
8-hour authenticated lifetime; anonymous CSRF sessions last 30 minutes. Login revokes the
old session and creates a fresh token. Logout revokes it in the database. Expired/revoked
sessions fail authentication. Expired rows older than 24 hours are removed on new session
issuance; schedule periodic deletion for an idle production service. Session secrets
never appear in response JSON or browser storage. CSRF values are separate, short-lived
in-memory frontend values; their hashes are bound to the server session.

Each mutation requires an exact configured Origin and a matching X-CSRF-Token. The client
obtains a fresh value immediately before every mutation. Cross-origin CORS stays disabled;
use the Vite/Nginx same-origin proxy. No wildcard credentialed origins. Multiple concurrent
tabs can invalidate each other's CSRF value; retry obtains a fresh value. Secure cookies
are mandatory in production and configuration rejects HTTP trusted origins there.

Authentication attempts are limited per connection IP and hashed normalized account to
10 per 15 minutes. The bounded, locked in-memory limiter is single-process and resets on
restart; Nginx's proxy IP also creates an aggregate local limit. A future production edge
must supply a correctly trusted client-IP policy and a shared limiter before scaling.
Duplicate registration intentionally reveals an existing email for usability; login errors
remain generic and perform a dummy Argon2 check for absent users. No email verification
or password recovery exists. Mutations require a bounded Content-Length (16 KiB maximum).

## Files changed

Backend: `app/auth.py`, `app/models.py`, `app/{config,main,errors}.py`, migration environment
and new revision, pyproject/uv lock, integration tests and updated foundation assertions.
Frontend: `authApi.ts`, `pages/Account.tsx`, routing, public account CTA/navigation,
preview destinations, workspace styles, account and adjusted preview tests.
Other: `.env.example`, README, preserved `PROMPTS/PHASE_02.md`, browser verification scripts
and evidence, this report. Existing marketing composition and security headers are retained.

## Implemented

Real registration/login, persistent sessions, organization onboarding/rename, authenticated
identity, protected workspace routes, session checks on reload/focus/60-second intervals,
logout/re-login handling, safe errors and genuine pending states. The UI does not store
credentials or authentication flags. Public preview and UI kit remain independently usable.

## Explicitly NOT implemented

Domains/DNS verification, external checks, findings, tasks, reports, invitations/RBAC,
OAuth/MFA, email verification/reset delivery, billing, deployment or Phase 03 work.

## Verification commands and actual results

Baseline: frontend 22 tests, lint, formatting and build passed; backend 12 tests passed.
Final commands (root unless noted), all successful:

| Command                                                                     | Actual result                                                              |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `npm test --prefix frontend`                                                | 32 tests passed in 4 files                                                 |
| `npm run lint --prefix frontend`                                            | Zero errors/warnings                                                       |
| `npm run typecheck --prefix frontend`                                       | Passed                                                                     |
| `npm run format:check --prefix frontend`                                    | All files conform                                                          |
| `npm run build --prefix frontend`                                           | 54 modules; JS 263.93 kB, CSS 22.62 kB                                     |
| `backend/.venv/bin/pytest -q` (run as `.venv/bin/pytest -q` inside backend) | 25 tests passed; existing Starlette warning                                |
| `.venv/bin/ruff check .` (backend)                                          | Passed                                                                     |
| `.venv/bin/ruff format --check .` (backend)                                 | 17 files conform                                                           |
| `.venv/bin/mypy app` (backend)                                              | 9 source files passed                                                      |
| `.venv/bin/alembic upgrade head` and `.venv/bin/alembic check` (backend)    | Upgrade passed; no schema drift                                            |
| `npm audit --audit-level=low` (frontend)                                    | Zero vulnerabilities                                                       |
| `.venv/bin/pip-audit` (backend)                                             | No known vulnerabilities                                                   |
| `docker compose up --build --wait`                                          | Final serialized build passed; both services healthy                       |
| `docker compose config --quiet`                                             | Passed                                                                     |
| `node scripts/verify-phase-02.cjs`                                          | Full real HTTP browser journey and 12 viewport/accessibility checks passed |
| `node scripts/verify-phase-01.cjs`                                          | 16 regression viewport checks and 16 interactions passed                   |
| `backend/.venv/bin/python scripts/verify-session-restart.py`                | Actual container restart preserved session/account/company; logout passed  |
| `git diff --check`                                                          | Passed                                                                     |

Browser commands require these installed QA-only paths; they are not application dependencies:

```sh
export PLAYWRIGHT_BROWSERS_PATH='<operator-home>/Documents/Codex/2026-10-23/extract-and-review-the-entire-archive/work/browsers'
export PLAYWRIGHT_MODULE='<operator-home>/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'
export AXE_MODULE='<operator-home>/Documents/Codex/2026-10-23/extract-and-review-the-entire-archive/work/phase01-tools/node_modules/axe-core'
node scripts/verify-phase-02.cjs
EVIDENCE_DIR="$PWD/docs/evidence/phase-02/regression" node scripts/verify-phase-01.cjs
```

Browser: Chromium 151.0.7922.34 / Playwright 1.62.1, axe-core 4.14.0. The first Docker
build spent about five minutes downloading locked dependencies. Two overlapping local
rebuilds initially collided on a container name; a serialized rebuild resolved this
without removing the database volume. Final verification uses the completed stack.

## Auth/session/CSRF/authorization test results

Integration tests use isolated SQLite databases migrated from foundation to head; a
separate new application instance verifies persisted identity/session/organization.
They cover password hashing/bounds, malformed/duplicate email, generic login failures,
unauthenticated reads/writes, two-owner isolation, injected organization IDs, duplicate
workspace, rename, cookie flags, expiry, logout replay, CSRF/origin, body limits and
registration/login rate limits. No external authentication service or network scan is used.

## Responsive/accessibility verification

Actual local browser screenshots and automated checks are stored in `docs/evidence/phase-02/`.
All 12 new page/viewport combinations at 360/768/1280/1920px had no horizontal overflow
and zero axe WCAG A/AA violations. Actual screenshots were inspected. Private headings
use calmer IBM Plex Sans; auth headings retain Anton. Keyboard field order, visible 3px
focus, reduced motion and invalid-session re-login passed. The preserved Phase 01 suite
also passed its keyboard/menu/FAQ/404/health recovery checks. Token contrast remains at
least 5.09:1 for the measured text pairs. Actual screen readers and Safari/Firefox are
NOT TESTED. No unhandled page errors occurred; signed-out 401 responses are expected.
Browser checks use generated disposable QA credentials; no shipped demo account exists.
Screenshots may contain the clearly named QA workspace created by that verification.

## Security and regression findings

The API has no caching of identity, tokens or company data. Existing CSP, safe exception
handling and restricted hosts remain. No secrets enter logs or Git. Frontend escapes all
rendered names. Current session ownership controls every company read/write; no ID-based
company API exists. Database/session authorization is independent of frontend guards.
Existing Node and Starlette deprecation warnings remain documented from earlier phases.

## Acceptance criteria

| Gate                                                           | Result |
| -------------------------------------------------------------- | ------ |
| Real signup/signin/reload/logout against persistent storage    | PASS   |
| High-entropy hashed sessions, expiry and revocation            | PASS   |
| Secure password hashes; no password exposure                   | PASS   |
| Frontend and backend private access guards                     | PASS   |
| Owner-scoped organization operations and cross-tenant tests    | PASS   |
| CSRF and exact Origin protection tested                        | PASS   |
| Registration/login abuse controls and limitations documented   | PASS   |
| Landing/brand intact; responsive and accessible interactions   | PASS   |
| No invented findings/scans/reports/billing/organization data   | PASS   |
| Existing regressions, new tests and build pass                 | PASS   |
| Clean/upgrade migration and actual Docker persistence verified | PASS   |
| Documentation/configuration updated without secrets            | PASS   |

## Local startup + manual signup walkthrough

From project root run `docker compose up --build --wait`, then open http://127.0.0.1:5173.
Choose Create account in Starter scope, provide an email and a 12–128 character password,
sign in, enter the company name, open settings and rename it, reload, then Sign out.
Private entry: `/app`; public design reference: `/preview`; UI kit: `/preview/ui-kit`.
Both local hostnames are permitted: `http://127.0.0.1:5173` and `http://localhost:5173`.
Use one hostname consistently because cookies are host-specific. Other ports require
explicit trusted-origin configuration. Compose uses fixed local development settings.

## Manual environment/production steps

No signing secret is needed for opaque database sessions. Protect the database and backups;
rotate sessions by revoking rows when responding to an incident. Configure production HTTPS,
Secure cookies, explicit HTTPS trusted origins and hosts, TLS proxy policy and no-store
caching. Run migrations before startup, schedule session cleanup, secure backups and a
shared rate limiter before multiple workers. `.env.example` contains development settings
only; Compose remains a local HTTP setup. Do not expose or deploy it without approval.

## Open issues/limitations

One owner/company per account. No password reset or email ownership verification. SQLite
and the in-process limiter are intended for the local single-worker MVP. CSRF tokens rotate
per request and may require retry across concurrent tabs. Real device, screen reader and
Safari/Firefox testing are outside the automated Chromium checks. No external security
audit is claimed. QA account records are local verification data, not customer traction.

## Git status and local commit

Only Phase 02 changes will be committed locally after verification. No push or deployment.
The final response records the commit hash and resulting status.

## Next phase: 03 — NOT STARTED
