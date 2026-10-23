# SHIELDMATE SME — CODEX IMPLEMENTATION BRIEF
## PHASE 04 — Authorized Security Scanning Engine

**Execution mode:** Implement this phase in the existing repository. Do not stop after a plan.  
**Scope:** Phase 04 only.  
**Previous baseline:** Phase 03 reportedly completed at local commit `f7f33b2`; verify the actual repository state rather than blindly trusting this statement.  
**Next phase:** Phase 05 — Risk Analysis & Prioritization (DO NOT START).

---

## 0. ROLE, SOURCE OF TRUTH, AND INITIAL INSPECTION

You are the senior full-stack engineer, application security engineer, and technical lead responsible for evolving ShieldMate SME into a defensible, working university MVP. Your output must be production-conscious, security-first, independently testable, and consistent with the existing codebase.

Before changing anything:

1. Read `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, `docs/design-system.md`, and relevant Phase 00–03 completion reports, where present.
2. Inspect the **actual** frontend/backend implementation, models, migrations, authentication/session/CSRF architecture, organization scoping, DNS TXT verification, and Docker configuration.
3. Run existing tests and core quality checks. Record the real baseline and any preexisting problems.
4. Identify and document any conflict between these instructions and the existing repository architecture. Preserve established behavior, schema, and design tokens; implement the safest coherent solution rather than introducing another redundant subsystem.
5. Begin with a brief written technical design (roughly 10–20 lines) explaining the scanner pipeline, safe outbound networking, persistence, concurrency, and failure handling. Then **implement** it.

If multiple reasonable implementation choices exist, choose one, briefly state the rationale, and proceed. Ask only if a truly blocking product/security decision cannot be resolved from the code or this brief.

## 1. PROJECT CONTEXT AND PHASE OUTCOME

**Product:** ShieldMate SME is a Kazakhstan-first cybersecurity SaaS for approximately 10–100-employee companies without a dedicated security team. Its differentiator is not replacing enterprise scanners/SOCs, but turning a small, reliable set of external-exposure signals into clear, prioritized business actions.

**Existing functionality (verify this is true):** React/TypeScript frontend, FastAPI backend, SQLite/Alembic persistence, Docker Compose, burgundy/red design system, secure authentication and organization tenancy, domain enrollment with consent, DNS TXT proof and freshness periods, organization-scoped domain CRUD.

**The goal of Phase 04:** An authenticated user who has an eligible, explicitly authorized, currently DNS-verified domain can start a **bounded, nonintrusive** security assessment, watch its honest status, and view real recorded observations and timestamps after completion. The results must survive reloads and backend restarts.

A demonstrable end-to-end journey:

1. Sign in and select/view the user's organization.
2. Open `/app/assets` and see verified vs. ineligible domains.
3. Start **Run security checks** on an eligible exact domain.
4. Receive a persistent scan ID and a queued/running state.
5. View actual DNS, TLS, HTTPS/HTTP and response-header observations as they finish.
6. Inspect each result's evidence, outcome, explanation, and observed timestamp.
7. Refresh or restart the server and still see the completed scan history.
8. Attempt the same workflow on an unverified, expired, rotated, deleted, or other tenant's domain and be refused server-side.

**This is NOT** a vulnerability exploitation tool, full attack-surface discovery engine, port scanner, CVE assessor, malware scanner, phishing platform, or enterprise SIEM. No intrusive scanning or externally hosted deployment in this phase.

## 2. NON-NEGOTIABLE SECURITY BOUNDARIES

### 2.1 Explicit authorization and ownership

- All checks require an authenticated user, their own organization, recorded explicit scan authorization, and a **current DNS TXT ownership proof** for the precise asset being checked. The proof's Phase 03 validity rules are authoritative.
- Verify authorization and proof freshness at **enqueue time** and **immediately before network execution**. Recheck any relevant state after acquiring the job. Fail closed after deletion, revocation, proof rotation, or expiry.
- Domain ownership proof does not authorize scanning arbitrary subdomains, resolved IPs, related domains, or redirect destinations. A verified `example.com` permits only the exact eligible hostname `example.com`, not `www.example.com` unless separately enrolled and verified.
- Never accept user-supplied URLs, schemes, IP literals, ports, custom DNS resolvers, paths, headers, callback URLs, or arbitrary probe parameters. Scan targets must be derived from a validated existing verified domain record, never directly from request JSON.
- Ensure all list/detail/start/status endpoints are scoped by authenticated organization. Do not trust client-supplied `organization_id` or `owner_id`. Test horizontal privilege escalation and IDOR for scan IDs as well as asset IDs.
- Preserve cookie-based session protection, existing CSRF checks and Origin policy on all mutation endpoints.

### 2.2 SSRF / network protection — CRITICAL

Treat verified domains as still attacker-controlled input: their DNS records may point to internal services or change over time.

- For every outbound HTTP/TLS connection, resolve the exact eligible hostname, classify **every** returned A/AAAA address, and permit connections only to globally routable public addresses. Reject private, loopback, link-local, multicast, reserved, unspecified, IPv4-mapped-private, unique-local, cloud metadata and any other non-public/special-use target. Fail closed if a mixed safe/unsafe answer set is returned.
- Guard against DNS rebinding / time-of-check-to-time-of-use attacks. The actual socket must connect to an already validated, pinned public IP. A naive `resolve -> check -> requests/httpx.get(hostname)` sequence is **not acceptable**, since the library could resolve the name again. Preserve correct hostname-based HTTP Host, TLS SNI, and certificate hostname verification while pinning the network destination.
- Restrict outbound application probes to TCP **80 and 443 only**. No user-selected ports, no port sweeping, banner grabbing on arbitrary protocols, shell commands, subprocess calls to nmap, exploitation or brute forcing.
- Disable automatic cross-host redirects. Prefer no automatic redirects at all. If implementing a small bounded redirect chain (maximum 2–3), enforce the **same exact verified hostname** at every hop, re-validate/pin each connection, reject non-HTTP(S), unsupported ports, credentials-in-URL and suspicious encoding, and detect loops. Record cross-host redirects as observations only; do not follow them.
- Apply hard DNS/connect/TLS/read/overall timeouts, bounded response-header/body sizes, bounded DNS record count and total evidence size, limited concurrent jobs, and explicit resource cleanup. Do not download pages, crawl links, submit forms, send credentials, inspect sensitive document content, or execute JavaScript. Prefer `HEAD /` with a narrowly controlled `GET /` fallback only when needed to obtain headers, using a strict read limit. No custom path or query strings.
- Do not pass environment-configured outbound proxies or untrusted proxy settings into probing code. A proxy path must not bypass destination validation. Use an identifiable `ShieldMate-SME-MVP/<version>` User-Agent and low-impact request behavior.
- Never print secrets, passwords, session cookies, raw authentication headers, DNS challenge values, or confidential response bodies in logs, scan evidence or reports. Avoid recording cookies/set-cookie header values.
- The scanner must fail **closed** on uncertain resolution, unsupported IDNA cases, timeout, TLS verification failure, DNS errors, and unexpected redirects. Show an accurate incomplete/error status, not a fabricated success or blanket security conclusion.
- Document the precise threat model and tests. If the current HTTP client cannot support safe destination pinning with hostname verification, implement a narrowly scoped safe transport with tests or explicitly leave the affected network probe unavailable and report the security blocker. **Do not silently ship SSRF-prone code to satisfy a checkbox.**

### 2.3 Abuse prevention

- Apply server-side per-user, per-organization and per-domain scan quotas with reasonable configurable defaults (e.g. no more than one active run per domain; at most a handful of new scans per organization per hour). Existing single-process rate limits may be reused only when their limitations are explicit.
- Enforce an upper bound on queued jobs, active workers, per-check concurrency, and accumulated stored evidence.
- Deduplicate concurrent requests atomically, not merely through a client-side disabled button.
- Persistent jobs must be recoverable or transitioned to a terminal interrupted/failed state after a worker crash or backend restart. Never leave `running` forever.
- Use explicit consent from Phase 03 for scans. A DNS ownership proof by itself is not an alternative to the recorded authorization declaration.

## 3. CHECK CATALOG — REAL, SMALL, HONEST

Implement a focused catalog of actual external configuration observations. Results should be structured and meaningful; do not imply comprehensive vulnerability coverage.

### 3.1 DNS / email domain posture

Read **only** the relevant DNS records for the exact domain and standard policy labels:

- Apex A/AAAA presence (observational context; IPs must not be automatically probed beyond allowed pinned connections).
- MX record presence (context only; absence can be normal for a domain not used for receiving mail).
- SPF: identify exact `v=spf1` TXT records at the domain apex; distinguish missing, one record, multiple records (invalid configuration), and inconclusive DNS retrieval. Avoid pretending that record existence proves correct or complete authorization.
- DMARC: inspect TXT at `_dmarc.<domain>`; identify presence and basic `v=DMARC1` / `p=none|quarantine|reject` policy when parseable; distinguish missing, malformed, and unknown. Do not invent deliverability or phishing-protection guarantees.
- DKIM must **not** be inferred from generic DNS because selectors are unknown; omit it unless a safe, explicit and separately agreed method exists (not needed in Phase 04).

DNS queries must have bounded timeouts and output limits. For malformed or ambiguous DNS results, return `inconclusive` with the reason.

### 3.2 TLS / HTTPS transport

For port 443 on the exact authorized hostname:

- Try a real TLS handshake with SNI, correct hostname validation and trusted certificate-chain verification, through the validated pinned-IP connection.
- Record handshake success/failure, certificate validity window when safely available, remaining days until expiration, certificate issuer/subject summary (sanitized and length-limited), and protocol version when available.
- Clearly distinguish **expired**, **hostname mismatch**, **untrusted/invalid chain**, **connection refused**, **timeout**, and **other TLS failure** where distinguishable. Do not equate all failures with a missing certificate.
- Do not fall back to insecure verification and then mark TLS as trusted. An optional diagnostic unverified handshake, if implemented, must be isolated, clearly untrusted, tightly scoped and never count as successful certificate validation.
- Do not claim that a single handshake proves absence of all TLS weaknesses or assesses every supported cipher/protocol.

### 3.3 HTTP and HTTPS configuration / response headers

For the root path `/` only, using bounded safe requests:

- Observe whether HTTPS responds and what status code it gives, without interpreting HTTP status alone as an overall website-security verdict.
- Optionally inspect HTTP port 80 **only** to establish whether it redirects to HTTPS. Do not follow a redirection to a different hostname, internal target or nonstandard port.
- Evaluate observed HTTPS response headers: `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and clickjacking controls (`X-Frame-Options` or `frame-ancestors` where appropriate).
- Represent checks as evidence-based observations: `present`, `missing`, `needs_review`, `inconclusive`, or `error` as appropriate; avoid inventing an exploitable CVE or claiming a header is universally mandatory.
- Be careful that header presence alone is not proof of a safe policy; perform simple explicitly documented checks only (e.g., `nosniff` value). Provide the observed safe non-sensitive value where useful, redacted/limited as needed.
- Some applications intentionally don't expose HTTP at port 80 or don't operate a website at all; avoid false overall failures for every absent service.

### 3.4 Results are observations, not invented findings

Separate **collected technical observations** from Phase 05 business-risk classification:

- Phase 04 may label a check result `pass`, `attention`, `informational`, `inconclusive`, or `error` using transparent, deterministic rules.
- Do **not** implement the final Security Score, severity/confidence formula, business impact prioritization, prioritized remediation plans, auto-generated tasks, or AI-based diagnosis. These belong to Phases 05–06.
- All results must include: a stable check identifier, asset reference, observed timestamp, factual summary, safe evidence (and its source), check outcome, explanation/limitation, and a check-engine version or ruleset identifier.
- Never label a finding as a confirmed vulnerability without sufficient evidence. Do not include fabricated CVEs, fake scan counts or made-up customer results.

## 4. ARCHITECTURE, EXECUTION, AND PERSISTENCE

Choose the smallest reliable implementation compatible with the current architecture.

**Recommended modular layout** (adapt names to existing structure):

- `scanner/policy.py`: scan authorization and public-IP/hostname/network guards.
- `scanner/dns_checks.py`: DNS policy observations.
- `scanner/tls_checks.py`: TLS certificate/transport checks.
- `scanner/http_checks.py`: low-impact HTTP/HTTPS observations via safe pinned transport.
- `scanner/runner.py`: sequencing, time budgets, partial-failure handling.
- `scanner/service.py`: enqueue/deduplicate/read/status and tenancy enforcement.
- `scanner/schemas.py`: stable response structures and parsing.
- `models` + Alembic migrations: durable scans and check results.

**Execution contract:**

- `POST /api/v1/domains/{id}/scans` creates or enqueues an authorized run and returns a durable ID; use `202 Accepted` if asynchronous.
- `GET /api/v1/domains/{id}/scans` returns the organization's history with pagination, newest first.
- `GET /api/v1/domains/{id}/scans/{scan_id}` returns status, limited observations and timestamps, strictly tenant scoped.
- Optionally provide a stable organization-wide scan-history route only if useful and appropriately tenant scoped; avoid unnecessary endpoints.
- Scan states: `queued`, `running`, `completed`, `partial`, `failed`, and optionally `cancelled`/`interrupted`. Specify allowed transitions and stable API semantics. Results from successful checks must survive failure of other checks.
- Record start/end timestamps, completed check counts, non-sensitive structured errors and progress. A scan with one failed DNS lookup must not erase successful TLS results.

**Durability:** Do not rely solely on FastAPI in-process `BackgroundTasks` or a process-global queue for work that users expect to survive restarts. Prefer a simple database-backed job table and a separately managed, bounded worker service under Docker Compose if this can be implemented without unnecessary dependencies; use short leases or equivalent restart recovery, and idempotent status updates.

**SQLite:** Keep current SQLite/Alembic unless a concrete limitation demands a change. Use transactions, indexed foreign keys, uniqueness/active-job constraints where possible, bounded query counts, and correct SQLite multi-process locking behavior. Implement a targeted new migration without rewriting Phase 02–03 history.

**Data minimization:** Store sanitized observations, not raw HTML bodies or arbitrary HTTP responses. Add retention guidance and bounded result/evidence lengths. Audit scan requests and outcomes without logging secrets.

**Versioned contracts:** Create explicit, typed API response models and frontend types. Keep check IDs stable; errors must be machine-readable and human-readable without exposing tracebacks.

## 5. FRONTEND PRODUCT EXPERIENCE

Preserve the bold **burgundy-and-red (NOT pink)** ShieldMate visual identity:

- Deep burgundy and confident crimson/red, with restrained warm-light neutrals only for legibility/contrast.
- Expressive condensed display headings where appropriate; normal readable text in dense operational areas.
- Follow existing design tokens, Anton/IBM Plex Sans or whatever was actually established in Phase 01, and existing shared components.
- No generic purple/blue cybersecurity dashboards, glassmorphism, excessive neon glows, meaningless stock imagery, fake graphs, gratuitous animations or cloned presentation layouts.

### Required user experience

1. **Assets page:** For a verified eligible asset, enable `Run security checks`. For unverified, expired, rotating or removed assets, show a disabled control with a specific explanation.
2. **Scan progress:** Clear queued/running/completed/partial/failed states; show time and truthful progress without invented percentages. Poll sparingly and stop on terminal state. Handle navigation/reload gracefully.
3. **Scan details:** Display DNS, TLS and HTTP sections with factual values, technical evidence snippets and concise understandable explanations. Clearly distinguish `Not checked`, `Failed to check`, `No issue observed for this check`, and `Needs attention`.
4. **Scan history:** Persistent chronological list with status, domain, timestamp and link to each details view. Empty-state wording should explain how to enroll and verify a domain.
5. **Eligibility/failure feedback:** Tell users why a scan did not run: unverified domain, stale proof, authorization missing, private DNS target, rate limit, already in progress, temporary network failure, etc., without disclosing secrets.
6. **Access and responsive design:** Restrict pages to authenticated users and their own organization; protect against data flashes. Verify at 360, 768, 1280 and 1920 px. Keyboard focus, screen-reader labels, reduced motion, contrast, error and loading states must remain sound.
7. **Honesty:** Show `No completed scans yet` until one exists. If a UI demo is needed, use a prominently labeled, logically isolated mock/fixture demonstration and never blend it into production tenant results.

Do not redesign the landing page or change the product's visual identity. Add only the UI components needed for Phase 04.

## 6. SECURITY, RELIABILITY, AND TEST MATRIX

Build comprehensive tests, not just happy-path checks. Include at minimum:

**Authorization / tenancy / CSRF**
- Unauthenticated access denied; CSRF/Origin protection on scan start.
- Owner A cannot start or read Owner B's asset scans by replacing asset ID, scan ID or organization ID.
- Unverified, expired, revoked/rotated, deleted or consent-revoked domain cannot be scanned.
- Confirm authorization is checked both before enqueue and immediately before execution, including races.

**Network SSRF / rebinding**
- Reject A/AAAA -> `127.0.0.1`, `10.0.0.1`, `192.168.1.1`, `172.16.0.1`, `169.254.169.254`, `::1`, `fc00::/7`, IPv4-mapped-private and other special-use addresses.
- Reject mixed public/private DNS results and no-address responses; no outbound TCP attempts after rejection.
- Simulate DNS answer change between validation and attempted connection; assert socket stays pinned to vetted address or attempt is refused.
- Block redirect to private IP, other host, `file:`, `ftp:`, URLs with credentials, and non-80/443 ports; no follow-up request escapes scope.
- Enforce DNS/transport timeouts, slow responses, oversized headers/bodies, redirects loops and overall job deadline.
- Assert no arbitrary user-provided URL or host can enter networking functions.

**Checks and evidence**
- DNS: missing/valid/multiple SPF, DMARC policy variants, NXDOMAIN, SERVFAIL, timeout, contradictory answers.
- TLS: valid cert, expired cert, hostname mismatch, invalid chain, connection failures, timeouts; ensure no false-positive trust verdict.
- HTTP: missing/present/incorrect headers, HEAD-to-GET fallback, HTTP->HTTPS behavior, cross-host redirects recorded but not followed.
- `partial` scan preserves successfully collected observations even when another check fails.
- Sanitize/redact and bound all persisted evidence; XSS-safe frontend rendering.

**Persistence / concurrency / UI**
- Double-click or concurrent API requests cannot enqueue duplicate active scans for one domain.
- Per-domain and per-org quotas enforced with real server-side behavior.
- Backend/worker restart recovers or closes interrupted jobs honestly; history and results remain.
- Alembic migrations upgrade existing accounts/domains/sessions without data loss and pass schema-drift checks.
- Browser E2E: unauthorized -> verified eligible asset -> start -> progress -> results -> reload -> history; plus error and blocked-asset cases.
- Responsive, accessibility, empty/loading/error states; no regressions to previous phases.

Use **mocked DNS and socket transports in CI** for deterministic negative cases, especially SSRF and TLS errors. If available, perform a bounded real-world smoke test **only** against a team-owned and freshly verified exact domain, with explicit authorization. If no such domain exists, explicitly mark LIVE E2E **NOT TESTED**. Never substitute public third-party targets just to tick a test box.

## 7. ENGINEERING QUALITY / SECURITY STANDARDS

Your code must look and behave as if written and maintained by careful human senior engineers, not a one-shot AI website generator.

- Small, cohesive modules with explicit dependencies; testable resolver, clock, transport and queue interfaces.
- Clear, nonduplicated naming and separation of networking, policy, database, API and presentation concerns.
- Use typed models, ORM/parameterized SQL, validated server-side inputs, safe string handling and contextual output escaping.
- No dead code, unfinished `TODO` pretending to be features, massive god files, questionable dependency bloat, or credentials in source/client bundles.
- Protect existing Argon2id auth, opaque session cookies, CSRF, production CSP, security headers, CORS and rate limits.
- Maintain a `.env.example` for new configurable timeouts, concurrency, scan quotas, outbound behavior and retention. No secret values committed.
- Pin/lock any new dependencies and justify them. Inspect dependency audits; document nonblocking warnings instead of hiding them.
- Use structured logs with correlation IDs where practical, redaction, no stack traces in client responses, and actionable server-side diagnostics.
- Maintain a single source of truth for run/check states and avoid mismatched string literals across backend/frontend.
- Preserve prior features, shared UI primitives, responsive behavior and Phase 00–03 test coverage.

## 8. DOCUMENTATION AND ASSIGNMENT 5 EVIDENCE

Update relevant README/docs with:

- Scanner architecture, data flow, worker startup/recovery and state transitions.
- Exactly what is checked, what is not checked, why results may be inconclusive and why this is not a full vulnerability assessment.
- Authorization/consent requirements, TXT ownership proof freshness, exact-host scope, DNS rebinding and SSRF safeguards, safe rate/resource limits.
- Reproducible local Docker startup, migration, manual walkthrough and test commands.
- A concise report at `docs/phase-04-results.md` with real changes, screenshots and measured results.
- Screenshots suitable for later Assignment 5 report appendix (3–6 will eventually be chosen); label any fixtures/QA simulations clearly. Never fabricate business-user interviews, beta results, customer numbers or scan results.
- Record which tests used injected transport fixtures versus a real team-controlled DNS/provider endpoint.

A simple sample/fixture tenant is acceptable **only** if isolated, clearly labeled `DEMO DATA`, never represented as a real customer or live assessment.

## 9. PHASE 04 ACCEPTANCE GATES (EACH MUST BE EXPLICITLY REPORTED)

Mark each `PASS`, `FAIL`, or `NOT TESTED`, with evidence:

1. Verified exact domain + consent + authenticated tenant required before and at execution.
2. Endpoints persist and return organization-scoped scan runs and observations.
3. Real DNS checks (SPF/DMARC plus context) work with bounded queries and clear limitations.
4. Real TLS certificate/hostname/expiration observations are correctly validated.
5. Real HTTP/HTTPS and security-header observations work without automatic out-of-scope requests.
6. Actual outbound connections cannot bypass validated public-IP destination pinning.
7. Private/special-use IPs, rebinding, redirects, dangerous ports, and arbitrary target input are blocked.
8. Quotas, concurrency, timeout budgets and job restart handling behave safely.
9. Partial failures are recorded honestly and do not destroy successful observations.
10. Frontend end-to-end scan flow, states, history and details function correctly.
11. No fabricated customers, scans, risk scores, CVEs or vulnerability claims.
12. Existing Phase 00–03 behavior and design remain intact.
13. Migrations, all relevant tests, lint/type/format/build, dependency audits, Docker and browser checks succeed.
14. Documentation, screenshots, manual configuration and open limitations are complete.
15. Phase 05+ functionality is not implemented; no push and no public deployment.

## 10. REQUIRED FINAL RESPONSE FROM CODEX

When implementation is complete, provide:

1. **Short engineering summary:** what was implemented and why the design is safe.
2. **Exact endpoints and schema/migration changes.**
3. **Actual check catalog:** each check, output meanings, and known detection limitations.
4. **Network protection analysis:** how public-only DNS resolution, IP pinning, TLS hostname validation, redirects and SSRF defense work in actual code, not just abstract claims.
5. **Persistence and worker lifecycle:** queue semantics, throttling, crash recovery, concurrency boundaries.
6. **Files changed**, grouped by purpose.
7. **Verification table:** exact commands and pass/fail counts; distinguish mocked CI tests from live end-to-end tests.
8. **UI screenshots / browser evidence** with 360/768/1280/1920 coverage when available.
9. **Phase 04 acceptance checklist** numbered 1–15 with PASS/FAIL/NOT TESTED.
10. **Outstanding risks and manual actions**, especially live owned-domain DNS verification and production deployment prerequisites.
11. **How to run locally** with Docker Compose and manually exercise a genuinely authorized scan.
12. **Git branch/status/commit hash.** Create a local commit for the completed phase only after tests pass, if this matches the repository's established workflow. Do not push.

**Do not declare full completion if the networking safety or ownership gates are not actually verified. Do not hide skipped checks.**

**Begin Phase 04 implementation now. Do not start Phase 05, do not push, and do not deploy without explicit approval.**
