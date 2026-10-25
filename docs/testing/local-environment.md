# Repeatable local research and engineering environments

Normal compiled release: `docker compose -f compose.local.yaml up --build -d --wait`, <http://127.0.0.1:8080>, readiness `/api/v1/health/ready`. See `../local-release-runbook.md` for exact backup/restore, permissions, failure recovery and cookies. Preserve its database and all earlier phase volumes. No Vite/public tunnel is used.

## Human beta — no seeded tenant and no account

Use a new guest browser/profile/context for each participant, with operator sessions/autofill absent. Open `/demo`, choose EN/RU/KK, reload to initial assets. The public sample is fixed, synthetic, read-only; its browser fetches omit credentials and use only public demo endpoints. It cannot enroll/verify/scan or alter real tenants. Resetting the view/recreating the context resets navigation without deleting any database. Fix the scenario version and consent before the timer. Do not let participants enter secrets into account/domain forms. No telemetry or study-server API is added.

Core human files belong in `research-private/`, initialized by the CLI, not in engineering evidence or Git. Limit access; agree retention/deletion and withdrawal handling before collection. Separate browser contexts prevent port-independent cookie collisions between RC and parallel QA stacks. Native validation language may follow browser settings.

## Developer engineering QA — never count as alpha/beta participants

Existing Phase08 fixtures are reused through a fixed `SHIELDMATE_QA_PHASE=09` configuration; defaults for Phase08 remain unchanged. Only phases08/09 and fixed loopback ports are accepted. Phase09 uses **new** `shieldmate-phase09-qa` and `shieldmate-phase09-restored` projects/volumes at16073/16173; it does not reset earlier data. The QA override mounts synthetic TXT/socket modules around real auth/queue/evaluation/tasks/reporting. Normal release images contain no QA scripts. Never use the override for real company data.

```sh
SHIELDMATE_RC_PORT=16073 docker compose -p shieldmate-phase09-qa -f compose.local.yaml -f scripts/qa/phase08.override.yaml up -d --build --wait
# Optional installed QA tools: PLAYWRIGHT_MODULE, PLAYWRIGHT_BROWSERS_PATH, AXE_MODULE.
SHIELDMATE_QA_PHASE=09 node scripts/verify-phase-08.cjs
SHIELDMATE_QA_PHASE=09 node scripts/verify-phase08-interactions.cjs
SHIELDMATE_QA_PHASE=09 node scripts/verify-phase08-operations.cjs
SHIELDMATE_QA_PHASE=09 node scripts/verify-phase08-report-ui.cjs
SHIELDMATE_QA_PHASE=09 backend/.venv/bin/python scripts/verify-phase-08-pdfs.py
```

The first workflow expects a fresh **disposable** Phase09 QA DB and consumes real quotas. Operations expects a new `phase09.sqlite` backup and an unused Phase09 restore volume. Do not rerun by erasing a valued workspace or bypassing quotas. Archive engineering results and explicitly choose new disposable storage if repeating; never remove another project's volumes. `runtime.cjs` fixes project/origin/output paths, so an unsupported phase is rejected before browser traffic. Phase09 raw outputs live outside Git under `../../work/phase09/engineering`; selected genuine images/PDF pages and logs are copied to `docs/evidence/phase-09/` with engineering-only captions. They contain synthetic data, not human research.

The operations script takes an online verified snapshot and restores into a **new** volume, checks original session/resources/private PDF hashes and migration failure behavior. It never overwrites an existing DB. The workflow also performs actual worker SIGKILL/lease recovery; this is controlled engineering disruption, not a beta task.

Stop test services without removing data:

```sh
SHIELDMATE_RC_PORT=16073 docker compose -p shieldmate-phase09-qa -f compose.local.yaml -f scripts/qa/phase08.override.yaml stop
SHIELDMATE_RC_PORT=16173 docker compose -p shieldmate-phase09-restored -f compose.local.yaml -f scripts/qa/phase08.override.yaml stop
```

Normal8080 remains available. If a real team-owned domain is supplied later, obtain explicit exact-host permission, publish the current real TXT challenge, verify normally and run the bounded check in the actual release. No such owned external E2E has been performed here. A configured resolver, CA/runtime and routing are trusted; there is no container egress firewall or public-deployment approval. See the Phase08 risk register before any later exposure.
