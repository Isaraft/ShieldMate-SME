# Phase 00 implementation and verification

Date: 23 October 2026. Scope: **Phase 00 only**. Phase 01 is **NOT STARTED**.

## Repository assessment and decisions

Reviewed all five supplied Markdown files and visually inspected all three PNGs before
implementation. All eight originals remain byte-for-byte unchanged; their hashes are in
`archive-review.json`. The source directory contained only the ZIP and had no repository
history. A local `main` repository now preserves the supplied kit in its own baseline commit.

The implementation uses the requested React/TypeScript/Vite/Tailwind and
FastAPI/Pydantic/SQLAlchemy/Alembic stack. SQLite has an empty foundation migration, not
premature business models. The only live API is `GET /api/v1/health`.

The visual concept is deep burgundy, crisp crimson accents and warm ivory, with Anton
display type and IBM Plex Sans body text. The small welcome panel is expressive; workspace
placeholders are restrained and legible. Fonts are local WOFF2 assets with included licenses.
Slide layouts, presenter details, subscription claims and fictional business metrics were
not copied into the interface. See `architecture.md` for the implementation rationale.

## Files and behavior

- `frontend/`: accessible shell, routing, planned-feature states, 404, real local API
  connection/loading/error/retry states, centralized tokens, tests and build/lint tools.
- `backend/`: modular settings, health router, stable error envelope, SQLAlchemy session
  foundation, SQLite constraints, Alembic baseline and isolated tests.
- Root: local Compose services, safe environment example, ignore rules and README.
- `docs/`: architecture, test guidance, archive review, actual screenshots and results.
- `frontend/package-lock.json` and `backend/uv.lock`: resolved dependency locks.

There is no authentication, organization onboarding, domain submission/verification,
scanning, finding engine, task persistence, PDF, sample dataset, billing or deployment.

## Commands and actual outcomes

Commands below were executed in the relevant project subdirectory. `uv` was installed
as version 0.13.5 in an isolated workspace tooling environment because it was initially
absent. Backend direct `.venv/bin` commands are equivalent to the README's `uv run` commands.

| Command | Actual result |
|---|---|
| `uv lock` and `uv sync --locked` | PASS — locked and installed Python dependencies. |
| `.venv/bin/pytest -q -o faulthandler_timeout=15` | PASS — 12 tests, one dependency deprecation warning. |
| `.venv/bin/ruff check .` | PASS. |
| `.venv/bin/ruff format --check .` | PASS — 13 files formatted. |
| `.venv/bin/mypy app` | PASS — seven source files, no issues. |
| `.venv/bin/alembic upgrade head` | PASS — revision `0001_foundation`. |
| `.venv/bin/alembic check` | PASS — no schema drift. |
| `.venv/bin/pip-audit --progress-spinner off` | PASS — no known vulnerabilities. |
| `npm install --no-fund` / subsequent patched install | PASS — lockfile generated and patched test tooling installed. |
| `npm test` | PASS — 15 tests across two files. |
| `npm run lint` | PASS — zero warnings. |
| `npm run typecheck` | PASS. |
| `npm run format:check` | PASS. |
| `npm run build` | PASS — production assets generated; four WOFF2 files. |
| `npm audit --audit-level=low` | PASS — zero reported vulnerabilities. |
| `docker compose config --quiet` | PASS. |
| `docker compose up --build --wait` | PASS after installer and network fixes — both images built and both services healthy. |
| Container runtime and recreation checks | PASS — health at ports 8000/5173, CSP/deep links, non-root users, read-only roots and unchanged SQLite file across `down` / `up --wait`. |
| `git diff --check` | PASS. |

Development startup was exercised with Uvicorn on loopback port 18000 and Vite on 15173
using `API_PROXY_TARGET=http://127.0.0.1:18000`, leaving the documented Docker ports free.
The real health response arrived through the frontend proxy. A real backend outage displayed
Unavailable; starting the backend and selecting Retry recovered to Responding.

Chromium 151 checked the welcome screen, asset placeholder and 404 at 360, 768, 1280 and
1920 CSS pixels: all 12 route/viewport combinations had no horizontal overflow. Skip-link
focus, visible 3px focus outline, route focus transfer, disabled registration, direct-route
refresh and reduced motion passed. No page errors or external browser requests occurred.
The same browser checks were run against both the Vite development server and the final
Docker-served static build. Six actual screenshots were visually inspected; they are in `evidence/` with the browser,
recovery and contrast results. Text color combinations tested range from 4.71:1 to 15.24:1,
meeting AA for normal text. These focused checks are not a full accessibility certification.

### Failures encountered and resolved

The first frontend test run found missing whitespace in the accessible heading across a
line break: 14 passed, one failed. The actual heading was corrected and all 15 passed.
The initial backend format check found one file to format; it was fixed. The first npm
audit reported one moderate and two critical dependency entries in the old Vitest chain;
Vitest was upgraded to patched 4.1.12 and ESLint to supported 10.13.0. The final audit is clean.

Initial sandboxed downloads failed DNS resolution; authorized network access resolved
installation. Sandboxed FastAPI TestClient hung and was stopped; the same tests passed
outside the socket-restricted sandbox in 0.20 seconds. The installed Starlette emits a
deprecation warning for its still-working HTTPX TestClient fallback. The host's Node 26
emits a `module.register()` deprecation warning during Vite builds; builds still pass.
Neither warning is hidden or represented as a failing test.

The initial Docker uv download step stalled for over nine minutes and was canceled. The
image now exports hashed requirements from the same frozen uv lock and installs using
pip `--require-hashes`; this completed successfully. The first internal Docker network
suppressed published ports despite passing in-container health. Runtime testing caught it;
a standard bridge with explicit loopback bindings fixed host access. Both fixes were
retested. No scanner or external-domain request endpoint is enabled.

## Security and quality checklist

- PASS: no secrets, credentials, remote checks, fabricated results or customer claims.
- PASS: explicit host allowlist; CORS disabled by default, no credentialed wildcard.
- PASS: typed health response, validated configuration, safe errors without submitted input.
- PASS: foreign keys enabled, migration-managed schema, temporary databases in tests.
- PASS: loopback ports, non-root container configuration, read-only roots, persistent volume,
  standard bridge network and no external font/image fetches. Outbound networking is not
  firewall-blocked; scanner egress controls are deferred with the scanning capability.
- PASS: keyboard navigation, state text alongside color, reduced motion and contrast checks.
- Deferred by phase: auth/session/CSRF, organization isolation, rate limits on sensitive
  actions, domain verification, SSRF and production TLS. No dependent capability is enabled.
- Owner setup: Docker/Compose or supported Node/Python/uv and free local ports. Phase 00
  requires no secret, domain, cloud account or production token. Do not expose it publicly.

## Phase 00 acceptance

| Objective from PHASE_00 | Status and evidence |
|---|---|
| 1. Assess repository and choose architecture | PASS — full archive review and architecture record. |
| 2. Establish understandable structure | PASS — frontend, backend, docs, root config and tests. |
| 3. Frontend shell, routing, tokens, 404 | PASS — automated and actual browser checks. |
| 4. Backend config, DB/migrations, health | PASS — 12 tests, migration drift check and real health response. |
| 5. Local Docker services and persistence | PASS — both services healthy; loopback access and volume persistence verified. |
| 6. Tests, lint, type checks, locks and safe config | PASS — checks above; zero audit findings. |
| 7. Reproducible documentation and explicit limitations | PASS — manual startup and fresh container builds/startup verified. |
| 8. Honest planned states, no fabricated features | PASS — all future routes clearly labeled. |
| 9. Safe foundation defaults | PASS for this scope; later controls explicitly deferred. |
| 10. Run and report actual checks | PASS — all required checks completed; actual outcomes and initial failures recorded. |

NOT TESTED / outside this phase: production hosting/TLS, full assistive-technology audit,
other browser engines, authentication, live scans, PDFs and real-user alpha/beta sessions.
No claims are made for these activities.

## Run locally and handoff

Use the exact Docker or two-terminal manual commands in `README.md`. The backend liveness
endpoint is `/api/v1/health`; the local UI is `http://127.0.0.1:5173` with the documented
default ports. No data migration or credential setup is needed beyond `alembic upgrade head`.

Phase 01 may define the complete brand system, landing page and reusable UI kit after owner
approval. Keep the existing foundation, locks, honest placeholders and tests. Do not start
authentication, scanning or any subsequent phase as part of that design work.
