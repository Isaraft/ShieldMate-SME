# Phase: 03 — Authorized Assets & DNS TXT Verification

Verified locally on 24 October 2026 (Asia/Almaty). Initial branch `main`, commit `b1b9b36`;
working tree was clean. The uploaded brief is preserved unchanged in `PROMPTS/PHASE_03.md`.

## Baseline checks before changes

`npm test --prefix frontend`: 32 tests passed; frontend lint, typecheck, format check and
production build passed. Backend `.venv/bin/pytest -q`: 25 tests passed; Ruff and mypy passed.
The existing Node module.register and Starlette/httpx deprecation warnings were present.

## Design and security decisions

The existing private `/app/assets` now manages real organization assets. Public preview,
marketing and the Phase 02 account flow retain their architecture and visual identity.
The new page uses IBM Plex Sans, sharp rules, warm ivory, burgundy and red; no fake metrics.
Consent is unchecked by default and stored with policy `starter-authorization-v1` and UTC
epoch acceptance time. DNS control proves control at a particular name/time, not legal
permission to assess every underlying host, CDN or SaaS service.

A centralized backend validator accepts ASCII and valid Punycode only; direct Unicode
input is deliberately rejected. It rejects whitespace (including at edges), URLs, IPs,
ports, paths, userinfo, wildcard/underscore labels, numeric IP forms, reserved namespaces,
malformed IDNA and public-suffix-only names. Case and one root dot normalize consistently.
IDNA round-trip validation enforces label limits. The derived challenge hostname must also
fit 253 DNS octets, so an otherwise valid excessively long asset is rejected with validation.

`tldextract==5.3.0` uses its packaged Public Suffix List, including private suffixes, with
network updates and cache writes explicitly disabled. Snapshot SHA-256:
`b69315c085d53972724b8f2df111ffc329b0c84fe0a47d62c8c91655cc774a38`.
Unknown suffixes are rejected; update/review the pinned snapshot deliberately in future.
`dnspython==2.8.0` performs one UDP TXT query using the OS-configured recursive resolver,
3-second timeout, no retries, no TCP fallback and no application-level CNAME following.
No A/AAAA, HTTP, TLS, IP probing or scanner operation exists. Oversized/truncated/failed
responses are inconclusive, never successful. No arbitrary resolver/record/type is accepted.

## Data schema and migration revision

`90bff5eabc24` follows `6b5520d9fa5d`, adding `domains` and `domain_events`. Existing account,
organization and session tables/revisions are unchanged. Domain rows have UUID identity,
indexed organization FK, unique `(organization_id, canonical_fqdn)`, immutable canonical
name, consent timestamp/version, public challenge token/generation/issue/expiry timestamps,
verification timestamp/freshness, last check and sanitized error code. Generation has a
positive database constraint. Audit events retain organization/asset ID, event and timestamp,
without TXT contents or credentials; deletion preserves the small audit trail.

Creation acquires SQLite BEGIN IMMEDIATE before quota/uniqueness decisions (default five
assets). Rotation/deletion use the same short lock. Network work runs after committing
its request audit entry and releasing the write lock. The completion UPDATE compares
owner, ID, generation and current expiry atomically. Rotation, deletion or expiry during
DNS therefore rejects the delayed result with 409; no stale result can resurrect a row.

## Implemented frontend pages / flows

`/app/assets`: real list and guided empty state; enrollment with explicit authorization;
owner-scoped reloadable instructions; complete hostname/value copy buttons and clipboard
failure guidance; localized dates with timezone; separate challenge and proof expiries;
verified/pending/expired/stale labels; missing-record and temporary-DNS feedback; deliberate
rotation/reverification; native accessible delete dialog with Escape/cancel/confirmation.
All scan controls remain disabled. Native required fields and server validation both apply.
Expired sessions return to login; request/CSRF failures show retryable feedback.

## Implemented API routes

| Method | Path                                          | Behavior                                                                           |
| ------ | --------------------------------------------- | ---------------------------------------------------------------------------------- |
| GET    | `/api/v1/domains`                             | Current organization's list and current owner-visible instructions                 |
| POST   | `/api/v1/domains`                             | 201 pending enrollment; accepts fqdn + strict true authorization_acknowledged only |
| GET    | `/api/v1/domains/{UUID}`                      | Owner-scoped detail, or non-enumerating 404                                        |
| DELETE | `/api/v1/domains/{UUID}`                      | Owner/CSRF-protected removal and audit                                             |
| POST   | `/api/v1/domains/{UUID}/verification/request` | Rotate and deliberately revoke existing proof                                      |
| POST   | `/api/v1/domains/{UUID}/verification/check`   | One bounded DNS lookup and atomic proof update                                     |

Example enrollment: `{"fqdn":"shop.example.com","authorization_acknowledged":true}`.
`organization_id`, `verified`, resolver and similar authority fields are forbidden.
Validation returns 422; own duplicate/quota returns 409; throttling returns 429;
unauthenticated returns 401; bad CSRF/origin returns 403; foreign/missing IDs return 404.
Private responses retain `Cache-Control: no-store`, safe errors and the existing CSP.
Verification returns `{"code":"verified|not_found|temporarily_unavailable|challenge_expired",
"domain":{...current persisted state...}}`; a race returns 409 and requests a reload.
The creation transaction performs no DNS. Deletion/list/detail never query DNS either.

## Verification mechanics

- Type TXT, exact hostname `_shieldmate-challenge.<canonical_fqdn>`.
- Exact complete value `shieldmate-verification=<secrets.token_urlsafe(32)>` (256 random bits).
- Owner-scoped token stored/retrievable after reload; public DNS proof is not a login secret.
- Default challenge lifetime 48 hours; default proof freshness 30 days from actual success.
- Multiple answers are permitted. TXT chunks concatenate byte-for-byte without added spaces.
  Only the exact expected value at the exact question name succeeds; substrings and alias
  target records do not. No low-level resolver data is returned or rendered as HTML.
- Status is derived from persisted timestamps: pending before proof; expired for an expired
  unverified challenge; verified while recorded proof remains fresh; stale after freshness.
  Read-only status computation does not silently extend trust or mutate proof timestamps.
- Challenge expiry does not invalidate an earlier still-fresh proof. A failed subsequent
  check records its outcome but does not erase an earlier proof or extend its freshness.
- Rotation increments generation, issues a new token and clears proof/freshness. Old values
  become invalid immediately. Stale assets must rotate, publish and verify again.
- `scan_available` is always false in Phase 03. Phase 04 must independently require fresh
  proof, consent and safe public-address/connection scope; DNS proof alone is insufficient.

Organization abuse budgets persist in audit events across restarts (20 recent events per
15 minutes by default; verification records both request and outcome). Connection-IP budget
is 100 asset actions/15 minutes in a bounded locked in-process limiter; Nginx shares an
aggregate proxy IP locally. Both configurable limits have validated bounds. Shared limiting
and trusted edge client-IP handling are future production requirements, not implemented here.

## Files changed

Backend: `app/{domains,domain_validation,domain_dns,domain_limits}.py`, models/config/router
registration, new migration, dependency manifest/lock, domain tests and foundation assertions.
Frontend: `pages/Assets.tsx`, private route, workspace styles, Assets tests. Documentation:
README, env sample, this report, architecture/testing notes, preserved prompt. Verification:
`verify-phase-03.cjs`, `verify-domain-restart.py`, QA-only isolated DNS harness and evidence.
The Phase 02 browser script gains an optional output directory so historical evidence stays intact.

## Commands executed and actual results

| Command                                                       | Actual result                                                             |
| ------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `npm test --prefix frontend`                                  | 36 tests in 5 files passed                                                |
| `npm run lint --prefix frontend`                              | Zero errors/warnings                                                      |
| `npm run format:check --prefix frontend`                      | All files conform                                                         |
| `npm run typecheck --prefix frontend`                         | Passed                                                                    |
| `npm run build --prefix frontend`                             | 55 modules; JS ~271.85 kB, CSS ~24.11 kB                                  |
| `.venv/bin/pytest -q` in backend                              | 81 passed; existing Starlette warning                                     |
| `.venv/bin/ruff check .` in backend                           | Passed                                                                    |
| `.venv/bin/ruff format --check .` in backend                  | 23 files conform                                                          |
| `.venv/bin/mypy app` in backend                               | 13 source files passed                                                    |
| `.venv/bin/alembic upgrade head` / `.venv/bin/alembic check`  | Passed; no schema drift                                                   |
| `npm audit --audit-level=low` in frontend                     | Zero vulnerabilities                                                      |
| `.venv/bin/pip-audit` in backend                              | No known vulnerabilities                                                  |
| `docker compose up --build --wait`                            | Both services healthy after additive migration                            |
| `docker compose config --quiet`                               | Passed                                                                    |
| `backend/.venv/bin/python scripts/verify-domain-restart.py`   | Domain/challenge/session survived actual container restart; no DNS lookup |
| `node scripts/verify-phase-03.cjs` with isolated test backend | Eight journey groups and four viewport/accessibility checks passed        |
| `node scripts/verify-phase-01.cjs` against Compose            | 16 viewport checks, 16 interactions passed                                |
| `node scripts/verify-phase-02.cjs` against Compose            | Account journey and 12 viewport/accessibility checks passed               |
| `git diff --check`                                            | Passed                                                                    |

Browser tooling: Chromium 151.0.7922.34, Playwright 1.62.1, axe-core 4.14.0. QA module paths
are the same as Phase 02. Phase 03 uses `BASE_URL=http://127.0.0.1:15173` and the QA-only
harness `scripts/qa/phase03_server.py`, an isolated `/tmp` SQLite database and injected DNS
outcomes. This module is never imported by the production application. Production Compose
retains the actual UDP resolver. Regression screenshots are stored separately under
`evidence/phase-03/regression` and `evidence/phase-03/auth-regression`.

To reproduce the isolated browser backend (development terminal commands, not production):

```sh
SHIELDMATE_DATABASE_URL=sqlite:////tmp/shieldmate-phase03-browser.db backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
PYTHONPATH=backend backend/.venv/bin/uvicorn scripts.qa.phase03_server:app --host 127.0.0.1 --port 15100 --no-access-log
# In another terminal:
API_PROXY_TARGET=http://127.0.0.1:15100 npm run dev --prefix frontend -- --port 15173
# With the QA module paths documented in Phase 02 exported:
BASE_URL=http://127.0.0.1:15173 node scripts/verify-phase-03.cjs
```

Temporary QA servers were stopped after verification; the actual Compose site remains running.

## Security tests and browser evidence

Automated backend tests cover 34 dangerous name inputs without DNS calls, canonicalization,
Punycode, PSL-only rejection, duplicates, quota, consent, malicious authority fields,
two organizations enrolling the same name, foreign-ID denial across every domain action,
CSRF/origin, IP/org budgets, exact TXT matching/chunks/multiple records, wrong hostname,
NXDOMAIN/empty answer/SERVFAIL/timeout, TCP prohibition, expiry/freshness, regeneration,
rotation/deletion/expiry races, persisted verified state, no scanner route, and clean/Phase 02
upgrades preserving real test users, organizations and sessions. Backend migration tests
use isolated SQLite files and injected DNS; no external DNS is used by the test suite.

Assets screenshots at 360, 768, 1280, 1920px were captured and visually inspected. No horizontal
overflow; zero axe A/AA violations at each width. Copy value was checked against the actual
clipboard; native dialog Escape, cancel and confirmed deletion passed. The existing
keyboard/focus, reduced-motion, contrast (minimum measured text pair 5.09:1), auth and
marketing browser checks passed. Mock DNS screenshots conspicuously state LOCAL QA and
must not be presented as live DNS verification. Screen readers and physical devices,
Safari/Firefox and actual external DNS-provider E2E are NOT TESTED.

## Acceptance gates

| Gate from the brief                                                  | Result |
| -------------------------------------------------------------------- | ------ |
| Phase 02 authentication and organization isolation preserved         | PASS   |
| Strict domain normalization and dangerous-input rejection            | PASS   |
| Tenant-scoped persistent CRUD including restart                      | PASS   |
| Enrollment authorization required and recorded                       | PASS   |
| Unique strong challenge generated, displayed and retrievable         | PASS   |
| Real backend DNS implementation with controlled test seam            | PASS   |
| Exact fresh current-generation matches only                          | PASS   |
| Failure/timeout/expiry/rotation/races/deletion cannot falsely verify | PASS   |
| Session, ownership, CSRF/origin and abuse limits                     | PASS   |
| Unverified/stale assets cannot scan; no scanner exists               | PASS   |
| Responsive copy/verification/error/delete UI                         | PASS   |
| Migrations, tests, build, restart and audits executed                | PASS   |
| Documentation and manual/untested behavior disclosed                 | PASS   |
| Phase 04 untouched; no push, deployment or public scanning           | PASS   |

Public DNS-provider end-to-end verification: NOT TESTED — no team-controlled domain was
provided. This is explicitly separate from the passed implementation/controlled-test gate.

## Manual DNS/provider setup and local demonstration

Run `docker compose up --build --wait` from the repository; open http://127.0.0.1:5173/app/assets,
register/sign in and create a workspace if needed. Add only a domain you control or have
written authorization for. Read and acknowledge the policy. Copy the full TXT name/value.
At your DNS provider create a separate TXT record; do not modify SPF/DMARC. Providers may
append the zone automatically: for `shop.your-domain` inside the parent zone the relative
host is `_shieldmate-challenge.shop`, whereas in the exact domain's own zone it is
`_shieldmate-challenge`. Confirm the final full name equals the displayed name.

After publishing, click Verify ownership. A missing record remains pending; retry after
checking the name/value and DNS caching. An inconclusive DNS result grants no new proof.
If expired or rotating, generate a new challenge and replace the previous value. Rotation
revokes prior proof deliberately. TXT values remain public until you remove them yourself.
A verified badge means DNS control at the stated time, not a secure site or blanket legal
permission. Scan stays disabled. To stop the local stack, `docker compose down` preserves
the database; never add `--volumes` unless intentionally erasing it.

## Open issues, limits and Phase 04 handoff

ASCII/Punycode input only; bundled PSL updates require deliberate dependency review.
DNS UDP truncation, CNAME-only configurations and transport restrictions are inconclusive;
there is intentionally no TCP fallback. No live DNS-provider workflow was tested. SQLite
write serialization and the in-process IP limiter suit the academic single-worker setup;
production scaling requires a shared limiter and edge policy. Existing Phase 02 concurrent-tab
CSRF retry and cookie/HTTPS requirements still apply. Public QA data in screenshot fixtures
is labeled; it is not customer evidence. Audit history needs a production retention policy.
Future scans must independently enforce fresh authorization, vetted public addresses,
rebinding protection, pinned connections and strict protocol/timeout boundaries.

## Git status / commit

Only Phase 03 changes are committed locally following the existing workflow. The final
response records the exact hash; no push or external deployment was performed.

## Next phase: 04 — NOT STARTED
