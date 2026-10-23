# ShieldMate SME Starter — Phase 02

**Phase 02: real accounts and one company workspace per owner.** Register, sign in,
create/rename your organization, reload with a persistent cookie session and sign out.
Domain verification, external scanning, findings, tasks, reports and payments remain planned.

The Phase 01 burgundy/red landing and public design preview are preserved at `/preview`;
`/app` is private and `/app/settings` edits your actual company. See
[Phase 02 implementation and security details](docs/phase-02-results.md).

## Run with Docker

Requirements: Docker Engine and Docker Compose v2 or newer, working registry access, free
loopback ports 5173 and 8000. From this project directory:

```sh
docker compose config --quiet
docker compose up --build --wait
docker compose ps
curl --fail http://127.0.0.1:8000/api/v1/health
```

Open <http://127.0.0.1:5173>. Expected health body: `{"status":"ok"}`. Compose runs migrations
before starting the backend and waits for its health before starting the frontend.
Both containers run as non-root and have read-only roots. A standard bridge network supports
the loopback port mappings; there is no scanner or domain request endpoint. The named
`database` volume stores SQLite at `/app/storage/shieldmate.db`.
Compose supplies fixed local settings; it does not import `.env` into containers.

```sh
docker compose logs backend frontend
docker compose down
```

`down` preserves the database volume. Do not add `--volumes` unless you intend to erase it.
This is a local HTTP setup, not an approved production deployment.

## Run without Docker

Requirements: Node 24 LTS recommended (22.12+ supported), Python 3.13 or 3.14, and
[uv](https://docs.astral.sh/uv/getting-started/installation/). Tested lock tooling is uv 0.13.5.
Install uv separately if needed: `python3 -m pip install --user uv==0.13.5` in an environment
that allows user installs, or use the official installer. Do not use system-wide sudo pip.

From the project root, copy local settings only if `.env` does not already exist:

```sh
cp -n .env.example .env
cd backend
uv sync --locked
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log --no-server-header
```

In a second terminal, starting at the project root:

```sh
cd frontend
npm ci
npm run dev
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` to port 8000, so no browser CORS
allowlist is needed. Stop each process with Ctrl+C. Local SQLite is in `backend/storage/`
and is ignored by Git. No secrets, credentials or cloud accounts are required for this preview.
On `/app`, if the API is stopped, the UI reports unavailable and provides a connection retry.

## Verify

From `backend/`:

```sh
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run alembic upgrade head
uv run alembic check
uv run pip-audit
```

From `frontend/`:

```sh
npm ci
npm test
npm run lint
npm run typecheck
npm run format:check
npm run build
npm audit
```

From the project root: `docker compose config --quiet`. See
[testing](docs/testing.md) for scope and manual checks, and
[Phase 01 results](docs/phase-01-results.md) for current outcomes and limitations.
[Phase 00 results](docs/phase-00-results.md) remain as historical evidence.
The `preview` script serves static build output only; use the dev server or Compose for
the same-origin backend connection.

## Layout and next steps

- `frontend/src/`: layout, routing, planned pages, connection state and centralized tokens.
- `frontend/tests/`: render, routing and connection-state smoke tests.
- `backend/app/`: versioned health/auth/organization routes, validated settings, models and safe errors.
- `backend/migrations/`: foundation plus user, organization and session schema.
- `backend/tests/`: API contract, safe errors/configuration and migration tests.
- `docs/`: architecture, review evidence, test guidance and original design references.
- `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, `PROMPTS/PHASE_00.md`: supplied rules.

Read [architecture and decisions](docs/architecture.md) before extending the app.
See [the design system](docs/design-system.md) for tokens, component patterns and SEO
limits. `/` is the public landing page, `/app` the private workspace, and `/preview/ui-kit`
the public interactive component reference. `/preview` holds the public design shell.

Phase 03 has NOT started. Do not implement it without explicit owner approval.
