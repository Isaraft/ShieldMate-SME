# SHIELDMATE SME — CODEX IMPLEMENTATION BRIEF
## PHASE 06 — Connected Dashboard, Remediation Tasks & Action Workflow

**Execution mode:** Implement the requested phase in the **existing** ShieldMate repository. Do not stop after outlining a plan. Build, test, inspect the rendered UI, document, and locally commit completed work.

**Scope:** Phase 06 only: the real organization dashboard, evidence-linked remediation task workflow, unified navigation, and usable scan/finding/task history. The dashboard is a presentation of persisted business and security state, **not** an additional scanning or risk-scoring engine.

**Reported baseline (VERIFY, do not assume):** Phase 05 completed on `main` at local commit `398c544`, with a clean working tree, six deterministic finding rules, persistent finding history, explainable server-ranked Top 3 priorities, 257 backend tests, 50 frontend tests, and 68 viewport checks. These are user-provided Codex results, not independently verified. Inspect the actual repository and `docs/phase-05-results.md` to confirm.

**Next phase:** Phase 07 — PDF Management Reports & Isolated Repeatable Demo. **DO NOT START PHASE 07.** Do not push or publicly deploy.

---

## 0. ROLE, SOURCE OF TRUTH, AND FIRST ACTIONS

Act as a senior full-stack engineer, application-security engineer, product designer and pragmatic maintainer. Build an actual usable cybersecurity SaaS workspace, not a fake dashboard or a generated-looking UI kit demonstration.

Before changing files:

1. Read `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, `docs/design-system.md`, `docs/scanner.md`, `docs/risk-methodology.md`, and `docs/phase-05-results.md` if present. Re-read the project's three visual references **as art direction, not as layouts to copy**.
2. Inspect the actual SQLAlchemy models/Alembic heads, organization scoping, cookie-session/CSRF behavior, domain and scan tables, finding status semantics, stable ranking API, frontend router, API client, error conventions, component library, and test infrastructure.
3. Run the existing baseline test, lint, typecheck, format, build and migration checks before editing. Record exact command output and identify any failures attributable to the baseline.
4. Confirm branch, HEAD and `git status`; never overwrite user changes, rewrite older migrations or discard files. If working tree is not clean, preserve it and explain the strategy.
5. Give a short, concrete implementation outline (approximately 10–20 lines): data model, task/finding relationship, summary API, status semantics, dashboard layout, tests and migration strategy. Then **implement the phase end-to-end**. Resolve normal engineering tradeoffs yourself and document them; ask a question only if genuinely blocked.

**Product positioning:** ShieldMate SME Starter is a lightweight security **risk-to-action** platform for digitally dependent SMEs in Kazakhstan, particularly non-specialist owners and IT generalists. Interviews in Assignment 3 showed customers want a short prioritized list with understandable reasons. Assignment 4 narrowed Starter to scoped external checks, prioritized findings, accountable action items and management-friendly reporting. This phase completes the practical loop: **verified domain → real check → evidence-backed finding → top priority → assigned task → recorded human action → later evidence-based recheck**.

## 1. DEFINITION OF SUCCESS: REAL END-TO-END JOURNEY

A logged-in organization owner must be able to:

1. Open `/app` and immediately see a useful **real-data overview** of their own organization: eligible/verified assets, current high-priority findings, task workload, latest scan status and recent activity, as permitted by existing models.
2. Identify the current **Top 3** priorities based on the existing Phase 05 server ranking; each priority links to the actual finding and explains the main reason and recommended next action.
3. Select an actionable current finding and create or open a persistent remediation task linked to that finding. Avoid creating duplicate active tasks through double clicks or request retries.
4. Assign a simple **owner label** (e.g. `IT administrator`, `External IT provider`), write a bounded note, and change task status through a clear, documented workflow.
5. Reload the page or restart the backend container and see the exact same task state, owner label, notes, timestamps and history.
6. Mark a task **done by a person** without the finding being marked technically resolved. If the latest conclusive check still supports the problem, show **“Task marked done — remediation not yet verified”** or equivalent.
7. Open the original finding/scan evidence and use existing authorized scan controls to recheck the relevant asset. Technical resolution remains controlled entirely by Phase 05 finding reconciliation and valid Phase 04 scan observations; a user task update must never override it.
8. Review recent authorized scan history and task changes, with working routes, loading/empty/error states and clear timestamps.
9. Switch between concise executive-oriented copy and fuller technical context **only if this can be done safely without undermining the core flow**. This display choice is not access control.
10. Complete the above flow on desktop and mobile, without fictional counts, decorative buttons, fabricated scan results, or silent failures.

**Explicitly OUT of scope:** New scanners/rules or changing Phase 05 severity policy; new login/roles/invitations/MFA; automatic remediation; SIEM/EDR, phishing campaigns, notifications by email, subscriptions/payments, third-party integrations, external analytics, deployment, report/PDF generation, seedable public demo accounts or unlabelled fake data. Phase 07 owns reports and deterministic demo data. Phase 09 owns real beta-testing evidence.

## 2. DOMAIN MODEL: HUMAN WORK VS TECHNICAL FINDINGS

The key engineering invariant is **task completion is not vulnerability resolution**.

- A **finding** is supported/updated/resolved/reopened by the **Phase 05** evidence evaluation and lifecycle, based on actually persisted Phase 04 observations.
- A **remediation task** represents a person's planned work and self-reported execution. It is neither a vulnerability detector nor a new source of technical truth.
- A task marked complete while its finding remains open should visibly say `Awaiting verification / recheck required`, not `Fixed`, `Verified`, or `Secure`.
- A finding resolved after a conclusive authorized scan can be displayed as `Evidence indicates resolved`, with its last-verification timestamp. This must not be inferred from task status, missing results, API failure, or scan timeout.
- If a finding reopens, surface a visible recurrence/recheck indicator on related tasks. Do **not** silently replace the owner's historical notes or misrepresent a previously completed task as still solving the recurrence. Provide an explicit way to reopen the existing task or document a conservative alternative.
- If a finding becomes stale or inconclusive, show that honestly. Never compute “resolved” or “secure” from stale/error/missing coverage.

### 2.1 Task statuses and lifecycle

Prefer a minimal stable set: `todo`, `in_progress`, `done`; include `archived` only as a separate archival flag/status if necessary. Match naming to repository conventions instead of forcing redundant enums.

- `todo → in_progress → done` is the normal path, but users can move backward (e.g. `done → in_progress`) to correct mistakes/reopen work.
- `done` means **manually reported as completed**; `completed_at` is a work timestamp, not a technical verification timestamp.
- Keep a clear, separate badge or line for the linked **finding lifecycle**, such as `Open finding`, `Resolved by latest evaluable scan`, `Reopened` or `Not recently checked`.
- Do not generate task severity independently. Display inherited current finding priority with appropriate explanation and fallbacks when the finding is resolved/stale.
- Preserve time-ordered task status transitions and note changes so a reviewer can tell what actually happened.
- A deleted/archived task must not erase the underlying finding, source scan, or historical security evidence.

### 2.2 Record design

Use a focused additive Alembic migration after the actual Phase 05 head; **inspect actual revision IDs**. Suggested fields (adapt to existing schema):

`remediation_tasks`: UUID/ID; `organization_id`; `finding_id`; `status`; `owner_label` (nullable, bounded); `note` (nullable, bounded) or separate note entries; `created_at`; `updated_at`; `completed_at` (nullable); `archived_at` (nullable); optional concurrency/version column if appropriate.

`task_events` (recommended for transparent audit): ID; organization/task IDs; actor user ID; event type; bounded old/new status or owner; optional bounded note/change summary; `created_at` UTC. Exclude sensitive authentication/session data and unnecessary PII. If existing audit-event infrastructure can express these events cleanly, reuse it.

Requirements:

- Foreign keys, tenant-scoped joins, indexes for organization/status/updated time and related finding, appropriate uniqueness, and referential integrity.
- **One canonical active task per finding** at a time for this MVP, with an idempotent “create or open existing task” action. Design a unique constraint/transaction strategy against concurrent POSTs and retries. If recurrence requires reopening the same task, preserve event history; don't silently create a second active task.
- Ensure domain/finding organization membership matches task organization. Do not trust `organization_id`, `actor_id`, finding severity or evidence in the request body.
- Constraints and validations for ownership label and note length; safe Unicode input. Reject overlong values and malformed enum values with clean typed errors.
- Transactional task updates and audit events. Use consistent timestamp sources in UTC, robust ordering/tie-breakers and sane handling of concurrent updates (optimistic locking/conditional update or a clearly documented last-write-wins policy with conflict messaging).
- Add migration upgrade and drift tests that preserve all pre-existing users, sessions, organizations, verified domains, scans, observations and finding histories. Never rewrite old revisions.
- Consider archiving over physical deletion if audit history would otherwise disappear. Expose destructive actions only with explicit confirmation and correct semantics.

Do not introduce a full multiuser assignment system: Phase 02 has **organization ownership**, not invitations or membership roles. `owner_label` is descriptive text and **not** an authorized user identity. Do not invent members or future permission controls.

## 3. BACKEND API AND SERVER-SIDE BUSINESS LOGIC

Implement versioned, typed, consistent backend endpoints matching the repository's existing API conventions. Suggested contract names are illustrative, not mandates:

- `GET /api/v1/dashboard/summary` — a tenant-scoped, stable JSON projection of persisted assets, scans, findings and tasks. The latest scan and top-priority data must have explicit timestamps/coverage metadata.
- `GET /api/v1/tasks?status=&domain_id=&priority=&page=&page_size=` — scoped, paginated, deterministic list; validate filters, limits and ordering.
- `POST /api/v1/findings/{finding_id}/task` — authenticated, CSRF/Origin-protected **create-or-return-existing** task associated with an authorized, existing finding.
- `GET /api/v1/tasks/{id}` — tenant-scoped task detail, source finding pointer, relevant evidence and event history.
- `PATCH /api/v1/tasks/{id}` — change owner label, note and/or status, with strict whitelist of fields and validated state transitions.
- `DELETE /api/v1/tasks/{id}` or an archive endpoint **only if** safe reversible archiving is included; otherwise clearly explain why deletion is not provided and avoid presenting a fake Delete button.

The task list and dashboard must not perform a separate client-side security assessment. Reuse the existing Phase 05 finding/ranking queries or a shared service layer; avoid duplicating ranking logic in React.

**Summary fidelity:**

- Separate counts for **verified assets**, **open supported findings**, **tasks by status**, and **recent scan runs**. Count only scope defined by actual SQL queries.
- Present critical/high/medium distribution only when Phase 05's real severity fields justify it. Never fabricate a “global security score”, “% secure”, threat trend, CVSS, SLA, compliance rating, customer growth or resolved-incident statistics.
- Explicitly distinguish `0 findings from sufficiently evaluated checks` from `no scans`, `scanning in progress`, `partially evaluated`, `checks failed`, and `stale data`.
- Avoid misleading aggregate percentages when coverage is unknown or insufficient. Explain the boundary: these are limited external-domain checks, not a full cybersecurity audit.
- A Top 3 list contains **at most three genuinely current actionable findings**, ranked by the existing deterministic policy. An empty list is correct when there are no supported findings.
- If a finding has no task, show a functional **Create task** action. If a task exists, show **Open task** and its human-work status. Buttons must work and route to real resources.
- Prevent N+1 queries, unbounded results or expensive in-memory whole-tenant joins. Use indexes and bounded pagination; aggregate securely within org scope.
- Document the API shapes with schemas and tests. Reuse current error envelope and success codes; make mutations idempotent where needed.

## 4. DASHBOARD: AN ACTUAL OWNER-READY COMMAND CENTER

Implement the existing `/app` shell as a useful **backend-connected dashboard** without destroying Phase 01's established art direction and route layout.

Recommended information hierarchy:

1. **Organization identity and last trustworthy data time** — selected/owned workspace, active domain scope and a short coverage qualifier.
2. **Immediate action / Top 3** — prioritized findings with concise business-language impact, why ranked, and one-step action. Highest priority gets useful emphasis; avoid enormous empty visual cards.
3. **Operational overview** — verified assets, open supported findings, tasks in progress/done, latest completed/partial scan status, with precise labels and links.
4. **Remediation queue** — actual tasks with status, owner label, linked domain/finding, change timestamp and one clear primary action.
5. **Recent scan activity** — timestamped status from existing real scan runs, links to their details/history and accurate error/inconclusive presentation.
6. **View details** links to real `/app/assets`, `/app/findings`, `/app/scans` (or existing equivalents), and `/app/tasks`.

**Information quality rules:**

- Use original compact human-written microcopy. An SME owner should answer **“What should I fix first and why?”** within roughly two minutes.
- Avoid scary broad claims such as “your company is unsafe” based on a missing header. Qualify business impacts appropriately.
- Provide specific and distinct state UI for: first-time empty org, no verified assets, verified asset without scans, scanning, completed scans with no supported issues, partial/error scans, open issues, all tasks done but findings still open, stale results, and API failure.
- “All tasks completed” must never be conflated with “All technical findings resolved”.
- Provide helpful next actions (Add/verify a domain, Run checks, Review finding, Create task, Recheck asset) only when eligible; no fake clickable CTAs.
- Display real timestamps with clear timezone semantics and sensible fallbacks, using the application's existing date formatting standards.
- Keep loading/error/retry accessible and deterministic; avoid flashes of other tenant data when session changes.

### Executive / Technical presentation

If the current UI kit and data contracts make it cheap and robust, add a **Business / Technical** view preference (purely frontend presentation or user preference) with different explanation density of the **same** records. It is **not role-based authorization**, does not hide private data from a user who is already authorized, and must not introduce a new RBAC model. If not feasible, document it as deliberately deferred. Do not sacrifice task CRUD or correctness for a decorative toggle.

## 5. REMEDIATION TASKS: FIRST-CLASS UI, NOT STATIC LIST ITEMS

Create accessible `/app/tasks` and `/app/tasks/:id` pages (or route equivalents consistent with existing router), and wire navigation from the dashboard and findings.

**Task list:** real task rows, search/filter where useful (status, severity, domain), stable sorting and pagination, clear owner labels, status, last update, linked finding and context; avoid overbuilt enterprise work management features.

**Task detail:** plain-language finding context, affected domain, current priority and finding lifecycle, exact recommendation inherited from Phase 05, source evidence link, current task status, owner label, editable note, status transitions, audit/history feed and a clear recheck path to Phase 04 existing scan controls.

**Create task action:** available only against a real authorized finding, clear duplication behavior (open existing); CSRF-protected save, success/error feedback, disabled/loading states preventing accidental double submission.

**Edit workflow:** meaningful form validation, dirty-state handling if appropriate, accessible status select and confirmation for archive, and accurate post-mutation refresh of dashboard counters and task views. Handle races where findings change while a task is edited.

**Status semantics visible on screen:** use wording equivalent to `Work marked complete; finding remains open until confirmed by a later successful check` whenever applicable. Show scan-confirmed resolution distinctly with its evidence date. Never present a task checkbox as an automatic patch/remediation engine.

**History:** at minimum status/owner/note changes with timestamp and actor (current authenticated user). Do not expose a fake activity feed. Protect all notes as untrusted text; render through escaped React text, not HTML injection.

**Responsive:** functional tables should become intentional compact rows or horizontally controlled content on narrow screens rather than clipping navigation or making actions inaccessible. Avoid dense mobile grids that require impossible horizontal scrolling.

## 6. SCAN/FINDING/TASK NAVIGATION AND CONSISTENCY

Preserve Phase 03 verified-asset ownership and Phase 04 scanning restrictions. The Phase 06 interface may link to existing scan/recheck flows, but cannot bypass verification freshness, quotas, DNS public-IP policies or other scanning gates.

- Link the task to its finding, the finding to its saved source observation/scan, and the scan to the verified domain.
- A user can follow links in both directions without losing context, where existing endpoints permit it.
- Correctly handle a finding resolved, reopened, stale, deleted/removed asset (if deletion is allowed), or temporarily unavailable without crashing pages or exposing an unauthorized record.
- Invalidate/refetch relevant view models after task mutation and scan/finding updates; avoid stale UI counters or incorrect optimistic status displays.
- Do not rewrite Phase 05 finding state from a task update. Do not mutate saved technical evidence, risk ranking, original observations, or scan run history.
- When existing records cannot be safely linked because of current model constraints, handle gracefully and document the gap rather than inventing evidence links.

## 7. SECURITY, PRIVACY, ACCESSIBILITY AND QUALITY

**Security invariants (non-negotiable):**

- Every read/write derives organization and user from the existing authenticated, expiring cookie session. Authorization is enforced **in the backend** for nested finding/task/history resources, list queries, aggregates and mutations. Test IDOR with two accounts and two organizations.
- Preserve CSRF token and Origin checks for every state-changing endpoint, existing cookie settings, session expiry, login rate limits and CORS/CSP. No new secrets or API keys in frontend bundles.
- Validate status enum, filters, pagination, owner label, note length, time values and all IDs server-side. Use SQLAlchemy bound parameters, not string interpolation. Reject unknown/forged fields with predictable errors.
- Protect user-written notes, labels and copied scanner evidence against XSS. No `dangerouslySetInnerHTML`, untrusted markdown rendering or HTML injection. Bound audit history entries and avoid writing secrets or tokens into log/event records.
- Keep task activity/audit records org-scoped; no cross-tenant inference through counts, timing, unsafe joins or export.
- Add focused abuse controls to high-frequency mutations consistent with existing Phase 02/03 approach. Do not claim a single-process limiter provides production-grade distributed abuse protection.
- No active exploit checks, direct remote commands, arbitrary network requests, phishing, new external calls, hidden telemetry or automatic mitigation introduced in this phase.
- Use actual DB transactions and constraints; double-clicks, retries, concurrent task creation and refresh/restart must not corrupt state.

**Design/UX invariants:**

- Keep **deep BURGUNDY + STRONG RED** identity (never burgundy-pink or generic blue cyber visuals). The existing Anton/IBM Plex Sans choices, warm ivory contrast, disciplined borders and controlled editorial asymmetry should carry forward.
- The public landing remains visually expressive; app dashboard is measured, dense enough for actual work and legible for non-experts. Do not copy the slide layouts or recreate generic three-cards-with-icons template.
- Accessible forms, controls, nav, status badges and task-history updates: semantic HTML, explicit labels, errors tied to fields, focus handling, screen-reader announcements where useful, keyboard-only flow, WCAG AA text contrast and `prefers-reduced-motion`.
- Test 360, 768, 1280 and 1920 CSS px. No horizontal overflow on required workflows.
- No fake clients, test results, reviews, security metrics, notification counts or green checkmarks suggesting a real external assessment. Clearly label fixtures/screenshots as **QA**, not production data.
- Keep existing Phase 00–05 page behavior, auth, assets, scans and findings functional.

## 8. REQUIRED AUTOMATED AND BROWSER TEST MATRIX

At a minimum, write/execute reproducible tests for:

**Task model / API**
1. Create a task from a legitimate current finding; persist after reload and container restart.
2. Deny creation for nonexistent, foreign-tenant, unscoped or otherwise unauthorized findings.
3. Duplicate rapid POST / retry returns the single canonical task; demonstrate DB uniqueness/concurrency safety.
4. Owner label and notes are validated, escaped, length-bound and successfully updated.
5. `todo → in_progress → done → in_progress` works; unauthorized/invalid transitions are rejected.
6. Task event history records correct actor/time/transitions without duplicates or secrets.
7. Completed task leaves finding open and unchanged; resolved finding depends only on new valid scan evidence. A failed/partial scan never produces false “fixed”.
8. Reopened or stale finding state is represented accurately on an existing task.
9. Tenanted list/detail/update/archive APIs enforce org scope; verify IDOR/aggregate leak rejection.
10. CSRF/Origin/session errors work; invalid status, unknown keys, ID formats, pagination and filter combinations are rejected safely.
11. Migration preserves existing entities; constraints/indexes/unique checks hold; no Alembic drift.

**Dashboard / integration**
12. Dashboard numbers equal backend aggregates for fixture scenarios (no organization, no domains, verified domain, no scans, several supported findings, partial scan, all tasks manually done, stale results).
13. Top 3 order matches the **same Phase 05 server ranking**, including deterministic tie breaks, and all cards link to the correct finding/task.
14. No duplicate counts after retries or repeated fixture evaluations.
15. After task changes, dashboard/list/detail refresh correctly; reload and session transition show only current-org state.
16. Complete E2E through login → organization → verified asset (using deterministic offline DNS seam) → saved scan fixtures → findings → create task → update owner/note/status → reload → inspect status/technical evidence and scan history.
17. Correct first-run/loading/empty/failed/stale/partial states with honest copy and useful next action.
18. Keyboard navigation, focus management, contrast/axe, 360/768/1280/1920 widths and no overflow.
19. Existing Phase 01–05 test suites and APIs continue passing.

Run and **report actual outcomes**, including:

- Backend pytest, Ruff check and format, mypy.
- Frontend tests, ESLint, formatting, TypeScript typecheck and production build.
- Alembic upgrade + drift validation; check existing data survives.
- Python and npm dependency audits.
- Docker Compose build/health and actual restart/persistence.
- Relevant browser verification scripts and, if possible, screenshots of dashboard, task list, and task detail at multiple widths.
- `git diff --check`, Git status and commit verification.

Use deterministic test fixtures with clearly visible **QA / synthetic test data** labels. No unapproved scans of real third-party domains. Since no team-controlled domain has yet been supplied, the true owned-domain DNS-provider/live scanner E2E must remain explicitly **NOT TESTED**, unless you actually run it using an expressly authorized owned domain and report the evidence. Distinguish passing fixture tests from a live real-world scan.

If anything is not actually tested, label **NOT TESTED**, not PASS. If there is a meaningful defect, report it and do not obscure it with optimistic wording.

## 9. DOCUMENTATION AND UNIVERSITY MVP ALIGNMENT

Update, as applicable:

- `docs/remediation-workflow.md`: task vs finding lifecycle, task status meaning, ownership label semantics, creation/deduplication policy, what constitutes verified technical resolution, event history, API examples, limits, data retention and known gaps.
- `docs/phase-06-results.md`: confirmed baseline commit/status, decision log, actual changed files/migration IDs, command outputs/test counts, screenshots, security checks, known limitations and evidence per acceptance criterion.
- README/API docs and local run instructions; explain the ownership verification prerequisite to any scan and where to access the workflow.

For Assignment 5, the Phase 06 user flow should let a real SME participant discover the top priority and recommendation within **120 seconds**. This is a **future evaluation hypothesis**, not a tested fact. Do not invent users, alpha/beta feedback, use durations or acceptance survey results. Preserve clean product screenshots but identify any screenshot made with injected fixture data as QA evidence.

Phase 07 will handle management PDF export and an isolated repeatable sample demo. Do **not** implement them here, and do not produce fake reports or misleading sample metrics. No paid subscriptions/billing.

## 10. PHASE 06 ACCEPTANCE GATES — MARK ALL PASS / FAIL / NOT TESTED

1. Actual baseline/source documents, previous features and Git state inspected; no unauthorized work discarded.
2. Additive task schema/migration preserves prior data and has valid scoped foreign keys, indexes and duplicate protection.
3. Task creation from a real owned finding is atomic, persistent and idempotent; duplicate requests cannot create multiple canonical active tasks.
4. Tenant-safe list, detail, update and any archive endpoints with validated, paginated APIs and CSRF/Origin/session enforcement.
5. Editable task owner label, bounded note, status transitions and durable activity history actually function.
6. Manual `done` remains distinct from Phase 05 evidence-backed finding `resolved`; stale/incomplete/reopened conditions are honest.
7. Dashboard metrics, Top 3 and last trustworthy scan/activity derive from real tenant-scoped backend data, with no fictional counts or risk scores.
8. All intended dashboard CTAs and cross-links to domains/scans/findings/tasks work; no dead interactive elements.
9. Responsive, accessible dashboard and task UI preserve **burgundy/red** identity and human-made visual quality.
10. No cross-organization leakage, no XSS via notes/scanner text and no auth/CSRF/SSRF scanning regression.
11. Accurate and distinct empty, loading, stale, error and partial-data states; task-finished/issue-open state clearly indicated.
12. Repeated requests, concurrency, restart and reload cannot lose or corrupt task data, counts or history.
13. Backend/frontend tests, lint, types, build, migration, dependency audit and Docker verification were really executed with recorded results.
14. Browser E2E and viewport checks were actually run, with links/paths to evidence; QA fixtures visibly distinguished from live results.
15. `docs/remediation-workflow.md`, `docs/phase-06-results.md` and any changed API/README docs are complete and technically accurate.
16. Final local commit and status clearly reported; no push, no public deployment, **no Phase 07 work**.

## 11. REQUIRED FINAL HANDOFF

Provide the following sections with actual evidence:

```text
Phase: 06 — Connected Dashboard, Remediation Tasks & Action Workflow
Baseline branch / commit / status:
Final local commit and Git status:
Engineering decisions and task/finding semantics:
Data models / additive Alembic revision:
API routes and authorization model:
Dashboard metrics and query definitions:
Task list/detail/workflow and history:
Navigation and executive/technical view (if implemented):
Changed files grouped by responsibility:
Implemented / deliberately deferred:
Tests executed (exact commands and real counts):
Security regression tests (IDOR, CSRF, XSS, concurrency, no false resolutions):
Browser/viewport/accessibility evidence and screenshot paths:
Acceptance gates 1–16 (PASS / FAIL / NOT TESTED + basis):
Limitations and any manual setup:
Local start instructions:
Push/deployment status (must remain none):
Next phase: 07 — NOT STARTED
```

**Implement Phase 06 now. Do not stop after proposing a plan. Work as a senior engineer and designer: clean architecture, robust tests, truthful UI, no fake product claims. Do not push, deploy, or begin Phase 07 without explicit approval.**
