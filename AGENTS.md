> Publication-copy note: the five original reference images are retained only in the private original repository/backups and excluded from this history. Use `docs/design-system.md` and the existing UI for visual guidance. Historical reference-file mentions below describe the original supplied materials. See `docs/publication/sanitization-results.md`.

# ShieldMate SME — Repository-wide Engineering Instructions

You are a senior software engineer, security engineer and thoughtful product designer building a genuine university-stage MVP, not a fake demo or a generic AI-generated website. Read `SHIELDMATE_MVP_SPEC.md` and `PHASES.md` before changing code. `PROMPTS/PHASE_00.md` starts the execution sequence. Preserve this project identity through every phase. If an existing repository already contains working equivalents, inspect and reuse them rather than rebuilding unnecessarily.

## Product truth and priorities

- Product: ShieldMate SME Starter, a lightweight B2B cybersecurity **risk-to-action** web application for Kazakhstan-based SMEs of roughly 10–100 employees, especially small e-commerce firms without a dedicated cybersecurity team.
- Users: owners/operations managers (business explanation), IT generalists (reproducible technical evidence).
- Main verified-domain flow: register → organization → add domain → prove ownership by DNS TXT → trigger limited check → see recorded findings and priorities → update remediation task → export owner-ready PDF.
- The core value is **clarity and prioritized action**, not competing with Nessus, a SOC, SIEM or EDR.
- Ship Must-have features and real end-to-end functionality before speculative features. Phishing campaigns, integrations, subscriptions/payments, exploit scanners and AI chatbot are out of scope.
- Results and metrics must never be invented. Synthetic data may appear only in an isolated, conspicuously labeled **Sample Demo**, including PDF marking. Old customer interviews are not actual MVP beta tests.
- Proposed pricing, user claims, testimonials, customer counts and security impact may not be represented as achieved facts.

## Design art direction — Burgundy & RED, not pink and not blue

The three images in `docs/design-references/` are references for **visual identity only**: oversized condensed typography, dramatic hierarchy, editorial/controlled-brutalist art direction, assertive deep burgundy and red blocks, sharp graphic contrasts and asymmetry. **Do not copy slide layouts, content blocks, presenter names, tables or screenshots into UI.**

1. Identity: **deep burgundy + crimson/vivid RED** are the primary colors. Warm ivory/off-white supports readable contrast; pale tones must not make the site pink-led. No corporate blue, blue-teal cyber default, violet gradients, neon glows or glassmorphism.
2. Starting tokens (refine for WCAG AA and screenshots): `--burgundy-950: #321015`, `--burgundy-900: #570711`, `--red-700: #98121F`, `--red-500: #CF2431`, `--surface: #F7F0EA`, `--surface-raised: #FFF9F5`, `--stroke: #D9C7C3`. Define semantic success/warning/error separately; never rely on color alone.
3. Public marketing pages: expressive, oversized editorial headlines, considered asymmetry, purposeful typography and whitespace. The security dashboard: same brand DNA but compact, restrained, legible, task-oriented, with dense tables and evidence shown carefully.
4. Choose at most two intentional licensed/open typography families, e.g. Anton for display headlines and IBM Plex Sans for UI/body. Keep local/system fallbacks. Avoid default Inter/Roboto/Arial as the design choice. Never ship font binaries unnecessarily.
5. Avoid generic AI-site patterns: centered hero + two buttons + three identical cards; endless rounded shadow cards; emojis as icons; icons in color circles above every heading; stock-looking placeholder images; fabricated logos/testimonials; stock metrics; lorem ipsum; meaningless jargon like "revolutionary", "seamless" or "next-gen".
6. Mobile-first responsiveness at 360, 768, 1280 and 1920 CSS pixels. Use a consistent 4/8px spacing system, content-width controls and readable 60–75 character paragraph measures where practical. No horizontal overflow in key app flows.
7. Accessibility: semantic HTML, accessible labels, keyboard focus, accurate aria only where needed, text alongside risk colors, WCAG AA contrast, reduced motion support, keyboard accessible dialogs and navigation.
8. Interactions: meaningful hover/focus/active/disabled/loading/empty/error/success states, subtle 150–300 ms transitions only where useful, explicit feedback after actions. 404 and empty states should be intentional.
9. Use the screenshots for art direction, not exact palette extraction from a compressed source; document selected final tokens and typography in `docs/design-system.md` during Phase 01.

## Architecture and development standards

- Default stack unless an already-functional equivalent is present: React + TypeScript + Vite + Tailwind CSS frontend; FastAPI + Pydantic + SQLAlchemy + Alembic backend; SQLite for academic MVP; Docker Compose for reproducible local execution; pytest and Vitest/React Testing Library. Avoid introducing heavier systems without clear proof of need.
- Keep the code modular and named for responsibilities. Use typed request/response schemas, migration-managed relational storage, consistent error structures, and real resource/organization authorization checks. No duplicated logic, abandoned files or excessive abstractions.
- Use design tokens. Limit libraries to justified choices; create and commit appropriate lockfiles. Avoid fetching external assets at runtime where unnecessary.
- Do not treat mock UI state as a completed feature. During early phases, not-yet-available functions must be clearly disabled or marked **Coming in a later phase**. Never connect fake counters to the live dashboard.
- Include health endpoint, meaningful logging without secrets, concise README, safe `.env.example`, safe `.gitignore`, clear local startup and test commands.
- If marketing SPA does not offer full SSR, deliver reasonable meta/OG/sitemap/robots fundamentals and document the SSR/SEO limitation rather than claiming perfect SEO.
- Errors displayed to users must be meaningful but not leak stack traces, secrets, configuration or package versions.

## Security — non-negotiable

- Treat **all user input as untrusted**. Validate on server; HTML escaping by default; never inject user data through unsafe HTML rendering. Use ORM/parameterized SQL. Restrict input sizes.
- Authentication: Argon2id preferred (or properly configured bcrypt), safe sessions, HttpOnly cookies, SameSite, short expiration, CSRF defenses for cookie-authenticated modifying requests. Enforce `Secure` on production HTTPS; document local HTTP development settings separately. Never log passwords or token values.
- Authorization: each backend read/write must be filtered to the authenticated organization; test direct object-reference attacks. Do not treat a UI "Executive/Technical" view switch as a permission system.
- Configure environment-managed secrets, specific CORS allowlist, rate limits on sensitive actions, security headers/CSP, HTTPS/TLS in production, non-root containers where practical, minimal PII and safe logging. Keep dependency locks and scan vulnerabilities using available package-manager checks.
- For security checks, require explicit domain ownership verification (DNS TXT) before TLS/HTTP probing. Accept FQDN only: no IP literals, arbitrary URLs, userinfo, custom ports, localhost or private/internal/reserved destinations. DNS resolution and connection must be guarded against SSRF and rebinding; pin connections to vetted public IPs or disable live checks if safe pinning is unavailable. Do not blindly follow redirects or issue unbounded requests. Strict timeout, response-size and egress/concurrency constraints.
- Only bounded read-only external DNS, TLS certificate and HTTPS/header checks; no exploitation, port-sweeping, brute-force, phishing email sending or credential harvesting. Do not run scans against an unverified third-party domain even for a demo.
- Checker errors, inconclusive states and absent application components are not proof of vulnerability or security. A task marked completed does not automatically resolve a technical finding. Do not claim a site is "secure" based on these limited checks.
- If safety requirements cannot be met within the phase, disable that capability and accurately report the missing component; never silently weaken security constraints.

## Execution rules for Codex

1. Work on **only the requested phase**. State brief design/implementation decisions before changing code; do not launch into unrequested features.
2. Inspect repo, dependencies and project instructions first. Preserve user work and do not overwrite unrelated changes. Never git push or deploy externally without explicit request.
3. Prefer actual implementation over pseudocode, mock functionality or partial stubs disguised as shipping. Clearly note any deliberate placeholder.
4. Run applicable commands (install, build, lint, typecheck, tests). Fix regressions caused by your changes; never report unrun tests as passed.
5. After each phase, output: brief design concept/choices where relevant; file/change summary; actual commands and their outcomes; acceptance checklist marked Pass/Fail/Not tested; real blockers and manual setup; next-phase handoff. Do not print every source file unless explicitly requested.
6. Ask at most five essential questions only if truly blocked; otherwise make conservative reversible choices and document them. No fake deployment, user testing, legal certification or penetration-test claims.
7. No invented screenshots, fake user interviews, fake QA metrics or fabricated alpha/beta evidence.

These instructions supersede any older branding text prescribing navy/blue/teal or a pink-dominant palette.
