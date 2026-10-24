# Phase 07.1 completion and verification

Implementation date: 24 October 2026 (Asia/Almaty). Starting branch: `main`; verified clean baseline: `8f295fa`. Scope is Phase 07.1 only. No push, public deployment, new scanner capability or Phase 08 work. The focused local commit containing this report is the phase completion commit; use `git log -1 --oneline` for its identifier and `git status --short` for the final tree state.

## What changed and why

The supplied PNGs were read as bug evidence, not implementation instructions. The full implementation brief is preserved in `PROMPTS/PHASE_07_1.md`; the screenshots are in `docs/qa-references/`. The English hero's inline red accent had padding outside its effective line box and intruded into the preceding row. It is now an in-flow grid/flex composition with measured line boxes, container-relative typography and contextual EN/RU/KK phrases. The baseline at the actual 1247px viewport did not reproduce the supplied image's clipped right edge: its gutter/type scale suggests a wider screenshot cropped to that width. This is distinct from the genuine headline overlap.

Step numerals were aligned to the top of variable-height content. They now center against the entire semantic list row, including the extra explanatory detail. Browser geometry checks allow less than 2px center deviation. Marketing grids, long headings/domains, dialogs, translated controls and table containers use intrinsic sizing and deliberate wrapping. Confirmation dialogs explicitly restore centered modal positioning after the global CSS reset and constrain height with internal scrolling on short screens. Actual testing also found Russian marketing min-content overflow and a long Kazakh word at 200% text size; both were fixed without concealing overflow. The expressive burgundy/red/ivory identity and Anton/Plex families remain.

Reports previously used a largely linear text presentation with weak grouping and inconsistent implicit frame padding. New `assessment-2` reports use an explicit A4 print grid, restrained burgundy table headers, dark body text, compact Top 3, narrative/evidence separation, repeated technical-table headings, grouped findings/tasks and an observation appendix. Section headings stay with introductory content; task completion warnings stay with the corresponding task. Long evidence/IDs wrap without truncation. Print-only Plex TTFs share the UI's licensed source; Kazakh glyphs and selectable text are checked. The optional template-version field does not change the evidence schema or require a migration.

## Routes and principal files

| Area | Implemented / reviewed routes and files |
|---|---|
| Public | `/`, `/login`, `/register`, `/demo` (all four steps), `/preview/ui-kit`, 404; `LandingHero.tsx`, `Landing.tsx`, `UiKit.tsx`, public shell and marketing styles |
| Workspace | `/app`, `/app/assets`, DNS instructions/removal dialog, `/app/assets/:id/scans`, `/app/findings`, finding details, `/app/tasks`, task details, `/app/reports`, `/app/settings`; onboarding and empty workspace states |
| Localization | Shared `backend/app/locales/{en,ru,kk}.json`, frontend `i18n/`, metadata in `App.tsx`, report locale schema, three-entry demo PDF cache, checker and regression tests |
| Reusable presentation | AssessmentSummary, FindingEvidence, FindingFilters, ReportScope, Table, language selector, dashboard summaries and workspace preview descriptions |
| Print | `backend/app/reports/pdf.py`, `pdf_layout.py`, `pdf_sections.py`, licensed font assets/source manifest, maintainer `scripts/build-report-fonts.py` |
| QA and docs | Phase 07.1 Compose harness and browser/PDF scripts, new regression tests, localization style guide, updated design/report/localization docs and README, actual evidence files |

No package/runtime dependency was added. Existing auth, proof, scanner, finding-ranking, task persistence and report authorization services retain their architecture.

## Localization

All three catalogs have exact parity across 974 keys and their named placeholders (575 literal UI references checked). The native selector reads **English / Русский / Қазақша**; the locale is `kk`, not `kz`. Existing EN/RU choices remain compatible, invalid saved preferences fall back to English, and switching preserves routes and unsent form values. Metadata/document language and date/number formatting update. Raw domains, protocol/evidence values, hashes, organization/owner names and notes remain exact. Filters now submit canonical enums in every language; Phase 07 had translated some option values, causing invalid API queries.

Russian copy was revised into professional product language: “Создать PDF-отчёт”, “Подтвердите управление доменом”, “Организуйте работу”. Kazakh uses contextual phrases such as “Неден бастау керегін біліңіз” and “Қауіпсіздік туралы есеп”. Dashboard count sentences use whole named templates rather than grammatically fragile fragments. English status labels such as “In progress” no longer expose underscore enums. Finding-detail headings and scan-history statuses use the same controlled catalog; Kazakh UI dates use a locale-aware numeric month to avoid the browser ICU “M10” fallback. `localization-style-guide.md` documents 22 canonical terms and the difference between a supported finding, a proven vulnerability, task completion and confirmed technical resolution.

Independent native-speaker review was unavailable. No native-language certification is claimed; idiom and specialist terminology should receive that review before a public release.

## Executed checks

Commands below ran from the repository root except backend commands, which ran from `backend/`. Exact commands, output logs and machine-readable browser/PDF results are in `docs/evidence/phase-07-1/checks/`. Stored text logs normalize terminal trailing whitespace; command output content is retained.

| Command | Actual result |
|---|---|
| Baseline `.venv/bin/pytest -q` | 308 passed |
| Baseline `npm test --prefix frontend` | 78 passed |
| Final `.venv/bin/pytest -q` | 314 passed; one existing Starlette/httpx deprecation warning |
| Final `npm test --prefix frontend -- --reporter=json --outputFile=../../../work/phase071-logs/frontend-tests.json` | 93 passed |
| `npm run lint --prefix frontend` | PASS, no lint warnings |
| `npm run typecheck --prefix frontend` | PASS |
| `npm run format:check --prefix frontend` | PASS |
| `npm run i18n:check --prefix frontend` | PASS, complete three-locale parity and named interpolation checks |
| `npm run build --prefix frontend` | PASS; Vite reports a non-blocking bundle-size warning |
| `.venv/bin/ruff check app tests` | PASS |
| `.venv/bin/ruff format --check app tests` | PASS |
| `.venv/bin/mypy app` | PASS, 48 source files |
| `.venv/bin/alembic current` / `.venv/bin/alembic check` | `f34f9df9b6a4` head; no new upgrade operations |
| `npm audit --prefix frontend` | 0 vulnerabilities reported |
| `.venv/bin/pip-audit` | No known vulnerabilities reported |
| `docker compose build` / `docker compose up -d --wait` | PASS, loopback-only preview; backend/frontend healthy |
| QA Compose `up -d --wait`, restart backend/worker | PASS; session, history and five report hashes retained |
| `node scripts/verify-phase-071.cjs` | 273 route/locale/viewport checks, zero overflow/axe violations and no runtime errors; hero/step geometry, 12 demo steps, text zoom and focus checks |
| `node scripts/verify-phase-071-interactions.cjs` | 195 auth/onboarding/empty/modal/error checks, zero overflow/axe violations; canonical filters, form state, keyboard focus restoration/menu checks |
| `node scripts/qa/phase071_refresh.cjs` | Six new persisted report records plus three public DEMO exports; final file hashes match their stored records |
| `python scripts/verify-phase-071-pdfs.py` | Nine PDFs rasterized; A4 bounds, word spacing, selectable Unicode, embedded Plex, context on every page, private-note exclusion and stored SHA-256 checks pass |
| `node scripts/qa/phase071_persistence.cjs` | Five stored artifacts unchanged after backend/worker restart, with authenticated session retained |
| `git diff --check` | PASS |

## Browser and visual evidence

The matrix covers EN/RU/KK at **360, 390, 768, 1024, 1280, 1440, 1920 CSS px**. Chromium and axe versions are recorded in the matrix/environment evidence. Desktop and mobile PNGs were actually opened and reviewed, including hero/steps, Russian dashboard, Kazakh landing, report pages, dialogs, forms, empty/error states and demo steps. Each route was checked for page-level horizontal overflow and WCAG A/AA axe violations. Tables may scroll inside their own labeled containers; page overflow is not hidden. Keyboard activation, Escape, dialog focus return, visible focus, language/form stability and reduced motion were separately exercised. Enlarged text was checked at 200% on the landing page in all three languages; this is text scaling, not a claim of browser-wide zoom certification.

Before/after pairs include `before/hero-en-1247.png` / `after/hero-en-1247.png` at 1247×827, `before/steps-ru-1082.png` / `after/steps-ru-1082.png` at 1082×679, and mobile hero/steps at 360px. Original Phase 07 PDF rasters are included under `before/pdf-ru-*.png`. The user-supplied defect captures remain separate in `docs/qa-references/`.

## PDF evidence and security

Final samples are under `docs/evidence/phase-07-1/pdfs/`; individual rendered pages are under `pdf-pages/`. All pages were rasterized and programmatically checked; contact sheets covering every page and selected full-size pages were actually inspected. Complex fixtures contain **24 persisted findings across four verified LOCAL QA domains**, long hostnames, three real task statuses and Kazakh characters in the organization/owner labels. Partial fixtures have one usable but incomplete assessment plus an unverified asset, with no invented findings. DEMO PDFs use only the isolated synthetic fixture. Exact final page counts and SHA-256 values are in `checks/pdf-validation.json`.

| Sample | EN pages | RU pages | KK pages |
|---|---:|---:|---:|
| Complex LOCAL QA | 24 | 27 | 27 |
| Partial LOCAL QA | 3 | 3 | 3 |
| DEMO | 6 | 6 | 6 |

Total: **105 pages**. Printable evidence values and raw timestamps remain intact; narrative dates are explicitly UTC. DEMO and LOCAL QA labels appear on every respective page. The licensed Plex regular/semibold text fonts are embedded with Unicode maps. ReportLab also declares an unused base Helvetica resource; report text uses the embedded Plex faces. These are selectable-text PDFs, not PDF/UA-certified/tagged documents.

Security verification includes the full existing session/auth/CSRF/Origin, IDOR/tenant-isolation, domain challenge/expiration, scanner SSRF/rebinding/bounds, finding lifecycle, task-resolution separation, report immutability/failure/resource-bound and demo-isolation tests. An additional real two-session report IDOR check returns 404. Two reports created through the actual Phase 07 images before replacement retain identical bytes after the new images and container restart (`legacy-before.json`, `legacy-after.json`, `restart-persistence.json`). No old report JSON/BLOB was rewritten. No migration was added. PDF rendering stays offline, escapes markup, strips unsafe controls, excludes private notes and preserves the existing 80-page/2MiB bounds and transactional failure behavior. No risk calculation or scanner guard was weakened.

## Acceptance gates (brief section G)

| Gate | Result | Evidence |
|---|---|---|
| 1. Responsive hero and established visual identity | PASS | Matched before/after captures, geometry and 3×7 viewport matrix |
| 2. Whole-row centered step numerals | PASS | Russian/mobile captures; center deviation <2px |
| 3. Significant-route layout/spacing/wrapping audit | PASS | 468 automated view checks plus actual PNG review |
| 4. Corrected RU and complete KK localization | PASS | Shared catalogs, parity/placeholder checks, complete UI/PDF implementation; independent native review NOT TESTED |
| 5. EN/RU/KK report UI and redesigned PDFs | PASS | Nine final PDFs and raster/bounds/Unicode checks |
| 6. Existing product/security invariants | PASS | 314 backend tests, 93 frontend tests, actual immutable history and restart checks |
| 7. Automatic locale/layout regression checks and screenshots | PASS | Maintained checker, tests, browser scripts and before/after PNGs |
| 8. Rendered PDF QA and honest coverage | PASS | All 105 pages rasterized/bounds checked and reviewed in contact sheets; selected full-size inspection |
| 9. Updated technical/design/localization documentation | PASS | This report, style guide, design-system/reports/localization docs and README |
| 10. Executed checks and focused local commit/clean tree | PASS | Final logs and local phase commit; no push/deployment |

## Limitations and NOT TESTED

No independent native-language certification, physical device testing, Safari/Firefox run, actual screen-reader session, PDF/UA certification, print-shop proof, or production deployment/load test. Forced-colors/high-contrast mode was not independently verified. No real customer/externally owned domain was enrolled for this polish phase: scanner data in visual QA is explicitly injected and labeled LOCAL QA. The browser matrix is Chromium-based; text-size checks do not certify every browser zoom combination. Browser-native validation language follows browser settings. Larger dictionaries produce a non-blocking Vite chunk-size warning; route/catalog splitting remains a future optimization, with no new dependency introduced. Existing Starlette/httpx and Node loader deprecation notices remain. A dependency audit is a point-in-time check, not a security certification.

## Local preview and repeatable QA

From the repository root:

```sh
docker compose up --build -d --wait
```

Open `http://127.0.0.1:5173` and `/demo`; backend health is `http://127.0.0.1:8000/api/v1/health`. All published ports bind to loopback. Use your existing account or register a local account; real workspace features retain ownership/security requirements. No credentials are included in this report.

The isolated browser stack uses `docker compose -p shieldmate-phase071-qa -f scripts/qa/phase071.compose.yaml up -d --wait`, on 15673/15600, with its own named database volume and fixture TXT provider. It is a QA harness, not a deployment configuration. Set `PLAYWRIGHT_MODULE`, `PLAYWRIGHT_BROWSERS_PATH` and `AXE_MODULE` to installed Playwright/Chromium/axe paths. Private browser state lives outside the repository in `../../work/` and must never be committed. For a fresh QA workspace, run `node scripts/qa/phase071_prepare.cjs`, then `SKIP_HISTORICAL=1 node scripts/verify-phase-071.cjs`; the historical two-report compatibility proof is specific to the original pre-update session and is retained as evidence rather than fabricated by a new run. Move aside stale private report/session manifests only when deliberately starting a fresh isolated QA database. `RESUME=1` resumes already passed view rows, while interaction/geometry checks rerun. Run the interactions and PDF scripts above; `phase071_refresh.cjs` creates fresh, clearly named QA organizations and persists the final PDFs through real API endpoints. Do not delete a database volume containing work you need.

Stop the isolated stack with `docker compose -p shieldmate-phase071-qa -f scripts/qa/phase071.compose.yaml down` (without `-v`). The isolated QA containers were stopped after verification; their volume was retained. The normal preview remains running at 127.0.0.1:5173. Phase 08 is not started.
