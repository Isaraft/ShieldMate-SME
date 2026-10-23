# ShieldMate SME Starter — Phase 06

**Phase 02: real accounts and one company workspace per owner.** Register, sign in,
create/rename your organization, reload with a persistent cookie session and sign out.
Domain enrollment and DNS TXT ownership proof are implemented. Authorized, bounded DNS/TLS/HTTP configuration checks now run through a durable worker.
Evidence-backed findings, contextual priorities and finding history are now available. A connected dashboard and persistent remediation tasks are available. Reports and payments remain planned.

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
before starting the backend and waits for its health before starting the frontend and worker.
All containers run as non-root and have read-only roots. A standard bridge network supports
the loopback port mappings. Application probes are pinned to vetted public IPs; no network-level
egress firewall is supplied for this local setup. The named
`database` volume stores SQLite at `/app/storage/shieldmate.db`.
Compose supplies fixed local settings; it does not import `.env` into containers.

```sh
docker compose logs backend frontend worker
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

Phase 07 has NOT started. Do not implement it without explicit owner approval.

## Domain ownership (Phase 03)

Open `/app/assets`. Enter a domain only, such as `shop.example.com`, with no URL, whitespace,
port or path. ASCII and valid Punycode are supported; direct Unicode input is rejected.
A public registrable domain is required; public suffixes and internal/special names are rejected.
Acknowledge that you control it or have written authorization. Enrollment makes no DNS request.

Create the displayed separate TXT record at your own DNS provider, then choose Verify ownership.
Check whether your provider appends the zone to avoid duplicating the hostname. Do not modify
SPF/DMARC. DNS propagation has no guaranteed time; missing records stay pending and resolver
failures remain inconclusive. Challenges expire after 48 hours; a successful proof is fresh for
30 days. Generate new challenge revokes previous proof and requires replacing the TXT value.
TXT values are public domain-control proofs, never login credentials. DNS control alone does
not authorize tests against every underlying server. Only the exact eligible hostname can be checked.

Default quota is five domains. `.env.example` documents limits and lifetimes. Restarting
`docker compose restart backend` preserves domains/challenges; `docker compose down` preserves
the database volume. See [Phase 03 results](docs/phase-03-results.md) for commands, state rules,
manual DNS setup, security tests and the explicit absence of live DNS-provider E2E evidence.

## Authorized security checks (Phase 04)

In a third terminal for manual development, from `backend/`, run:

```sh
uv run python -m app.scanner.worker
```

Compose starts this worker automatically. After enrolling an **actually authorized, team-controlled**
domain, publish and verify the real TXT proof. Choose **Run security checks** in Assets.
The scan record polls while queued/running and stops on completion, partial completion, failure
or interruption. Open **Scan history** for persisted records. Status is execution status,
not a whole-site safety verdict. Findings now interpret these saved observations offline; no security score is calculated.

Defaults: 6 scans/user/hour, 6/org/hour, 2/domain/hour; one active scan/domain;
20 queued/running jobs globally; one worker slot, sequential checks; 45s network budget,
3s individual I/O timeout, 90s worker lease and 15m queue expiry. `.env.example` applies
to manual execution; edit matching service environment values to change Compose settings.
History retains up to 100 runs/org, evicting an oldest terminal run older than one hour
when a new run needs space. Deleted assets revoke execution; their minimal scan snapshots
remain under that bounded organization retention policy, inaccessible through deleted-asset routes.

DNS A/AAAA, MX, SPF and basic DMARC context; trusted TLS hostname/certificate validity;
root HTTPS status/security-header observations; optional HTTP80 redirect observation are checked.
Every application connection re-resolves all A/AAAA answers, rejects mixed/nonpublic answers,
and connects to one pinned public numeric IP with the correct Host/SNI/trust validation.
No redirects, proxies, crawling, response bodies, cookie collection, arbitrary ports or paths.
CNAME-only, truncated/ambiguous DNS, unsupported names, TLS failures and timeouts are inconclusive.
The configured OS recursive DNS resolver is the trusted DNS infrastructure boundary.

See [Phase 04 implementation, threat model and actual evidence](docs/phase-04-results.md)
and [the scanner design](docs/scanner.md). No real owned-domain live scan has been exercised
in the supplied environment; browser screenshots use an isolated, visibly labeled QA fixture stack.
Never run the `scripts/qa/` harness as the application or present it as live security evidence.

## Evidence-backed findings (Phase 05)

Open `/app/findings` after an authorized scan. The existing worker evaluates retained
terminal scans offline and persists six versioned rule decisions. The list includes a
Limited External Configuration Assessment, a server-ranked Top 3 of actual open findings,
filters, pagination and a Business/Technical presentation toggle. Each detail shows impact,
action, sanitized evidence, source time, severity reasoning and lifecycle history. Scan
history links directly to its related findings.

Only comparable conclusive evidence resolves a finding. Failed, missing or inapplicable
checks preserve the previous state with a Not rechecked label; fresh evidence can reopen
the same finding. Old evidence is labeled stale (default seven days). No fabricated CVEs,
security score, task completion or whole-company security verdict is provided.

The worker automatically backfills existing eligible Phase 04 scans. For an explicit,
organization-scoped local maintenance pass (from `backend/`):

```sh
uv run python -m app.findings.backfill --organization-id YOUR_ORGANIZATION_UUID
```

For Compose, run from the project root:

```sh
docker compose exec -T backend .venv/bin/python -m app.findings.backfill --organization-id YOUR_ORGANIZATION_UUID
```

Repeating the command returns zero new evaluations.
It makes no network requests and never accepts user-supplied findings. Start the normal
scanner worker even if only backfilling; API reads do not evaluate scans.

Revision `9752376ee8f2` adds findings/evaluations/events after the Phase 04 migration.
Source scan retention remains bounded; sanitized finding snapshots survive source pruning.
History retains at most 50 events per finding, visibly disclosing compaction. Removing an
asset deletes its derived findings/history, as disclosed by the confirmation dialog.
See [risk methodology](docs/risk-methodology.md), [Phase 05 results](docs/phase-05-results.md)
and [architecture](docs/architecture.md) for rule caveats, API contracts and actual checks.

## Dashboard and action workflow (Phase 06)

Open `/app` for your organization overview: current ownership scope, saved findings and
Phase 05 Top 3, human task workload, coverage, recent scans and real work activity. Counts
come from scoped persisted records; no global security score is calculated. Create a task
from a supported open finding, then use `/app/tasks` to filter work or edit its owner label,
note and status. Work history records actual changes and survives reload/restart.

**Done by a person is not technical resolution.** An open finding remains open until a
later authorized, conclusive check resolves that exact condition. Stale/incomplete evidence
and recurrence are labeled. Recheck links lead to existing asset controls; fresh DNS proof,
authorization, quotas and network safety still apply. No automatic scans or remediation occur.

Additive migration `e53b215e4b66` follows Phase 05. Compose applies it on startup; manual
execution remains `cd backend && uv run alembic upgrade head`. No seeding or new credentials
are required. Existing local data remains in the same volume. Never use the isolated QA
harness as the ordinary app or present its screenshots as live assessments.

See [remediation workflow/API/retention](docs/remediation-workflow.md) and
[Phase 06 verification and screenshots](docs/phase-06-results.md). Phase 07 reports/demo
remain unimplemented and require explicit approval.
