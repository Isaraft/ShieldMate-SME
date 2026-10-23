# SHIELDMATE SME — CODEX IMPLEMENTATION BRIEF
## PHASE 05 — Evidence-Backed Finding Engine & Contextual Risk Prioritization

**Execution mode:** Implement the requested work in the **existing** ShieldMate repository. Do not stop at a plan or a prototype mockup.

**Scope:** Phase 05 only: translating persisted Phase 04 observations into defensible, explainable, prioritized findings and a working finding-review interface.

**Reported baseline:** Phase 04 completed locally at commit `a40e4be` on `main`, with a clean working tree, migration `1806ce4b7076`, 199 backend and 41 frontend tests. **Verify these claims against the actual working tree.**

**Next phase:** Phase 06 — Connected Dashboard, Remediation Tasks & History. **DO NOT START PHASE 06.**

---

## 0. ROLE, FIRST ACTIONS, AND SOURCE OF TRUTH

Act as a thoughtful senior full-stack engineer, application-security engineer, and product designer. ShieldMate must feel like a carefully designed human-built cybersecurity SaaS, not a collection of generated pages or invented security claims.

Before editing any code:

1. Read `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, `docs/design-system.md`, `docs/scanner.md`, and `docs/phase-04-results.md`, as available. Inspect existing models, Alembic migrations, Phase 04 scanner outputs, scan run states, observation types, serialization, API conventions, UI components, tests, and background worker lifecycle.
2. Confirm the real Git branch, commit, and status. Do **not** overwrite unrelated changes or edit existing migrations.
3. Run the previous baseline tests, lint, type checking, formatting, and frontend build; report actual baseline results. Identify existing technical debt without quietly changing scope.
4. Produce a short technical plan (roughly 10–20 lines) specifying your proposed finding model, rule registry, evidence provenance, risk policy, persistence and update mechanism, API/UI contracts, and reconciliation behavior.
5. Then **implement Phase 05 end-to-end**. When instructions conflict with real scanner semantics, inspect the implementation, pick a safe coherent design, document the tradeoff, and continue. Ask a question only for a true blocker.

**Product truth:** ShieldMate SME Starter helps Kazakhstan-based SMEs (about 10–100 staff) understand their limited external security exposure and what deserves attention first. Assignment 3 interviewed eight people and indicated a need for central visibility, business-language explanations and prioritization, not another noisy scanner. Assignment 4 narrowed the initial Starter offering to safe external checks, actionable priorities, weekly tasks and owner-friendly reports. This phase establishes the critical **observation → finding → priority → recommendation** portion.

## 1. PHASE OUTCOME AND DEMONSTRABLE USER JOURNEY

At the end of this phase, a user must be able to:

1. Sign in to an actual organization workspace with Phase 02 security intact.
2. View an enrolled, owned, verified domain and its persisted Phase 04 security scans.
3. Open an existing completed or partially completed scan containing genuine normalized DNS/TLS/HTTP observations.
4. See understandable findings derived **only** from those saved observations, including affected domain, evidence, classification, severity, reasoning, remediation, detection time, and limitations.
5. Identify a clearly ranked **Top 3** of current priorities, with an explanation of *why* each ranks where it does.
6. Switch between a concise business explanation and enough technical detail for an IT generalist to verify the evidence. This is only a presentation toggle, **not a new permission system**.
7. Filter or sort findings by priority, status, domain, and category; open a detail view; reload and get identical persisted results.
8. Rerun an authorized scan and see findings remain, update, resolve, or reopen according to valid new evidence, without fake resolutions during timeouts or incomplete scans.
9. See a truthful empty/incomplete state when no issue is supported by the evidence. Never see invented live metrics or fictional CVEs.

**Not in Phase 05:** remediation task CRUD, task owners/notes, marking tasks done, operational dashboard rebuild, reporting/PDF, demo-data seeding for final defense, phishing simulations, payment processing, external security integrations, LLM recommendations, attack-surface expansion, CVE matching, exploit testing, or deployment. Keep controls for these later features disabled/labeled where necessary.

## 2. ARCHITECTURE AND IMPLEMENTATION BOUNDARIES

### 2.1 Separation of responsibilities

Maintain a clean modular boundary:

- **Scanner/observation layer (existing Phase 04):** performs bounded, authorized observations; owns immutable technical evidence, checked-at timestamps and scan lifecycle.
- **Normalization/adaptation layer (Phase 05):** consumes actual persisted observation contracts without network calls; maps source-specific check outputs into typed evaluation inputs.
- **Rule engine (Phase 05):** evaluates conditions with versioned, deterministic rule IDs and returns explicit supported findings or `not_evaluable` states.
- **Priority policy (Phase 05):** computes explainable severity/order based on a stable documented rubric, rather than opaque or model-generated guesses.
- **Persistence/reconciliation (Phase 05):** maps each finding to source run/observation evidence, handles deduplication and lifecycle across scans, and exposes tenant-scoped current state/history.
- **API and frontend (Phase 05):** serve stored results and help users read them. UI must never become the source of truth for security severity or risk.

Do not modify scanner network safety or add network checks to evaluate findings. The engine must be **offline and pure** wherever feasible: deterministic output from the same stored inputs, policy version and clock context.

### 2.2 Persisted data and migrations

Design a focused, migration-managed schema appropriate to the existing SQLAlchemy/SQLite stack. Prefer adapting an existing model if it already expresses the correct concepts; avoid redundant tables.

Suggested minimum fields for a finding (names may follow project conventions):

- Stable DB ID; `organization_id`, `domain_id`, and a stable fingerprint computed from `(domain, rule_id, relevant finding discriminator)`.
- Rule identifier and **rule/policy version**; technical category (`dns_email`, `tls`, `https`, `http_headers`, etc.).
- Current lifecycle: `open`, `resolved`, and if useful a distinct `not_rechecked` or `stale` annotation **without equating it to resolved**. Distinguish lifecycle from priority.
- Severity/priority and clear reason; transparent ordering components, where applicable.
- Business-readable title, impact explanation, concrete recommended action and optional technical implementation notes. Avoid duplicated hardcoded text spread across layers.
- Sanitized, size-limited evidence pointer or snapshot, source scan ID, source observation ID(s), observed timestamp, `first_seen_at`, `last_seen_at`, `resolved_at` (nullable), latest evaluation timestamp.
- Confidence or evaluation status (supported, informational, inconclusive) if the existing model benefits from it. A failed check must not become a confirmed vulnerability.

Maintain a way to inspect previous evaluation/scan lineage: a compact evaluation-event table or immutable history snapshots if needed. Do not destroy earlier source evidence when a finding changes.

Requirements:

- New **additive** Alembic migration only, after `1806ce4b7076`; do not rewrite past revisions.
- Foreign keys, tenant-safe joins, uniqueness constraints/fingerprints and indexes supporting organization/asset/status/priority queries.
- Transactional persistence; safe retries; idempotent reconciliation of the same scan run (no duplicate findings or doubled `first_seen`).
- Existing organizations, accounts, sessions, domains, ownership proofs, scans, and observations must survive upgrades, restarts and new feature use.
- Avoid unconstrained historical growth or storing full HTTP responses. Document retention/size decisions.

### 2.3 Evaluation trigger and backfill

An eligible **terminal** scan should be evaluated exactly once logically, with idempotent retry/recovery if the worker dies or the process restarts. Completion hooks, an explicit reconciliation service or database-backed work are acceptable; choose the simplest reliable design matching Phase 04.

- Evaluate source observations after the run has reached a terminal state and observations are committed.
- Handle `completed`, `partial`, `failed`, `interrupted` according to their **actual** semantic contracts; a partially successful scan may yield findings only for checks that produced sufficient evidence.
- Do not evaluate incomplete/in-flight observations as definitive.
- Existing Phase 04 runs should be eligible for **safe, idempotent backfill** into findings. Provide an explicit controlled command or documented one-time migration strategy where needed; do not silently rewrite observation history.
- Use a clearly versioned policy for re-evaluation so results are reproducible and rule changes cannot invisibly overwrite the meaning of old snapshots.
- Scans and findings from other tenants must never be accessible through this pipeline.

## 3. RULE CATALOG: EVIDENCE, NOT SPECULATION

Implement a **small, high-confidence set of rules** using only the check IDs and fields that Phase 04 really persisted. Inspect the code first; do not invent observation data or claim visibility the scanner does not have.

For each implemented rule, document:

1. Immutable stable `rule_id`, version, category and user-facing title.
2. Exact source check(s)/fields and conditions necessary to evaluate.
3. Supported positive/negative/not-applicable/inconclusive outcomes.
4. Recommended severity, confidence, urgency and justified business impact.
5. Concrete step a small-business IT contact can take and a way to recheck the result.
6. Caveats/false-positive conditions and examples of unsupported conclusions.
7. Deterministic tests with representative observation fixtures.

**Suggested catalog, subject to actual available Phase 04 evidence:**

| Signal supported by saved evidence | Allowed conclusion / priority guidance | Important restraint |
|---|---|---|
| TLS certificate rejected as expired or outside its validity period | Strong actionable TLS trust/availability issue; high if conclusively identified | A generic handshake failure is **not** proof of an expired certificate. |
| TLS certificate currently valid but close to expiry | Time-bounded maintenance risk; use explicitly documented thresholds, e.g. <=7 days high, 8–30 days medium | Use source timestamp; do not claim current expiry state from stale data without fresh checking. |
| TLS hostname mismatch or verifiably invalid trust chain | Clear trust/configuration concern if the scanner produces unambiguous evidence | If the failure reason is unspecified, show an inconclusive check instead of a named vulnerability. |
| HTTPS unavailable while HTTP is observed | Potential transport exposure/availability concern; severity depends on reliable available signals | DNS errors or failed probes cannot establish absence of HTTPS. |
| HTTP→HTTPS redirect not configured where assessed | Reasonable web transport hardening recommendation | Do not follow redirects or infer behavior that was never tested. |
| Missing HSTS on a **successfully inspected HTTPS response** | Contextual configuration finding, typically low/medium | Missing HSTS does not prove exploitation; uninspected HTTPS is unknown. |
| Missing `X-Content-Type-Options: nosniff` on evaluated web response | Low-priority hardening recommendation | Do not pretend it is a critical vulnerability. |
| Missing/weak CSP, frame protection, referrer policy, etc. | Apply cautious, documented conditions to real observed response headers | Not all services serve HTML; missing CSP is not proof of XSS. Treat inapplicable contexts honestly. |
| Multiple/conflicting SPF TXT policies or syntactically invalid SPF | Email-authentication configuration issue when parsing reliably supports the conclusion | No SPF != compromised email. Some domains do not send mail. |
| Missing SPF on a domain with evidence suggesting email use | Contextual recommendation rather than an unconditional severe incident | MX alone suggests inbound handling, not necessarily outbound email. |
| Missing/monitor-only DMARC | Email-domain hardening recommendation with justified low/medium risk | `p=none` is not equivalent to being unprotected in every respect; no proof of phishing compromise. |
| Missing MX records | **Informational/context only** in most situations | Many legitimate domains do not receive mail. Do not label as a vulnerability. |
| DNS lookup timeout / SERVFAIL / unknown check | `inconclusive` / `could not assess` | An error is not a finding of safety or compromise. |

Do not implement rules that require unperformed intrusive checks, page crawling, authenticated access, exploit validation, IP reputation, CVE feeds, OS fingerprints, breached credentials or customer business criticality inputs that do not exist.

A domain can legitimately be mail-less. A TLS timeout can be temporary. Security headers are contextual. Favor **fewer well-justified findings** over a flood of generic alerts.

Preserve and display concrete supporting values where safe (e.g., certificate expiration date, header presence, SPF/DMARC policy), scan time and observation method. Avoid storing raw sensitive bodies, session cookies, challenge tokens, arbitrary HTML, or uncontrolled response text. Escape all untrusted evidence in the UI.

## 4. RISK RANKING, EXPLAINABILITY AND COVERAGE

### 4.1 Prioritization methodology

Implement **deterministic, comprehensible prioritization**. Document the method and design tradeoffs in `docs/risk-methodology.md`.

A good MVP approach is a small rubric rather than pseudo-precise "AI risk scores":

- **Impact:** realistic business consequence of the particular configuration issue, based on what the check supports.
- **Exposure/relevance:** only directly observed public-facing exposure or applicable policy context; do not invent the company's data sensitivity or asset criticality.
- **Urgency:** action timescale, e.g., a certificate expiring soon is more urgent than a cosmetic response-header gap.
- **Confidence:** whether the evidence is conclusive, contextual or insufficient; insufficient evidence is excluded from asserted findings.

Either use an explicit, documented weighted formula with bounded values or a stable ordered severity/urgency rubric. The exact arithmetic must be understandable and accompanied by worked examples. Prefer labels such as `Critical / High / Medium / Low / Informational` only where defensible; no obligation to use Critical if none of these limited checks warrants it.

**Never manufacture CVSS values, CVEs, exploitation likelihood, attack probability, financial losses, threat-actor activity, compliance certification, or 0-day claims.** Your internally defined score must never be labeled "CVSS" or presented as an external industry benchmark.

### 4.2 Stable Top 3 priorities

Derive the **Top 3 current open, evidence-backed priorities** on the server from the same database records shown in the findings list.

- Define a reproducible sort order, including explicit tie-breakers: severity/priority, urgency, applicable context, observed time, stable identifier.
- Deduplicate repeats across scans; do not show identical unresolved issues three times because a user reran the same scan.
- If fewer than three supported open findings exist, display the actual number; do not invent entries.
- Each priority must include `Why this matters` + `Recommended next step` + verifiable source evidence.
- Support concise **Business** and expandable **Technical evidence** explanations using the same truth source.
- Do not call low-priority informational records a "critical" issue merely to fill the summary.

### 4.3 Posture / score discipline

The product concept mentions a simple security posture score, but this MVP examines only a **narrow subset of external configuration**.

**Preferred:** show a clearly named **Limited External Configuration Assessment** with the number of evaluated checks, passed/attention/inconclusive/not-applicable counts, and an actionable priority list.

**Optional only if reliable and documented:** introduce an **Indicative External Configuration Score** (0–100) derived deterministically from applicable successfully assessed checks. If implemented:

- Put *Indicative / limited checks only* directly next to the value and show the checked scope and timestamp.
- Explain the exact formula, weighting, normalizer, and missing-data handling in plain language.
- Distinguish `0 successful checks` = **No score available**, never 100/100 or 0/100 by default.
- Do **not** silently treat `error`, `inconclusive`, `not_applicable` or `not_checked` as passed.
- State that this does not measure full company security, endpoint protection, incident readiness, phishing resistance or regulatory compliance.
- If coverage is too low, withhold a numerical score rather than imply precision.

Avoid meaningless animated gauges or vanity charts. Phase 06 owns the broader operational dashboard; implement only the assessment/priority summary needed for Findings in Phase 05.

## 5. FINDING LIFECYCLE, DEDUPLICATION, AND SCAN COMPARISON

The lifecycle policy is a **high-priority acceptance area**:

1. **New supported issue:** create an `open` finding with real source evidence, timestamps and stable fingerprint.
2. **Same issue confirmed in a later eligible scan:** keep the same logical finding; refresh `last_seen`, latest evidence and severity if warranted; do not duplicate or reset `first_seen`.
3. **Issue no longer present in a later conclusive, relevant successful check:** mark it `resolved` with `resolved_at` and record the scan that supports resolution. Only a comparable check of the same exact asset/rule can resolve it.
4. **Later scan fails, times out, returns `not_applicable` without meaningful equivalence, or omits a check:** **do not resolve** the prior finding. Show `Not rechecked / verification unavailable` or analogous accurate status, retaining the last known state and timestamp.
5. **Previously resolved issue reappears in a later conclusive scan:** reopen the same logical finding (or create an explicitly linked recurrence) with a visible history. Never silently overwrite the prior resolution event.
6. **Manual task completion (future Phase 06):** must never automatically mark a technical finding resolved. Only new conclusive technical evidence can do that.
7. **No scans yet:** do not generate a fabricated finding inventory, a zero-risk score, or a false green "Secure" verdict.
8. **Old data:** distinguish the time when a result was last observed from the present time; label data stale using a configurable policy. Expired proof does not retroactively erase historical findings, but it prevents fresh scans until reverified.
9. **Repeated processing/restart/race:** same scan evaluation is idempotent. Use robust transactional uniqueness/locking appropriate for SQLite; test worker restart, multiple callers and backfill retry.

Keep finding evidence and resolution provenance durable. Never imply that the user's company remediated anything simply because an unrelated later scan completed.

## 6. API CONTRACTS AND BACKEND AUTHORIZATION

Inspect existing `/api/v1` conventions and implement the minimum endpoints that best fit the codebase. Suggested read-only surface (adapt to existing routes rather than duplicate):

- `GET /api/v1/findings` — tenant-scoped list with bounded pagination and validated filters (`status`, `severity`, `category`, `domain_id`, sort).
- `GET /api/v1/findings/{finding_id}` — full details, evidence provenance, timestamps and appropriate lifecycle history.
- `GET /api/v1/findings/priorities` — stable top-three current actions; document whether a single summary endpoint is preferable to avoid N+1 calls.
- `GET /api/v1/findings/summary` — actual counts by priority/status/category and assessment coverage. No fictional metrics.

If enabling optional explicit re-evaluation/backfill endpoint is necessary, make it admin/maintenance-only or use a local management command. Do not allow end users to submit their own observation payloads, severity ratings, internal rule parameters, arbitrary URLs, or force fake resolution.

API requirements:

- Derive tenant ownership from the authenticated server-side session and organization relationship; never trust arbitrary `organization_id`.
- Return no existence hints for other tenants' finding IDs (consistent 404/denied semantics). Test IDOR via finding ID, scan ID, domain ID and filters.
- Limit result sizes, evidence lengths, cursor/page size and sort fields; validate all request parameters.
- Preserve existing CSRF/Origin protections for any new mutation, and avoid changes to secure cookie/session behavior.
- Typed request/response models, versioned/consistent enums, predictable error envelopes, UTC timestamps and stable pagination order.
- Do not expose raw SQL objects, server tracebacks, secrets, security challenge tokens or unfiltered user-controlled HTTP headers.
- Use query indexes; avoid inefficient N+1 queries and compute aggregate totals only from scoped persisted data.

## 7. FRONTEND — REAL FINDINGS, NOT DECORATIVE METRICS

Implement actual, polished app integration using the **existing** React/TypeScript components and established navigation. Prefer `/app/findings` and `/app/findings/:id` or the repository's route conventions.

**Required screens/behaviors:**

- **Findings list:** actual open/resolved/stale state, priority labels, affected domain, evidence timestamp, category, plain-language title; stable sorting and functional filters. Clear pagination if needed.
- **Top priorities:** no more than three *actual* actionable findings, each with a short explanation and next step, linked to details.
- **Detail view:** easy-to-understand issue, why it matters to an SME, precise recommended action, observed evidence, check provenance and time, severity rationale, confidence/limitations and resolution/reopening history when available.
- **Mode toggle:** Business / Technical changes detail level only; both views represent the same finding and same underlying data.
- **Links from scan details:** where supported, expose an accessible route from a Phase 04 observation/scan to its related finding(s). Preserve the original technical observation; do not replace the scanner screen with generalized findings.
- **Honest states:** first-use/no scans, clean evaluated scope, still processing, insufficient evidence, stale scan, network/error state, access denied, loading, and unsupported assessments. Differentiate "No supported issues found in the checks performed" from "No security risks exist."
- **Usability:** keyboard navigation, semantic tables, visible focus, screen-reader labels, accessible filtering and dialogs, contrast compliant with WCAG AA, responsive layout at 360/768/1280/1920 CSS px, reduced motion, human-written concise copy.

**Visual language:** maintain **BURGUNDY + RED**, not burgundy-pink or generic blue. Bold editorial identity (Anton display if established, IBM Plex Sans body), warm ivory for contrast, decisive spacing, disciplined density, no glassmorphism/gradient clichés, fake company stats, decorative charts, gratuitous animations or meaningless icons. This is a technical security workspace, not a pasted marketing-slide design. Preserve all Phase 01–04 screens and navigation.

Any remediation task CTA must be marked **Coming in Phase 06** unless a pre-existing feature already legitimately supports it. Do not silently implement task persistence.

## 8. SECURITY, CORRECTNESS, AND TEST MATRIX

Automated checks must include **at least** the following relevant cases and use deterministic, injected fixtures rather than live third-party scans in CI:

**Rule correctness**
- Conclusive vs. inconclusive check results; missing/ambiguous fields; unsupported check versions.
- Representative SPF/DMARC, TLS expiry/trust/hostname and HTTP-header checks that are actually supported by Phase 04 observation schema.
- Missing MX as informational, not a high-severity finding; no email-policy assumptions beyond available signals.
- TLS connection failure vs. conclusively expired certificate; HTTP timeout vs. confirmed missing header.
- HTML/non-HTML contextual applicability for browser response headers if evidence supports it; otherwise conservative classification.
- Deterministic evaluation on identical inputs; policy version recorded; explicit priority tie-breaking.

**Lifecycle & persistence**
- First detection, repeated scan without duplication, severity update, valid resolution, recurrence/reopening.
- Failed/partial scan does not resolve unrelated findings; missing checks do not resolve findings.
- Worker restart or retry evaluation idempotency; concurrent evaluations safe.
- Stored results survive container restart; migration preserves all existing entities and histories; no Alembic drift.
- Existing Phase 04 scans can be backfilled safely and repeatably.

**Authorization & data protection**
- Unauthenticated access denied; tenant A cannot list/read tenant B's findings or change results by forging IDs.
- Input filtering/pagination cannot escape organization scope or expose hidden records.
- Untrusted DNS/HTTP header values rendered as text only; no script injection/XSS.
- Evidence bounded/redacted; no cookies, tokens, DNS ownership challenge values or secret headers leaked.
- No external network probes from finding evaluation, and no regression to scanning SSRF protections.

**UI / integration**
- End-to-end flow against seeded **explicitly labeled test fixtures**: authentic account → owned asset → test scan observations → persisted findings → top-three → detail → reload → filters.
- Empty, clean, partial, stale and error states all accurate and accessible.
- 360 / 768 / 1280 / 1920 widths, keyboard focus, axe/accessibility checks and no horizontal overflow.
- Test exact API counts vs displayed counters; no random/hardcoded production findings.

Run: backend pytest, Ruff and mypy; frontend Vitest, lint, typecheck, format, production build; Alembic upgrade/drift; Docker build/health/restart; dependency audits; relevant browser checks; `git diff --check`. Report exact commands/counts, not estimates. If a test cannot be run, label **NOT TESTED** and explain.

**Real-world smoke testing:** No new external network access is required to complete Phase 05. If no team-controlled, freshly DNS-verified domain is available, keep live owned-domain E2E explicitly **NOT TESTED**. Never scan a third-party domain to make the report look complete. Keep fixture-produced output labeled QA/fixture and separate from real assessments.

## 9. DOCUMENTATION AND ASSIGNMENT 5 ALIGNMENT

Create/update:

- `docs/risk-methodology.md`: each rule ID, source check, applicability, severity rationale, confidence/unknown states, ranking formula/rubric, tie breaks, coverage caveats, lifecycle rules, worked examples and known false positives.
- `docs/phase-05-results.md`: baseline, decisions, changed files, real commands/output, test results, safety findings, screenshot paths, known limitations, exact acceptance status and Git information.
- Architecture/API documentation and README where behavior changed; Alembic version and local startup instructions.
- Where practical, preserve real screenshots for Assignment 5, distinguishing any injected fixture or QA session from actual live scan evidence.

For later alpha/beta testing, structure top-priority wording so an SME owner/IT generalist can answer **"What should I fix first, and why?"** quickly. The future hypothesis is >=80% of at least five real SME testers correctly identify the top issue and its next action unaided within 120 seconds. **Do not fabricate beta testers, survey responses, durations or outcomes in this phase.**

No new user analytics, telemetry, external AI API or third-party service is required. Do not claim security certifications, validated customer demand or production deployment.

## 10. PHASE 05 ACCEPTANCE GATES — REPORT EACH AS PASS / FAIL / NOT TESTED

1. Baseline verified; existing repository, previous features and branding preserved.
2. A typed, versioned, deterministic evaluator consumes **actual saved Phase 04 observations** with no network probes.
3. Rules assert only defensible findings and distinguish pass/attention/inconclusive/not-applicable correctly.
4. Each finding shows affected asset, rule ID, evidence source, observed-at, severity rationale, business impact and actionable remediation.
5. Documented priority rubric and deterministic server-side Top 3; no false CVSS, exploit claims or manufactured findings.
6. Honest scope/coverage and missing-data handling; numerical posture score (if any) is limited, justified and withheld on insufficient evidence.
7. Tenant-scoped persistent current findings and history; migration is additive and preserves old data.
8. Deduplication, idempotent retries, backfill and crash/restart behavior verified.
9. Genuine same-rule new-evidence resolution and reopening; partial/error/missing checks cannot falsely resolve findings.
10. Protected, typed APIs with validated filters/pagination and tested organization isolation / IDOR.
11. Fully connected list, detail, priority summary, filters and useful loading/empty/partial/stale states.
12. Burgundy/red UI preserved; 360/768/1280/1920 responsive and accessibility checks reported.
13. No backend scanning/auth/session/CSRF regression and no unbounded/sensitive evidence exposure.
14. Backend/frontend tests, quality checks, migrations, dependency audits and Docker checks actually executed; outcomes documented.
15. `docs/risk-methodology.md` and `docs/phase-05-results.md` are complete with limitations and test-fixture distinctions.
16. Local Git commit and clean status if permitted by existing workflow; **no push, no deployment, no Phase 06 work**.

## 11. REQUIRED HANDOFF FORMAT

Report concisely but substantively:

```text
Phase: 05 — Evidence-Backed Finding Engine & Contextual Prioritization
Baseline commit / final local commit / branch:
Architecture & ranking decisions:
Rule catalog and evidence limitations:
Files changed and Alembic revision:
Implemented / intentionally not implemented:
How historical scans are evaluated/backfilled:
Findings and lifecycle examples:
API routes and frontend screens:
Exact commands executed & ACTUAL results:
Security tests (including tenant/IDOR and inconclusive/resolution cases):
Responsive and accessibility results:
Acceptance gates 1–16: PASS / FAIL / NOT TESTED + evidence:
Known limitations and manual actions:
Local run instructions:
Git status / no push / no deploy:
Next phase: 06 — NOT STARTED
```

**Complete Phase 05 now, not merely the plan. If a difficult requirement cannot be met safely, do not fake it: document the blocker and leave the unsafe path unavailable. Do not push or deploy, and do not begin Phase 06 without explicit user approval.**
