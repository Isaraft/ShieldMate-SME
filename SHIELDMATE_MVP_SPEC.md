# ShieldMate SME — Technical Specification for Starter MVP

**Project:** ShieldMate SME  
**Course:** Technological Entrepreneurship — Assignment 5: Creating an MVP  
**Status:** implementation specification, not a claim of completed functionality  
**Prepared from:** Assignments 1, 2, 3, 4 and Assignment 5 requirements; design references supplied by the team  
**Primary market:** Kazakhstan; digitally dependent SMEs with roughly 10–100 employees  
**Initial focus:** e-commerce; also relevant to accounting/outsourcing and private clinics

---

## 0. Product decision and boundaries

ShieldMate SME is **not** a SIEM, SOC, EDR or general-purpose vulnerability scanner. It is a lightweight **risk-to-action platform**: gather a small number of meaningful, verifiable signals from authorized internet-facing assets, normalize them, explain business impact, prioritize issues and turn them into manageable remediation tasks and an owner-ready report.

Assignment 3 (eight respondent interviews) showed demand for consolidated visibility, understandable explanations and prioritization. Assignment 4 refines this into **Starter**, with limited external checks, prioritized actions and reports. Phishing simulation, extensive integrations and expert response belong to a future **Plus** package rather than the first build.

**Golden path:** user opens demo or signs in → adds/chooses an authorized company domain → verifies ownership → starts a check → sees evidence-backed findings → understands the top priority → creates/updates a remediation task → downloads a management PDF. A clearly labeled sample organization/data set must support predictable offline demonstrations; it must never be passed off as live results.

**Primary success hypothesis for testing (one sentence):** “A simplified dashboard with contextual priorities enables at least 80% of target SME users to identify their highest-priority external security issue and its recommended action without assistance within two minutes.”

**Prespecified success criterion:** in a beta with **at least 5** real target-audience participants, **at least 80%** successfully complete that task within 120 seconds. Secondary metrics: task completion, time to first useful action, task-status completion, perceived clarity (1–5), and qualitative feedback. These are targets, **not actual test results**.

## 1. Users and jobs

1. **Owner / operations manager:** needs a short high-level summary: current issues, critical priorities, responsible next action and progress. No security jargon without explanation.
2. **IT generalist / administrator:** needs source evidence, affected asset, check method, timestamp, remediation instructions and task state.
3. **Beta evaluator:** may be a small-business owner, operations manager, outsourced IT provider or SME IT staff member; no need to expose any real organization’s sensitive data for testing.

Do not create full enterprise role management or multi-tenant administration. For MVP support one organization workspace per authenticated account and a presentation toggle **Executive / Technical**; this toggle changes content density, not user permissions. Keep authorization rules enforced in the backend and isolate workspaces by organization.

## 2. Must-have use cases and acceptance criteria

| ID | Use case | What must demonstrably work |
|---|---|---|
| UC-01 | Enter product | User can register/sign in for a workspace or select labeled Sample Demo; session persists securely across page refresh, sign-out works. |
| UC-02 | Manage authorized domain | Add syntactically valid FQDN; see pending/verified state; obtain a unique DNS TXT challenge; perform backend check of TXT record and mark verified only on match. |
| UC-03 | Run authorized security checks | On a verified public domain, start a non-intrusive check, show running/finished/failed status and timestamps, persist results. Unverified domains cannot be scanned. |
| UC-04 | Review findings | Each finding has asset, check type, severity, observation, plain-language impact, concrete remediation, technical evidence and last checked time. |
| UC-05 | See prioritized dashboard | Dashboard displays transparent counts and top actions derived from persisted findings, not random hardcoded production numbers. |
| UC-06 | Track remediation | User can start a task, assign an owner label, add a note and mark it completed; values survive reload. Completion is NOT automatically represented as verified remediation. |
| UC-07 | View different detail levels | Executive mode gives business-oriented summary; Technical mode shows DNS/HTTP/TLS evidence and check outcomes from the same data. |
| UC-08 | Export owner report | Download a real PDF with organization, reporting timestamp, scope, summary, open findings, priority actions and clear label for demo versus actual data. |
| UC-09 | Demonstrate without external services | A realistic, explicitly labeled Sample Demo workspace works predictably, including findings, task updates and export. |
| UC-10 | Safely handle errors | Invalid domain, private address, unverified asset, missing DNS, inaccessible HTTPS, invalid cert, timeout and empty results display honest states; never invent a successful scan. |

## 3. Feature prioritization (MoSCoW)

We choose **MoSCoW** because the deadline and team capacity constrain scope more than precise reach/impact estimates; Assignment 5 requires at least eight possible features with justified priorities.

| Feature | Priority | Reason |
|---|---|---|
| F01 Company workspace + basic sign-in | Must | Persist a real user flow and separate organizations. |
| F02 Domain addition and ownership verification | Must | Required authorization before probing an asset. |
| F03 Passive DNS checks (MX, SPF, DMARC) | Must | Low-impact, actionable configuration signals. |
| F04 HTTPS certificate and basic HTTP security-header checks | Must | Practical, checkable external exposure signals. |
| F05 Finding normalization and severity/risk ordering | Must | Core differentiation: transform evidence into actions. |
| F06 Dashboard with top three priorities | Must | Management-friendly view supported by interviews. |
| F07 Finding detail + concrete remediation instructions | Must | Lets technical users act on findings. |
| F08 Task status, owner label and history | Must | Proves risk-to-action workflow, rather than scanner-only UI. |
| F09 Labeled sample/demo workspace | Must | Enables reliable defense and beta testing without real target access. |
| F10 PDF management report | Must | Required by narrow Starter positioning and compelling live demo. |
| F11 Executive/Technical view toggle | Should | Connects distinct customer needs from interviews. Implement after core flow. |
| F12 Russian/English UI strings | Should | Local market differentiator. Prioritize critical workflow strings. |
| F13 Scan history and simple progress trend | Should | Show only from actual stored snapshots; no invented time series. |
| F14 Manual CSV finding import | Could | Useful multi-tool consolidation after core workflow works; not needed for acceptance. |
| F15 Weekly email summary | Could | Later engagement improvement; not needed for prototype demo. |
| F16 Phishing simulations and microtraining | Won’t (MVP) | Assignment 4 puts this in Plus; consent/compliance and email infrastructure add scope. |
| F17 SIEM/EDR/cloud API integrations, SOAR | Won’t (MVP) | Scope and maintenance overhead beyond Starter. |
| F18 Billing/payments, production subscriptions | Won’t (MVP) | ₸50,000/month remains an unvalidated proposed price, not a paid product. |
| F19 Exploitation, port sweeping, credential testing | Won’t | Not needed for hypothesis; unsafe and misleading as a Starter capability. |

**Scope precedence:** Implement Must features fully, then Should if stable. Do not sacrifice functional checks or test evidence to add decorative graphs, AI chatbot, subscription checkout or phishing campaigns.

## 4. Check catalog and evidence rules

Implement individual check functions with deterministic IDs and structured results (`pass`, `fail`, `error`, `not_applicable`). Error never equals secure/pass. Record UTC timestamp, target, source/check ID, raw-but-sanitized observation, verdict and explanation. For findings, apply stable rule IDs so repeated scans update current state without duplicating infinitely.

**Minimum live checks, only for verified domains:**

1. `DNS_MX_PRESENT`: does domain have MX records? Missing MX is **informational**, not automatically a vulnerability: some domains intentionally do not receive mail.
2. `DNS_SPF_PRESENT`: inspect relevant TXT SPF record presence. Missing SPF is a possible **medium** concern if domain sends email; state this condition, don't pretend to validate full policy semantics.
3. `DNS_DMARC_PRESENT`: inspect `_dmarc.<domain>` TXT record presence and basic syntax. Missing policy is a possible **medium** concern if domain sends mail.
4. `TLS_CERT_VALID`: HTTPS TLS handshake and certificate trust / hostname validation. Invalid/expired certificate can be **high**, but distinguish unreachable service from an invalid certificate.
5. `TLS_EXPIRING_SOON`: certificate expires within **30 days**; **medium** operational warning. Avoid duplicate higher-severity finding if already expired.
6. `HTTP_HSTS_PRESENT`: for reachable HTTPS response, detect HSTS. Missing HSTS is a **low/medium** hardening recommendation depending on context; do not call it an exploitable vulnerability.
7. `HTTP_SECURITY_HEADERS`: check `Content-Security-Policy`, `X-Content-Type-Options` and `Referrer-Policy`, each independently and conservatively. Missing headers are **hardening findings** with context, not proof of compromise. CSP is not universally appropriate for all sites.

A domain that is unreachable by HTTPS can have `not_applicable` header checks; do not claim that all headers are missing. A certificate validity problem should not be silently bypassed merely to produce green HTTP results.

**Finding schema:** `rule_id`, `domain`, `severity`, `status`, `title`, `business_impact`, `technical_evidence`, `recommendation`, `detected_at`, `last_seen_at`, `source_scan_id`. Severity values: `critical`, `high`, `medium`, `low`, `info`. Only assign severity according to explicit written check rules, not arbitrary LLM judgment.

**Prioritization logic (transparent and testable):** Sort open findings by severity weight (`critical=25`, `high=15`, `medium=7`, `low=3`, `info=0`), then by exposure relevance and freshness; ties deterministic. Optional **illustrative posture indicator** = `max(0, 100 - min(100, sum(weights of unique active findings)))`. Label it **“Indicative exposure score — limited checks only”**, show calculation/method, and never market it as a comprehensive security rating. The top three issues should each include an action and estimated effort label (`quick`, `moderate`, `requires IT review`), chosen from static rules, not hallucinated.

**Scan/update semantics:** A prior finding is considered no longer observed only when the corresponding check later returns a real `pass` for the same verified asset. `error`/`not_applicable` must not close findings. User marking a remediation task completed is a workflow action and is not equivalent to retest confirmation.

## 5. Security and legal constraints (non-negotiable)

1. Do not scan or probe assets without explicit control/authorization. Use domain-specific DNS TXT ownership challenge (random, expiring token) before active TLS/HTTP checks. Sample data are local fixtures only.
2. Accept only FQDNs, not arbitrary URLs, IP literals, ports, URLs with userinfo, or paths. Normalize IDNA safely; reject localhost, `.local`, invalid names and domains pointing only to internal/private/link-local/reserved/metadata IPs.
3. Re-resolve before connection and **pin actual connections to a validated public IP**; reject DNS rebinding/private IP transitions. Never blindly delegate arbitrary user-controlled URLs to a general HTTP client. Do not follow redirects to other hosts. Add strict connect/read timeouts, size limits and egress rate limits.
4. Restrict external requests to DNS and a bounded HTTPS check on port 443. No port sweeps, vulnerability exploits, brute force, phishing emails, or credential acquisition.
5. Handle HTTPS certificate problems as honest findings or errors, rather than disabling TLS validation globally.
6. Backend owns all authorization and organization filtering; never trust frontend-supplied organization IDs. Basic password hashing, secure session cookies, CSRF protection where appropriate, environment-based secrets, no hardcoded production credentials.
7. Do not save secrets, unnecessary personal data or full HTTP response bodies. Sanitize recorded observations and logs. Keep audit timestamps for scans/task changes.
8. User-visible disclaimer: “ShieldMate Starter performs limited external configuration checks. It does not guarantee security or detect all vulnerabilities.”
9. If a safety constraint cannot be implemented correctly, disable the affected live check and explain the limitation instead of silently bypassing the constraint.

## 6. Screens and UX specification

**Visual target (authoritative override):** bold **BURGUNDY–RED** identity, never blue/teal or pink-led. Visual references are the three presentation screenshots in `docs/design-references/`, used for *mood, colors, strong condensed typography and art direction only*, not for copying slides or their content. An editorial / restrained brutalist public website may use oversized condensed headings and asymmetry; the authenticated SaaS UI must be calmer and exceptionally readable for evidence tables, risk priorities and tasks. Initial candidate tokens (adjust only for contrast and coherent final art direction): deep burgundy `#570711`, dark wine `#321015`, crimson red `#98121F`, vivid red `#CF2431`, warm off-white `#F7F0EA`, near-white `#FFF9F5`, muted borders `#D9C7C3`. These are **burgundy and red** first; any light pastel is neutral contrast, never the main brand. Pick at most two deliberately chosen families, for example Anton (headlines) and IBM Plex Sans (UI/body), with system fallbacks and legitimate sources. Enforce WCAG AA contrast. No default blue cyber palette, neon/glassmorphism, purple gradients, emoji icons, repetitive AI-generated cards, fabricated testimonials/stats or overanimated components. Prefer strong information hierarchy, editorial layouts on marketing pages, precise states in-app, consistent tokens and reduced-motion support. Verify at 360/768/1280/1920px. Mobile-first responsive implementation.

### S01 — Welcome / workspace
- Project name and concise value proposition: “Know what to fix first.”
- Sign in / create organization; distinct **Explore Sample Demo** entry.
- Clear scope disclaimer. No fake corporate logos/testimonials.

### S02 — Overview Dashboard
- Header: org name, last successful scan, number of verified domains, Demo/Live label.
- Four metrics: open high-priority findings, medium/low findings, tasks awaiting action, verified assets. Derive each from DB.
- “Your top 3 actions” cards, prioritized from actual findings.
- High-level exposure score if implemented, with tooltip/methodology.
- Executive/Technical display switch if F11 implemented.
- Empty state after new signup instructs to verify a domain, not a meaningless zero-risk score.

### S03 — Assets
- List added FQDNs with `pending`, `verified`, `verification_failed`, `last_scan`.
- Add domain dialog; DNS TXT instructions with exact generated name/value and copy controls.
- Verify ownership button; Run Check disabled until verified.
- Live scan progress and last outcome, helpful failure details.

### S04 — Findings
- List/table sortable by severity, asset, first/last seen, status.
- Filter by severity, status and domain.
- Each finding opens detail with one-sentence business explanation, technical evidence, affected scope, timestamp and exact remediation guidance.
- Create task / go to task action.

### S05 — Action Plan
- Focus on short priority queue, not a complex Jira clone.
- Fields: finding, priority, owner label, `open`/`in_progress`/`completed`, free-text note, updated timestamp.
- All updates persist and are included in summary reports.
- Distinguish task completion from issue verification.

### S06 — Reports
- Summary preview and Generate PDF / Download PDF.
- Must include data provenance, time period or “as of” time, domain scope, top three actions, findings by severity, task progress, limitation/disclaimer and Demo/Live marking.
- If insufficient live data, say so; do not generate fabricated trends.

### S07 — Optional history/settings
- Honest per-scan history (timestamp, checks, count, errors, status). Trend only with at least two actual scans; otherwise “Not enough historical data”.
- RU/EN setting if F12.

## 7. Suggested architecture

Keep the stack conventional and locally runnable:

```text
frontend/     React + TypeScript + Vite + Tailwind CSS
backend/      FastAPI + Pydantic + SQLAlchemy + Alembic
backend/tests/ pytest + FastAPI TestClient/HTTPX testing helpers
frontend/tests/ Vitest + React Testing Library
storage/      SQLite persistent volume for MVP
Dockerfile(s), docker-compose.yml, .env.example
README.md, docs/architecture.md, docs/testing.md, docs/demo-guide.md
```

Alternative: if a pre-existing repository contains a working equivalent stack, **adapt to it instead of rewriting**. SQLite is sufficient for low-concurrency academic MVP; migrations and a single backend worker are fine. Do not add Kubernetes, Elasticsearch, Kafka, Redis, Celery, microservices, LLMs, payment gateway, or cloud vendor dependencies for this version.

**Scanning execution:** persisted `ScanRun` record (`queued`, `running`, `completed`, `failed`); basic controlled async/background execution with one deployment worker is acceptable for MVP. Requests should return a scan ID promptly and frontend polls for status. Persist failures, detect abandoned `running` jobs after restart and mark them failed; document that this is not a durable multi-worker production queue.

**Suggested relational entities:**
- `User(id, email, password_hash, created_at)`
- `Organization(id, name, owner_user_id, created_at)`
- `Domain(id, organization_id, fqdn, verification_token_hash, verification_expires_at, verified_at, created_at)`
- `ScanRun(id, organization_id, domain_id, status, started_at, finished_at, failure_reason, is_demo)`
- `CheckResult(id, scan_run_id, rule_id, verdict, normalized_observation, checked_at)`
- `Finding(id, organization_id, domain_id, rule_id, severity, lifecycle_state, title, business_impact, technical_evidence, recommendation, first_seen_at, last_seen_at, last_scan_id)`
- `RemediationTask(id, organization_id, finding_id, status, owner_label, note, created_at, updated_at, completed_at)`
- `AuditEvent(id, organization_id, event_type, subject_id, occurred_at)`

Enforce uniqueness `(organization_id, fqdn)` and `(organization_id, domain_id, rule_id)` for current findings. Use migrations. Never expose password hashes, raw tokens or internal stack traces in API responses.

### 7.1 API contract (suggested)

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/me
GET    /api/v1/organization
GET    /api/v1/domains
POST   /api/v1/domains
POST   /api/v1/domains/{id}/verification/request
POST   /api/v1/domains/{id}/verification/check
POST   /api/v1/domains/{id}/scans
GET    /api/v1/scans/{id}
GET    /api/v1/findings?severity=&state=&domain_id=
GET    /api/v1/findings/{id}
GET    /api/v1/dashboard/summary
GET    /api/v1/tasks
POST   /api/v1/tasks
PATCH  /api/v1/tasks/{id}
GET    /api/v1/reports/summary.pdf
GET    /api/v1/demo/metadata
```

Prefer stable JSON shapes and consistent `error: {code, message, details?}`. Restrict every resource to authenticated user’s organization. The Sample Demo can be its own seeded immutable account/organization, or copied data to a temporary local workspace; in either case, don't let one demo visitor modify another visitor's shared state.

### 7.2 Sample demo dataset

Seed one fictitious e-commerce SME (`Sample Store KZ`), 1–2 **fictional** assets and 5–7 labeled, synthetic findings across high/medium/low levels. Sample data must be generated locally and marked in the UI, JSON and PDF. Include one already-completed task to show progress; retain a straightforward path for tester to update another task. Avoid using someone else's real domain as a scan target. Provide a reset command to recover deterministic demo state before defense. Demo reports must say **“Illustrative sample data, not a live security assessment.”**

## 8. Key non-functional requirements

- **Launch:** `docker compose up --build` and a documented local address; `.env.example` contains no real secrets. Run migrations/seed with repeatable commands.
- **Responsiveness:** dashboard usable from laptop and mobile; no horizontal overflow in primary tasks.
- **Speed:** local UI should feel responsive; live checks have strict timeouts, background status and no indefinite spinner. No fictional SLA claims.
- **Reliability:** failed individual checks should not crash entire scan; errors are visible and persisted.
- **Accessibility:** labels, keyboard focus, alt/aria where appropriate, adequate contrast; severity always represented with text + icon, not color alone.
- **Security:** least-privilege container, safe input validation, no hardcoded secrets, read-only checks.
- **Maintainability:** typed schemas, modular checkers, small rule engine, meaningful test fixtures, explicit errors, no mock values on live API paths.
- **Observability:** structured log of scan/task lifecycle (without secrets); `/health` endpoint.

## 9. Tests and definition of done

### Backend automated tests
1. DNS TXT ownership proof: valid, invalid, expired, mismatch.
2. Domain validation/SSRF controls: IP literals, localhost, private/link-local/metadata, DNS rebinding, redirect to other host, timeout.
3. Checkers via mocked DNS/TLS/HTTP: pass/fail/error/not_applicable; valid and expired cert; missing DMARC; absent headers.
4. Prioritization: correct order and deterministic score; info severity not harmful; duplicate finding across repeated scan not duplicated.
5. Findings lifecycle: error does NOT resolve previous finding; actual pass closes/marks no longer observed.
6. Remediation tasks: create/update/read persists; completed task does not silently indicate technical remediation verified.
7. Access isolation: users cannot fetch another organization’s scans/findings/tasks/PDF.
8. PDF: generates nonempty, valid PDF and contains org name, scope, timestamp and demo marker when applicable.
9. Authentication: session creation, invalid credentials, logout; sensible validation and safe errors.

### Frontend automated and manual tests
- Login/demo entry; dashboard load; empty/loading/error states.
- Assets page validation and verification instructions.
- Scan progress and completion; meaningful error on unavailable host.
- Findings filtering, details, top priority.
- Task change persists after refresh.
- Actual PDF download.
- Mobile viewport, accessibility keyboard focus.

### Mandatory live acceptance demonstration
**Case A — deterministic sample:** open Sample Demo → overview → show highest risk and explanation → mark task in progress → reload and confirm persistence → export correctly labeled PDF.  
**Case B — verified real domain:** create workspace → add a domain owned by team → place DNS TXT token → verify → run bounded DNS/TLS/HTTP check → show results, including errors if applicable.  
**Case C — safety:** unverified or private/loopback target cannot be scanned; app shows reason.  
**Case D — integrity:** show that demo source and real live data have different labels and are not conflated.

**Definition of Done:** no dead-end buttons in mandatory workflow; no fake live metrics; project can be started from clean clone with README; tests documented and passing; all major screens usable; screenshot evidence available; no unsafe network probing.

## 10. Assignment 5 testing and evidence plan

### Alpha (internal team / people close to team)
Run at least 3 structured test sessions (team can be testers), documenting date, build/commit, scenario, tester code, pass/fail and discovered problems. Repair major issues and show before/after or changelog evidence. Alpha tests focus on technical correctness and workflow breakage.

### Beta (real target audience)
Recruit at least **5 people from the relevant audience**, preferably owners, operations managers, or SME IT generalists. At least some should not be teammates or people merely acting as customers. The earlier eight interview respondents may be invited, but those earlier interviews are **not a substitute** for hands-on Assignment 5 prototype testing. Use sample data by default. Get voluntary permission for anonymous research notes.

Give each participant a fixed short scenario:
1. Open the product/sample company.
2. Find the highest-priority risk and explain in their own words why it matters.
3. Find a recommended next action and change its task status.
4. Find/export the owner report; rate clarity 1–5.

Record `tester_code`, `role_segment`, `date`, `build_id`, `task_1_success`, `task_1_seconds`, `task_2_success`, `task_3_success`, `clarity_rating_1_to_5`, `notes`; do not store their sensitive company data. Measure 120 seconds for the primary hypothesis. Do not fabricate responses. Calculate raw `n/N` and %, preserving individual anonymized responses and evidence.

**Evidence appendix materials:** screenshots (3–6 actual prototype screens in report), test script, anonymized CSV/table of beta results, dated interview/testing notes, alpha issue/fix log, build/commit identifier, screenshot of generated PDF, contribution table, AI tool disclosure (e.g. Codex used for coding assistance, ChatGPT used for drafting/specification, subject to accuracy). Keep personal data out.

**Success analysis:** with N=5, at least 4 users must independently succeed in the main task within 120 s to reach 80%; report failures candidly. The result measures usability/task comprehension, **not** a statistically validated reduction in cybersecurity incidents or confirmed willingness to pay.

## 11. Assignment 5 alignment

| Assignment section | What prototype/team can supply |
|---|---|
| 1 Introduction | Problem, target users and risk-to-action value from A1–A4. |
| 2 Literature Review | Team separately cites at least 2 academic sources + 1 course lecture; do not invent citations. |
| 3 User's Path Map | Discover → Onboard/verify → First scan → Understand priority → Fix/track → Return/report (6 stages). |
| 4 Feature Prioritization | MoSCoW table of 19 features above (at least 8 required). |
| 5 MVP Scope | Must features + hypothesis and numeric success criterion above. |
| 6 MVP Management | Functional prototype versus landing page/Wizard-of-Oz alternative; Kanban/iterative delivery versus sequential waterfall; document decisions and roles. |
| 7 Alpha/Beta | Run actual sessions and retain primary evidence; report measurements as actually observed. |
| 8 Conclusion | Decide whether criterion met based on beta, not assumptions. |
| 9 References | APA 7 handled by report team. |
| 10 Appendix | Actual testing evidence, contributions and AI disclosure. |
| Part B | 3–6 real screenshots and explicit feature-implementation comparison. |
| Part C | ≤10 PDF slides, live product demo and individual Q&A. |

### Proposed development and responsibility split

The original assignments name **Muratbay Bekzat, Aisagaliev Islam, Taubayeva Aina**. This is a **proposed** split for Assignment 5, not evidence that these tasks have already been agreed:
- **Aisagaliev Islam:** technical lead and actual prototype implementation; architecture, scanning safety, backend/frontend integration, demo and automated tests.
- **Muratbay Bekzat:** user journey, feature prioritization, alpha plan, beta recruitment and analysis, business findings.
- **Taubayeva Aina:** usability materials and participant instructions, beta evidence/feedback organization, report formatting, slides and documentation.
- All three: alpha walkthrough, presentation, defense, honest AI disclosure.

## 12. Delivery sequence for Codex

See `PHASES.md` for the **authoritative, detailed phase-by-phase roadmap and acceptance gates**. The phases are 00 Foundation, 01 Brand/Marketing, 02 Auth/Organization, 03 Verified Assets, 04 Safe Security Checks, 05 Findings/Prioritization, 06 Dashboard/Tasks, 07 PDF/Demo/Localization, 08 Deployment/Hardening, and 09 Alpha/Beta/Evidence. Complete and verify one phase at a time; never start the next unrequested phase. The initial execution prompt is in `PROMPTS/PHASE_00.md`.

Project-wide engineering and brand standards live in `AGENTS.md`; apply them along with this specification.

## 14. Explicit exclusions and truthful claims

The prototype **can** demonstrate checks for DNS email records, HTTPS/certificate issues, simple HTTP-header hardening, prioritization, task management and PDF reports on a verified domain. It **cannot honestly claim** to find all CVEs, assess internal networks, monitor endpoints, prevent phishing or guarantee an organization is secure. The team must distinguish proposed `₸50,000/month` pricing from a paid verified subscription and distinguish previous customer-discovery interviews from new hands-on beta tests.

**Final deliverable package:** source repository; working local deployment; README and env sample; automated-test results; demo scenario; genuine screenshots; anonymized alpha/beta evidence and implementation notes that team can use in their 1500–2000 word PDF report and ≤10-slide defense.
