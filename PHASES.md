# ShieldMate SME — Phased Implementation Roadmap

Source of truth: `SHIELDMATE_MVP_SPEC.md` for product behavior and safety, `AGENTS.md` for engineering/design rules, the three `docs/design-references/` screenshots for visual *style only*. This roadmap controls the order of execution.

**Definition of a finished phase:** implementation exists, functions promised for that phase demonstrably work, relevant automated tests pass, no known critical security regression, README is current, next phase is not started without approval. Status labels must reflect actual tests rather than assertions.

## Phase 00 — Foundation & Architecture

**Goal:** reproducible, clean repo with bootable frontend/backend and recognizable brand tokens, no fabricated business features.

**Do:** inspect repository; preserve existing work; document architecture; establish frontend React/TS/Vite/Tailwind and backend FastAPI/Pydantic/SQLAlchemy/Alembic + SQLite; add route/layout skeleton and design tokens (burgundy/red); add `/api/v1/health`; set environment config, Docker Compose (or explain blockers), lint/typecheck/test infrastructure; README, `.env.example`, `.gitignore` and initial smoke tests.

**Accept:** clean-clone documented start works; frontend shell renders; health endpoint responds; tests/build/lint actually run; unimplemented functions are not represented as operational; no external asset probing.

**Do not:** implement authentication, scans, task workflows, reports or an elaborate marketing page yet.

## Phase 01 — Brand Identity, Landing Page & Product UI Kit

**Goal:** impressive, professional, intentional burgundy-red product design without compromising app legibility.

**Do:** audit three provided visual references; define `docs/design-system.md` with design concept and typography; responsive landing page explaining value, target audience, steps and demo invitation (disabled/clearly labeled if not functional); navigation, footer, honest Starter feature descriptions, accessible CTA states, 404; reusable form/table/tag/dialog/feedback components; dashboard app-shell layout with no invented live metrics; mobile-first and reduced-motion. SEO essentials suitable for the selected stack.

**Accept:** intentional original composition across 360/768/1280/1920; no layout copied from slides; branding uses *burgundy + RED*, not pink or blue; no dead pretending-to-work CTA; keyboard flow and contrast checked; frontend tests/build pass.

**Do not:** fake client quotes/stats, simulate real scans, build auth business logic yet.

## Phase 02 — Authentication & Organization Workspace

**Goal:** secure accounts and isolated organization workspaces.

**Do:** user/organization models and migrations; signup/login/logout/me; password hashing and validation; secure cookie sessions + appropriate CSRF defense; protected routes; organization resolution derived from session, not untrusted frontend data; registration rate limiting; integration tests for sessions and cross-org isolation; clear local vs HTTPS production cookie config.

**Accept:** signup/login/logout works after reload; users cannot see or alter other org data; invalid credentials fail safely; tests pass.

**Do not:** prematurely implement subscriptions, complex multi-org RBAC or payments.

## Phase 03 — Authorized Assets & DNS TXT Ownership Verification

**Goal:** asset onboarding with verified authorization before any active network check.

**Do:** strict FQDN/IDNA validation; reject IP/URL/port/private/internal target forms; domain CRUD scoped to org; random short-lived DNS TXT proof of control; verify challenge from DNS; verification states; expiry and re-verification, audit; easy-to-copy instructions. Test spoofing, token mismatches, expiry and org isolation.

**Accept:** ownership is never marked verified without real TXT match; unverified assets cannot trigger scan; proper error/empty states and tests.

**Do not:** turn domain submission into arbitrary network scan or SSRF vector.

## Phase 04 — Safe External Security Checks

**Goal:** real, limited checks of confirmed public assets; structured stored evidence.

**Do:** safe DNS MX/SPF/DMARC observations; TLS handshake/certificate/expiry checks; bounded HTTPS/HSTS/security-header checks; explicit `pass/fail/error/not_applicable`; safe request limitations, validated public DNS/IP with rebinding protection/pinning; no automatic external redirects; strict timeouts and body limits; queued/running/completed/failed scan-run persistence and polling; tests with mocked network, no random external targets in CI.

**Accept:** a team-controlled verified domain can be checked; unverified/private target is rejected; errors are not shown as safety; results have evidence and timestamps; repeated scans don't corrupt data.

**Do not:** claim CVE detection, malware hunting, phishing resistance or full company risk coverage.

## Phase 05 — Finding Engine & Contextual Prioritization

**Goal:** technical results translate into explainable business decisions.

**Do:** deterministic rule IDs, lifecycle and deduplication; severity weights with written rationale; plain-language risk impact, affected asset, exact remediation and technical evidence; stable top-three priorities; optional clearly labeled **indicative** limited-check score; finding detail & filters; handle `error` and `not_applicable` correctly; repeated scan reopens/resolves findings only based on valid observations; robust tests.

**Accept:** same evidence creates stable priorities; informational missing MX is not misrepresented as confirmed flaw; no fake CVSS/AI severity; errors cannot auto-resolve findings.

## Phase 06 — Dashboard, Remediation Tasks & History

**Goal:** fully navigable, understandable risk-to-action loop.

**Do:** backend-connected dashboard metrics, top actions, assets/findings tables, evidence details; owner-label/status/note task CRUD; persistence after reload; user-driven completed task status distinct from verified technical remediation; Executive/Technical view if core stable; honest scan history; responsive empty/loading/error states and accessibility.

**Accept:** user can find highest risk, see why, take action, refresh without state loss; all live figures match persisted backend data; basic E2E walkthrough passes.

## Phase 07 — Real PDF Reports & Repeatable Sample Demo

**Goal:** credible presentation-ready MVP without relying on successful network access during defense.

**Do:** export valid management PDF from stored org findings/tasks; timestamp, scope, top risks, progress, limitations; sample fictitious e-commerce company with deterministic synthetic findings, separate isolated/demo workspace, clear visible DEMO marking in UI/API/PDF; reliable reset command; optionally critical RU/EN strings and report metadata. Add tests for PDF and demo separation.

**Accept:** PDF is downloadable/openable; changes to task status are reflected; sample data cannot be confused with real live scans; demo cannot leak or change other tenants.

## Phase 08 — Production Hardening & Public Deployment

**Goal:** reachable site, secure-by-default configuration and trustworthy live demo.

**Do:** hardening pass (auth, CSRF, CORS, security headers, SSRF, dependencies, logging, secrets); run backend/frontend tests and E2E; document deployment via chosen hosting with HTTPS, persistent storage and backups; production environment variables; monitoring/health; smoke test against owned environment; fix critical issues. Do not purchase domains or deploy before explicit user approval and credentials.

**Accept:** deployed URL actually tested, TLS functional, persistence verified, no leaked secrets, known limitations documented. If deployment is unavailable, report accurate remaining steps instead of claiming success.

## Phase 09 — Alpha, Beta Testing & Submission Evidence

**Goal:** genuine Assignment 5 results, not simulated user feedback.

**Do:** internal alpha sessions with timestamped bug/evidence log; recruit >=5 real target SME owner/manager/IT-generalist beta participants; present consistent task scenario; primary hypothesis is >=80% independently identify top risk and action within 120 seconds (4/5 if n=5); record anonymized role/date/build ID/task status/time/clarity/notes and consent; fix major issues; capture 3–6 actual screenshots; assist teammates preparing PDF report sections, prototype link and <=10 slide defense. Disclose AI tools and contributions.

**Accept:** traceable evidence, honest `n/N` outcome and observed times, no invented respondents, report clearly distinguishes hypothesis/results/demo vs production.

## Explicit phase handoff format

```text
Phase:
Files changed:
Implemented / not implemented:
Commands executed & actual results:
Security checks & regressions:
Acceptance criteria: PASS / FAIL / NOT TESTED
Local run instructions:
Manual actions required:
Next phase: NOT STARTED
```
