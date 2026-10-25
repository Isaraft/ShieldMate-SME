# Phase 10 — local preparation complete; upload blocked

**Date:** 25 October 2026 (Asia/Almaty). **Baseline:** clean `main` at `8040755`;13 commits; one reachable ref (`refs/heads/main`);no remote/tag. **Final tested code/packaging candidate:** `4964696`. The ending local commit is the handoff commit containing this report (`git log -1 --format='%h %s'`); final status is checked after committing. No push, GitHub repository creation, tag/release publication, external deployment, tunnel, ref deletion or history rewrite occurred.

**Decision:** local release-engineering work is complete, but **neither private upload nor public publication is cleared**. Personal/history exposure and team/asset permissions remain blocked. There are no completed human alpha/beta results; Phase 09 H13–H18 remain PENDING.

## Review and implementation

Read the full supplied Phase 10 brief (retained in `PROMPTS/PHASE_10.md`), AGENTS, specification/roadmap, architecture/scanner/reporting/security documentation, prior phase reports, research kit, local release/recovery procedures, existing source/manifests/configuration and reachable Git history. Initial source statements were reviewed as historical instructions, not evidence of actual users, ownership permissions or deployment.

- Replaced the stale README with a portable English overview, current scope/stack/architecture diagram, actual labeled captures, clean local setup, workflow, tests, backup/stop references, limitations, team acknowledgment and accurate unselected-license status. Removed contradictory “Phase07 not started” assertions. Public demo is read-only and synthetic; no claim of live assessments/customer adoption is added.
- Added `SECURITY.md`, `THIRD_PARTY_NOTICES.md`, proposed unreleased `CHANGELOG.md`, publication audit and 20-gate readiness report. No project license or attribution ownership was assigned. Existing font OFL notices stay intact; full installed notices for **nine npm runtime packages** now ship as `frontend/public/licenses/third-party-runtime.txt`.
- Added least-privilege GitHub Actions with immutable reviewed action SHAs, `contents: read`, no persisted checkout credentials, bounded jobs and no secrets, privileged pull_request_target, release/upload/deployment steps. Portable deterministic tests run without real owned DNS, instructor materials or research participants. Hosted Actions has **not** run.
- Added typed standard-library `scripts/publication/audit.py`: all reachable refs/trees/blob aliases, current tracked bytes, sensitive paths/modes, signatures/literals and redacted locations. It refuses output overwrite; it does not modify history or emit matched values. Six internal-marker tests exercise detectors and deleted/aliased historical data without real credentials. gitleaks is absent and is not claimed as passed.
- Redacted identifying checkout/home prefixes in **19 current documentation/evidence files**; recorded the manifest and kept outcomes/dates/counts. Original history remains exposed and blocked pending consent/remediation. No archived source specification or binary was removed. Current architecture/testing docs distinguish historical phase snapshots from the implemented MVP.
- Extended Git ignores for private publication/QA/report/backup outputs and key/archive formats. Verified 21 allowed/ignored path cases. Fixed actual Docker context gaps, described below.

## Confirmed defects fixed

### Accessible brand name

The actual demo browser's full axe rules found `label-content-name-mismatch` in header/footer across EN/RU/KK: DOM text joined `SHIELDMATE` and `SME` without a space while aria-label used two words. Added explicit text spacing in `frontend/src/components/SiteChrome.tsx`. Styling/tokens/layout/catalogs are unchanged. Three new language-specific tests **failed before** the fix and pass afterward; full frontend grows98→101. New actual browser smoke finds zero violations in 12 localized views.

### Docker build-context privacy

The root allowlist re-included all frontend files, so a nested frontend environment file could enter the build; backend ignore rules also lacked generalized secret/private-file exclusions. Two **harmless marker files**, not credentials, reproduced inclusion with controlled scratch COPY builds. Both `.dockerignore` files now exclude nested env/key/P12/PFX/database/log/private-storage/QA outputs. Repeating both probes produces expected COPY-not-found exit1. Probe files were removed; no real env/private material was read/copied. Production frontend/backend builds and served runtime notices pass after tightening. No scanner/auth/tenant policy was weakened.

Backend app source, migrations, dependency locks and all catalogs remain unchanged. The only frontend source change is the logo's text whitespace; public license notices are additional static text. No feature sprint, redesign, fake assessment or research data was introduced.

## Redacted audit findings

[Publication audit](phase-10-publication-audit.md) contains classifications and remediation; [raw redacted candidate output](evidence/phase-10/history-audit-packaging-candidate.json) contains only locations/categories/object identifiers, not values.

- Baseline reachable history: **13 commits, 2,019 objects, 1,766 unique blobs, 151,027,426 bytes**. Repeated through all preparation candidates: **17 commits, 2,107 objects, 1,814 unique blobs, 151,378,643 bytes**. Final handoff adds docs/evidence and is scanned again locally after commit. No unexpected branch/tag/remote/ref was found.
- No real credential requiring rotation, committed SQLite database/private runtime `.env`, browser state/cookie dump or human participant-storage tree was confirmed by targeted review. Risky historical filenames were only the two safe environment examples. Credential candidates were reserved-name rejection/auth fixtures, UI labels, deliberate internal test markers, one fake Assets challenge literal and public upstream contact/copyright notices retained under their licenses. This is not proof that every possible secret is absent.
- **1,080 unique images** were actually OCR-processed and **37 PDFs** text-extracted; final extraction errors: 0. All PDFs contain QA/DEMO context. Twelve images produced email-like candidates, all reserved-domain synthetic fixtures on reinspection. Four historical font binary versions retain adjacent OFL notices; current source hashes and renamed derivative internal names match. No incompatible font license was confirmed.
- **BLOCKED:** personal author/committer email in history (value withheld), historical identifying home prefixes, intentional team/instructor identities and unconfirmed team/IP/reference-slide/QA-image redistribution permissions. Source possession is not publication permission. Unknown source rights are not falsely labeled incompatible licenses, and private visibility does not make exposure safe.
- English OCR can miss small/Cyrillic/Kazakh text and does not verify consent/rights. Only selected captures were visually reviewed; no manual inspection of all 1,080 images is claimed. Patterns do not provide an entropy audit, credential validity check, independent penetration test or unreachable/reflog scan. gitleaks and independent final privacy/native review remain unavailable/pending. Ignored real operator data was not ingested.

## Commands and real outcomes

Commands were executed in the main checkout and, separately, a local no-hardlink clone from committed files. Logs under `docs/evidence/phase-10/` are redacted for path privacy. The fresh clone used no existing `.env`, app volume, account or seed DB. Dependency caches may be reused for exact locked downloads; environments/node_modules were installed afresh. Host: Python 3.14/Node 26.12.1 (supported range); Docker builds use Python 3.13/Node 24. CI targets 3.13/24 but has not run on GitHub.

| Directory / command | Actual result |
|---|---|
| root: `git status --porcelain`, `git branch --show-current`, `git rev-parse HEAD`, `git log`, `git for-each-ref`, `git remote` | Clean expected baseline; one main ref; no remote; no URLs/identity values printed in report |
| root: `python scripts/publication/audit.py --output <new-private-output.json>` | Full reachable baseline/candidate and current tracked-category scans completed; limits above |
| private audit tooling: Git blob reads + `pdftotext -layout` / `tesseract --psm 11` |37 PDFs +1080 images processed; 0 final extraction errors; 12 reserved-fixture email candidates |
| backend: `.venv/bin/pytest -q` | **325 passed**, 72.92s, one existing Starlette/httpx deprecation warning |
| backend: `.venv/bin/ruff check .`; `.venv/bin/ruff format --check .`; `.venv/bin/mypy app` | PASS; 51 app source files typed |
| frontend: `npm test -- --reporter=json --outputFile=<private-output.json>` | Baseline98 passed; after logo fix **101 passed**,0 failed |
| frontend: `npm run lint`; `npm run typecheck`; `npm run format:check`; `npm run i18n:check`; `npm run build` | PASS; 976 keys×3/576 references; existing >500kB build warning retained |
| root: `backend/.venv/bin/pytest scripts/tests -q` | **55 passed**, 0.75s; 49 research +6 publication internal-marker tests |
| root: `backend/.venv/bin/mypy --strict scripts/research scripts/research_evidence.py scripts/publication` | PASS, 8 sources |
| root: `backend/.venv/bin/ruff check --config backend/pyproject.toml scripts/research scripts/research_evidence.py scripts/publication scripts/tests scripts/verify-phase-08-pdfs.py` | PASS |
| root: same targets with `ruff format --check` | PASS, 12 files |
| root: `node --test --test-reporter=tap scripts/tests/qa-runtime.test.cjs` | **3 passed** |
| root: `python -S scripts/research_evidence.py scenario` | PASS, frozen fixture/rubric/material/UI/catalog definition remains unchanged |
| frontend: `npm audit --json` |0 known advisories, 347 dependency records |
| backend: `.venv/bin/pip-audit --format json` |0 known advisories, 68 packages |
| local tool: `actionlint -color=false .github/workflows/ci.yml` | PASS, actionlint 1.7.12,official release checksum verified; hosted execution NOT TESTED |
| root: `frontend/node_modules/.bin/prettier --check .github/workflows/ci.yml scripts/verify-publication-smoke.cjs` | PASS |
| local clone: `git clone --no-local <local-source> <isolated-checkout>`; `uv sync --locked --python 3.14` from backend | PASS; fresh backend environment, safe config, no secret env/seed |
| clone backend: `uv run --frozen pytest -q`; Ruff/format/mypy commands | **325 passed**, 91.50s; all static checks PASS |
| clone backend: `uv run --frozen alembic upgrade head`; `uv run --frozen alembic check` | PASS, head `f34f9df9b6a4`,no drift |
| clone frontend: `npm ci`; full npm test/lint/typecheck/format/i18n/build commands | PASS; after final source refresh **101 tests passed**; runtime notices match build output |
| clone root: evidence/tool tests/static; Node tests; scenario check | PASS; final55 tooling, 8 typed sources, 3 Node tests; detailed command arrays in `clean-results.json` and refreshed final logs |
| clone root: `SHIELDMATE_RC_PORT=16273 docker compose -p shieldmate-phase10-clean -f compose.local.yaml up --build -d --wait` | PASS from final candidate 4964696; new private volume, compiled frontend, loopback-only entry |
| clone: same Compose prefix `exec -T backend .venv/bin/alembic current` / `alembic check` | Correct head; no new operations |
| controlled scratch Docker builds before/after privacy fix | Both env markers included before; both excluded after with expected exit1; no real secrets used |
| root: `node scripts/verify-publication-smoke.cjs` with optional local browser modules and private output env | **12 views PASS**: EN/RU/KK×360/768/1280/1920,zero axe violations/overflow/page errors; `/app`→`/login`,unauthenticated reports 401; CSP remains enforced |
| fresh downloaded demo PDFs: pypdf extraction/marking checks | **3 PDFs /18 pages**,each page DEMO, text extractable, hashes retained; no real private report copied |
| root: `docker compose -f compose.local.yaml up --build -d --wait`; readiness curl | PASS; current preview8080 updated, existing database retained |
| `git check-ignore --no-index` assertions; `git diff --check`; unchanged-backend/migration/lock diff | PASS; 21 ignore cases; only described frontend source change |

Initial new browser instrumentation using addScriptTag was blocked by the real CSP; the harness now uses debugger init injection and separately asserts unchanged restrictive response headers. Its first guessed sign-in route was corrected to the actual `/login`. Repeated debug PDF downloads legitimately reached 429; no limits were raised. Only the disposable clean backend was restarted, and a premature connection attempt during recreation was rerun after actual readiness. Final once-ready run passes. These harness/environment failures are not hidden as application passes. Initial OCR attempts failed because English data was missing; official immutable-source language data was downloaded outside Git and all images were successfully rerun. Source/checksum records remain; downloaded tools/data are not redistributed.

## Acceptance, files and remaining work

**17 PASS; G04/G05/G18 BLOCKED.** All20 rows and evidence are in [release readiness](phase-10-release-readiness.md). CI definition/portable commands pass locally; an actual hosted GitHub run is NOT TESTED. No production security certification, complete-image CVE/SBOM scan, independent legal/privacy/native review or real owned-domain external E2E is claimed. Mutable image tags, SQLite/single worker/process-local limits and the Phase 08 risk register still apply.

[Changed-file manifest](evidence/phase-10/changed-files.txt) lists the complete baseline-to-handoff set. Main groups: README/security/notices/changelog/prompt; `.github/workflows/ci.yml`; Git/Docker ignores; current architecture/testing and redacted historic docs/logs; publication audit tooling/tests; logo whitespace/regressions; redacted technical evidence. No new binary/font/dependency or human dataset is committed.

Preview remains at <http://127.0.0.1:8080>. Start from root with `docker compose -f compose.local.yaml up --build -d --wait`; stop with `docker compose -f compose.local.yaml down` **without -v**. The isolated16273 clone stack is stopped after verification; its volume is retained. No existing user volume or baseline QA data is deleted. Backup/restore procedures remain in [local release runbook](local-release-runbook.md).

## Approval and private-first handoff

1. Confirm team/lecturer/IP/license and reference-image permissions; approve whether existing author/instructor/team names and historical home/email exposure may be uploaded. Values are intentionally withheld from this report. If remediation is needed, separately approve an exact strategy; no history rewrite has occurred.
2. Arrange independent final binary/privacy review and, if desired, an additional established secret scan. If an actual secret is found, stop uploads and rotate/revoke it before deciding on history cleanup.
3. Approve exact GitHub account/repository name and **private-first** visibility. No owner, URL, contact address or remote was invented.
4. Only after approval: recheck the clean branch/audit, create an empty private repository, add the approved origin if absent, and push main only. Independently audit the remote copy and actual Actions runs. Public visibility/tag/release/deployment require separate approval.
5. Phase 09 H13–H18 remain pending: actual alpha/beta consent, sessions, timings, analysis, contributions, academic submission and lecturer logistics. GitHub publication does not manufacture that evidence.

**Stop here. No upload or next phase is authorized by this report.**
