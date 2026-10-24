# Local release candidate — Phase 08

This profile runs compiled React assets behind Nginx and proxies `/api` to FastAPI on the same origin. It is for one local operator, HTTP loopback only. It does not configure internet access, TLS termination, tunnels, trusted proxies or a network egress firewall. Use Docker Engine/Compose v2; first build needs registry/package access.

## Start and inspect

From the repository root:

```sh
docker compose -f compose.local.yaml config --quiet
docker compose -f compose.local.yaml up --build -d --wait
docker compose -f compose.local.yaml ps
curl --fail http://127.0.0.1:8080/api/v1/health/ready
```

Open <http://127.0.0.1:8080>. The default project is `shieldmate-rc`. Only Nginx publishes `127.0.0.1:8080`; backend/worker have no host ports. The normal Phase 00–07 development stack and its `shieldmate_database` volume remain separate. The RC creates `shieldmate-rc_database` and `shieldmate-rc_backups`; no existing database is copied into it automatically.

To choose another loopback port, supply the same value to **every** Compose invocation (including recovery). `.env.local.example` documents it. Compose automatically reads `.env`, not `.env.local.example`; avoid overwriting existing local settings.

```sh
SHIELDMATE_RC_PORT=8081 docker compose -f compose.local.yaml up -d --wait
```

Configuration is explicit in the profile: `local_release`, SQLite file storage, no CORS, fixed loopback HTTP origins, restricted Host values. Validation rejects HTTPS/HTTP-cookie mismatches, malformed origins, memory storage or widened local hosts. HTTPS production remains a different configuration and still requires Secure cookies and HTTPS origins. This profile deliberately does not implement that deployment.

Cookies are HttpOnly, SameSite=Lax, host-only, Path=/api, eight hours; Secure is false **only for local HTTP**. RC uses `shieldmate_rc_session`, development uses `shieldmate_session` to avoid port-independent cookie collisions. Two RC projects on the same hostname still share the RC cookie name: use separate browser profiles for parallel QA/restore/RC sessions. Only language preference is stored in localStorage. Password reset, email verification and MFA are unavailable.

## Health, logs, stop and restart

```sh
curl --fail http://127.0.0.1:8080/api/v1/health
curl --fail http://127.0.0.1:8080/api/v1/health/ready
docker compose -f compose.local.yaml logs --tail=100 backend worker frontend
docker compose -f compose.local.yaml restart backend worker
docker compose -f compose.local.yaml up -d --wait
docker compose -f compose.local.yaml down
```

`/health` is liveness; `/health/ready` requires a readable DB at the exact migration head. It does not prove free disk space, a working external resolver, worker progress or a safe scan result. Worker has process/restart supervision, not a dedicated HTTP health endpoint. Inspect its logs and persisted scan status. `down` retains volumes. Never add `-v` for a valuable workspace.

API startup executes Alembic before Uvicorn; a failed migration exits without starting HTTP. Back up before updating images. Historical migrations remain unchanged; Phase 08 has no schema migration. Check:

```sh
docker compose -f compose.local.yaml exec backend .venv/bin/alembic current
docker compose -f compose.local.yaml exec backend .venv/bin/alembic check
```

Nginx refreshes the internal Docker DNS name; backend recreation may briefly return 502/503. Retry readiness after recovery. Unknown SPA paths render the intentional React 404 page with HTTP 200; API unknown paths return JSON 404. Deep links reload through Nginx. There is no SSR HTTP-status routing.

A graceful worker stop waits up to 65 seconds (network deadline at most 60). A hard crash leaves the run `running` until its 90-second lease expires; API reads/new worker claims reconcile it to `interrupted`. It is never retried automatically. Retained partial evidence must not imply a clean assessment. Retry manually only after restoring safe service and checking the persisted hourly quotas and domain proof. Do not increase quotas to conceal failures.

## Consistent backup

The DB is `/app/storage/shieldmate.db`, user/group 10001. New RC storage/backups directories are mode 0700; entrypoint umask 077 creates DB/backups mode 0600. Existing volumes retain their existing ownership/modes; inspect them before using an older development volume with valuable data. Containers run non-root with read-only roots, tmpfs `/tmp`, dropped capabilities and no-new-privileges.

SQLite currently uses its default rollback journal. If an operator enables WAL, committed records may be in `-wal` while `-shm` coordinates clients. **Never copy only the live main file or remove sidecars.** This command uses SQLite's online backup API, including committed WAL pages, into a new exclusive file:

```sh
docker compose -f compose.local.yaml exec backend .venv/bin/python -m app.maintenance backup /app/backups/pre-update-01.sqlite
```

Choose a fresh filename each time. Verification checks integrity, foreign keys, exact schema revision, all ready PDF blob lengths/SHA256s, and table counts before atomically publishing. Deadline is 120 seconds. It refuses an existing destination, symlink or SQLite sidecar; there is no force/overwrite option. Failures do not replace a good backup. Keep the returned manifest/hash securely alongside the backup. It contains counts, not credentials.

Backups contain password hashes, sessions, evidence, private notes and report blobs. They are not encrypted by this application. Keep the named volume private, retain multiple dated copies on trusted storage, and restrict operator access. Do not commit or upload DBs. Docker host administrator access is outside application tenant isolation.

## Restore into a new volume — never over the running DB

Use the **matching build/schema head**. Stop nothing in the source; backup is consistent online. Create a fresh destination name; the command refuses reuse:

```sh
docker run --rm --network none --read-only --tmpfs /tmp \
  --mount source=shieldmate-rc_backups,target=/backups,readonly \
  --mount source=shieldmate-restore-check_database,target=/app/storage \
  shieldmate-backend .venv/bin/python -m app.maintenance restore \
  /backups/pre-update-01.sqlite /app/storage/shieldmate.db
SHIELDMATE_RC_PORT=8082 docker compose -p shieldmate-restore-check -f compose.local.yaml up -d --wait
curl --fail http://127.0.0.1:8082/api/v1/health/ready
```

Compare manifests, sign in using the original account in a separate browser profile, and check organization, domains, scan observations, findings, task history and immutable PDF hashes. Sessions are restored, but already-expired/revoked sessions remain invalid. Application-level counts naturally change when downloads append audit events. This procedure does not roll migrations backward or merge databases. Keep the source volume intact until recovery is accepted. To switch the operator to the recovered data, use the recovered project's localhost URL; do not overwrite the old volume.

The Phase 08 rehearsal restored 9 saved reports and all account/domain/scan/finding/task records into `shieldmate-phase08-restored_database`; see `evidence/phase-08/checks/operations.json` for exact counts and hashes. WAL consistency and storage-full/no-partial-backup failures also have regression tests.

## Disposable fixture QA

Fixtures are mounted only by the QA override and are absent from production images. They use reserved `qa-*.example.com` names and synthetic DNS/socket responses around the real persistent queue and evaluator. Never add this override to a real workspace.

```sh
SHIELDMATE_RC_PORT=15873 docker compose -p shieldmate-phase08-qa -f compose.local.yaml -f scripts/qa/phase08.override.yaml up -d --wait
# Requires local optional Playwright Chromium and axe-core; see docs/testing.md.
node scripts/verify-phase-08.cjs
node scripts/verify-phase08-interactions.cjs
node scripts/verify-phase08-operations.cjs
node scripts/verify-phase08-report-ui.cjs
python scripts/verify-phase-08-pdfs.py
python scripts/phase08-contact-sheets.py
```

The browser workflow expects a fresh QA database and consumes real quotas. The operations script expects a new `phase08.sqlite` backup and unused restore destination. Preserve evidence before resetting. To deliberately erase only these disposable fixtures, stop the two named QA projects and remove their volumes, after checking project names with `docker volume ls`. Do not reset `shieldmate`, `shieldmate-rc`, or an operator workspace. Browser storage-state/credential files belong in private ignored work storage, never in Git.

## Failure recovery

- Readiness 503: inspect schema/revision, file permissions, disk capacity and DB lock contention. Correct the cause; do not bypass migration validation.
- Disk full: free trusted expendable storage, retain backups, retry. Transactions roll back; generic API 500 does not expose SQL parameters. Do not treat a failed report as ready.
- Invalid environment: startup validation exits with values hidden. Fix configuration rather than enabling wildcards/CORS or weakening cookies.
- Missing owned DNS/network: use the clearly labeled public Sample Demo. Never invent TXT proof or scan a third-party target.
- Corrupt report/renderer failure: download is denied for failed/corrupt artifacts; retry generation with a new request only after the underlying cause is fixed. Existing ready bytes are immutable.
- Browser network failure: private data remains hidden during identity revalidation; retry or sign in again. Cross-tab logout clears the old workspace/drafts. A malicious local process or existing XSS is outside this frontend privacy boundary.
