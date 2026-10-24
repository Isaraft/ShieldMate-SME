# ShieldMate SME — Phase 08
## Security Hardening, Reliability, Local Release Candidate & Independent QA

**Execution baseline:** Phase 07.1, local commit `e2c58b6` on `main`.
**Scope constraint:** This is a LOCAL release-candidate phase. Do not purchase infrastructure, configure Cloudflare Tunnel, expose ports to the internet, push to a remote, or publicly deploy anything. Those actions require separate, explicit approval.

You are working as a senior application-security engineer, backend engineer, frontend engineer, QA lead, and product-minded technical reviewer. **Do not merely generate an audit report.** Inspect the current code, perform and document a risk-driven audit, fix in-scope issues, implement tests, verify the full application, and produce a reproducible local release candidate.

## 0. Mandatory preparation and guardrails

1. Confirm branch, current commit and working-tree status. Never overwrite unrelated or uncommitted work; if the tree is dirty, inspect it and preserve it.
2. Read `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, `docs/scanner.md`, the reports architecture, the security documentation, `docs/phase-07-results.md` and `docs/phase-07-1-results.md`. Inspect the relevant code and migration history, not only the documentation.
3. Run a baseline: frontend/backend tests, lint/type/format, production build, DB migrations and Docker health. Record real counts, failures, warnings and environment details.
4. Map the complete user flow: registration → company onboarding → explicit scan consent → domain enrollment → TXT verification → authorized scan → technical observations → evidence-backed findings → priorities → remediation tasks → reports/PDF → logout; plus separate synthetic demo, EN/RU/KK switching and unauthenticated access.
5. Preserve the existing burgundy-and-red editorial identity and the three languages (`en`, `ru`, `kk`). Treat user-facing Ukrainian or unexpected fallback strings as defects unless the product intentionally supports them. No rebrand, framework migration, backend rewrite, speculative new features, billing, MFA or external integrations.
6. Never invent test outcomes, security claims, vulnerabilities, CVEs, customer data, translations or browser results. Mark an unavailable test **NOT TESTED**, with its reason. Never create fake test passes.
7. Work incrementally. Prefer small, reviewable changes, clean code and narrow dependencies. Do not disable a security control just to make tests pass.

## 1. Threat model and prioritized risk register

Document the actual deployed-in-Docker, localhost-first architecture and its trust boundaries:

- Untrusted browser/client input vs FastAPI and application sessions.
- Account and tenant data vs other accounts and tenants.
- Public domain claims and owner consent vs DNS verification.
- The scan queue/worker vs the outside network and DNS/TLS/HTTP endpoints.
- Scanner observations vs the deterministic finding engine and dashboard.
- Report generation, stored PDF blobs, file downloads and localization resources.
- Public synthetic demo vs private live customer data.
- Docker images, mounts, environment secrets, SQLite files, migration and backups.

Build `docs/phase-08-risk-register.md` with each finding's severity, exploit preconditions, affected code paths, evidence, mitigation and verification. Clearly differentiate **confirmed defect**, **defense-in-depth improvement**, **environmental risk**, and **accepted local-MVP limitation**. Fix credible high/critical issues before considering the phase complete. Do not overstate the strength of controls based solely on passing unit tests or dependency audits.

## 2. Authentication, authorization and API hardening

Inspect and directly test:

- Password hashing, timing-safe comparisons, password limits, generic failure messages and registration/login abuse controls.
- Session token randomness, hashed-at-rest storage, expiration, revocation and cleanup. Re-test logout and restart persistence.
- Cookie flags for each environment: HttpOnly, Secure in HTTPS production, appropriate SameSite, path/domain restrictions; do not silently disable these in production. Explain localhost exceptions.
- Session-bound CSRF protection on *all* state-changing endpoints, including newly added report/domain/task actions; Origin/Host validation and safe behavior after CSRF rotation or concurrent tabs.
- Server-side authorization and BOLA/IDOR resistance on every account, organization, asset, scan, observation, finding, task, event, report, PDF download and indirect relationship.
- Invalid or stale object IDs, malformed JSON, excessive payload sizes, repeated login attempts, quotas, and enumeration attempts.
- Trusted Host validation, restrictive CORS, CSP and other relevant response headers; compatibility with the local production-like entrypoint.
- Session and organization transitions that might accidentally expose previous tenants' cached frontend data, including refresh, back navigation, language switching, tab changes and logout.

Repair issues and add negative tests that demonstrate the intended security properties. Preserve existing data and API contracts whenever practical.

## 3. Scanner isolation, DNS safety and authorization integrity

The scanner is the highest-risk module. Review the actual network calls, not merely user-input regexes. Verify:

- All DNS/TLS/HTTP probes require a fresh, authorized, currently verified exact domain and recorded permission; repeat authorization before execution, not only enqueue.
- Safe registrable-domain and public-suffix handling; IDNA/Punycode validation, wildcards, dot segments, trailing dots, IP literals and edge-case hostnames.
- Redirects remain disabled (or rigorously destination-validated if current code requires redirects), probes are bounded, protocol/port choices are fixed to the documented safe scope, and no arbitrary user-controlled URL or port reaches the transport layer.
- All resolved destinations are validated as globally routable/public before connection; excluded ranges include loopback, private, link-local, multicast, reserved and metadata destinations, including IPv4/IPv6 edge cases and mixed-family responses.
- Transport connects to the validated numeric destination while retaining correct Host header, SNI and certificate verification, preventing a re-resolution race.
- DNS rebinding, CNAMEs, truncation, timeouts, invalid answers, certificate problems, redirect attempts and DNS/TLS/HTTP partial failures lead to safe, honest states.
- Per-organization and global rate limits, cooldowns, concurrency and timeout bounds are effective under rapid repeat submissions and failures; enforce persisted quotas where previously implemented.
- Queue state, retries, worker restart and crash recovery do not cause duplicate uncontrolled traffic or silently treat failure as a clean scan.

Implement controlled tests with mocked/injected DNS and transport, plus a *strictly local owned test service* as appropriate. **Do not scan arbitrary public hosts or private networks as part of this phase.** Do not claim that code-level safeguards replace an eventual OS/container egress firewall. Document a future firewall requirement separately.

## 4. Evidence lifecycle, tasks, report integrity and safe rendering

Verify invariants end to end:

- Each finding refers to real, persisted observations from an authorized scan; never synthesize technical evidence or unsupported vulnerability names/CVEs.
- Missing, failed, partial, outdated or stale scans are never interpreted as a secure result.
- Duplicate observations and repeated scans do not create endless duplicate findings/tasks or skew the shared Top 3 ranking.
- Human task completion is separate from observed technical remediation. Reopen/resolve transitions are evidence-backed and have a consistent audit trail.
- Reports accurately scope covered assets, data timestamp/freshness, known limitations, task status and unresolved findings. Snapshots remain immutable after creation.
- Report rendering avoids injection via asset names, comments and user-controlled fields; all PDFs/downloads are owner-scoped. Verify content-type, filename, size and safe errors.
- Generated PDFs render correctly on A4, with professional readable typography, page headers/footers, repeated table headers, sensible orphan/widow handling and stable page numbering. Existing report bytes must not be retroactively rewritten.
- Public demo data and PDF pages are visibly marked `DEMO`/synthetic and can never leak or impersonate live tenant data.

For PDFs, render and visually inspect a representative short, long and edge-case report **in EN, RU and KK**. Create screenshots/page samples or a contact sheet. Test Cyrillic and Kazakh letters `Ә Ғ Қ Ң Ө Ұ Ү Һ І` and natural line wrapping. Treat a 25+ page report as an opportunity to assess whether the executive summary is concise; **do not remove required supporting evidence** or add arbitrary page-count ceilings.

## 5. Localization and cross-language visual QA

Perform a full UI audit on the *real rendered application*, including public landing, login/register, onboarding, assets, scans, findings, action plan, dashboard, reports and demo:

- All three languages have complete key coverage and no leaked raw keys or unintended English fallback.
- Refine unnatural technical Russian and Kazakh copy. Use proper cybersecurity terminology appropriate for Kazakhstani SME owners and IT administrators; preserve meaning, not literal word order. If native-speaker review is unavailable, note the limitation and supply a review checklist rather than claiming linguistic certification.
- Validate changing language without losing form input, access control, or visible state.
- Check headline word wrapping/overlap, step-number vertical centering, labels in buttons, nav overflow, error messages, filters, dialogs, long entity names, table columns and page headings.
- Recheck screen widths at 360, 390, 768, 1024, 1280, 1440 and 1920 pixels for `en`, `ru`, `kk`, both empty and populated views where practical.
- Check actual contrast, keyboard focus and semantics, reduced motion, zoom/text enlargement, tab sequence, visible action feedback and modal focus management.

Retain deliberate typography and hierarchy. Do not flatten the interface into generic rounded cards. Provide actual screenshots for visual issues fixed; passing axe alone is not visual validation.

## 6. Production-like LOCAL runtime and operability

Create or improve an optional, documented local release-candidate profile that **serves compiled frontend assets** and the FastAPI app through a suitable same-origin entrypoint, rather than exposing a development Vite server as if it were production. Prefer minimal changes compatible with the existing Docker architecture. Requirements:

- Bind externally facing development/release ports to `127.0.0.1` by default. No public tunnel and no public IP binding.
- Keep `/api` and frontend routing coherent, including reload, deep links, cookies, CSRF and the correct 404 behavior where supported.
- Use explicit environment configuration with `.env.example`, startup validation for production-like safety settings, and no hardcoded secrets.
- Minimize container privileges and accessible files, avoid unnecessary exposed ports and prevent debug-mode stack traces from reaching the user.
- Document database location and SQLite WAL handling, file/directory permissions and backup consistency.
- Implement a **safe backup and restore procedure**, preferably using SQLite's consistent online backup mechanism; do not merely copy a live WAL-mode DB blindly. Test restore into an isolated temporary environment, including old accounts, domains, scans, findings, tasks and report history. Do not overwrite the user's existing live DB.
- Document service start, stop, restart, migrations, log viewing, backup/restore, resetting disposable QA/demo data, and local health verification.
- Verify graceful behavior on failed migrations, missing env configuration, restart mid-scan, full/near-full storage when feasible, and report-renderer failure. Avoid broad operational rewrites that cannot be validated.

Important: **the objective is local release readiness, not proof of internet-exposure security**. Cloudflare Tunnel, VPS, DNS records, actual public origin, production trusted-proxy setup and external egress firewall remain future work.

## 7. Automated, integration and manual verification

Run and honestly report the existing project-specific commands for:

1. Frontend and backend unit/integration tests.
2. Lint, typecheck, formatting and optimized frontend build.
3. Alembic upgrade and drift tests; preserve every historical migration unchanged.
4. Dependency checks (`npm audit`, `pip-audit` or equivalents), plus repository secret scanning if available.
5. Docker image build, startup, health, restart and SQLite persistence.
6. Browser regression tests and newly added release-candidate E2E tests.
7. IDOR, session, CSRF/Origin, malicious-input, scanner-network and report/demo isolation tests.
8. EN/RU/KK report generation, extraction and real rendering/visual inspection.
9. Backup and restore into an isolated location with documented integrity checks.
10. A guided *manual local defense rehearsal* exercising the complete safe user flow; use explicitly labeled fixture/test DNS when real owned-domain proof is unavailable.

Do not create fake live-domain proof. If an authorized real domain is not available, mark `Live domain DNS TXT + external HTTPS scan E2E: NOT TESTED`, record how to perform it later and still test controlled internal paths.

## 8. Documentation and handoff artifacts

Produce these durable files, updating existing files rather than duplicating contradictory content:

- `docs/phase-08-results.md`: scope, baseline, changed files, risks fixed, actual commands/counts/results, regressions, limitations, acceptance gates and Git info.
- `docs/phase-08-risk-register.md`: ranked risks, evidence and mitigations.
- `docs/local-release-runbook.md`: exact commands and configuration for a localhost-only production-like run, failure recovery and tested backup/restore.
- `docs/defense-demo-runbook.md`: a clean 5–8 minute demo with an authentic product journey, safe alternate demo mode, where screenshots/PDF evidence are found, what is synthetic, and recovery steps if the network/DNS is unavailable.
- Representative visual QA evidence for EN/RU/KK at desktop/mobile and actual PDF render samples or contact sheets. Do not mistake a local filesystem hyperlink for an uploaded artifact.
- A concise list of manual blockers for future external exposure and beta testing, including actual owned-domain E2E and independent native-speaker review.

## 9. Acceptance gates — PASS / FAIL / NOT TESTED, with evidence

A01. Existing Phase 00–07.1 functionality and historical migrations preserved.
A02. Risk register and real threat-model review completed.
A03. Authentication, sessions, CSRF, origin and tenant boundary attacks re-tested.
A04. Domain proof and scan-eligibility boundary re-tested, including concurrency/expiry.
A05. Scanner transport prevents SSRF/rebinding under controlled adversarial cases.
A06. Findings, priority ranking and task lifecycle remain evidence-based and internally consistent.
A07. Report history, tenant-private PDF access and demo isolation are secure and truthful.
A08. EN/RU/KK keys and important flows are consistent and language switching preserves state.
A09. Actual visual inspections across required widths and languages, with recorded evidence.
A10. PDFs in all languages are rendered, checked for typography/glyphs, and professionally laid out.
A11. Production-like **localhost-only** runtime works without Vite dev server exposure.
A12. Reproducible, tested SQLite backup and isolated restore procedure exists.
A13. Full frontend/backend build, lint, typing, migration and dependency checks pass; unresolved issues documented.
A14. Docker startup, restart, persistence and error recovery checks pass.
A15. Clear local defense walkthrough and troubleshooting runbook prepared.
A16. No fabricated security data, no uncontrolled external scans, no push or public deployment.
A17. Real owned-domain and external-browser tests are labeled truthfully, not falsely passed.
A18. Clean or fully explained Git status; changes committed locally only after verification.

Do not mark a gate PASS based on assumption. For blocked requirements, mark FAIL or NOT TESTED with precise explanation and corrective next steps. Fix in-scope failures before signing off.

## 10. Final response format

Provide a concise but evidence-backed report covering:

1. Current branch, baseline commit, final local commit, Git status.
2. What was audited; most important security/reliability changes (or no changes, if evidence supports that).
3. Architecture/runtime changes and commands to start the local release profile.
4. Actual commands executed and exact test counts/results; do not estimate.
5. The 18 acceptance gates and honest exceptions.
6. Screenshots and rendered PDF evidence paths.
7. New runbook paths and backup/restore confirmation.
8. Remaining limitations and manual checks before any internet exposure.

**Do not implement Phase 09, push to GitHub, create a public tunnel, buy a domain, or deploy publicly. Implement Phase 08 locally now, rather than stopping after writing a plan.**
