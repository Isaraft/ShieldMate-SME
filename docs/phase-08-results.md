# Phase 08 — Local release candidate completion report

Implemented on `main` from clean Phase 07.1 baseline **`e2c58b6`**. Verification ran 24 October 2026 UTC / 24–25 October Asia/Almaty. The deliverable is a local security/reliability release candidate, not an internet deployment. The final local commit is the commit containing this report (`git log -1 --format='%h %s'`); no push, tunnel, public exposure or Phase 09 work was performed.

## Implementation and review

Read the complete Phase 08 brief (retained as `PROMPTS/PHASE_08.md`), AGENTS, MVP spec, roadmap, architecture/scanner/reports/testing docs and Phase 07/07.1 reports, then reviewed actual auth, organization scopes, database constraints/migrations, domain proof, scanner transport/queue, deterministic findings, task events, report storage/rendering, frontend state and Docker/Nginx. The baseline passed before changes: **314 backend tests**, **93 frontend tests**, lint/types/format/build, Alembic head/no drift and normal Docker health. Baseline evidence is retained under `evidence/phase-08/checks/baseline/`.

Confirmed issues fixed: session CSRF reads invalidating another tab; unexpected exceptions escaping into the server traceback boundary; trusting declared rather than actual ASGI body length; stale tenant content/drafts during identity transitions; untranslated domain status. Additional defenses bound anonymous session bootstrap, explicitly reject newer special IPv6 ranges, separate development/RC cookies, validate local origins/settings, add storage/schema readiness and harden the same-origin proxy. No credible high/critical tenant or SSRF bypass was confirmed in the inspected scope. The detailed threat model, exploit preconditions, evidence and residual risks are in `phase-08-risk-register.md`; passing tests are not a general security guarantee.

The optional standalone `compose.local.yaml` uses compiled frontend assets, same-origin Nginx/API, unpublished backend/worker ports, loopback-only frontend, non-root users, read-only roots, dropped capabilities, private storage directories and umask077. `/health/ready` detects unavailable/stale storage separately from liveness. `app.maintenance` implements deadline-bound SQLite online snapshots, integrity/foreign-key/schema/PDF hash checks and exclusive atomic publication. Restore refuses existing destinations/sidecars and uses a new isolated volume. No new schema, dependency, framework or product feature was added. Historical migrations remain byte-identical to the baseline.

The burgundy/red visual system, typography and Phase 07.1 CSS/PDF renderer remain intact. One raw status badge now uses the shared dictionary. EN/RU/KK catalog additions cover the new fixed errors. Customer text and exact technical identifiers remain unmodified; independent native-speaker review is pending.

## Changed files

- Runtime/security: `backend/app/auth.py`, `config.py`, `errors.py`, `main.py`, new `http_security.py`, `api/readiness.py`, `maintenance.py`, `scanner/policy.py`.
- Container/runtime configuration: `backend/Dockerfile`, `backend/deploy/entrypoint.sh`, `frontend/nginx.conf`, `compose.local.yaml`, `.env.local.example`, `.env.example`, `.gitignore`.
- Frontend identity boundary and localization: `frontend/src/sessionEvents.ts`, `authApi.ts`, `pages/Account.tsx`, `pages/Assets.tsx`, three shared backend locale catalogs.
- Meaningful regressions: new backend hardening/maintenance/owned-loopback transport tests; task atomic-rollback assertion now verifies a sanitized 500 instead of an escaped exception; frontend session-boundary tests and three-language domain-status tests.
- QA tools: `scripts/check-secrets.py`, Phase 08 fixture override/server/worker, browser workflow/interactions/operations/report-button scripts, PDF validator and contact sheets. QA modules are mounted only for tests and absent from the release images.
- Handoff: this report, risk register, local-release and defense runbooks; updated README/current architecture/testing and a historical note on the superseded Phase 02 CSRF behavior; actual screenshots/PDFs/check logs.

`evidence/phase-08/checks/changed-files.txt` records the final staged file list, including evidence artifacts. No unrelated user changes were present initially or overwritten.

## Exact checks and results

Commands below ran from the stated directory; redirections only stored their actual output. Logs live in `evidence/phase-08/checks/`. Optional browser tool paths are environment-specific (see runbook); no app dependency was added for QA.

| Directory | Actual command | Final result |
|---|---|---|
| backend | `.venv/bin/pytest -q` | **325 passed**, 1 pre-existing Starlette/httpx deprecation warning, 69.53s |
| backend | `.venv/bin/ruff check .` | PASS |
| backend | `.venv/bin/ruff format --check .` | PASS, 75 files formatted |
| backend | `.venv/bin/mypy app` | PASS, 51 source files |
| frontend | `npm test -- --reporter=json --outputFile=../../../work/phase08/audit/frontend-tests.json` | **98 passed**, 0 failed |
| frontend | `npm run lint` | PASS, zero ESLint warnings |
| frontend | `npm run typecheck` | PASS |
| frontend | `npm run format:check` | PASS |
| frontend | `npm run i18n:check` | PASS, **976 keys ×3**, 576 UI references, no missing keys/placeholder mismatch |
| frontend | `npm run build` | PASS; existing >500kB chunk-size warning (648.95kB JS / 184.13kB gzip) |
| frontend | `npm audit --json` | PASS, **0 vulnerabilities**, 347 dependency records |
| backend | `.venv/bin/pip-audit --format json` | PASS, **68 packages**, 0 known vulnerabilities |
| root | `backend/.venv/bin/python scripts/check-secrets.py` | PASS, no high-confidence signature matches; working-tree text only, excludes history/binaries |
| root | `git diff --exit-code e2c58b6 -- backend/migrations` | PASS, historical migrations unchanged |
| root | `docker compose -f compose.local.yaml exec -T backend .venv/bin/alembic current` | `f34f9df9b6a4 (head)` |
| root | `docker compose -f compose.local.yaml exec -T backend .venv/bin/alembic check` | PASS, no new upgrade operations |
| root | `SHIELDMATE_RC_PORT=15873 docker compose -p shieldmate-phase08-qa -f compose.local.yaml -f scripts/qa/phase08.override.yaml up -d --build --wait` | PASS, isolated fixture build/start/health |
| root | `docker compose -f compose.local.yaml up -d --wait` (and final `up -d --build --wait`) | PASS, actual compiled localhost RC |
| root | `docker compose -f compose.local.yaml exec -T frontend nginx -t` | PASS |
| root | `node scripts/verify-phase-08.cjs` | PASS, **399 rendered/axe views**, 5 product/security/recovery flow groups, 12 report samples, 0 page errors |
| root | `node scripts/verify-phase08-interactions.cjs` | PASS, **132 additional rendered/axe views**, keyboard/menu/dialog/filter/error/form tests in EN/RU/KK |
| root | `node scripts/verify-phase08-report-ui.cjs` | PASS, **3 actual localized generate-button/browser-download flows**, retry after controlled error, **12 demo-step interactions**, 0 page errors |
| root | `node scripts/verify-phase08-operations.cjs` | PASS, consistent backup + isolated restore, original session/data/private PDFs, RC headers/Host/body/deep links, non-root/modes, failed migration exits before HTTP |
| root | `backend/.venv/bin/python scripts/verify-phase-08-pdfs.py` | PASS, **12 PDFs / 135 pages**, extraction, bounds, non-overlap, embedded fonts, Kazakh glyphs, per-page QA/DEMO markers and API hashes |
| root | `backend/.venv/bin/python scripts/phase08-contact-sheets.py` | PASS, all rendered PDF review sheets; stale prior sheets removed |
| root | `frontend/node_modules/.bin/prettier --check scripts/verify-phase-08.cjs scripts/verify-phase08-operations.cjs scripts/verify-phase08-interactions.cjs scripts/verify-phase08-report-ui.cjs compose.local.yaml scripts/qa/phase08.override.yaml` | PASS |
| root | `backend/.venv/bin/ruff check --config backend/pyproject.toml scripts/check-secrets.py scripts/verify-phase-08-pdfs.py scripts/phase08-contact-sheets.py scripts/qa/phase08_server.py scripts/qa/phase08_worker.py` and matching `ruff format --check` | PASS |
| root | `git diff --check` | PASS |

A separate network-disabled, read-only container checked the retained `shieldmate-phase071-qa_database`: **41** ready PDF blobs match their stored SHA256s; **all 6** records in the committed prior-phase manifest still match. The normal development DB had no ready reports and was left untouched. Container Python 3.13 also rejects the added special IPv6, loopback, metadata and mapped-address cases. The release image has no `/app/scripts` QA modules.

Failures found during verification were corrected, not counted as passes: one full-suite test expected an exception to escape rather than the new safe 500 (rollback assertions retained); Ruff found import/line formatting; an initial Nginx regex needed quoting; the QA restart helper initially omitted its port setting (real Origin rejection), readiness polling initially failed on an expected transient 502, and a fixture count assertion raced asynchronous finding evaluation. The final clean fixture run passed after fixing those harness waits/configuration. An unsupported initial pip-audit `--disable-pip` invocation was replaced with its valid installed-environment command. No security control was bypassed to accommodate QA.

## Security, integrity and recovery evidence

Backend coverage preserves password/expiry/revocation, Origin/CSRF, IDOR/relationship isolation, invalid inputs/quotas, domain challenge concurrency/expiry, all scanner DNS/TLS/HTTP hostile cases, lifecycle deduplication/resolution/reopening, task version/event atomicity, immutable reports and renderer failure checks. New tests exercise actual ASGI body mismatches, marker-safe errors, stable cross-tab CSRF, bootstrap quotas, readiness, cookie namespaces, real SQLite allocation-full rollback, committed-WAL snapshots and no-partial backup publication.

The Docker browser path creates a real account/workspace, records explicit consent, uses injected TXT proof, queues a real persisted scan around **synthetic DNS/socket responses**, views findings/Top 3, creates/edits a task and confirms that done does not resolve its finding. A subsequent conclusive clean fixture resolves technical findings without changing old PDF bytes. Cross-tenant reads of eight domain/scan/finding/assessment/task/report/download resources return 404; missing CSRF and hostile Origin reject writes. Actual same-browser tabs clear tenant A drafts on logout and deny A's old task after login B.

An actual worker SIGKILL leaves **4 persisted observations**, then the real 90-second lease recovers to `interrupted`; restarting does not duplicate/retry it. A controlled unsafe-destination scan fails closed. A separate real owned loopback HTTP service verifies HEAD/Host, no redirect follow and no application-body consumption; production target policy still rejects loopback. No public host was scanned.

The online backup and isolated restore have identical SHA256 **`70cac2a18d6bba28c5df184ba4db7ff3a1ce35a35a0650f2eb9edcc2de23668e`**, integrity/foreign-key/schema/PDF checks and table counts: **4 users, 4 organizations, 9 domains, 9 scans, 108 observations, 34 finding records, 40 finding events, 1 task, 2 task events, 9 saved reports**. Seven original/restored API projections agree; three private report downloads match their original hashes; an existing session and done task work after restore. A later separate report-button rehearsal creates another synthetic account; the backup is the earlier consistent snapshot, not a claim to include later writes. Existing destinations are refused. An invalid migration exits 255 and never starts Uvicorn. Physical host disk exhaustion was not induced: real SQLite allocation caps and injected backup I/O errors exercise those failure paths safely.

## Visual/localization/PDF verification

**531 rendered/axe views**, EN/RU/KK, widths **360, 390, 768, 1024, 1280, 1440, 1920**. The main matrix includes landing/auth, dashboard, assets/scans, findings/details, tasks/details, reports/settings, demo/404 and empty workspaces. Supplemental checks cover filters with canonical values, language/form retention, all-width landing/dashboard/report screenshots, native dialog placement/keyboard/Escape/focus restoration, mobile menu and report errors. No overflow or WCAG A/AA-tagged axe violations were detected in those views. Reduced motion, visible keyboard focus and 200% text enlargement pass. Axe does not certify all accessibility needs.

Actual PNGs and nine cross-width review sheets were inspected for typography, wrapping, spacing, hierarchy and navigation. Hero lines do not overlap; step numerals remain vertically centered within 2px. Long company names and literal `<script>` text remain escaped and wrap. The Codex in-app browser independently opened the **compiled 8080** landing, switched to Kazakh, navigated the clearly labeled demo and its PDF step, and was visually inspected. This is an additional local smoke check, not Safari/Firefox or independent human beta evidence.

All **12 final PDFs** were rasterized and visually reviewed through **17 sheets**, with full-size page samples checked for glyphs/readability. Short reports have **8/9/9** pages (EN/RU/KK); long **24/26/26**; partial/long-name edge cases **5/5/5**; DEMO **6/6/6**. The long reports keep the executive summary and Top 3 on page 1; supporting finding evidence and full check inventory remain available. No new page cap or evidence removal was introduced. Existing safety limits remain. Headers/footers, repeated table headers, evidence wrapping, whitespace and selectable Kazakh/Cyrillic text are preserved. Some final appendix pages contain few rows; that natural continuation is preferable to discarding evidence or shrinking type. No PDF/UA or professional print certification is claimed.

See `evidence/phase-08/checks/visual-review.md`, `browser-matrix.json`, `interactions.json`, `pdf-validation.json`, actual `screenshots/` and `pdf-pages/`. All QA artifacts are synthetic and visibly labeled. Immutable technical source strings/customer-entered names are intentionally not translated. Native RU/KK linguistic certification is **NOT TESTED**; a reviewer checklist is supplied in the risk register.

## Acceptance gates

| Gate | Result | Evidence / qualification |
|---|---|---|
| A01 Existing functionality/migrations | PASS | 325/98 tests; old migration diff empty; 41 historical PDF hashes retained; original dev DB untouched |
| A02 Threat model/risk review | PASS | Ranked `phase-08-risk-register.md`, actual code paths and pre-fix evidence |
| A03 Auth/session/CSRF/tenant attacks | PASS | Full negative suites, eight Docker IDOR denials, stable CSRF and actual two-tab account change |
| A04 Proof/eligibility/concurrency/expiry | PASS | Existing domain/scan adversarial and transaction suites preserved; current proof/consent enforced |
| A05 SSRF/rebinding controlled cases | PASS | Numeric pinning/peer/SNI/DNS/TLS tests, added ranges, owned parser service; external firewall remains future work |
| A06 Evidence/Top 3/task lifecycle | PASS | Shared priority IDs, task done ≠ finding resolved, conclusive clean scan, dedup/history tests |
| A07 Report history/private access/demo | PASS | Cross-tenant download denial, immutable bytes/history, report UI downloads, demo separation and per-page labels |
| A08 Three-language important flows | PASS | 976-key parity, actual UI generation/downloads/form state/filter checks; native review pending |
| A09 Actual responsive visual inspection | PASS | 531 rendered checks, seven widths ×3 languages; saved images and reviewed cross-width sheets |
| A10 EN/RU/KK PDF rendering | PASS | 12 PDFs, 135 rendered pages, 17 inspected sheets, glyph/extraction/bounds/hash checks |
| A11 Compiled localhost runtime | PASS | Actual Nginx static build on loopback8080, unpublished API/worker ports, same-origin cookies/CSRF/deep links |
| A12 Safe backup/isolated restore | PASS | Consistent online snapshot, identical verified restore, original account/data/history/private PDF access; no overwrite |
| A13 Build/lint/types/migrations/audits | PASS | Exact commands above; deprecation/chunk-size warnings and audit scope disclosed |
| A14 Docker restart/persistence/failure | PASS | Real SIGKILL/lease recovery, API restart, restored DB, failed migration and storage/renderer tests |
| A15 Defense walkthrough/runbooks | PASS | Tested browser journey and in-app smoke review; 5–8 minute guided runbook/troubleshooting supplied; second human timed rehearsal pending |
| A16 Truthful data/local scope | PASS | Explicit synthetic fixtures, no uncontrolled scans, push, tunnel, public deploy or Phase 09 |
| A17 Unavailable external tests labeled | PASS | **Owned-domain TXT + external HTTPS E2E: NOT TESTED**; external browser/native reviewer/assistive checks explicitly pending |
| A18 Explained/committed local Git state | PASS | Focused local phase commit after verification; clean final tree checked; no push |

## Local handoff and remaining limits

Start: `docker compose -f compose.local.yaml up --build -d --wait`, then <http://127.0.0.1:8080>. The RC remains running. Disposable QA/restore stacks are stopped after evidence collection, with their private volumes retained. The original normal development stack/volume is preserved. Do not combine fixture overrides with a valuable real company workspace.

Read `local-release-runbook.md` for exact start/stop/migration/log/backup/no-overwrite restore commands and local HTTP cookie exceptions. Read `defense-demo-runbook.md` for the guided product flow and truthful offline fallback. Backups/session state/credentials remain in private Docker volumes or ignored operator work, not the repository.

Before internet exposure: real owned-domain DNS/TXT/TLS E2E with explicit owner permission; independent native RU/KK review; supported external browsers, physical devices and screen readers; TLS/trusted-proxy/Origin/cookie architecture; network egress firewall; monitoring, durable abuse controls and encrypted/retained operator backups. No independent penetration test, SME beta cohort, load test, base-image CVE scan, PDF/UA audit, physical disk exhaustion or external deployment was performed. Single SQLite writer/worker, process-local abuse limits, aggregate proxy IP, registration 409 enumeration, conservative CNAME refusal, snapshot PSL and SPA HTTP200 404 routing remain documented local-MVP limitations. Public deployment and Phase 09 require explicit approval.
