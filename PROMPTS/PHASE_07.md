# SHIELDMATE SME — CODEX IMPLEMENTATION BRIEF
## PHASE 07 — PDF Reporting, Honest Demo Experience & English/Russian Localization

**Baseline:** Phase 06 completed on `main` at local commit `a3713dd` (as reported by the preceding Codex session). 286 backend tests, 64 frontend tests, the Docker stack, migration checks, responsive browser checks, and all 16 Phase 06 acceptance gates were reported passing. These results are a starting claim to verify against the real repository, not permission to skip regression tests.

**Scope:** Implement Phase 07 completely; do **not** start Phase 08 deployment or Phase 09 user testing. No pushes, public deployments, or destructive repository changes without explicit user approval.

---

## 0. Role, Product Context and Non-negotiable Working Principles

Act as a senior full-stack engineer, application-security reviewer, product designer, and rigorous QA engineer working on an actual B2B cybersecurity SaaS product. This is an implementation task, **not** a request for a proposal or a mockup.

ShieldMate SME targets digitally dependent Kazakhstan small/medium businesses (roughly 10–100 employees) lacking a full security team. It is a focused risk-to-action service, not an enterprise SOC, SIEM, EDR, penetration-testing platform, or comprehensive security certification. Previous phases implemented authentication and organization isolation, domain enrollment and DNS TXT proof, restricted external configuration checks, evidence-backed findings and Top 3 priorities, and durable remediation tasks.

The purpose of Phase 07 is to let a real owner or IT generalist understand and export a truthful account of their organization's **limited external-security posture**, and to let instructors/early testers examine a clearly labeled **synthetic demonstration** without requiring ownership of a real domain.

Use the existing React/TypeScript frontend, FastAPI backend, SQLAlchemy/Alembic persistence, Docker stack, authentication/session/CSRF protections, scanner and finding services, and design system. Inspect actual implementation rather than assuming file names or exact API contracts. Reuse stable services and shared UI primitives. Preserve all Phase 00–06 functionality and data.

**Brand:** bold, editorial, premium, professionally restrained when handling dense information. The palette is **BURGUNDY AND RED**, emphatically **not burgundy-and-pink** and not the generic blue/purple/neon cybersecurity palette. Existing design reference screenshots guide *visual language only*, not literal layouts or content. Use the existing condensed display typeface and readable body text, without installing a random font for decoration. No glassmorphism, bloated rounded-card grids, decorative emoji, fake marketing stats, meaningless animations, or templated AI copy.

**Code:** strongly typed, modular, testable, readable, dependency-conscious, documented only where non-obvious. Do not rewrite working modules simply to make them stylistically uniform. Every enabled control must function. No mock security data displayed as real data. Follow `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, `docs/design-system.md`, the scanner documentation, and the previous completion reports. If an existing instruction is inconsistent with this explicitly approved Phase 07 scope, describe the conflict and use the narrower, safer interpretation. Do not silently discard acceptance criteria.

## 1. Required Preflight and Phase Boundary

1. Verify repository path, branch, clean/dirty state, and current HEAD. **Never discard uncommitted work.** Verify the expected Phase 06 baseline or report any discrepancy before modifying files.
2. Read the existing backend models, findings and Top 3 logic, scans/observations, task lifecycle, tenant guards, auth/CSRF implementation, frontend routing, design tokens, i18n (if any), tests, Docker, migrations, and operational docs.
3. Run a reasonably complete baseline: frontend/backend tests, lint/typecheck, migration status, and production build. Record existing warnings and failing checks distinctly from new regressions.
4. Write a short 3–5 sentence architecture/design concept and concise implementation sequence, **then implement it in the same session**. Do not stop at a plan unless a genuine blocker prevents safe execution.
5. Preserve historical migrations; add only additive migrations if the chosen reporting persistence requires them.
6. Do **not** implement phishing campaigns, billing/subscription processing, email campaigns, external SaaS connectors, SOC features, MFA, production deployment, or real beta-test results in this phase.

## 2. Primary User Journeys

**Real account:**

1. Owner signs in and selects their existing organization.
2. Opens **Reports** from protected application navigation.
3. Sees an honest organization-level assessment summary based on saved, real records (verified assets, scans, observation coverage, findings, tasks, timestamps and completeness).
4. Understands which domains were checked, which were not, how fresh the evidence is, and which risks/actions deserve attention.
5. Generates a **server-produced PDF** and downloads it.
6. Opens the persistent report history, downloads the same immutable artifact later, refreshes and sees the same document rather than a silently recalculated one.
7. Sees actionable empty/error/incomplete states if no verified assets or qualifying scans exist.

**Public/isolated demo:**

1. Visitor opens a clearly designated demo route (prefer `/demo`; preserve `/preview` and existing protected `/app` behavior).
2. Sees a guided **Sample Company** journey using fixed, synthetic security data: assets → assessment observations → findings/priorities → example remediation tasks → sample report.
3. All demo views prominently and persistently say **SAMPLE DATA / DEMO — NOT A LIVE ASSESSMENT** (translated into Russian when selected).
4. Can download a **sample PDF marked DEMO** if that feature is provided; its contents must come from exactly the same synthetic dataset and rendering pipeline.
5. No demo interaction can enroll/verify real domains, enqueue scans, mutate production/customer records, read other tenants, or produce a misleading green “secure” certification.

**Localization:**

Users can switch between clear English and natural Russian labels/instructions across Phase 07's public, auth, core app, reports and demo flows without breaking state or navigation.

## 3. Report Data Contract: Evidence Before Appearance

Create a centralized report aggregation/serialization layer that calls or reuses **existing authoritative business logic**. Do not re-implement Phase 05 prioritization or Phase 06 task-state interpretation inside a PDF component.

Minimum explicitly typed report snapshot should contain:

- Report identifier/version, organization identifier and display name, creation time (stored UTC), requested locale, report title and kind, and a prominent assessment scope notice.
- Report generation timestamp versus each underlying scan completion timestamp; deterministic as-of semantics.
- Counts of total enrolled domains, currently verified/freshly authorized domains, unverified/expired domains, domains with completed evidence, domains without usable evidence, and (where appropriate) scan outcomes. Define denominators and labels clearly.
- Each eligible domain and the relevant check coverage, including DNS/SPF/DMARC, TLS/certificate and HTTP/HTTPS/header categories **only if implemented and actually observed**. Do not imply port scanning, malware detection, application security, account auditing, internal network inspection, or any other unimplemented coverage.
- Finding counts grouped by existing severity and lifecycle states. Include open findings and the authoritative Top 3 priorities with explanations, supporting evidence references and last-observed times. Preserve uncertainty (inconclusive, not checked, failed, stale, incomplete).
- Real remediation-task status counts and concise action details, including any distinction between “a task marked done” and “technical issue verified resolved”.
- Source references or stable identifiers that let an authenticated user navigate from a displayed PDF finding to the appropriate real app view; links must not expose sensitive tokens or synthetic-looking proof claims.
- A plainly worded limitations paragraph: this is a limited automated **external configuration assessment**, not a full vulnerability assessment, compliance audit, warranty of safety, or penetration test.

**Critical truthfulness invariants:**

- No scan / failed scan / timed-out check / stale evidence ≠ clean or secure.
- Absence of findings in observed checks ≠ absence of vulnerabilities.
- Task completion ≠ evidence-confirmed finding resolution.
- An unverified domain is not in assessed coverage.
- A domain's historical verification is not silently treated as current proof after expiry or revocation.
- Existing risk grades/priorities remain owned by the Phase 05 service; do not invent CVSS scores, CVEs or “AI insights”.
- A chart or percentage can only use documented, non-zero and correct denominators. If data are unavailable, render “Insufficient data”, not `0%` or `100%`.
- Do not fabricate report period comparisons or changes since last month when historical data do not support them. Name the MVP report **Security Snapshot** rather than falsely promising a monthly longitudinal report.
- Date/time stored in UTC; presentation must consistently show locale/timezone explicitly. For Kazakhstan-facing examples, `Asia/Almaty` is a sensible display default if aligned with existing settings; never manipulate stored timestamps.

Document the snapshot schema and its interpretation, including which scan results qualify as current and how stale data are presented. Prefer to keep underlying data provenance machine-testable.

## 4. Server-Side PDF Generation and Persistence

Generate a **real, selectable-text, paginated PDF on the backend**; do not call browser Print, screenshot a webpage, embed a rasterized page, or ship a static sample as a user's real report.

- Prefer a stable lightweight Python PDF library suited to the existing image/container setup (e.g. ReportLab if it fits). Add and lock only necessary dependencies and record why. Do not introduce an entire browser rendering stack merely to create a few report pages unless the repo already uses it.
- Support English and Russian, including legible Cyrillic glyphs. Use a legitimately licensed embeddable Unicode font available to the project, bundle only the required font artifact if license permits, and preserve its notice. Do not silently fall back to missing-glyph squares.
- Use a polished, print-friendly visual design reflecting the burgundy/red brand with restrained red emphasis, good black/dark text contrast, readable table widths, clean margins and clear page numbers. The PDF is a business document, not a giant display-type poster. Avoid oversaturated full-bleed backgrounds and excessive toner use.
- Include: cover/title + organization and generated-at, executive summary with explicit coverage, scope/limitations, observed findings and Top 3, remediation/task summary, asset/check details, source/evidence timestamps and explanations, and an honest footer/disclaimer. Sections may contract or expand as the data dictates; avoid pointless blank pages.
- Handle long organization/domain names, punycode, long URL-safe evidence strings, wrapping, multi-page tables, Unicode, missing/null fields, zero-result cases, and long datasets without clipped text or collisions. Escape/encode all user-controlled strings and sanitize dangerous control/bidirectional characters as needed without corrupting legitimate names.
- The **report artifact must be immutable once created**, representing the snapshot at creation time. Generate its bytes from a consistent snapshot; write atomically and store metadata (owner org, creator, locale, timestamp, file size, sha256 checksum, creation status, maybe schema version). On partial failure, do not publish a broken/truncated PDF as successful.
- Store PDFs outside the frontend/static public tree. Downloads must pass server-side authentication **and organization authorization** every time. Never trust a path supplied by a client. Prefer opaque report IDs rather than filesystem paths. Prevent directory traversal, unsafe filenames, and IDOR.
- Add sensible per-org and per-user generation quotas and concurrency controls; bounded output size and maximum included records. Verify the chosen limits are documented and not surprising.
- Download headers: `Content-Type: application/pdf`, attachment `Content-Disposition` with a safe filename, `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store` where appropriate. Keep auth errors generic. Never expose PDFs or report metadata through an unauthenticated static route.
- Audit successful/failed generation and downloads without logging secrets, entire reports, session tokens, or sensitive content.
- Keep persistence/backup assumptions realistic for current SQLite + Docker. Verify saved reports survive container restart if history is advertised as durable; clearly explain how Docker volumes/storage map to report files.

Suggested routes **only after reconciling with existing conventions**:

- `GET /api/v1/reports/overview` — authoritative, org-scoped current summary and readiness/completeness.
- `GET /api/v1/reports` — authorized paginated report history.
- `POST /api/v1/reports` — CSRF-protected creation of an immutable PDF snapshot.
- `GET /api/v1/reports/{id}` — authorized report metadata.
- `GET /api/v1/reports/{id}/download` — authenticated PDF bytes.

Do not add endpoints solely to satisfy an arbitrary URL list if the existing API already provides an equivalent secure capability. Align naming and error envelopes with the repo. No public URL-based report fetching or client-supplied organization identifiers determining authority.

## 5. Report UI and UX

Add a real protected `/app/reports` route, discoverable through existing navigation, with:

- An evidence/coverage summary (not a fabricated posture certification or trust score).
- An explicit “What ShieldMate checks / does not check” note in plain language.
- A clear readiness state: no assets, unverified assets only, verified but never scanned, processing, incomplete/stale, current evidence, error.
- A primary **Generate PDF Snapshot** action only when the organization has enough real data to make a meaningful scoped report. If generating a no-data report is supported, explicitly label it “No assessment data” rather than misleading the user.
- Real loading/progress, outcome feedback, safe retry, report list with date/locale/status, authenticated downloads, empty/loading/error states, and keyboard-accessible controls.
- Consistency with dashboard/findings/task figures via the backend authoritative aggregators, not a second calculation in the frontend.
- Correct behavior after hard refresh, logout, two browser tabs, session expiry, revoked access, and report generation failure.
- Layout QA at **360, 768, 1280 and 1920px**, without horizontal overflow. Avoid wide tables that become unreadable on mobile; use purposeful stacked layouts and content hierarchy instead.

Preserve the established editorial burgundy/red brand: confident hierarchy and selective strong visual accents, but business figures and findings must remain legible. Do not redesign the public site or other app sections without need.

## 6. Isolated Public Demo: Honest, Cohesive, Useful

The current public `/preview` is a design preview, not a real assessment. Keep its purpose and route stable; build a distinct, clearly labeled sample story at `/demo` or integrate a clearly separate demo section without confusing `/preview` and `/app`.

Create a **single canonical, deterministic, typed synthetic dataset** with deliberately fictional organization/domains (use reserved example names such as `merchant.example`, never a real business domain), traceable example scans, check observations, findings, severity logic, Top 3, and task states. Synthetic records should be internally consistent: if a sample issue appears in Top 3 it must have matching evidence and task references; timestamps should be deterministic or clearly anchored to the demo scenario, not pretend to be from an actual live customer today.

Build a high-quality guided read-only exploration with a visible “SAMPLE DATA” banner on every demo content view. It should illustrate the entire product value proposition, not merely show a row of fictional cards: what was checked, what was found, why it matters, next action, and how an owner would read the report.

Security separation is mandatory:

- Prefer a standalone demo data module that cannot access production customer endpoints at all. Demo rendering and its API contract (if any) must not reuse logged-in account context or leak another organization's data.
- **No writes to live users, organizations, assets, scans, findings or tasks. No DNS/TLS/HTTP network scanning from the demo.** A public demo visitor must not be able to trigger outbound network probes or circumvent enrollment and DNS ownership checks.
- No seeded demo tenant disguised as a real customer; do not pollute real dashboards, analytics, reports or aggregate counts with demo fixtures.
- If the demo offers a PDF download, reuse the real report rendering component with the synthetic snapshot via a tightly isolated, rate-limited endpoint or a generated demo artifact; mark every page **DEMO / SAMPLE DATA / NOT A REAL SECURITY ASSESSMENT**. Do not grant public access to any real report ID as part of this.
- Keep the demo read-only; interactive navigation, expansions, filters and an optional client-local, obviously simulated walkthrough are acceptable, but never describe those interactions as backend persistence or live scanning.
- Allow users to clearly exit the demo and go to sign-up/login without accidentally transferring demo data into their account.

Ensure a skeptical examiner can tell within two seconds that sample data are sample data. Demo screenshots must be visibly labeled, and any documentation must distinguish **automated tests**, **synthetic demo**, and **live owned-domain assessment**.

## 7. English/Russian Localization (Functional, Not Cosmetic)

Implement an intentionally small, maintainable i18n layer consistent with the existing architecture. Use a mature lightweight library if it meaningfully reduces complexity; otherwise a typed local dictionary can be appropriate. Avoid an enormous framework solely to translate a modest MVP.

At minimum translate:

- Public landing navigation and core product proposition/CTA labels, login/register, logout, organization onboarding/settings, global navigation.
- Assets and domain verification instructions, scanning controls/states, findings labels, priority explanations *where template-generated*, dashboard/task workflow controls/statuses.
- New reports interface, download feedback, report PDF headings/disclaimers, demo labels and guided narrative.
- Core validation/error/empty/loading labels encountered during the primary assignment defense journey.

Requirements:

- Language toggle (`EN` / `RU`) is keyboard accessible, has correct `lang` semantics, retains the current route and relevant state, and visibly updates texts without a page breaking or requiring a new user account.
- Persist **only language preference** in browser storage where useful; never store sessions, tokens or security data there. Default to established product preference or browser preference with a deterministic fallback (English acceptable).
- Translate static and controlled template text, **not** user-entered company names, domain names, DNS records, raw scanner evidence or other immutable technical data.
- Use natural, concise Russian security terminology. No awkward literal translations, dummy bracket strings, or accidental mixing of English/Russian in critical instructions. Proper technical tokens (DNS, SPF, DMARC, TLS) remain recognizable.
- Locale-aware display of dates and numeric values, with unambiguous timezones. Preserve UTC storage and API semantics.
- Test localization fallback and missing-key detection. Long Russian labels should wrap cleanly without clipping at mobile widths.
- Avoid regressions to accessibility metadata, semantic headings, alt text, or screen-reader labels.

Do not expand scope into Kazakh or more languages without explicit permission.

## 8. Application Security and Data-Minimization Controls

Existing Phase 02–06 security rules still apply. Phase 07 introduces **sensitive downloadable artifacts** and a **public route**, so threat-model both carefully.

- Authenticate and authorize every report read/download on the backend, with tenant isolation independent of UI navigation. Explicitly test cross-account and guessed-ID access.
- CSRF and Origin checks for report generation or other state-changing operations; cookie/session expiration and logout invalidate access. No credential or signed access material in query strings.
- Prevent path traversal and symlink abuse in artifact retrieval; map opaque ID → server-authorized storage reference, not `?file=`.
- Bounded workloads and abuse controls: pagination, maximum pages/records/size, request rate limits and overlapping-generation guard. Do not let arbitrary user text or number fields cause memory/CPU exhaustion.
- No remote image/URL loading while rendering reports. The PDF generator must not fetch user-provided URLs, parse external HTML, run subprocesses with tainted strings, or invoke the scanner.
- Sanitize rich/untrusted text, neutralize template injection and unsafe markup; preserve regular Unicode text. Never leak server paths, stack traces, source code, secrets, session cookies, passwords, or unrelated organization information into PDFs.
- No publicly readable bucket/static path for customer reports. For public demo output use distinct clearly marked assets and routes.
- Maintain secure CSP/CORS/origin assumptions; do not weaken protections for easier previews. Avoid unsafe inline scripts and unnecessary third-party tracking.
- Ensure user logout while a file is being generated has well-defined access semantics and that late-generation completion cannot bypass ownership checks on download.
- Dependence audits should be rerun, with lockfiles updated only intentionally.

## 9. Automated Test Matrix (Must Actually Execute)

Extend—not replace—existing tests, and run appropriate subsets during implementation plus the full suite before the phase is declared complete.

**Backend unit/integration:**

- Report aggregation on no data, single/multi-domain, mixed verified/unverified, current/stale scans, partial/error scans, inconclusive checks, zero/high findings, resolved/reopened findings, and mixed task statuses.
- Stable Top 3 from shared Phase 05 service; evidence/priority provenance matches persisted observations. Task done does not imply technical resolution.
- Immutable snapshot: create, alter underlying findings/tasks, download old report and prove old artifact/checksum unchanged; generate new snapshot and verify it differs for grounded reasons.
- Valid PDF signature/readability/page count and text extraction. Check English and Cyrillic using a PDF text extractor, then render sample pages to images and inspect for missing glyphs/overlap/clipping.
- Tricky text: extremely long organization names, Punycode, punctuation, Cyrillic, encoded control characters, null/missing metadata, multi-page tables and input escaping.
- Tenant A cannot list/view/download tenant B's report by changing URL or ID; unauthenticated, expired or revoked sessions cannot access reports.
- CSRF/origin protections, report generation quotas, concurrency/duplicate submissions, storage path validation, download headers and file-size bounds.
- Atomic failure during write, restart durability, stale files, safe clean-up behavior (if cleanup exists), and migration upgrades from earlier database revisions.
- Demo endpoint (if used) has no tenant or scan access and cannot serve real PDF artifacts.

**Frontend/component/browser:**

- Reports page, multiple report states, generation, list, download, auth expiration and forbidden states; every enabled control works.
- Demo clear persistent labeling, guided narrative, read-only behavior and exit/sign-up route; no authenticated real-data fetches from demo.
- EN/RU switching and persistence, missing-key checks, form errors and long-text/mobile wrapping.
- All principal pages across 360/768/1280/1920px, keyboard/focus/reduced motion, axe accessibility, zero horizontal overflow, and screenshot review.
- Regression: existing enrollment, ownership verification, scans, findings, Top 3, dashboard, tasks, auth and registration flows remain operational.

**Tooling/runtime:**

Run `pytest`, `npm test`, Python lint/format/mypy, ESLint/TypeScript/format checks, frontend production build, migration upgrade/drift validation, Python/npm dependency audits, Docker build/health, container restart/storage durability, and browser QA scripts consistent with repository tooling. Do not invent PASS entries for environments not tested. Capture exact commands and counts.

**Manual owned-domain E2E:** No team-controlled domain was provided previously. It is still **NOT TESTED** until one is actually verified and scanned with the owner's permission. Do not treat injected DNS or QA fixtures as a real owned-domain E2E. Document precise steps to complete this later, with permission boundaries.

## 10. Documentation and Assignment 5 Evidence Preparation

Update concise, accurate docs:

- `docs/reports.md` (snapshot contract, source mapping, PDF content, technical limits, storage, security, how to reproduce).
- `docs/demo.md` (synthetic nature, fixture contract, navigation, how to validate no live scans/tenant access).
- `docs/localization.md` (language files, fallback, extending translations, Russian font requirements).
- `docs/phase-07-results.md` with commands/results, decisions, known gaps, migration(s), security tests, screenshots and 100% honest acceptance-gate statuses.
- README / user journey with routes, local startup, how to generate and download a real report, sample-demo URL, and environment controls. Keep any existing operational or security documentation accurate.

Capture labeled screenshot evidence suitable for eventually selecting **3–6 prototype screenshots** for Assignment 5. Suggested views: protected reports readiness, real or explicitly labeled QA report history, PDF sample first/content pages, and isolated demo. Do not claim beta-user feedback or numeric success metrics without actually conducting user tests in Phase 09. This phase should help prepare evidence, not falsify it.

No deployment work. No payment integration. No marketing claims of completed customer audits or real-world breach prevention.

## 11. Completion Gates — Report PASS / FAIL / NOT TESTED Individually

1. Existing repo baseline verified and Phase 00–06 behavior preserved.
2. Protected `/app/reports` connected to real, authorized persisted evidence.
3. Snapshot correctly identifies coverage, age, incomplete/missing data and limitations.
4. Top 3 and remediation-state semantics reuse authoritative services without fake scoring.
5. Actual backend-generated, paginated and machine-readable English PDF.
6. Actual readable Cyrillic and Russian PDF, with no missing glyphs or collisions.
7. Durable immutable report history and repeated authenticated download across restart.
8. No IDOR, report file traversal, unauthenticated customer PDF access, or sensitive artifacts exposed publicly.
9. Correct CSRF/Origin, bounded report generation and clean failures/quotas.
10. Protected reports page works in normal/empty/incomplete/error states with functional UI.
11. Public isolated guided demo with persistent SAMPLE DATA labels and **no real network probes or tenant leakage**.
12. If offered, sample PDF carries DEMO markings on **every page** and matches deterministic fixture data.
13. Working EN/RU toggle with coverage of primary user flow and accurate technical terminology.
14. Strong burgundy/red visual consistency; responsive at 360/768/1280/1920px and accessibility checks.
15. Full backend/frontend/security/tooling regression suites executed and passing, or honestly documented blockers.
16. Migrations, PDF storage and Docker restart persistence verified.
17. Updated readable implementation docs and screenshot/test evidence, explicitly distinguishing QA/demo/live.
18. No Phase 08/09 implementation, no push or external deployment; final local commit and clean Git status (unless existing unrelated changes must be preserved).

If a feature is genuinely blocked, mark its gate **FAIL or NOT TESTED** with evidence and corrective work. Never mark an unexecuted test PASS. Fix issues while still working within Phase 07.

## 12. Final Codex Response Contract

After implementation and verification, deliver the following in order:

1. **Status:** Phase 07 complete/incomplete; current branch, baseline and final commit; clean/dirty working tree.
2. **Technical summary:** key architecture and what real users can now do; report data provenance and immutability model.
3. **Implemented frontend routes and backend APIs**, matching actual code.
4. **PDF:** actual generation method, font/Cyrillic solution, storage and report example/preview locations, pages verified and limitations.
5. **Demo:** exact URL, synthetic source and guaranteed separation from real assessment, sample PDF behavior.
6. **Localization:** languages/routes covered, exceptions and fallback.
7. **Security review:** tenant/CSRF/file isolation, abuse/resource controls, known production concerns.
8. **Exact commands and real results:** backend/frontend test counts, lint/types, migration/drift, dependency audits, Docker/persistence, browser/axe/responsive checks, PDF text/render inspection.
9. **All 18 acceptance gates**, each PASS / FAIL / NOT TESTED with a one-line basis.
10. **Known limitations and manual actions**, including the outstanding real owned-domain E2E and actual screen-reader/non-Chromium/browser/device testing where not performed.
11. **How to run locally** and test both the real reports experience and the synthetic demo.
12. **Files changed / docs / screenshots / git status**. No marketing exaggeration, invented source data, or unsupported confidence claims.

**Final directive:** Implement the Phase 07 requirements now. Do not merely produce a plan. Do not weaken Phase 00–06 security. Do not start Phase 08, push to a remote, deploy publicly, or fabricate assignment testing results without explicit approval.
