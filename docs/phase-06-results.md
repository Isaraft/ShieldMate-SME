# Phase 06 — Connected Dashboard, Remediation Tasks & Action Workflow

## Baseline and scope

Verified `main`, HEAD **`398c544`**, clean working tree before changes. The uploaded
`SHIELDMATE_PHASE_06_CODEX_PROMPT.md` was read completely and preserved unchanged as
`PROMPTS/PHASE_06.md`; SHA-256:
`6f4e5ae414e5668f2d1aea4cd7dece0a411750a1ad7483bab1d961fc9ad8efbc`.
Repository instructions, MVP specification, phase roadmap, design system, scanner architecture,
risk methodology, Phase 05 results and existing source/tests were reviewed. All three design
references were visually inspected as art direction; their slide layouts were not copied.

Baseline commands passed before implementation: **257 backend tests** (48.81s), **50 frontend
tests**, Ruff check/format, mypy (32 source files), frontend lint/types/format/build and Alembic
upgrade/drift. Existing Starlette/httpx and host Node module.register deprecation warnings
were recorded; they are not introduced by this phase.

Implemented only Phase 06. No new scanner, risk rules, authentication system, roles, report/PDF,
public demo, payments, external analytics, deployment or Phase 07 work. No dependency or lockfile
change was needed. No user changes were discarded and no previous migration was edited.

## Engineering decisions and task/finding semantics

A remediation task is human work; a finding is technical evidence. Task endpoints never write
finding state, risk fields, observation rows, scan history or ownership proof, and never probe
the network. A task marked Done by a person remains separate from a finding resolved by
comparable new evidence. The UI explicitly shows **Task marked done — remediation not yet
verified** when the finding is open. Stale and Not rechecked annotations remain visible.

There is one canonical task per finding for its lifetime, including after completion. Creation
is atomic and idempotent; repeated requests open the same record. New tasks require an owned
open finding. Historical/stale findings can be planned against, but another scan still requires
the unchanged fresh-proof/authorization/safety controls. No archive/delete operation is offered:
users can move work backward while preserving accountability. Explicit domain deletion still
removes derived findings/tasks/history, disclosed in the confirmation dialog.

`todo`, `in_progress`, `done` are the only human statuses; all forward/backward corrections
are allowed. The owner label is descriptive text, **not** a member account, permission or
notification recipient. Notes/labels are bounded escaped text. `completed_at` tracks human
work only. Finding recurrence is read from real Phase 05 reopening history; it never silently
resets task status or notes. Users explicitly return a task to In progress when needed.

Updates require a positive integer revision. A SQLite write transaction checks the revision
and saves both work and event; a conflicting stale edit returns 409. Repeating an already
applied payload is a no-op without duplicate events or timestamp changes. Responses use a
fresh coherent read snapshot. Drafts retain their base revision during refresh; conflict
recovery explicitly reloads/discards them. Ordinary link navigation and window unload warn
about unsaved edits. Browser Back/Forward remains a documented BrowserRouter limitation.

## Models and migration

**Additive Alembic `e53b215e4b66`**, after Phase 05 `9752376ee8f2`:

- `remediation_tasks`: organization/finding IDs, human status, owner label (80 characters),
  note (2000), created/updated/completed UTC epochs, revision and history-compacted flag.
- `task_events`: scoped task/actor references, revision, event kind/time and bounded old/new
  values. No password, session/CSRF token, scanner bodies or fictional actor is recorded.
- Unique finding reference prevents canonical duplicates; composite foreign keys enforce
  finding/task/event tenant agreement. Indexes support organization/status/update and event
  organization/time queries; the matching finding identity index is additive.

History retains creation plus the latest 99 changes (100 events/task), with visible compaction.
Creation/edit transactions, FK/uniqueness, concurrency, rollback and upgrade/downgrade/re-upgrade
were tested. Existing Phase 05 finding/scanner/auth data and sessions survived migration.
No task deletion can erase underlying technical evidence because that endpoint does not exist.
Source pruning preserves Phase 05 finding snapshots and task usability; unavailable links are
labeled. Domain deletion intentionally cascades derived work as documented.

The retained event history supplies a 60-change/15-minute organization budget; a bounded
per-process organization request limiter also covers repeats/no-ops (180/15 minutes).
Compaction retains more recent events than the change budget. Domain deletion intentionally
removes its task audit records and therefore can reduce the event-backed count; the process
request limiter remains. This follows the existing local-MVP abuse-control approach, not a
claim of distributed production rate limiting. See [workflow/retention details](remediation-workflow.md).

## APIs and authorization

| Route                                     | Actual behavior                                                                                                                   |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `GET /api/v1/dashboard/summary`           | One owned read projection of organization, domains, Phase 05 findings/Top 3/coverage, work counts, queue, scans and real activity |
| `GET /api/v1/tasks`                       | Validated filters, deterministic sort, bounded pagination, owned domain options                                                   |
| `GET /api/v1/tasks/{id}`                  | Task, current finding/evidence context, recurrence time and scoped work history                                                   |
| `POST /api/v1/findings/{finding_id}/task` | CSRF/Origin-protected create-or-open; `{}` only; 200 on both insert and repeat                                                    |
| `PATCH /api/v1/tasks/{id}`                | Revision + whitelisted human fields; 409 conflict; no finding mutation                                                            |

Session identity determines the organization and actor. Foreign finding/task/domain references
return consistent 404; missing/expired identity returns 401, missing workspace 404, invalid
filters/fields 422, mutation budgets 429. No client organization/actor/severity/evidence input
is trusted. Existing cookie flags, Origin/CSRF, safe error envelopes, security headers, body
cap, CORS and scanner pinning controls are unchanged.

Task filters: status, inherited finding severity, domain UUID, sort updated/oldest/priority,
offset 0–10000, limit 1–50. Unknown fields/enums and malformed IDs are rejected. Task priority
sort reuses Phase 05's tuple, without an independent work-risk calculation.

## Dashboard query definitions and navigation

Phase 05 query functions moved into `app/findings/queries.py`. **The ordering tuple,
evaluator, rule registry and reconciliation policy are unchanged.** Dashboard and Findings
share this service, with task pointers attached in batch. No React ranking or per-card
summary fetch occurs. Read snapshots keep counts, rows and priorities mutually consistent.

- Domain scope: current owned enrolled assets. Fresh proofs have verified_at and future
  validity; eligible count additionally reuses existing scanner eligibility. Eligibility
  does not promise available quota or bypass network checks.
- Findings: current owned **open** records; actual Top 3 from Phase 05, retaining stale/
  not-rechecked context. No security score, trend, SLA, CVSS or compliance claim.
- Coverage: Phase 05 latest source per current asset, with source outcomes and rule decisions
  kept separate. Empty/no scan, pending/in-flight, incomplete, stale and unknown differ.
- Task workload: grouped human statuses. Done-unverified is exactly task done + finding open.
  Queue is up to five recently changed tasks; activity is up to five genuine saved events.
- Scan count: all retained runs for current assets; list shows five latest creation/insertion
  ordered runs, with actual execution status and collection count. Deleted-asset snapshots
  are excluded because their review route is unavailable.
- Last useful observation: newest stored pass/attention/informational observation under the
  known scanner version, excluding revoked-authorization runs. It does not certify all rules
  or whole-company safety; last scan time and coverage are shown separately.

`/app` now shows this real overview. `/app/tasks` has filters, pagination and linked work rows;
`/app/tasks/:id` has current evidence context, editable work, history and recheck navigation.
Create/Open task controls also appear on finding detail and the reused priority summary.
Task → finding → source scan → derived findings → task links work. The recheck link focuses
the correct asynchronously loaded asset; it does not start a scan or bypass any gate.
Task mutations refetch saved context/history; navigation reloads counters. Overview/list
refresh on focus and every 15 seconds while visible; task detail refreshes on focus, preserving
drafts. Route/session keys and request sequencing reject late responses from prior contexts.

The optional Business/Technical display reuses Phase 05 components and the same records.
Design retains deep burgundy, assertive red, warm ivory, Anton branding and Plex UI typography.
A ruled operating strip, first-priority emphasis, compact work/scan columns and restrained
forms preserve a readable operational hierarchy. No decorative metric gauges or fake activity.

## Changed files by responsibility

- Backend: `app/tasks/{schemas,service,api}.py`, `app/dashboard.py`, ORM models and additive
  migration; router registration and shared finding queries/task pointers.
- Tests: 29 new backend cases in `test_tasks.py`; migration head/table expectations updated.
  Fourteen frontend workflow cases plus fixtures; old account/finding expectations now use
  the real dashboard contract and remove the superseded planned-task message.
- Frontend: `Dashboard`, `Tasks`, `TaskDetail`, `TaskAction`, `TaskContext`, resource-loading
  hook, typed workflow API, routing and private navigation integration; finding actions,
  asset anchor/focus/deletion disclosure and operational styles.
- Verification/docs: isolated Phase 06 Compose/browser harness, EVIDENCE_DIR support in
  Phase 05 browser script, new labeled screenshots/JSON, this report, workflow methodology,
  architecture, README, testing and design notes. Authoritative brief preserved unchanged.

## Exact final verification commands and actual results

From the repository root unless `cd backend` is shown. Existing locked environments reused.

| Command                                                                                                      | Actual outcome                                                           |
| ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| `cd backend && .venv/bin/pytest`                                                                             | **286 passed**, 72.41s; one existing Starlette/httpx deprecation warning |
| `cd backend && .venv/bin/pytest tests/test_tasks.py::test_database_tenant_constraints_and_delete_cascade -q` | 1 passed after strengthening the two-valid-tenant composite FK assertion |
| `cd backend && .venv/bin/ruff check .`                                                                       | All checks passed                                                        |
| `cd backend && .venv/bin/ruff format --check .`                                                              | 56 files already formatted                                               |
| `cd backend && .venv/bin/mypy app`                                                                           | No issues in 38 source files                                             |
| `cd backend && .venv/bin/alembic upgrade head`                                                               | Success, `e53b215e4b66`                                                  |
| `cd backend && .venv/bin/alembic check`                                                                      | No new upgrade operations detected                                       |
| `cd backend && .venv/bin/pip-audit --progress-spinner off`                                                   | No known vulnerabilities found                                           |
| `npm test --prefix frontend`                                                                                 | **64 passed**, eight files, 4.21s                                        |
| `npm run lint --prefix frontend`                                                                             | Passed with zero warnings                                                |
| `npm run typecheck --prefix frontend`                                                                        | Passed                                                                   |
| `npm run format:check --prefix frontend`                                                                     | All matched files use Prettier style                                     |
| `npm run build --prefix frontend`                                                                            | Passed, 71 modules; JS 309.98 kB, CSS 30.61 kB before gzip               |
| `npm audit --audit-level=low --prefix frontend`                                                              | Zero vulnerabilities                                                     |
| `docker compose config --quiet`                                                                              | Passed                                                                   |
| `docker compose up --build --wait`                                                                           | All images built; backend/frontend/worker healthy                        |
| `docker compose exec -T backend .venv/bin/alembic current`                                                   | `e53b215e4b66 (head)`                                                    |
| `docker compose exec -T backend .venv/bin/alembic check`                                                     | No drift                                                                 |
| `docker compose exec -T backend id`                                                                          | UID 10001                                                                |
| `docker compose exec -T worker id`                                                                           | UID 10001                                                                |
| `docker compose exec -T frontend id`                                                                         | UID 101                                                                  |
| `curl --fail --silent http://127.0.0.1:5173/api/v1/health`                                                   | `{"status":"ok"}`                                                        |
| `git diff --check`                                                                                           | Passed before commit                                                     |

Host Node's existing module.register deprecation warning remains; Docker Node 24 build passed.
Audits reflect known advisories at execution time, not penetration testing or certification.
Earlier implementation iterations failed on a test cookie fixture that accidentally replayed
a revoked cookie, and old frontend mocks that returned identity JSON for the new dashboard
endpoint. Those test-contract issues were corrected and the complete suites rerun. No failed
check was silently reported as passing. Draft/conflict safety and response snapshot refinements
were included in final tests/build/browser verification.

### Security and correctness cases

- Two-account/two-organization task list/detail/edit/create and dashboard aggregates reject
  foreign IDs; malformed IDs/filters, forged actor/org fields and body limits fail safely.
- Session absence/revocation, missing CSRF and malicious Origin fail; auth/ownership/scanner
  regression suites remain passing. Task fields cannot change technical evidence/status.
- Rapid concurrent POSTs return one canonical ID/event; competing revision edits produce one
  success and one 409; identical retries are no-ops. Forced event failure rolls back task
  insertion; a later retry succeeds with no half-published work.
- Unicode labels and bounded notes save, status forward/backward edits work, history records
  actual actor/revision/time/changes. Overlong/null/control values and unknown statuses reject.
- Done leaves the finding open; failed/partial evidence cannot claim repair; clean comparable
  evidence resolves only the finding; reopening retains work/status/notes and shows recurrence.
- Configured stale technical state is retained. History compaction/change budgets, migration
  preservation and explicit domain-deletion cascades are tested. No task/dashboard network
  probes are allowed in the dedicated test.
- Plain React text escapes note/scanner content. The browser entered an `<img onerror>` string;
  no image element or script effect appeared. No untrusted HTML/Markdown rendering exists.

## Browser, viewport and accessibility verification

Playwright 1.62.1, Chromium **151.0.7922.34**, axe-core 4.14, loaded from the existing QA tooling
outside application dependencies via `source ../../work/browser-env.sh`.

Exact browser commands (same repository root):

```sh
# Final Phase 06: injected TXT + saved observations, real task APIs/worker, isolated volume
 docker compose -p shieldmate-phase06-qa -f scripts/qa/phase06.compose.yaml up --force-recreate --wait
 node scripts/verify-phase-06.cjs

# Earlier public/account journeys on ordinary loopback Compose
 EVIDENCE_DIR="$PWD/docs/evidence/phase-06/public-regression" node scripts/verify-phase-01.cjs
 EVIDENCE_DIR="$PWD/docs/evidence/phase-06/auth-regression" node scripts/verify-phase-02.cjs

# Earlier scanner/domain journeys on the injected transport stack
 docker compose -p shieldmate-phase04-qa -f scripts/qa/phase04.compose.yaml up --force-recreate --wait
 BASE_URL=http://127.0.0.1:15273 EVIDENCE_DIR="$PWD/docs/evidence/phase-06/scan-regression" node scripts/verify-phase-04.cjs
 BASE_URL=http://127.0.0.1:15273 EVIDENCE_DIR="$PWD/docs/evidence/phase-06/domain-regression" node scripts/verify-phase-03.cjs

# Earlier finding reconciliation/lifecycle journey on its own saved-observation stack
 docker compose -p shieldmate-phase05-qa -f scripts/qa/phase05.compose.yaml up --force-recreate --wait
 EVIDENCE_DIR="$PWD/docs/evidence/phase-06/findings-regression" node scripts/verify-phase-05.cjs
```

All six browser scripts completed successfully. **92 route/viewport checks** at **360, 768,
1280 and 1920 CSS pixels**: Phase 06 24, public 16, account 12, scanner 16, domains four,
findings 20. No tested axe A/AA violations, horizontal page overflow or browser page errors.
Public token contrast minimum: **5.09:1**. Keyboard focus, native controls/disclosures/dialogs,
review modes, reduced motion, 404 recovery and the asset-specific recheck focus were verified.
Manual screenshot review inspected rendered dashboard and mobile task detail, not just DOM.
This is automated/visual QA, not a full accessibility certification.

The new journey actually performs registration → organization → enrolled/verified fixture
asset → saved observations → stable Top 3 → task → label/note/in-progress → reload → done
with open finding → conflict preserving draft → partial/clean/reopened evidence → backend and
worker container restart → source scan and recheck links → stale coverage → controlled API
failure/retry. Restart preserved the exact task/history/session JSON; repeat create returned
the same ID and one task. Earlier findings browser backfill/restart checks also passed.

Screenshots/JSON under `docs/evidence/phase-06/`:

- [Desktop dashboard](evidence/phase-06/dashboard-1280.png),
  [mobile dashboard](evidence/phase-06/dashboard-360.png),
  [empty overview](evidence/phase-06/empty-dashboard-768.png).
- [Task list](evidence/phase-06/task-list-1280.png),
  [mobile task editor](evidence/phase-06/task-detail-360.png),
  [done awaiting verification](evidence/phase-06/done-unverified-1280.png).
- [Recurrence/history](evidence/phase-06/recurrence.png),
  [stale overview](evidence/phase-06/stale-dashboard-768.png),
  [API error](evidence/phase-06/dashboard-error.png),
  [machine-readable results](evidence/phase-06/browser-results.json).
- Regression subdirectories preserve their own results and screenshots; historical phase
  evidence was not overwritten.

**Every security-data screenshot is labeled LOCAL QA and uses isolated synthetic saved
observations/injected TXT or socket seams, never a live security assessment.** Ordinary
public/auth screenshots contain no fabricated security results. QA modules are mounted only
in isolated stacks and absent from production images. No public demo seed/account/reset
functionality was implemented. Temporary QA stacks were stopped with volumes preserved.

## Acceptance gates

| Gate                                         | Status | Basis                                                                             |
| -------------------------------------------- | ------ | --------------------------------------------------------------------------------- |
| 1. Baseline/docs/Git inspected               | PASS   | Clean `398c544`, original docs/images/code and actual baseline checks             |
| 2. Additive scoped task schema               | PASS   | `e53b215e4b66`, composite FKs/indexes/unique key and migration tests              |
| 3. Atomic idempotent owned creation          | PASS   | Real fixture finding; concurrent POST/rollback/retry tests                        |
| 4. Scoped typed APIs/session/CSRF            | PASS   | Validated bounded list/detail/create/edit; no deletion route; IDOR/Origin tests   |
| 5. Owner/note/status/history function        | PASS   | API/UI tests and real saved browser edits/reload                                  |
| 6. Human done separate from evidence         | PASS   | Unchanged finding assertions plus partial/clean/recurrence browser flow           |
| 7. Real dashboard counts/Top 3/time          | PASS   | Shared Phase 05 service, exact SQL/UI comparisons, documented coverage            |
| 8. Working CTAs/cross-links                  | PASS   | Create/Open, queue/filters/history, source-scan round trip and exact asset focus  |
| 9. Responsive accessible brand UI            | PASS   | Original tokens/fonts; four widths, axe, focus/reduced motion and visual review   |
| 10. Isolation/XSS/security regression        | PASS   | Two tenants, escaped malicious note, original scanner/auth/CSRF suites            |
| 11. Honest operational states                | PASS   | First-use/no scan, pending/partial/stale/error, done-unverified tests/screenshots |
| 12. Concurrent/repeated/restart safety       | PASS   | Uniqueness/revisions/no-op/rollback and actual container persistence              |
| 13. Actual tests/quality/build/audits/Docker | PASS   | Exact successful commands/counts above                                            |
| 14. Actual browser E2E/viewport evidence     | PASS   | Six completed scripts, 92 checks, labeled fixture screenshots/JSON                |
| 15. Complete current documentation           | PASS   | This report, workflow/API/retention, README/architecture/testing/design notes     |
| 16. Local commit/status and scope            | PASS   | Local Phase 06 commit on main, clean post-commit status; no push/deploy/Phase 07  |

## Known limitations and manual setup

- **NOT TESTED: true team-owned domain DNS-provider/live scanner E2E.** No such domain was
  supplied, and none was probed to manufacture evidence. Authorized fixture tests are distinct.
- **NOT TESTED:** real screen readers/physical mobile devices, Safari/Firefox, genuine SME
  comprehension/beta testing. The future 120-second hypothesis has no invented participants,
  times, feedback or claimed outcome.
- No multiuser membership/assignment, notifications, deadlines, bulk editing, offline work,
  archive/delete, full immutable audit or production distributed limiter. Domain deletion is
  explicitly destructive; source/event retention is bounded as documented.
- Browser Back/Forward does not invoke the unsaved-link confirmation; save before navigating
  history. Window unload and ordinary links are guarded. Shared-client CSRF rotation follows
  the existing API client; simultaneous independent mutation attempts can require a retry.
- Refresh is focus/15-second polling, not live push. Evidence can change while editing; version
  conflicts protect human work and fresh technical state remains independently displayed.
- Existing application-level SSRF/rebinding/pinning is preserved; local Compose still does
  not provide an infrastructure egress firewall or a public-production security guarantee.
- Reports/PDF, isolated repeatable demo, billing, public deployment and **Phase 07 are absent**.

## Local start and Git handoff

From the repository directory:

```sh
docker compose up --build --wait
```

Open <http://127.0.0.1:5173/app> (overview), <http://127.0.0.1:5173/app/tasks> (action plan),
or <http://127.0.0.1:5173/app/findings>. Create/sign in to your real local account and
organization. Without observations there are no fabricated findings or tasks. For live data,
enroll only an expressly authorized exact team-owned domain, publish/verify its TXT proof,
then use existing bounded scan controls. Compose starts the real worker and migrations.
README contains manual Vite/Uvicorn/worker startup. `docker compose down` preserves the
ordinary database volume; do not add `--volumes` unless intentional erasure is required.

Baseline branch/commit: `main` / `398c544`. Final commit is the local commit containing
this report, **Implement Phase 06 connected dashboard and remediation workflow**; the handoff
states its exact hash and verified clean status. No push or public deployment was performed.
**Next phase: 07 — NOT STARTED.**
