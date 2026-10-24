# Phase 07 completion and verification

Phase 07 implements real, protected PDF snapshots/history, an isolated synthetic demo and English/Russian localization. Baseline: clean `main`, `a3713dd` (Phase 06). No Phase 08/09 work, push or public deployment. The Phase 07 local commit is the commit containing this report; obtain its hash with `git log -1 --oneline` (the final response records it). No unrelated user changes existed at preflight.

## Architecture and delivered behavior

The report aggregator creates a typed, consistent, current-authorization-scoped snapshot from existing organization/domain/scan/observation/finding/task records. It reuses the Phase 05 query and Top 3 ordering, with internal scope filters; there is no new risk score or second finding evaluator. Partial, stale, missing, expired and unevaluated data remain explicit. Human task completion remains separate from technical resolution. Sensitive freeform work notes are not exported.

ReportLab generates selectable, paginated A4 PDFs entirely offline. Immutable snapshot JSON and PDF bytes/size/SHA-256 persist atomically in SQLite. History survives container restarts. Each metadata/download request rechecks authentication and tenant ownership. Report reservation, idempotency, failure handling, quotas and bounded operational audit events are documented in [reports.md](reports.md).

Burgundy/red rules, sharp borders, restrained workspace density and the existing UI families are retained. Local Plex Cyrillic faces make the Russian interface readable; licensed embedded Liberation Sans regular/bold provides printable Cyrillic and Kazakhstan company-name characters. The language selector switches text/background together to avoid transient low contrast. [Design decisions](design-system.md).

The public `/demo` consumes one typed, fixed, fictional reserved-name fixture through separate read-only endpoints; it uses no tenant database or scanner. Every screen and every sample PDF page is labeled DEMO. `/preview` retains its design-preview purpose. The shared small locale catalog translates controlled text, not user-entered or raw technical evidence. [Demo isolation](demo.md), [localization](localization.md).

## Routes and files

New protected frontend: `/app/reports`. New public frontend: `/demo`. Existing public/auth/onboarding/settings/domain/scan/finding/dashboard/task routes receive EN/RU presentation; their permissions and business behavior remain intact.

New API routes:

| Method | Path                              | Behavior                                           |
| ------ | --------------------------------- | -------------------------------------------------- |
| GET    | `/api/v1/reports/overview`        | Current own-organization readiness and coverage    |
| GET    | `/api/v1/reports`                 | Own saved metadata, bounded pagination             |
| POST   | `/api/v1/reports`                 | CSRF/Origin-protected idempotent snapshot creation |
| GET    | `/api/v1/reports/{UUID}`          | Own report metadata                                |
| GET    | `/api/v1/reports/{UUID}/download` | Own immutable authenticated PDF                    |
| GET    | `/api/v1/demo?locale=en           | ru`                                                | Canonical public synthetic snapshot         |
| GET    | `/api/v1/demo/report?locale=en    | ru`                                                | Same-renderer PDF marked DEMO on every page |

Main changes: `backend/app/reports/*`, `backend/app/locales/*`, report models/additive migration, main router/header integration and internal finding-query scope filters; typed `frontend/src/reportApi.ts`, Reports/Demo/ReportScope and small i18n store/components; existing pages/components annotated for controlled translations; fonts/styles; intentional PDF dependencies/lock; frontend Docker build limited to the shared catalog; expanded tests and QA scripts; architecture/design/testing/README and the three focused guides. No existing migration was rewritten. `PROMPTS/PHASE_07.md` preserves the complete user-authorized brief.

## Baseline and final automated results

Pre-change baseline actually executed: **286 backend tests, 64 frontend tests**, lint/types/format/build and migration checks passing; baseline head `e53b215e4b66`, no drift. Existing Starlette/httpx and Node module-registration deprecation warnings were recorded.

Final commands below ran from the repository root except backend commands, which ran from `backend/`:

| Exact command                                                                                               | Actual result                                                                                                    |
| ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `.venv/bin/pytest -q`                                                                                       | **308 passed**, one existing Starlette/httpx deprecation warning                                                 |
| `.venv/bin/pytest -q tests/test_reports.py`                                                                 | Focused run: **21 passed** before the final catalog-completeness test; full run includes all **22** report cases |
| `.venv/bin/ruff check .`                                                                                    | PASS; 66 Python files in format check                                                                            |
| `.venv/bin/ruff format --check .`                                                                           | PASS, 66 files already formatted                                                                                 |
| `.venv/bin/mypy app`                                                                                        | PASS, 46 source files                                                                                            |
| `.venv/bin/alembic upgrade head`                                                                            | PASS, additive head `f34f9df9b6a4`                                                                               |
| `.venv/bin/alembic check`                                                                                   | PASS, no new upgrade operations/schema drift                                                                     |
| `.venv/bin/alembic current`                                                                                 | `f34f9df9b6a4 (head)`                                                                                            |
| `.venv/bin/pip-audit --progress-spinner off`                                                                | No known vulnerabilities found                                                                                   |
| `npm test --prefix frontend -- --reporter=json --outputFile=/tmp/phase07-front.json`                        | **78 passed**, 10 suites, no failures                                                                            |
| `npm run lint --prefix frontend`                                                                            | PASS, zero warnings                                                                                              |
| `npm run typecheck --prefix frontend`                                                                       | PASS                                                                                                             |
| `npm run format:check --prefix frontend`                                                                    | PASS                                                                                                             |
| `npm run i18n:check --prefix frontend`                                                                      | PASS, **573** explicit static references, no missing keys                                                        |
| `npm run build --prefix frontend`                                                                           | PASS; existing Node `module.register()` deprecation warning                                                      |
| `npm audit --audit-level=low --prefix frontend`                                                             | Zero vulnerabilities                                                                                             |
| `backend/.venv/bin/ruff check --config backend/pyproject.toml scripts/build-demo.py scripts/verify-pdfs.py` | PASS                                                                                                             |
| `git diff --check`                                                                                          | PASS                                                                                                             |

[Machine-readable frontend results and passing output summaries](evidence/phase-07/checks/). During development, failing tests and harness assumptions were fixed: the locale date export, Node 26 test Storage behavior, label spacing, updated verification URL, restart polling and alert selectors, new keyboard language controls, and the real transient contrast issue. Failed attempts were not counted as passes. Scanner error assertions now include the same explanatory sentence alongside its added visible technical error code.

## Security verification

Backend tests cover current/expired/rotated authorization, no evidence, unverified/mixed/stale/partial/pending data, pruned sources, shared priorities, technical resolution versus work completion, immutable old artifacts after later evidence changes, failed rendering, quotas/idempotency/concurrent creation, corrupt bytes, interrupted reservations, bounded audit/history, strict input schemas and pagination, two-tenant IDOR, unauthenticated/expired access, CSRF/bad Origin, traversal-shaped IDs, and logout during rendering. Late completion does not restore a revoked session's access.

Untrusted text is escaped; control/bidi characters are removed; long company names, Punycode/technical punctuation, Cyrillic and Kazakhstan glyphs are exercised. No customer path parameter is converted into a filesystem path. BLOB storage eliminates symlinks/orphan artifact files. Downloads use attachment, `private, no-store` and `nosniff`, with integrity checks. Renderer and public-demo tests fail on attempted sockets/customer storage. No report generation invokes scanner/network transport or remote HTML/assets. Customer notes/secrets are excluded. Existing auth/tenant/scanner security tests remain passing.

Production concerns remain explicit: SQLite and local HTTP deployment, process-local request rate budgets, bounded rather than forensic report audit, conservative lifetime report cap and no retention UI. Existing production Secure-cookie/TLS requirements remain unchanged. This is not a production penetration test or certification.

## Docker, migration and persistence

Executed:

```sh
docker compose config --quiet
docker compose up -d --build --wait
docker compose exec -T backend .venv/bin/alembic check
docker compose ps
docker compose -p shieldmate-phase07-qa -f scripts/qa/phase07.compose.yaml up -d --wait
```

The final backend/frontend/worker images build; backend/frontend health checks pass and the worker is running with read-only roots/non-root users and loopback bindings. The QA browser script restarts backend and worker, retains the actual session/history and verifies identical old PDF bytes/checksum after restart and after a newer clean evaluation. The JSON/PDF BLOB is in the existing named database volume. Migration tests exercise upgrade, no drift and downgrade/re-upgrade while preserving earlier domain/finding/session data. Historical migrations remain unchanged. Temporary QA stacks were stopped with `down` while retaining their volumes; the ordinary preview remains available.

## Actual browser, responsive and accessibility checks

Tooling: Chromium **151.0.7922.34**, Playwright **1.62.1**, axe **4.14.0**, using the existing outside-repository browser tooling. Before commands:

```sh
source ../../work/browser-env.sh
```

| Executed command                                                                                                     | Result                                                            |
| -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `node scripts/verify-phase-07.cjs`                                                                                   | PASS: **100** views, 3 grouped end-to-end flows, zero page errors |
| `EVIDENCE_DIR=docs/evidence/phase-07/regression-01 node scripts/verify-phase-01.cjs`                                 | PASS: 16 views, 16 interactions, zero page errors                 |
| `EVIDENCE_DIR=docs/evidence/phase-07/regression-02 node scripts/verify-phase-02.cjs`                                 | PASS: 12 views, 8 flow checks, zero page errors                   |
| `BASE_URL=http://127.0.0.1:15273 EVIDENCE_DIR=docs/evidence/phase-07/regression-04 node scripts/verify-phase-04.cjs` | PASS: 16 views, 7 flow checks, zero page errors                   |
| `EVIDENCE_DIR=docs/evidence/phase-07/regression-05 node scripts/verify-phase-05.cjs`                                 | PASS: 20 views, 7 flow checks, zero page errors                   |
| `EVIDENCE_DIR=docs/evidence/phase-07/regression-06 node scripts/verify-phase-06.cjs`                                 | PASS: 24 views, 7 flow checks, zero page errors                   |

Regression stacks started with `docker compose -p shieldmate-phaseNN-qa -f scripts/qa/phaseNN.compose.yaml up -d --wait` for NN 04, 05 and 06. Phase 02/public checks used the ordinary local preview. All **188** views use 360/768/1280/1920 CSS pixels, with zero horizontal overflow and zero axe violations. Marketing axe reports a few incomplete checks on decorative arrow glyphs; they remain manual-review items, not claimed automated passes. The palette contrast checks and visual review support the actual text/control colors. Keyboard skip/menu/language controls/focus, reduced motion, real storage preference persistence, preserved form values, second-tab access, logout, 404, empty/incomplete/error/retry and authenticated downloads are exercised. Russian wrapping and actual screenshots were reviewed, including controlled task titles/history. This does not substitute for a real screen-reader audit.

The public demo is exercised in both languages and all four read-only steps while signed in. Its requests are restricted to public demo endpoints; actual report history stays unchanged. Test TXT answers and scanner transports/saved observations are **injected QA fixtures**, never third-party network probes.

## PDF validation and screenshot evidence

Executed `backend/.venv/bin/python scripts/verify-pdfs.py`, which invokes `pdftoppm -scale-to 1200 -png` and `pdftotext -layout` for each of the four downloaded PDFs. **22 total pages** were extracted, rasterized and visually reviewed: LOCAL QA EN **6**, LOCAL QA RU **6**, DEMO EN **5**, DEMO RU **5**. Headers, readable text, wrapped long identifiers, glyphs, margins, page numbers, no clipping/overlap and DEMO on all ten sample pages were checked. [PDF manifest with sizes/hashes and page paths](evidence/phase-07/pdf-results.json). These PDFs are selectable text, not screenshots; PDF/UA tagging/conformance is not certified.

Candidate assignment evidence (actual screenshots; no beta-test claims):

1. [LOCAL QA report readiness, 360px](evidence/phase-07/reports-empty-360.png).
2. [LOCAL QA Russian report history, 1280px](evidence/phase-07/reports-history-ru-1280.png).
3. [Russian guided DEMO priorities, 360px](evidence/phase-07/demo-ru-2-360.png).
4. [LOCAL QA Russian PDF first page](evidence/phase-07/pdf-pages/LOCAL-QA-security-snapshot-ru-1.png).
5. [Russian DEMO PDF work/coverage page](evidence/phase-07/pdf-pages/DEMO-security-snapshot-ru-4.png).
6. [LOCAL QA Russian task details](evidence/phase-07/task-detail-ru-360.png).

[English LOCAL QA PDF](evidence/phase-07/LOCAL-QA-security-snapshot-en.pdf), [Russian LOCAL QA PDF](evidence/phase-07/LOCAL-QA-security-snapshot-ru.pdf), [English DEMO PDF](evidence/phase-07/DEMO-security-snapshot-en.pdf), [Russian DEMO PDF](evidence/phase-07/DEMO-security-snapshot-ru.pdf). LOCAL QA artifacts use real server aggregation/persistence/rendering against deliberately injected observations; they are not real customer assessments. DEMO artifacts use the fixed public fixture. **Live owned-domain E2E remains NOT TESTED.**

## All 18 acceptance gates

| #   | Gate                                                | Status | Basis                                                                                         |
| --- | --------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------- |
| 1   | Baseline and Phase 00–06 preserved                  | PASS   | Verified baseline; full suites plus prior browser flows                                       |
| 2   | Protected reports use persisted authorized evidence | PASS   | Actual API/UI and proof-scoped aggregation tests                                              |
| 3   | Honest coverage, age and incompleteness             | PASS   | No-data/mixed/expired/partial/stale/pending cases                                             |
| 4   | Shared Top 3 and remediation semantics              | PASS   | Existing query reused; done task retains open finding                                         |
| 5   | Actual English PDF                                  | PASS   | Server-rendered selectable six-page QA PDF                                                    |
| 6   | Readable Russian/Cyrillic PDF                       | PASS   | Extraction, glyph checks and rendered visual review                                           |
| 7   | Durable immutable history/downloads                 | PASS   | Changed evidence and restarted containers; identical bytes                                    |
| 8   | Tenant/file/auth isolation                          | PASS   | IDOR/session/traversal-shaped IDs; private DB BLOBs                                           |
| 9   | CSRF/Origin, bounds and failure behavior            | PASS   | Strict payloads, concurrency/idempotency/quotas/failure tests                                 |
| 10  | Reports UI states and controls                      | PASS   | Empty/normal/incomplete/error/retry/download/browser flows                                    |
| 11  | Isolated labeled public demo                        | PASS   | Read-only fixture; database/socket and browser isolation tests                                |
| 12  | Every-page DEMO PDF markings                        | PASS   | All ten sample pages extracted/rendered/checked                                               |
| 13  | Functional EN/RU primary journey                    | PASS   | Catalog gates, toggling/persistence/forms and browser journey                                 |
| 14  | Burgundy/red, responsive and accessibility          | PASS   | 188 responsive/axe views, keyboard/reduced-motion and visual review; manual AT limits below   |
| 15  | Automated/tooling/security regressions              | PASS   | 308 backend/78 frontend, quality/build/audits and browser checks                              |
| 16  | Migrations/storage/Docker durability                | PASS   | Additive head/no drift; actual restart byte/session persistence                               |
| 17  | Docs/screenshots/honest evidence                    | PASS   | This report, three guides and labeled QA/DEMO outputs                                         |
| 18  | Scope, local commit and clean tree                  | PASS   | Only Phase 07; final local commit/clean status verified before completion; no push/deployment |

## Known limitations and outstanding manual checks

- **NOT TESTED:** actual owned-domain proof → live bounded collection → real assessment → PDF. No owner-controlled domain/permission was provided. Register/sign in, enroll only your authorized domain, publish its current exact TXT, verify, run bounded checks, wait for evaluation, compare report evidence/Top 3/task semantics and re-download across restart. Do not substitute QA fixtures for this check.
- **NOT TESTED:** Firefox/WebKit, physical devices, real assistive-technology reading and a professional Russian-language review. Native form-validation text follows the browser's locale. Raw immutable technical/source text and customer-entered content intentionally stay unchanged.
- English/Russian and Kazakhstan company-name glyphs are covered; arbitrary scripts/color emoji are not guaranteed by the embedded PDF font. PDFs are not claimed PDF/UA certified.
- Single-owner SQLite MVP, synchronous bounded rendering, process-local request budgets, 20 report attempts/organization lifetime, maximum 80 pages/2 MiB and no report retention/deletion UI. Exceeding limits rejects explicitly, without silently dropping a claimed complete dataset. More extensive storage/worker/distributed rate/retention operations need a later approved scope.
- No production deployment, HTTPS termination setup, external customer testing, beta success metrics, billing or Phase 08/09 features were performed.

## Local use

From this repository run `docker compose up -d --build --wait`; open `http://127.0.0.1:5173`. Existing private `/app` and `/app/reports` require real sign-in/onboarding. The public synthetic story is `http://127.0.0.1:5173/demo`; the design preview is `/preview`. API health is `http://127.0.0.1:8000/api/v1/health`. EN/RU selection does not require another account. Follow [README](../README.md) for the non-Docker frontend/backend/worker commands and [reports.md](reports.md) for evidence eligibility and export steps.
