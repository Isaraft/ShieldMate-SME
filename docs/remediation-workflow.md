# Human work and technical evidence — Phase 06

A task records a person's work. A finding records a technical condition supported by saved
observations. Task mutations never call the evaluator, start scans or write findings,
finding events, observations or scan history. Severity is inherited from the current finding;
there is no task risk policy, task score, automatic patch or new authorization role.

## Canonical task and state

An authenticated organization owner creates work from an existing owned **open** finding.
`POST /api/v1/findings/{finding_id}/task` accepts only `{}`. It returns the one canonical
task for that finding, including after completion or later technical resolution. First
creation against an already resolved finding returns 409; an existing task is still returned.
All successful create-or-open responses use 200, whether inserted or already present.
Unique finding ID and SQLite BEGIN IMMEDIATE make concurrent creation and retries idempotent.
Creation does not require a fresh DNS proof: planning work on historical evidence is allowed,
while any subsequent scan still requires the unchanged Phase 03/04 authorization controls.

Statuses are `todo`, `in_progress`, `done`. Any owner may move between these three states,
including backward corrections. `done` means **Done by a person**. `completed_at` is set on
entry to done and cleared when leaving it; it never represents technical verification.
The normal path is To do → In progress → Done by a person. No assignee accounts, invitations,
permissions or notifications are created. The owner label is descriptive text only.

Finding status is shown independently:

- Open + task done: **Task marked done — remediation not yet verified**.
- Comparable conclusive later evidence: **Evidence indicates resolved**, with source time.
- Incomplete, missing or failed checks: retain the last known technical state and show
  Not rechecked. Stale evidence is explicitly historical, even if its saved state is resolved.
- Recurrence: the latest retained Phase 05 reopening event is surfaced on the task. Notes,
  status and completed_at are not rewritten. The owner can explicitly move work back to
  In progress. A later re-resolution does not erase the recurrence history.

No task deletion/archive endpoint or fake Delete button is provided. Keeping one canonical
record preserves accountability and avoids inactive duplicates. Correct work by editing
or moving its status backward. **Explicit domain deletion cascades its findings, tasks and
histories**; the confirmation dialog discloses this. Deleting a task independently cannot
erase technical evidence because no such operation exists. Source-scan pruning still retains
Phase 05 evidence snapshots, so tasks remain usable when an original scan link is unavailable.

## Editing, conflicts and audit history

Owner label: at most 80 characters; note: at most 2000 characters. UTF-8 text is accepted;
control characters other than newline/tab are rejected, surrounding whitespace trimmed,
unknown body fields forbidden. Empty strings clear text; null is rejected. Do not store
passwords, tokens or customer personal information in work notes. Notes are plain escaped
text, never HTML or rendered Markdown. Server errors contain fixed safe messages.

`PATCH /api/v1/tasks/{id}` requires a positive integer `version` plus at least one of
`status`, `owner_label`, `note`. No organization/actor/finding ID, severity or technical
resolution parameter is accepted. A transaction locks the database, verifies ownership and
revision, changes work fields and appends one event together. Conflicting stale changes
return 409. A repeated payload already matching current fields is a no-op: no timestamp,
version or event changes. The response reads one fresh snapshot after the write commits.

Each actual change increments version and records the authenticated actor ID, UTC epoch,
event kind and bounded old/new values. The UI labels the actor Workspace owner; it invents
no team members. Events order by task version, avoiding random-UUID/equal-second ambiguity.
The first creation and latest 99 changes are retained; compaction is disclosed. At most
100 events/task and one task/finding bound history (six findings per enrolled domain under
the current policy). This is a local MVP audit, not an immutable compliance archive.

A persisted organization budget permits at most 60 actual task changes in a rolling 15
minutes. Because retained recent history exceeds that budget, compaction cannot remove
current-window budget evidence before the limit is enforced. No-op writes and create/open
retries also consume a bounded per-process request budget of 180/15 minutes/organization.
Deleting a domain also removes its task events and can reduce the event-backed count;
the organization request limiter remains. This limiter follows the existing local MVP approach; it is not distributed production abuse
protection and resets its request budget on restart. The event-backed change budget persists.

The editor retains its draft and base revision across context refreshes. A conflict requires
explicit **Reload latest and discard draft**; it never silently overwrites another edit.
Unsaved drafts are labeled, can be discarded explicitly, and warn on reload/window close or
ordinary link navigation. Browser Back/Forward is not blocked by the BrowserRouter; save
before using browser history. Saved state refetches after mutations and page navigation.
Overview/list poll every 15 seconds while visible and refresh on focus; task detail refreshes
on focus. Late requests cannot populate a different route/session or replace newer requests.
There is no claim of instantaneous cross-browser synchronization or offline editing.

## API and tenant boundary

All endpoints derive the organization through the authenticated session. Composite foreign
keys additionally enforce matching finding/task/event organizations, with normal user/org
references. Each query joins the owned finding and current domain. Foreign resource IDs
return 404; absent/expired sessions return 401; missing workspace returns 404.
Every POST/PATCH uses the existing exact Origin plus session-bound CSRF token validation.
The existing body cap, safe errors, no-store/security headers, cookie policy and CORS remain.

- `GET /api/v1/tasks`: deterministic filtered page and owned domain options. Filters:
  `status=all|todo|in_progress|done`, `severity=all|high|medium|low|info`, domain UUID,
  `sort=updated|oldest|priority`, offset 0–10000 and limit 1–50. Unknown/invalid fields fail
  with 422. Priority sort reuses the Phase 05 ordering tuple; it is inherited finding priority.
- `GET /api/v1/tasks/{id}`: task, current finding/evidence context, latest recurrence time,
  and up to 100 scoped work events.
- `POST /api/v1/findings/{finding_id}/task`: create or open canonical work, `{}` only.
- `PATCH /api/v1/tasks/{id}`: versioned work edit; 409 conflict, 422 validation, 429 budget.
- `GET /api/v1/dashboard/summary`: organization, generated timestamp, fresh-proof and
  authorization-eligible domain counts, open findings/Top 3, task counts, recent work,
  retained scans, useful observation timestamp and coverage. It is read-only/offline.

Example patch (send using the application's secure client with current Origin/CSRF):

```json
{
  "version": 1,
  "status": "in_progress",
  "owner_label": "External IT provider",
  "note": "Review hosting renewal; request an authorized recheck afterward."
}
```

## Dashboard query definitions

One SQLite read snapshot covers the summary. Domain counts include only current enrolled
assets in the owned organization. Fresh proofs require a recorded verified_at and future
verification_valid_until; eligible counts additionally apply the existing scanner eligibility
function. No eligibility label bypasses quotas, active-run limits or destination safety checks.

Open finding counts and Top 3 come from the **same shared Phase 05 query service** used by
Findings; the policy/ranking tuple and evaluator remain unchanged. Stale/not-rechecked labels
are retained, not silently removed to improve the display. Source and rule coverage use the
latest scan per current asset and retain Phase 05 missing-data semantics; no score is computed.
Finding responses now attach canonical task ID/status in batch, avoiding per-priority calls.

Task counts aggregate the owned current asset/finding/task joins by human status. The
separate done_unverified count is task done + finding open; it does not imply other open
findings have tasks. Recent queue: up to five tasks sorted by updated_at descending, stable
ID tie-break. Recent activity: up to five actual scoped task events, UTC time/insertion order.
Dashboard activity omits note bodies and authentication data.

The scan count is **all retained runs for current assets**, not a calendar-window or lifetime
count; the recent list shows at most five, ordered by source creation/insertion. Each links
to the existing exact asset/run route. Last useful observation is the newest saved pass,
attention or informational collection outcome under the known scanner version, excluding
revoked-authorization runs. It is not a whole-company trust timestamp or a guarantee that
all rules were evaluable. Last scan time and coverage remain visible separately. Deleted
assets' minimal scan snapshots are excluded because their review routes no longer exist.

Dashboard, `/app/tasks` and `/app/tasks/:id` use the established private shell. The optional
Business/Technical control reuses the Phase 05 presentation components; it changes no
permission or calculation. Task/finding/source-scan/asset controls cross-link to real records.
Reports/PDF, repeatable public demo, automation, multiuser assignment, payments and Phase 07
are deliberately absent. Test fixtures are isolated, labeled QA and never shipped as live data.
