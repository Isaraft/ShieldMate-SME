# Phase 04 — Authorized Security Scanning Engine

Implemented and verified locally on 24 October 2026, Asia/Almaty. Starting branch `main`, clean
commit `f7f33b2`. The uploaded brief was read completely and preserved byte-for-byte in
`PROMPTS/PHASE_04.md`, SHA256
`2f3b5ba6438429b8a0c5f2c4edf7dd0310ab05f2ffee2bb43a7905755f92bd4d`.
AGENTS, MVP spec, phases, design system, architecture, test guidance, prior reports and the
actual Phase 03 application were reviewed. Baseline: 81 backend tests, 36 frontend tests,
backend/frontend lint/format/types and frontend build passed. No preexisting failure found.

## Engineering outcome

The existing FastAPI/SQLAlchemy/SQLite and React/TypeScript architecture is preserved.
A durable, bounded database queue and separate single-slot worker collect real DNS,
trusted TLS and root HTTP/HTTPS observations. No new dependencies or lockfile changes.
The frontend now starts eligible scans, polls actual progress, renders technical evidence
and retrieves persistent chronological history. The public landing page is preserved.
Burgundy/red, warm ivory, IBM Plex Sans, sharp rules and existing controls continue into
the operational pages; no fake metrics, graphics, security scores or risk priorities.

Detailed [pipeline, threat model, limits and catalog](scanner.md) explain the actual code.
The brief's optional 80/443 scope is implemented; no other application port is accepted.
LIVE owned-domain end-to-end remains **NOT TESTED**, because no team-controlled domain
or real provider setup was supplied. Automated/backend/browser evidence uses explicit
controlled network fixtures; it is not proof of an actual live domain assessment.

## API and database

All paths below are prefixed `/api/v1`. Cookie authentication, owner-derived organization,
no-store responses, safe errors and existing Origin/CSRF protections remain in force.

| Method | Path                                           | Result                                                |
| ------ | ---------------------------------------------- | ----------------------------------------------------- |
| POST   | `/domains/{domain_id}/scans`                   | 202 durable queued ID; empty body only                |
| GET    | `/domains/{domain_id}/scans?offset=0&limit=20` | Newest-first scoped history; limit 1–50               |
| GET    | `/domains/{domain_id}/scans/{scan_id}`         | Scoped status/progress/times and bounded observations |

Start refuses unverified/stale/rotated/consent-revoked assets, foreign/missing assets,
invalid CSRF/origin, injected target parameters, duplicate active jobs, quota/capacity excess.
Responses distinguish 401/403/404/409/422/429. Existing domain responses now derive
`scan_available` from actual consent and proof freshness; they never bypass backend checks.
Each observation includes asset ID, observed timestamp, stable check ID, source, outcome,
safe evidence, factual summary, limitation and engine version `starter-checks-1`.

Additive revision `1806ce4b7076` follows `90bff5eabc24`. `scan_runs` stores organization/user
FKs, exact asset/name/proof snapshot, state/times/lease, error/progress and version.
Indexed status/created/asset/tenant fields support claims/history. A unique partial index
allows one queued/running scan per asset. `check_observations` has a scan FK with delete
cascade and unique `(scan_id,check_id)`. Old migrations are preserved unchanged. Upgrade,
drift, downgrade/re-upgrade and existing account/domain/session retention were tested.
Asset ID is an indexed historical reference, deliberately not a domain FK: Phase 03 physical
deletions revoke execution without erasing minimal job audit/history. Deleted-asset routes return 404.

## Actual check catalog

13 stable checks: DNS_ADDRESS, DNS_MX_PRESENT, DNS_SPF_PRESENT, DNS_DMARC_PRESENT,
TLS_CERTIFICATE, HTTPS_RESPONSE, HTTP_REDIRECT, HTTPS_HSTS, HTTPS_CSP, HTTPS_NOSNIFF,
HTTPS_REFERRER, HTTPS_PERMISSIONS and HTTPS_FRAME. See [exact rules](scanner.md).

`pass` means only the documented narrow condition was observed. `attention` requests review;
`informational` is context; `inconclusive`/`error` never count as evidence of safety.
SPF zero/one/multiple and DMARC missing/basic policy/malformed/ambiguous are distinguished.
MX absence is informational. TLS validates trust chain and exact hostname, records validity,
remaining days, sanitized issuer/subject and negotiated protocol; no insecure retry exists.
Certificate expiry/hostname/chain errors, refused connections, timeout and other failures
have separate fixed codes where available. Header presence does not establish safe policy.
HTTPS redirects yield inconclusive destination-header checks; no redirect is followed.
No DKIM inference, CVEs, exploitation, scores, business severity, tasks or remediation engine.

## Security controls and verification

- Eligibility is checked under the enqueue lock, after claim, before DNS work, after fresh
  destination resolution, before requests and before terminal publication. The worker checks
  the current organization owner as well as exact proof generation/verified time. Final
  publication rechecks eligibility under the same short write lock used by rotation/deletion.
- Every connection vets all returned A/AAAA answers and rejects unsafe/mixed/empty/uncertain
  sets. Numeric socket destinations stay pinned; Host/SNI retain the exact verified name.
  A mocked rebinding test makes getaddrinfo fail and asserts the actual socket tuple/SNI.
- IPv4/IPv6 private, metadata, loopback, reserved, multicast, documentation, mapped,
  transition/NAT64, protocol-assignment, Azure platform and scoped addresses are rejected. Direct transport syntax checks also
  reject URLs, IP literals and header-injection hostnames before creating a socket.
- No proxy-discovering HTTP library, redirect following, arbitrary port/path/header inputs,
  credentials, cookies or body collection. HEAD-to-GET fallback only 405/501 and one fresh
  authorized/pinned connection. Header/record/evidence and monotonic network budgets are hard-bounded.
- Tests cover auth/CSRF/Origin and asset/scan-ID tenant attacks, enqueue/acquisition/in-flight/
  terminal-commit revocation races, concurrency, quotas, queue/history limits, partial results,
  evidence limits, restart recovery, SPF/DMARC/DNS errors, TLS errors, HTTP fallback/limits,
  unsafe redirect categories and XSS escaping. CI performs no external scan.

## Worker durability and abuse bounds

SQLite BEGIN IMMEDIATE serializes starts/claims; the partial index independently prevents
active duplicates. One global running slot works across processes, sequential checks,
20 active/queued jobs maximum. Persisted rolling hourly quotas: 6/user, 6/org, 2/exact asset.
Default network budget 45s, I/O 3s, lease 90s, queue expiry 15m. Successful checks commit
incrementally. `completed` means all 13 useful check outcomes; `partial` keeps available
observations when other checks fail; `failed` makes no whole-site conclusion. Revocation
always fails. Stale running jobs become `interrupted`, never silently retried.

History is capped 100 runs/org by default. On insertion only the oldest terminal run older
than 1h can be evicted, preserving recent quota accounting. Evidence <= 4KiB/check and 13
checks bounds result storage. Existing audit events still require an operator retention
policy before production. Worker output logs IDs/state/types, not raw network exceptions.

Actual isolated container restart verification preserved queued jobs/session and completed
observations across API/worker restarts. SIGKILL of a running worker recovered honestly to
`interrupted` after 89.0 seconds of waiting for its actual 90s lease; no timestamp fabrication.
See [restart evidence](evidence/phase-04/restart-results.json). The normal production worker
entry is separate from the test-only mounted fixture entry. No external probe was performed.
The final Python 3.13.17 image also passed 24 special-use destination assertions and default
TLS trust/hostname checks without network requests; see [runtime evidence](evidence/phase-04/runtime-results.json).

## Files changed by purpose

- Backend engine: `app/scanner/{contracts,policy,dns_checks,transport,tls_checks,http_checks,
runner,service,worker}.py`; config/models/router/domain eligibility integration.
- Persistence: new additive scan migration; existing migration/schema assertions updated.
- Frontend: `scanApi.ts`, `pages/Scans.tsx`, Assets actions/eligibility/history links, private
  routes/titles and workspace styles, using existing typed components.
- Verification: scanner network/integration tests and React flow/polling tests; browser
  runner, isolated QA modules/Compose, real container restart script; Phase 03 regression
  runner updated for the intentional availability of scanning and separate evidence output.
- Operations/docs: Compose worker, `.env.example`, README, architecture/testing notes,
  this report, scanner design, unchanged uploaded brief and actual screenshot/JSON evidence.

## Commands executed and actual results

Commands are from the indicated directory; browser tooling environment is below.

| Directory | Exact command                                                                                           | Actual result                                                  |
| --------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| backend   | `.venv/bin/pytest -q`                                                                                   | 199 tests passed; existing Starlette/httpx deprecation warning |
| backend   | `.venv/bin/ruff check .`                                                                                | Passed                                                         |
| backend   | `.venv/bin/ruff format --check .`                                                                       | 36 files conform                                               |
| backend   | `.venv/bin/mypy app`                                                                                    | 23 source files passed                                         |
| backend   | `.venv/bin/alembic upgrade head`                                                                        | Head 1806ce4b7076                                              |
| backend   | `.venv/bin/alembic check`                                                                               | No schema drift                                                |
| backend   | `.venv/bin/pip-audit --progress-spinner off`                                                            | No known vulnerabilities                                       |
| frontend  | `npm test`                                                                                              | 41 tests in 6 files passed                                     |
| frontend  | `npm run lint`                                                                                          | Zero errors/warnings                                           |
| frontend  | `npm run typecheck`                                                                                     | Passed                                                         |
| frontend  | `npm run format:check`                                                                                  | All files conform                                              |
| frontend  | `npm run build`                                                                                         | 57 modules; JS 278.32 kB, CSS 25.43 kB                         |
| frontend  | `npm audit --audit-level=low`                                                                           | Zero vulnerabilities                                           |
| root      | `docker compose config --quiet`                                                                         | Passed                                                         |
| root      | `docker compose up --build --wait`                                                                      | Images built; API/frontend healthy; worker running             |
| root      | `docker compose -p shieldmate-phase04-qa -f scripts/qa/phase04.compose.yaml up --force-recreate --wait` | Isolated fixture containers started                            |
| root      | `backend/.venv/bin/python scripts/verify-scan-restart.py`                                               | Actual queue/session/results/crash recovery passed             |
| root      | `node scripts/verify-phase-04.cjs`                                                                      | Seven journey groups;16 viewport/axe checks passed             |
| root      | `node scripts/verify-phase-01.cjs`                                                                      | 16 viewport checks,16 interactions; no browser errors          |
| root      | `node scripts/verify-phase-02.cjs`                                                                      | Account journey,12 viewport/axe checks passed                  |
| root      | `node scripts/verify-phase-03.cjs`                                                                      | Domain journey and 4 viewport/axe checks passed                |
| root      | `git diff --check`                                                                                      | Passed                                                         |

Sandboxed TestClient execution hangs in this environment; the actual successful integration
runs used authorized local socket access, as in prior phases. Existing host Node 26
module.register and Starlette/httpx deprecation warnings remain; Node 24 Docker builds pass.
An initial hardening pass caught a misplaced policy condition in lint and an in-progress
test run. That run was stopped, the condition corrected, and the complete final suite rerun. One new React fake-timer test initially lacked an `act` boundary; it was corrected and the
final 41-test suite passes. No production regression was hidden by deleting existing tests.
The old "scanner absent" assertion was deliberately updated to verify the authorized 202 flow.

## Browser evidence and reproduction

Chromium 151.0.7922.34, Playwright 1.62.1, axe-core 4.14.0. Required widths 360/768/1280/1920
cover Assets, empty history, completed details and populated history: 16 checks, zero
horizontal overflow and zero axe WCAG A/AA violations. Keyboard disclosure/visible focus,
reduced motion, active polling/terminal stop, reload, partial/error/blocked states and API
outage retry passed. Existing phase regressions add 32 viewport checks and account/domain
journeys. Minimum previously defined tested normal-text contrast is 5.09:1. Screenshots
were actually rendered and inspected; fixtures are conspicuously labeled LOCAL QA.

Examples: [mobile details](evidence/phase-04/completed-360.png),
[desktop details](evidence/phase-04/completed-1280.png),
[history](evidence/phase-04/history-768.png), [assets](evidence/phase-04/assets-1920.png),
[partial](evidence/phase-04/partial.png), [blocked](evidence/phase-04/blocked.png).
Machine-readable [scan browser results](evidence/phase-04/browser-results.json) and
regression evidence reside in separate subfolders; prior-phase evidence is preserved.

```sh
export PLAYWRIGHT_BROWSERS_PATH='<operator-home>/Documents/Codex/2026-10-23/extract-and-review-the-entire-archive/work/browsers'
export PLAYWRIGHT_MODULE='<operator-home>/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'
export AXE_MODULE='<operator-home>/Documents/Codex/2026-10-23/extract-and-review-the-entire-archive/work/phase01-tools/node_modules/axe-core'
# Built production frontend + actual application APIs/worker, injected network fixtures only:
docker compose -p shieldmate-phase04-qa -f scripts/qa/phase04.compose.yaml up --wait
BASE_URL=http://127.0.0.1:15273 node scripts/verify-phase-04.cjs
BASE_URL=http://127.0.0.1:15273 EVIDENCE_DIR="$PWD/docs/evidence/phase-04/domain-regression" node scripts/verify-phase-03.cjs
EVIDENCE_DIR="$PWD/docs/evidence/phase-04/regression" node scripts/verify-phase-01.cjs
EVIDENCE_DIR="$PWD/docs/evidence/phase-04/auth-regression" node scripts/verify-phase-02.cjs
backend/.venv/bin/python scripts/verify-scan-restart.py
docker compose -p shieldmate-phase04-qa -f scripts/qa/phase04.compose.yaml down
```

QA module paths are installed test tooling outside application dependencies. The fixture
stack must have its own named project/volume; do not expose it publicly. Manual Vite QA on
15173/15100 was also exercised, then the built Docker frontend on 15273. Temporary QA servers
and containers are stopped after verification; the normal stack remains available on 5173.

## Acceptance gates from the brief

| #   | Gate                                                                 | Result / evidence                                       |
| --- | -------------------------------------------------------------------- | ------------------------------------------------------- |
| 1   | Fresh exact-domain proof/consent/tenant before enqueue and execution | PASS — authorization and race tests                     |
| 2   | Persistent organization-scoped scan/observation APIs                 | PASS — API/IDOR/restart tests                           |
| 3   | Real bounded DNS SPF/DMARC/context implementation                    | PASS — wire-fixture and policy tests                    |
| 4   | Trusted TLS hostname/certificate validity observations               | PASS — pinned transport/context/error tests             |
| 5   | Bounded HTTP/HTTPS/header observations, no scope escape              | PASS — wire/fallback/redirect tests                     |
| 6   | Actual numeric destination pinning enforced                          | PASS — socket connect/SNI/getaddrinfo assertions        |
| 7   | Private/special/rebinding/redirect/port/arbitrary-target defenses    | PASS — negative matrix                                  |
| 8   | Quotas/concurrency/deadlines/restart lifecycle                       | PASS — concurrent API/workers + actual SIGKILL recovery |
| 9   | Honest partial failure and preserved successful evidence             | PASS — backend/browser tests                            |
| 10  | Frontend start/progress/details/history                              | PASS — React + rendered browser journey                 |
| 11  | No fabricated live results/scores/CVEs/customer claims               | PASS — fixtures isolated/labeled; no Phase 05 engine    |
| 12  | Phase 00–03 and design preserved                                     | PASS — regression suites and screenshot review          |
| 13  | Migrations/tests/lint/types/format/build/audits/Docker/browser       | PASS — commands above                                   |
| 14  | Documentation/screenshots/manual setup/limitations                   | PASS — report/design/README/evidence                    |
| 15  | No Phase 05, push or public deployment                               | PASS — local scope only                                 |

Separate acceptance demonstration: **LIVE team-owned domain/DNS-provider/network E2E —
NOT TESTED**. Passing controlled implementation gates is not a claim that this live exercise
occurred. Screen readers, physical mobile devices, Firefox/Safari and public hosting are also
NOT TESTED. Automated axe is not a full accessibility certification or penetration test.

## Limitations and manual next actions

No authorized live domain supplied. The exact-host/CNAME refusal and one-address policy
can yield inconclusive results for CDNs, aliases and multi-address deployments. Header rules
are intentionally narrow; no body/application logic/cipher inventory assessment. No DNSSEC
validation, DKIM selectors, SPF expansion or whole-company security guarantee. OS resolver,
CA store, system clock and network routing are trusted. Local Compose uses application
network guards, not a deployment-level egress firewall. SQLite, one global worker slot,
existing in-process auth/IP limiting and local HTTP cookies remain academic-MVP constraints;
production requires the documented HTTPS/edge/shared-limiter/audit-retention review. The
worker has process/restart supervision and lease recovery, no independent health endpoint.

The user must supply actual permission and DNS-provider access for a live demonstration;
no arbitrary public target is substituted. In the normal stack, register/login, create a
workspace, add the authorized exact domain, publish its separate current TXT challenge,
Verify ownership, choose Run security checks, then review timestamps/outcomes and history.
Use `docker compose up --build --wait`; open http://127.0.0.1:5173/app/assets.
Manual startup adds `uv run python -m app.scanner.worker` beside the existing API/Vite commands.
`docker compose down` preserves data; never add `--volumes` unless intentionally erasing it.

## Git and phase handoff

All Phase 04 changes, source, tests and evidence are committed locally on `main` after passing
verification. The final response records the exact commit hash and clean status. No push
or public deployment was performed. Phase 05 is **NOT STARTED** and requires explicit approval.
