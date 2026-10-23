# Phase 05 — Evidence-Backed Finding Engine & Contextual Prioritization

## Baseline and scope

Baseline verified on `main` at `a40e4be`, with a clean working tree and Alembic
`1806ce4b7076`. Before changes: **199 backend tests and 41 frontend tests passed**;
Ruff, mypy, frontend lint/typecheck/format/build passed. The uploaded Phase 05 brief was
read in full and preserved verbatim as `PROMPTS/PHASE_05.md` (SHA-256
`6737ed3246e758b0d80071c762a773e3e3e3158af1eed6b2049e356a677cfe5d`).
Repository rules, MVP spec, phase roadmap, design system, scanner architecture and Phase 04
results were reviewed. Existing authentication, ownership proofs, scanner transport and
burgundy/red identity are preserved. This is Phase 05 only; Phase 06 is **NOT STARTED**.

## Architecture, ranking and rule decisions

`app/findings/` separates typed contracts, allowlisted normalization, pure evaluation,
immutable editorial rule definitions, transactional reconciliation, schemas and read APIs.
It consumes actual saved `starter-checks-1` observations; it performs no DNS or socket I/O.
Policy `starter-risk-1` records its version in assessments, findings and history snapshots.

Six rule IDs are implemented:

| Rule                     | Supported conclusion                                                                 | Priority/context                                                              |
| ------------------------ | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| `TLS_CERTIFICATE_ACTION` | Precise trust rejection or source-time renewal deadline                              | High for specific trust errors / renewal within 7 days; Medium within 30 days |
| `HTTP_ROOT_REDIRECT`     | Inspected root HTTP did not immediately redirect, with working trusted HTTPS context | Low, contextual; no redirect followed                                         |
| `HTTPS_HSTS`             | Missing/basic-review HSTS on inspected trusted HTTPS root                            | Low, contextual; no exploitation claim                                        |
| `HTTPS_NOSNIFF`          | Missing/unexpected nosniff on that inspected response                                | Low, conditional hardening; content type unknown                              |
| `DNS_SPF_MULTIPLE`       | More than one saved SPF version policy                                               | Medium, conclusive multiplicity; mail-use impact conditional                  |
| `DNS_DMARC_POLICY`       | Basic malformed DMARC or missing/monitor policy with limited MX context              | Medium malformed; Low contextual missing/monitor-only                         |

Missing MX, generic TLS failures, missing SPF without outbound-mail proof, CSP effectiveness,
XSS, CVEs and unavailable HTTPS inferred from timeouts are deliberately not asserted.
MX is weak mail context and cannot distinguish Null MX; recommendations disclose that caveat.
Phase 04's SPF count-zero `attention` can clear _multiplicity only_: the collection outcome is
not the rule decision, and the result never claims SPF validity. Precise TLS trust errors can
support a finding despite an `inconclusive` collection label; generic failures cannot.

The server orders open records by severity, urgency, observed relevance, confidence, latest
issue time and stable fingerprint. Up to three actual records are returned from the same
filtered query as the table; fewer records produce fewer priorities. Changing table sort
cannot change the priority rubric. Business impact, next action, severity reasoning, confidence,
source evidence and limitations are visible. No numerical posture score is calculated.
See [the complete rule conditions, thresholds and worked examples](risk-methodology.md).

## Persistence and lifecycle

Additive migration **`9752376ee8f2`**, after `1806ce4b7076`, adds `findings`,
`finding_evaluations` and `finding_events`; no previous migration was edited. Unique
organization/fingerprint and run/policy keys, tenant-safe joins and query indexes support
consistent storage. A SQLite `BEGIN IMMEDIATE` transaction publishes each evaluation and
all derived changes atomically. API summaries use a single read snapshot.

The existing worker reconciles up to five eligible terminal sources each loop. In-flight
sources wait; completed/partial/failed/interrupted sources support only conclusive applicable
rules. Unknown versions and authorization-changed sources cannot manufacture assertions.
A later supported issue updates the same identity and preserves first detection. Comparable
same-rule clear evidence resolves it; repeated clear evidence preserves the original
resolution time. Recurrence reopens that identity with resolution history intact. Unknown,
missing or inapplicable evidence preserves status and annotates Not rechecked.

Equal-second chronology uses SQLite insertion order, not random UUID ordering. Out-of-order
older assessments are archived with `applied=false` and cannot overwrite a newer clean state.
Normal backfill is chronological. A rolled-back/crashed transaction is safely retried.

Current records are bounded to six per asset. Event history is capped at 50 per finding,
retaining first detection, latest resolution/reopening and recent events with a visible
compaction notice. Source retention remains Phase 04's bounded policy. Finding/event evidence
snapshots survive source pruning; dead source links become an explicit unavailable message.
Deleting an asset cascades derived records, with confirmation copy disclosing this behavior.
Staleness defaults to seven days and is configurable; expired ownership proof does not erase
historical evidence or grant permission for another scan.

Explicit local maintenance, from `backend/`:

```sh
.venv/bin/python -m app.findings.backfill --organization-id YOUR_ORGANIZATION_UUID
```

The same command is available with `uv run python`, or from the root:

```sh
docker compose exec -T backend .venv/bin/python -m app.findings.backfill --organization-id YOUR_ORGANIZATION_UUID
```

It accepts only an organization UUID, uses stored sources and performs no network requests.
Repeated browser QA backfill after processing reported **Evaluated 0 terminal scans**.
Retained historical Phase 04 runs are eligible automatically; pruned sources cannot be recovered.

## APIs, screens and changed files

- `GET /api/v1/findings`: paginated list, exact scoped counts, server Top 3, domain options and
  source/rule coverage bundled in one response. No redundant summary/priorities endpoints.
- `GET /api/v1/findings/{finding_id}`: evidence, impact/action, rationale, confidence,
  current lifecycle, timestamps, provenance and bounded history.
- `GET /api/v1/findings/assessments/{scan_id}`: source coverage, six policy decisions,
  evaluation version/state and applied flag.
- Filters validate status/severity/category/freshness, domain/scan UUIDs, four sort options,
  offset 0–10000 and limit 1–50. Unknown fields/enums fail validation. Ownership comes from
  the session. Foreign asset/scan/finding IDs return 404; unauthenticated reads return 401.
  There are no finding mutation, fake-resolution or evidence-submission endpoints.
- `/app/findings` and `/app/findings/:findingId`: real connected list/detail, filters,
  pagination, review modes, stable priorities, source links and honest loading/empty/pending/
  partial/stale/unsupported/error states. Polling stops after terminal evaluation.
- Reusable `AssessmentSummary`, `PrioritySummary`, `FindingFilters`, `FindingEvidence` and
  `ReviewMode` components use existing primitives, tokens, Plex UI typography and navigation.
  Anton display branding, deep burgundy, red and warm ivory remain intact.

Principal changes: new backend findings module, three ORM models, additive migration and
58 new backend test cases; typed frontend API, two pages, five reusable components, styles
and nine new frontend tests; worker reconciliation hook, route registration, source-scan link,
asset deletion disclosure, stale setting, QA harness/evidence and project documentation.
No new dependencies or lockfile changes. Scanner network policy/transport/check implementations,
authentication and CSRF code were not changed. See Git diff for the complete file list.

## Exact final commands and actual results

Commands below ran from the repository root unless noted. Existing virtual environments and
locked dependencies were reused. Baseline commands were also run before implementation.

| Command                                                            | Actual final result                                                             |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| `cd backend && .venv/bin/pytest`                                   | **257 passed**, 46.42 seconds; one existing Starlette/httpx deprecation warning |
| `cd backend && .venv/bin/ruff check .`                             | All checks passed                                                               |
| `cd backend && .venv/bin/ruff format --check .`                    | 48 files already formatted                                                      |
| `cd backend && .venv/bin/mypy app`                                 | No issues in 32 source files                                                    |
| `cd backend && .venv/bin/alembic upgrade head`                     | Success, head `9752376ee8f2`                                                    |
| `cd backend && .venv/bin/alembic check`                            | No new upgrade operations detected                                              |
| `cd backend && .venv/bin/pip-audit --progress-spinner off`         | No known vulnerabilities found                                                  |
| `npm test --prefix frontend`                                       | **50 passed**, seven test files                                                 |
| `npm run lint --prefix frontend`                                   | Passed, zero warnings                                                           |
| `npm run typecheck --prefix frontend`                              | Passed                                                                          |
| `npm run format:check --prefix frontend`                           | All matched files use Prettier style                                            |
| `npm run build --prefix frontend`                                  | Passed; 64 modules, JS 293.59 kB and CSS 28.76 kB before gzip                   |
| `npm audit --audit-level=low --prefix frontend`                    | Zero vulnerabilities                                                            |
| `backend/.venv/bin/ruff check scripts/qa/phase05_seed.py`          | Passed after fixing two QA-only unused imports                                  |
| `backend/.venv/bin/ruff format --check scripts/qa/phase05_seed.py` | Passed                                                                          |
| `docker compose config --quiet`                                    | Passed                                                                          |
| `docker compose up --build --wait`                                 | All three images built; backend, frontend and worker healthy                    |
| `docker compose exec -T backend .venv/bin/alembic current`         | `9752376ee8f2 (head)`                                                           |
| `docker compose exec -T backend .venv/bin/alembic check`           | No new upgrade operations detected                                              |
| `docker compose exec -T backend id`                                | UID 10001                                                                       |
| `docker compose exec -T worker id`                                 | UID 10001                                                                       |
| `docker compose exec -T frontend id`                               | UID 101                                                                         |
| `git diff --check`                                                 | Passed before commit                                                            |

Host Node emitted an existing `module.register()` deprecation warning during build. Docker's
Node 24 production build passed. No warning was hidden or upgraded into a correctness claim.
Audits are a time-limited advisory check, not a penetration test or proof of security.

The backend additions comprise 41 pure rule cases and 17 integration cases. They verify
precise vs generic errors; header inspection context; expiry boundaries; mail-less/Null-MX
limits; malformed/missing/versioned evidence; deterministic ordering; first/repeat/severity/
resolution/reopening; incomplete scan preservation; atomic crash rollback; concurrent
processors/read snapshots; chronological and out-of-order processing; migration preservation;
retention/compaction/deletion; staleness/proof expiry; tenant IDOR and filter boundaries;
redaction and zero evaluator network activity. All original scanner SSRF/rebinding/pinning,
DNS proof, session, Origin/CSRF and migration tests remain in the passing full suite.
Frontend additions cover counts/short priority lists, filters/provenance, mode/escaped text,
empty/stale/not-rechecked/resolved states, polling termination, failure/retry and session expiry.

## Browser, responsive and accessibility evidence

Tooling lives outside application dependencies: Playwright 1.62.1, Chromium
151.0.7922.34 and axe-core 4.14. Browser scripts used the production frontend image.
Browser environment was loaded with `source ../../work/browser-env.sh`.

```sh
# Phase 05: injected saved observations, real reconciliation worker, isolated volume
 docker compose -p shieldmate-phase05-qa -f scripts/qa/phase05.compose.yaml up --force-recreate --wait
 node scripts/verify-phase-05.cjs

# Original public and account journeys against ordinary local Compose
 EVIDENCE_DIR="$PWD/docs/evidence/phase-05/public-regression" node scripts/verify-phase-01.cjs
 EVIDENCE_DIR="$PWD/docs/evidence/phase-05/auth-regression" node scripts/verify-phase-02.cjs

# Scanner/domain regression: separate injected DNS/socket worker, no external scans
 docker compose -p shieldmate-phase04-qa -f scripts/qa/phase04.compose.yaml up --force-recreate --wait
 BASE_URL=http://127.0.0.1:15273 EVIDENCE_DIR="$PWD/docs/evidence/phase-05/scan-regression" node scripts/verify-phase-04.cjs
 BASE_URL=http://127.0.0.1:15273 EVIDENCE_DIR="$PWD/docs/evidence/phase-05/domain-regression" node scripts/verify-phase-03.cjs
```

All scripts completed successfully. **68 route/viewport checks**: 20 findings, 16 public,
12 account, 16 scanner and four domain checks at **360, 768, 1280 and 1920 CSS px**.
No horizontal overflow or tested axe A/AA violations; no browser page errors. Public token
contrast minimum was **5.09:1**. Keyboard focus, native disclosures, review modes, navigation,
filters, confirmation dialogs and reduced motion were checked. The public suite includes
404 recovery. Automated axe results are not a full accessibility certification.

The findings journey uses actual registration, session, organization and ownership routes,
explicit injected TXT proof and synthetic persisted Phase 04-shaped observations. The real
worker creates six findings and three priorities matching API identities/counts exactly.
Reload is stable; filters produce one real priority; partial sources preserve all six as Not
rechecked; clean sources resolve all six and produce zero priorities; recurrence preserves
IDs/first-seen and records reopening. Backend/worker restart preserves sessions/history;
backfill is idempotent. A second stale asset and controlled API outage/retry are verified.

Screenshot inspection found and fixed a 360px table-caption wrapping defect missed by axe
and overflow checks; a caption-width assertion now guards it. Certificate epochs also show
readable dates/timezones. Investigation of an intermittent browser assertion found its wait matched the old list
heading before navigation committed. It now waits for the detail URL and unique detail
container and loaded source observations, then checks the native disclosure state; the final clean browser pass succeeded. These fixes were made
before completion, not left as known defects.

Evidence is in `docs/evidence/phase-05/`:

- [Findings desktop](evidence/phase-05/findings-1280.png),
  [findings mobile](evidence/phase-05/findings-360.png),
  [technical detail](evidence/phase-05/detail-1280.png).
- [Resolved state](evidence/phase-05/resolved.png),
  [reopening history](evidence/phase-05/lifecycle-history.png),
  [stale state](evidence/phase-05/stale-768.png),
  [error](evidence/phase-05/error.png),
  [pending](evidence/phase-05/pending.png).
- [Machine-readable findings results](evidence/phase-05/browser-results.json) and regression
  subdirectories retain their own JSON and screenshots.

**These are visibly labeled LOCAL QA fixtures, never live security evidence.** No production
seed route, demo inventory, real-domain probe, fabricated tester or successful-remediation
claim was added. QA modules are mounted only in isolated test containers and are absent
from shipped images. Temporary QA stacks were stopped after verification; volumes preserved.

## Acceptance gates

| Gate                                            | Status | Evidence                                                                                |
| ----------------------------------------------- | ------ | --------------------------------------------------------------------------------------- |
| 1. Baseline and previous work preserved         | PASS   | Clean `a40e4be`; baseline 199/41; full regression and earlier browser journeys          |
| 2. Typed deterministic offline evaluator        | PASS   | Contracts, policy/version, pure rule tests and forbidden-network test                   |
| 3. Defensible conclusions/unknown handling      | PASS   | Six documented rules; missing/ambiguous/timeout/context cases                           |
| 4. Complete evidence-backed finding explanation | PASS   | Connected detail/priority components and screenshots                                    |
| 5. Explainable stable server Top 3              | PASS   | Ordered rubric, API tests and identity-stable browser reload                            |
| 6. Honest coverage and score discipline         | PASS   | Collection vs rule counts, missing-data states, no numerical score                      |
| 7. Tenant-scoped persistence/additive upgrade   | PASS   | Migration preservation, IDOR, durable snapshots/history                                 |
| 8. Dedup/retry/backfill/crash/restart           | PASS   | Unique transactions, concurrency/rollback tests and Docker restart/backfill             |
| 9. Confirmed resolution and reopening           | PASS   | Same-rule lifecycle tests; partial/error retention; browser recurrence                  |
| 10. Protected validated read APIs               | PASS   | Typed schemas, bounds/unknown filters and finding/scan/domain IDOR tests                |
| 11. Connected screens and truthful states       | PASS   | Nine new frontend tests and full local fixture journey                                  |
| 12. Design/responsive/accessibility             | PASS   | Preserved identity; 68 viewport checks, axe, keyboard and visual review                 |
| 13. Security boundaries and bounded evidence    | PASS   | Original scanner/auth/CSRF suite plus redaction/no-network/retention tests              |
| 14. Actual required verification                | PASS   | Commands/results above, Docker health/restart and zero-advisory audits                  |
| 15. Complete documentation/fixture distinctions | PASS   | This report, methodology, README, architecture and labeled evidence                     |
| 16. Local commit and clean status; scope limits | PASS   | Local Phase 05 commit on main; clean verification after commit; no push/deploy/Phase 06 |

## Limitations and manual actions

- **NOT TESTED: real freshly verified, team-owned domain E2E.** None was supplied. No external
  network access is needed for Phase 05; no third-party domain was scanned to fill this gap.
- **NOT TESTED:** real screen-reader/physical-device use, Firefox/Safari and real SME beta
  comprehension testing. Chromium keyboard/axe results do not substitute for those checks.
- This is a limited external configuration policy, not full site/company security, CVSS,
  compliance or exploitation validation. No score, Critical/CVE finding, business-criticality
  inference, task CRUD, report generation, payment or Phase 06 dashboard is implemented.
- Saved source dates describe observation time, not present certificate status. Weak mail
  context and uncollected HTML/content-type data constrain conclusions as documented.
- Event compaction/source pruning deliberately bound history; export needed research evidence
  before removing assets. Source-order/read-lock behavior is SQLite-specific and requires
  review before a future database migration or multi-worker deployment.
- Existing Phase 04 local Compose has no infrastructure egress firewall; its application
  pinning and strict network boundary tests remain intact. No production-readiness or
  public-deployment claim is made.

## Local preview and Git handoff

From the repository root:

```sh
docker compose up --build --wait
```

Open <http://127.0.0.1:5173/app/findings>. Sign in/create an account and organization.
For live sources, enroll only an authorized team-owned exact domain, publish/verify the real
TXT proof and run its bounded checks from Assets. The worker derives findings automatically.
Without source scans, the page honestly shows no assessments. Do not load QA data into the
ordinary application. Backend health is <http://127.0.0.1:8000/api/v1/health>.
Manual development/startup and worker commands are in README. `docker compose down` preserves
data; never add `--volumes` unless intentional deletion is required.

Baseline: `a40e4be`; branch: `main`. Final local commit is the commit containing this report,
with message **Implement Phase 05 evidence-backed findings and priorities**; its exact hash
and final `git status --short` are reported in the handoff. No push, public deployment or
Phase 06 work was performed.
