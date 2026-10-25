# Phase 09 — Engineering ready; human validation pending

**Date:** 25 October 2026, Asia/Almaty. **Branch/baseline:** clean `main` at `e9c7db4` before modifications. The ending local commit is the commit containing this report (`git log -1 --format='%h %s'`); final Git status was checked after committing. No push, public deployment, tunnel, recruitment messages or Phase 10 work was performed.

**Research status: HUMAN ALPHA NOT CONDUCTED; REAL BETA NOT CONDUCTED; HYPOTHESIS PROPOSED, NOT TEAM-ADOPTED.** No participant, interview, consent, survey answer, observed task time, quotation or business result was invented. Automated fixtures/unit cases are engineering tests, not real people. The academic assignment is not complete merely because the kit/code is ready.

## Preparation, source alignment and baseline

Read the entire attached Phase 09 brief (retained as `PROMPTS/PHASE_09.md`), AGENTS, MVP specification, roadmap, current architecture/security/scanner/reporting documentation, Phase 08 report/risk register, local release/restore and defense procedures, actual demo/UI/test harnesses. The actual three-page “Assignment 5: Creating an MVP” course PDF was found in Downloads and read completely. Its path/SHA256, requirements and clarifications are recorded in `testing/assignment-05-mapping.md`.

The source agrees with the brief's major requirements; the mapping also retains original details omitted from the brief's summary:≥3 sources (two academic and one actual course lecture), Times New Roman12 pt/1.5/justified/2.5cm margins, cover fields and Part A/B/C criteria. No literature references were fabricated and no final 1500–2000-word academic report or slide deck was generated. Project-proposed ≥3 alpha sessions/≥5 beta people are not course-mandated minima. The older mutable-demo wording and public-deployment roadmap heading are explicitly reconciled with the approved read-only demo/local-only runtime, rather than silently claimed as implemented.

**Before modifications:** backend **325 passed**,65.00s, one existing Starlette/httpx warning; frontend **98 passed** (runner start 2026-10-25T16:24:44+05:00); Ruff/format/mypy (51 sources), ESLint/TypeScript/format/catalog/build passed. Alembic was at `f34f9df9b6a4`, no drift. Docker localhost release/readiness passed. A fresh browser inspected 12 EN/RU/KK combinations across demo/login/authenticated dashboard/reports using retained explicitly synthetic QA data. Baseline classification and actual logs are in `evidence/phase-09/checks/baseline/`. No actual customer assessment or human study was used.

## What changed

### Application and test environment

Application source, styles, UI catalogs, renderer, auth/tenant/scanner controls, historical migrations and dependency locks are **unchanged** from `e9c7db4` (`git diff --exit-code` verified). No reproducible application defect requiring a product patch was found in the exercised scope. Current documentation's stale EN/RU-only demo wording was corrected to EN/RU/KK.

Existing engineering harnesses now accept only a fixed test-only `SHIELDMATE_QA_PHASE=08|09` runtime. Default08 behavior/paths remain;09 uses new isolated projects/volumes at 16073/16173 and engineering output outside Git. No existing database/volume was reset or overwritten. Added fresh-context demo isolation/reset checks on the actual compiled 8080 release; they block unexpected external/private browser requests. No app server/form/analytics/telemetry was added for research. Normal release images still exclude QA/study scripts. Existing Docker build-context allowlisting was tested to exclude `research-private/` (expected COPY denial), not weakened.

### Research/evidence implementation

`docs/testing/` now contains an executable alpha checklist with blank actual-result/tester/date/evidence fields; a realistic beta recruitment/consent/timing/grading/withdrawal/accessibility protocol; **six translated participant/alpha handouts** (EN/RU/KK), each with relevant consent/safety instructions; a six-question closing survey; header-only alpha/beta/manifest CSVs; blank participant/issue notes; a study declaration; a source-bound moderator rubric; Assignment 5 journey/MoSCoW/method/contribution/AI-disclosure support; and a nontechnical defense/environment checklist.

`python scripts/research_evidence.py` provides standard-library-only `init`, `scenario`, `hash`, `alpha`, `beta` commands and JSON/Markdown aggregate outputs. It never generates participant rows/answers. It checks exact schemas, bounded input, IDs/duplicates, ISO timestamps, finite measured times, enums/ratings, eligibility/relationship, declared consent, independent media permissions, file ownership/session links, safe paths/no symlinks, hashes, private human roots, retention and scenario/build consistency. Human inputs inside the repo are restricted to ignored `research-private/`; init creates 0700/0600 artifacts and refuses overwrite. Analysis does not purge anything or export raw responses.

The fixed definition binds actual demo snapshot/Top1/action, grading rubric, numeric criterion, beta protocol, participant wording, demo UI and EN/RU/KK catalogs. Changing source/materials or mixing builds is rejected rather than silently pooling a changed scenario. Test-classified rows require explicit internal mode and can never produce a real human criterion result. Real mode rejects them. Declared records/checksums still **cannot prove human authenticity, genuine consent or correct manual grading**; team review remains mandatory.

### Hypothesis, measurements and current result

**PROPOSED only:** at least 80% of genuine target-user beta participants identify the fixed scenario's highest-priority issue **and** explain one sensible next action, unaided, within 120 seconds. Recommend ≥5 distinct analyzed participants; 4/5 reaches 80%,3/5 does not. This measures comprehension/usability, not security improvement, ROI, paid demand or exhaustive detection. No team adoption is confirmed.

Timer starts when the identical primary prompt is first shown/read; use a consistent actual monotonic/manual stopwatch, never infer time. Primary success requires completed first trial, correct issue/action, observed time≤120, no hint/pause. Exact terminology or every technical detail is unnecessary. Unknown/missing/late/hinted/paused/incomplete/aborted primary starts cannot pass. All eligible consented primary starts remain in N, except explicitly withdrawn records; withdrawals are separately counted with a conservative sensitivity bound, including an explicitly declared aggregate for fully removed records. Optional secondary tasks/questions/ratings may be skipped without invalidating an already completed primary task or inventing a negative answer. Different builds and retakes are not silently pooled.

A **private blank workspace** is initialized at `research-private/phase09` and ignored by Git. Actual CLI outputs: **NO REAL BETA RESULTS YET**, percentage `null`, criterion `PENDING_MANUAL_EVIDENCE`; **NO HUMAN ALPHA SESSIONS CONDUCTED**, zero recorded sessions. Those describe empty files, not 0% usability or a passing study. Custodian/retention/adoption fields remain blank for the team to complete before real data collection.

## Actual final commands and results

Commands ran from the indicated directory. Logs/results are under `docs/evidence/phase-09/checks/`; baseline/final logs are separate. No test pass below represents a human session.

| Directory | Command | Actual result |
|---|---|---|
| backend | `.venv/bin/pytest -q` | **325 passed**,75.20s; one pre-existing Starlette/httpx deprecation warning |
| backend | `.venv/bin/ruff check .` | PASS |
| backend | `.venv/bin/ruff format --check .` | PASS |
| backend | `.venv/bin/mypy app` | PASS, 51 source files |
| root | `backend/.venv/bin/pytest scripts/tests -q` | **49 passed**, 0.42s; all participant-like fixtures explicitly INTERNAL TEST DATA in temporary directories |
| root | `backend/.venv/bin/mypy --strict scripts/research scripts/research_evidence.py` | PASS, 7 source files |
| root | `backend/.venv/bin/ruff check --config backend/pyproject.toml scripts/research scripts/research_evidence.py scripts/tests scripts/verify-phase-08-pdfs.py` | PASS |
| root | Same targets with `ruff format --check` | PASS, 10 files |
| root | `node --test --test-reporter=tap scripts/tests/qa-runtime.test.cjs` | **3 passed**: default 08, isolated09, arbitrary-phase rejection |
| frontend | `npm test -- --reporter=json --outputFile=../../../work/phase09/final/frontend-tests.json` | **98 passed**,0 failed; runner start 2026-10-25T17:29:04+05:00 |
| frontend | `npm run lint` | PASS |
| frontend | `npm run typecheck` | PASS |
| frontend | `npm run format:check` | PASS |
| frontend | `npm run i18n:check` | PASS, 976 keys×3,576 UI references, no missing keys/placeholder mismatches |
| frontend | `npm run build` | PASS; existing >500kB chunk warning,648.95kB JS /184.13kB gzip |
| frontend | `npm audit --json` | PASS,0 known vulnerabilities /347 dependency records |
| backend | `.venv/bin/pip-audit --format json` | PASS,68 packages,0 known vulnerabilities |
| root | `docker compose -f compose.local.yaml up -d --build --wait` | PASS, compiled loopback8080 release; no Vite/public exposure |
| root | `docker compose -f compose.local.yaml exec -T backend .venv/bin/alembic upgrade head` | PASS, existing head retained |
| root | Same exec prefix with `alembic current`, `alembic history`, `alembic check` | Head `f34f9df9b6a4`, historical chain intact, no new upgrade operations |
| root | `SHIELDMATE_RC_PORT=16073 docker compose -p shieldmate-phase09-qa -f compose.local.yaml -f scripts/qa/phase08.override.yaml up -d --build --wait` | PASS, new isolated fixture project |
| root | `SHIELDMATE_QA_PHASE=09 node scripts/verify-phase-08.cjs` | PASS,**399 rendered/axe views**,5 technical flow groups,12 PDFs,0 page errors |
| root | `SHIELDMATE_QA_PHASE=09 node scripts/verify-phase08-interactions.cjs` | PASS,**132 additional rendered/axe views**, canonical filters, form retention, keyboard dialogs/menu/errors in all 3 languages |
| root | `SHIELDMATE_QA_PHASE=09 node scripts/verify-phase08-operations.cjs` | PASS, verified online backup/new-volume restore, preserved session/data/report bytes, localhost runtime/headers/Host/body checks, failed migration never starts HTTP |
| root | `SHIELDMATE_QA_PHASE=09 node scripts/verify-phase08-report-ui.cjs` | PASS, 3 actual localized generate/browser-download flows, report retry, 12 demo-step interactions,0 page errors |
| root | `node scripts/verify-phase09-demo-isolation.cjs` | PASS,**12 fresh-guest reset/isolation cases**,3 languages×360/768/1280/1920; 0 unexpected external/private requests,0 cookies, language-only localStorage, exact sample content plus validated schema default |
| root | `SHIELDMATE_QA_PHASE=09 backend/.venv/bin/python scripts/verify-phase-08-pdfs.py` | PASS,**12 PDFs /135 pages** extracted/rasterized/bounds/fonts/markers/hashes validated |
| root | `python -S scripts/research_evidence.py scenario` | PASS, source/rubric/materials frozen; `-S` proves no site-package dependency |
| root | `python -S scripts/research_evidence.py beta --csv research-private/phase09/beta-results.csv --manifest research-private/phase09/evidence-manifest.csv --evidence-root research-private/phase09 --study research-private/phase09/study-declaration.json` | NO REAL BETA RESULTS YET, null percentage, pending criterion |
| root | `python -S scripts/research_evidence.py alpha --csv research-private/phase09/alpha-results.csv --manifest research-private/phase09/evidence-manifest.csv --evidence-root research-private/phase09` | NO HUMAN ALPHA SESSIONS CONDUCTED |
| root | `git check-ignore research-private/phase09/beta-results.csv` | PASS, private folder ignored |
| root | `docker build --no-cache -f ../../work/phase09/final/context-check.Dockerfile .` (controlled scratch COPY probe) | **Expected exit 1 / COPY not found**, privacy assertion PASS; no human data was present |
| root | `backend/.venv/bin/python scripts/check-secrets.py` | PASS, no high-confidence working-tree text matches; history/binaries/ignored private evidence not scanned |
| root | `git diff --exit-code e9c7db4 -- backend/app frontend/src backend/migrations backend/uv.lock frontend/package-lock.json` | PASS, product source/migrations/locks unchanged |
| root | Prettier `--check` on the7 modified/new CJS tools; `git diff --check` | PASS |

The test runner needed normal local process permissions for Node child tests; the restricted sandbox run failed, then the actual unsandboxed local runner passed 3/3. Early new-tool tests caught an alpha UTC import, a missing mixed-build guard and the optional-secondary/completed-primary issue; they were fixed and covered by regressions. A new demo-isolation test initially compared raw fixture JSON with serialized API output without accounting for the existing `template_version=assessment-2` schema default; it now explicitly validates that default and compares every remaining value. This was a test assumption, not an application defect. None of the auth/scanner controls was bypassed to make checks pass.

## Security, Docker and visual evidence

The full backend suite preserves CSRF/session/expiry/revocation, tenant/relationship IDOR, domain proof/consent/expiry/quotas, SSRF/DNS rebinding/numeric pinning/SNI/peer/TLS/header limits, evidence lifecycle/dedup/resolution/reopening, task atomicity and immutable private report checks. The actual browser flow verifies eight foreign-resource denials, missing CSRF/hostile Origin rejection, real two-tab logout/account transition and task Done≠technical resolution. A subsequent conclusive clean fixture changes findings without rewriting old PDFs. An actual worker SIGKILL/90-second lease recovers 4 retained observations to interrupted without automatic retry; unsafe-destination fixtures fail closed. No arbitrary public/private target was scanned.

Online backup/isolated restore SHA256 is **`a7182e60159c4cd7691f568b3e1f3199ecc7d9337d75250961c21c03077f67f6`**, identical before restored API use. Verified snapshot: 4 synthetic accounts/organizations,9 domains,9 scans,108 observations,34 findings,1 task/2 task events,9 reports; all relevant tables, schema/integrity/foreign keys and ready PDF hashes agree. Seven original/restored API projections and 3 private report downloads agree. This is a technical fixture snapshot, not customer adoption or participant evidence. The later export-button rehearsal uses a separate synthetic workspace and does not retroactively enter the earlier backup. Existing backups/destinations were refused rather than overwritten.

**531 automated axe/overflow views** cover EN/RU/KK at 360/390/768/1024/1280/1440/1920, including marketing/demo/sign-in/private dashboard/assets/scans/findings/details/tasks/reports/settings/404 and empty states. No detected axe violations/page errors in the completed workflows. Additional 12 fresh guest cases verify research reset/no-auth isolation at the four requested widths. All are automated developer QA, not observed people or a claim that531 screenshots were manually inspected.

**Six genuine selected prototype screenshots** were opened/visually reviewed and captioned in `evidence/phase-09/screenshots/captions.md`; capture metadata/SHA256s are in `checks/engineering-evidence-index.json`. They retain the distinctive burgundy/red system and explicit LOCAL QA/DEMO labels. **12 PDFs /135 pages** were actually generated/extracted/rasterized; **18 representative pages**, spanning short/long/partial/demo in every language, were visually reviewed in 3 sheets plus a full-size Kazakh page. This is a manageable sample, not manual inspection of every page. Glyphs, wrapping, summaries, headers/footers/context and evidence tables were legible. See `checks/visual-review.md`, `pdf-pages/` and `pdfs/`. No security certificates or PDF/UA/native accessibility certification are claimed.

## Acceptance gates — separated honestly

| Gate | Status | Evidence / boundary |
|---|---|---|
| E01 Phase 08 baseline preserved | PASS — ENGINEERING READY | Clean e9c7db4 baseline,325/98 suites, unchanged app/migrations/locks, separate volumes |
| E02 Safe alpha plan/records | PASS — ENGINEERING READY |8 actionable checks, blank actual/tester/date/evidence fields, triage/retest and translated tasks; no human pass prefill |
| E03 Eligible/neutral beta protocol | PASS — ENGINEERING READY | Real SME-role screening, unhinted script, fixed first attempt, translated invitation/tasks/questions |
| E04 Consent/anonymity/private storage | PASS — ENGINEERING READY | Separate media/quote choices, private modes/ignored paths, safe manifest/CLI, existing Docker exclusion verified |
| E05 Scenario/rubric/denominator | PASS — ENGINEERING READY | Frozen source/materials/build guards, proposed 80%/120s/5-person plan, transparent incomplete/withdrawn policy |
| E06 Templates/validator/tests | PASS — ENGINEERING READY | Header-only CSVs/notes/declaration,49 internal tests,7 strictly typed modules, no network/data fabrication |
| E07 Assignment source mapping | PASS — ENGINEERING READY | Actual source inspected;≥4 journey stages/≥8MoSCoW features, methods/alternatives, blank contribution matrix, AI disclosure, exclusions/source clarifications |
| E08 Stable isolated local environment | PASS — ENGINEERING READY | Real 8080 release, new16073/16173 technical QA, guest resets/immutable demo, real backup/recovery checks |
| E09 EN/RU/KK study support | PASS — ENGINEERING READY |6 handouts, multilingual CSV/scenario/PDF/UI support; independent native review explicitly NOT TESTED |
| E10 Product/security regressions | PASS — ENGINEERING READY |325 backend,98 frontend,49 evidence,3 config tests; audits/static/Docker/browser/PDF checks above |
| E11 Evidence/defense preflight | PASS — ENGINEERING READY |6 actual captioned images,18 reviewed PDF pages, lecturer-friendly preflight/click path/fallback/recovery |
| E12 Integrity/local Git/scope | PASS — ENGINEERING READY | No fabricated study, push/public exposure/Phase 10; focused local commit and clean final tree |
| H13 Dated real internal alpha | **PENDING MANUAL EVIDENCE** | Team/close testers have not conducted documented sessions |
| H14 Real target-audience beta | **PENDING MANUAL EVIDENCE** | No recruitment, consent or observed eligible sessions completed |
| H15 Real hypothesis calculation | **PENDING MANUAL EVIDENCE** | No adopted-before-testing real data; no human percentage or criterion conclusion |
| H16 Evidence-linked team conclusion/change | **PENDING MANUAL EVIDENCE** | Requires actual observations, interpretation and team validation |
| H17 Completed academic appendix/contributions | **PENDING MANUAL EVIDENCE** | Templates/technical evidence exist; real testing proof, confirmed human contributions and final academic report not supplied |
| H18 Lecturer/prototype logistics | **PENDING MANUAL EVIDENCE** | Localhost cannot serve another computer; lecturer/LMS/live-defense access agreement not confirmed |

## Files, limitations and handoff

Primary entrypoint: `docs/testing/README.md`; protocols `alpha-plan.md`/`beta-protocol.md`; source/feature/method/contribution mapping `assignment-05-mapping.md`; actual lecturer click/recovery path `defense-checklist.md`; reproducible environment `local-environment.md`. Templates are the three `*-template.csv` files, study declaration, participant/issue notes and 6 handouts. `scripts/research_evidence.py` and typed `scripts/research/` implement the CLI; `scripts/tests/` contains internal-only regressions. Current README/architecture/demo/testing/defense docs link these materials. Full changed-file list is `evidence/phase-09/checks/changed-files.txt`.

Normal release remains running at <http://127.0.0.1:8080> (`docker compose -f compose.local.yaml up --build -d --wait`). Temporary QA/restore services are stopped after verification with volumes retained; no prior volume was deleted. The initialized private study folder remains blank and uncommitted. Original Phase 08 risk/operability limitations remain: SQLite/single worker/process-local abuse limits, no deployment-level egress firewall, no public TLS/proxy configuration, no independent penetration test or base-image CVE audit. App dependency audits are point-in-time advisory checks, not guarantees. Existing deprecation/chunk-size warnings remain disclosed.

**NOT TESTED:** real owned-domain TXT+external TLS/HTTPS E2E (no authorized real target supplied), independent native RU/KK review, non-Chromium/physical-device/screen-reader evaluation, actual SME beta testing, timed human defense rehearsal and lecturer access acceptance. No academic literature sourcing, final report/deck or human conclusion is invented. Engineering readiness does not remove these requirements.

## HUMAN NEXT ACTIONS

1. Confirm actual member roles/deadline/lecturer access and arrange native review. Agree the proposed hypothesis/sample/denominators; fill actual custodian, consented deletion date and adoption time before testing. Record clean app/kit commits and frozen definition hash.
2. Conduct real internal alpha sessions with the translated sheet; record actual dates/actions/issues/consented evidence and separate retests. Do not copy technical automation into human rows.
3. Actually recruit about 5 distinct genuine target SME decision-makers, using neutral invitations. Obtain core consent and each optional media/quote choice separately; no company secrets/accounts are needed for public-demo usability.
4. Run the same fresh-context scenario/first prompt with actual stopwatch measurements and no hints. Preserve incomplete/aborted/withdrawn dispositions and optional skipped answers; keep raw notes/media only in private ignored storage.
5. Hash/link actual consented files, run the CLI in **real mode**, review grading/evidence with the team, and report exact n/N/withdrawal sensitivity/limits. Empty files or internal fixtures cannot support a conclusion.
6. Prepare the source-verified 1500–2000-word PDF report, actual appendix/contributions/AI disclosure, 3–6 genuine screenshots and ≤10 PDF slides. Verify two academic+one course-lecture references in APA7. Confirm live prototype logistics with the lecturer; do not claim a remotely usable localhost URL or deploy without separate approval.
