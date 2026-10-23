# ShieldMate SME — Phase 03: Authorized Assets & DNS TXT Ownership Verification

## Execution mandate

You are the senior full-stack engineer, application-security engineer, and product designer maintaining **the existing ShieldMate SME repository**. Your task is to **implement Phase 03 fully**, not merely propose architecture. Do not start Phase 04 or implement the security scanner.

**Current handoff reported by Codex:** Phase 02 is complete on local `main`, commit `b1b9b36`. The existing application has a React/TypeScript frontend, FastAPI backend, SQLite/SQLAlchemy/Alembic, Docker Compose, real registration/login/logout, Argon2id password hashing, database-backed opaque sessions, HttpOnly cookies, session-bound CSRF defense, a single-owner organization workspace, and the burgundy/red design system. Codex reported **32 passing frontend tests and 25 passing backend tests**, plus build, type checks, audits, migrations and Docker persistence. **Treat these as a handoff report, not as a substitute for inspecting the real repository and rerunning checks.**

### Non-negotiable sequence

1. Read `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, `docs/design-system.md`, `docs/phase-02-results.md`, and the relevant source/migrations/tests. Review the three files under `docs/design-references/` only when a design decision requires them.
2. Check the current branch, working tree and existing architecture. Never overwrite unrelated work. If there are uncommitted user changes, inspect/preserve them.
3. Run the relevant Phase 02 baseline tests/build before modifying code. Record the actual commands/outcomes.
4. Briefly describe your chosen data model, challenge lifecycle, authorization boundaries and UI approach. Then implement Phase 03.
5. Run comprehensive verification, fix regressions you caused, document limitations, and give an evidence-based completion report.
6. Do **not** push, deploy, procure services, run security scans, or proceed to Phase 04 without explicit approval.

## 1. Product objective and exact scope

ShieldMate is a **risk-to-action** product for Kazakhstan SMEs. Its future workflow is: authenticate → create an organization → add a company-controlled domain → prove domain control → run limited external checks → receive prioritized actions. **This phase delivers only the asset-onboarding and verification segment.**

At the end of Phase 03, a signed-in organization owner can:

- Open a real **Assets / Domains** page inside the existing private `/app` workspace.
- See a true, empty-state domain list for their own organization.
- Add a strictly validated public DNS domain name (not a URL, IP or arbitrary host/network target).
- Explicitly acknowledge that they control the domain or have authorization to request the limited tests specified by ShieldMate.
- Receive a unique, copyable DNS TXT record name/value with sensible DNS-provider instructions.
- Publish that record in their DNS provider independently of ShieldMate.
- Click **Verify ownership** and have the backend check the TXT record using actual DNS resolution.
- See **Verified** only when the expected fresh challenge is truly present at the exact name; see meaningful pending, expired, and inconclusive states otherwise.
- Regenerate an expired or compromised challenge, with prior challenges invalidated.
- Remove an asset through a deliberate confirmation flow; all data stay organization-scoped.
- Reload the page and see the same durable database-backed state.

**No imaginary verification successes or fake scan results. No active TLS/HTTPS probes, port scans, vulnerability checks, CVE lookups, phishing campaigns, findings, report generation, paid billing, or automated scheduled monitoring in Phase 03.** No backend endpoint may initiate Phase 04 checks, even when a domain is verified. Any existing planned Scan button must remain disabled with accurate explanation.

## 2. Domain validation: strict and centralized

Implement a **single backend domain canonicalization and validation function**, with separate frontend validation only for usability.

Requirements:

- Input accepts a domain/FQDN only, for example `example.com` or `shop.example.com` (examples in documentation, **never auto-scan or test real third-party domains**).
- Reject `https://example.com`, `http://`, usernames, `@`, query strings, fragments, `/`, backslashes, custom ports, trailing path components, wildcard forms (`*.example.com`), IP literals (IPv4 and IPv6), IP-looking numeric edge cases, whitespace/control characters, embedded NUL, labels with underscores in the **user-supplied domain**, and malformed encodings.
- Reject `localhost`, `.localhost`, `.local`, `.internal`, `test`, obvious special-use/internal namespace cases and public-suffix-only names such as `com`/`co.uk`. Use a reliable Public Suffix List-aware approach where needed, with pinned dependency/data and tests; do not approximate `co.uk` as a normal registrable domain. Preserve ability to use an explicitly authorized full subdomain as its own asset.
- Normalize case and an optional final DNS root dot consistently, apply rigorous IDNA encoding/validation, store canonical ASCII/Punycode form, enforce DNS label <=63 octets and full domain <=253 octets, and prevent duplicate representations. If Unicode support cannot be made correct and secure in the current stack, explicitly reject it and document the narrower scope rather than handling it incorrectly.
- Add database uniqueness for **(organization_id, canonical_fqdn)**. Independently verified organizations may have the same public domain recorded; do not leak their existence to one another.
- Limit the number of live domain records per organization to a configurable small academic-MVP quota (default **5**). Give an honest user-facing quota error; do not build billing.
- Invalid domain submission must never trigger DNS, TCP or HTTP calls, and domain creation itself must not perform an external probe.
- Avoid trusting a `user_id`, `organization_id`, `verified`, `status`, `verified_at`, `verification_token` or similar client-supplied authority field. Organization identity must come solely from the authenticated server-side session.

### Important distinction: DNS control vs security-scan authorization

A DNS TXT proof demonstrates ability to configure DNS at a specific name at a specific time; it does **not** by itself guarantee legal authorization to assess every web server, SaaS host, CDN or IP address the domain resolves to. Require a clearly worded explicit authorization/acceptable-use acknowledgement as part of asset enrollment and store the acceptance timestamp and policy/version. The later scanning phase must still apply its strict safe-target and scope constraints; Phase 03 must not claim that arbitrary infrastructure is authorized based on a DNS proof.

## 3. Ownership challenge design and lifecycle

Implement short-lived, high-entropy DNS TXT challenges. Suggested defaults are **48-hour challenge validity** and **30-day verification freshness** (configurable and covered in tests). Make precise documented choices and keep them consistent in UI/API/tests.

### Challenge format

For a submitted canonical domain `<fqdn>`:

- Record type: `TXT`
- Exact record hostname: `_shieldmate-challenge.<fqdn>`
- TXT value: `shieldmate-verification=<cryptographically-random-token>`
- Generate at least **256 bits of randomness** using `secrets` / a cryptographically secure library. Token must be unguessable and unique per new challenge.
- Prefer to provide the full hostname and the relative name for provider convenience; explain that DNS providers differ in how they append the zone automatically. Never suggest changing an existing SPF or DMARC record.
- TXT is public by design; it is a **domain-control challenge, not an application login credential**. Protect it from exposure across tenants and avoid unnecessary log output. It must never grant API privileges by itself.
- Challenges must be bound to the organization, asset, canonical domain and generation/issuance time. A challenge for one domain or org may never verify another.
- Support returning the **current active challenge to the owner after page reload**. Public TXT tokens do not require password-style hashing; a guarded, owner-scoped stored token is acceptable. Alternatively, use a secure reversible/deterministic design if justified. Do not build fragile one-time-only UI instructions.

### Lifecycle requirements

1. Creation: asset created as `pending`, unique active challenge issued, `verified_at = null`. Never mark verified simply because the user checked an authorization box.
2. Verification attempt: server resolves the exact TXT hostname; accept only an **exact complete match** to the expected value for the currently active, unexpired challenge. Multiple TXT answers are allowed; never accept substring matches. Handle legitimate DNS TXT chunk concatenation properly.
3. Success: persist `verified_at`, `last_verification_checked_at` and appropriate proof metadata/status server-side, then return state the UI can render.
4. Failure: do not mark verified on wrong token, absent record (`NXDOMAIN`/`NoAnswer`), timeout, resolver failure, malformed answers, or expired token. Distinguish **not found** from **temporarily unable to check**. Avoid disclosing low-level server details.
5. Expiry: expired challenges cannot be accepted even when their record remains in DNS. Offer a regeneration action. A successful verification has its **own freshness lifecycle**; do not collapse “challenge expired” into “previous verification automatically invalidated” unless that behavior is explicitly chosen and documented.
6. Regenerate: create a completely new token, invalidate the old challenge, increment a generation/version and ensure a delayed in-flight verification using an older generation cannot mark the current challenge verified. If regenerating from verified state, document whether it deliberately revokes verification and ensure the UI mirrors the resulting state.
7. Reverification: provide an explicit pathway for stale verified assets to return to pending/reverify; Phase 04 should require a still-fresh verification and explicit authorization before scanning. Do not silently extend trust forever.
8. Deletion: revoke ability to verify or eventually scan the deleted asset; a concurrent pending verification must not resurrect it.
9. Store and display UTC timestamps in a human-readable localized UI. Keep challenge expiration and verification freshness separate.

### DNS lookup limits and safe failure

- Only query `TXT` at the **server-derived** `_shieldmate-challenge.<validated_fqdn>` hostname; no client-supplied DNS server, arbitrary record name, URL, redirect target, IP address or port.
- Use a well-maintained DNS resolver library already in the repo where suitable, or add **one justified dependency** with pinned/locked version.
- Set a strict DNS lookup timeout/lifetime (e.g. 3–5s), bounded attempt behavior and no request-triggered unbounded retries. Distinguish temporary DNS failures from absent records.
- Never use untrusted TXT content in raw HTML, arbitrary shell commands, insecure dynamic evaluation, or logs containing sensitive account data.
- Apply abuse protection to challenge creation/regeneration and verification checks. Account/org limits must accompany per-IP limits where appropriate; note that Phase 02's in-memory limiter is single-process and is **not** distributed production throttling.
- DNS lookup can resolve attacker-managed zones; ensure it cannot be used as an arbitrary DNS query proxy beyond the exact approved challenge-name pattern. No outbound TCP/HTTPS from Phase 03 verification.
- Avoid using real external DNS/network in CI tests. Use deterministic injected/mocked resolver implementations, while offering an optional clearly controlled manual verification against a domain the operator actually owns.

## 4. Data model and migration

Extend the **existing** SQLAlchemy/Alembic models, don't restructure completed Phase 02 user/session/organization tables. Use a new Alembic revision after `6b5520d9fa5d` (confirm actual head in repo).

Suggested `domains`/`DomainAsset` fields; adjust field naming to existing repo conventions:

- `id`: stable identifier (UUID/other existing safe convention)
- `organization_id`: FK, non-null, indexed
- `canonical_fqdn`: normalized ASCII domain, required
- `created_at`, `updated_at`: UTC
- `authorization_attested_at`, `authorization_policy_version`: evidence of deliberate enrollment authorization
- `verification_status`: well-defined enum/state, e.g. `pending`, `verified`, `expired` (document each transition)
- `challenge_token`: owner-scoped, non-authenticating public DNS proof (or an equivalent securely reproducible design)
- `challenge_generation`: increasing version/nonce to reject stale attempts
- `challenge_issued_at`, `challenge_expires_at`: UTC
- `last_verification_checked_at`, `verified_at`: nullable UTC
- `verification_valid_until`: nullable UTC, or compute it reliably from verified timestamp with configured duration
- `last_verification_error_code`: sanitized limited code, optional

Database invariants: unique org+domain, indexed org key, NOT NULL as appropriate, nonnegative generations, and sane delete behavior. Don't add fake `last_scan` timestamps or `security_score` columns populated with invented values. If the app uses a generic Organization model, wire the asset relationship correctly.

Test upgrade of an existing Phase 02 DB **without losing user/session/org data**, upgrade of a new DB, and schema drift checks. Consider SQLite migration limitations when choosing constraints. Avoid writing fake migration data; actual existing user/org records should remain usable.

## 5. API contract: authenticated, CSRF-safe, owner-scoped

Prefer the API prefix and response/error conventions already used by the repository. The product specification suggests these resource paths:

```text
GET    /api/v1/domains
POST   /api/v1/domains
GET    /api/v1/domains/{domain_id}
DELETE /api/v1/domains/{domain_id}
POST   /api/v1/domains/{domain_id}/verification/request
POST   /api/v1/domains/{domain_id}/verification/check
```

Use a clean, consistent JSON response schema rather than following the exact names blindly if the existing repository uses equivalent naming; document any contract difference. Never let a supplied organization ID override the authenticated one.

**POST domain:** accepts only `fqdn` and an explicit authorization acknowledgement (and any narrowly necessary policy/version metadata). Server validates/canonicalizes, checks quota/uniqueness, creates pending domain and challenge in one transaction. Errors use correct semantics (e.g., 400/422 malformed, 409 own duplicate, 429 throttle/quota if modeled that way). There is no domain checking or HTTP probing triggered by mere creation.

**GET list/detail:** returns only the current organization's assets with canonical name, verification state, user-readable timestamps, current challenge instructions where appropriate, and actual persisted information. For someone else's asset ID, use a consistent 404/non-enumerating result; a missing organization should use the established onboarding behavior. Never leak raw internal DNS resolver output to unrelated users.

**POST verification/request:** deliberate reissue/rotation action; authenticated, CSRF-protected, limited; rejects unauthorized or deleted assets; handle in-flight attempts atomically.

**POST verification/check:** performs precisely one bounded DNS TXT validation attempt, returns `verified`, `pending/not_found`, `challenge_expired`, or `temporarily_unavailable` with stable machine-readable codes and helpful safe messages. Use 2xx for legitimate “record not found yet” workflow as appropriate, and reserve 5xx for unexpected backend failures. The response should not claim success unless the database state reflects a valid current-generation proof.

**DELETE:** requires authorization and CSRF, confirmation in the UI, and safe handling of concurrent verification and future scan associations (no scan records exist yet). Support safe not-found semantics. Do not expose a multi-tenant bulk-delete endpoint.

Use the **existing session/CSRF/origin/CORS layers**; test cookie semantics through the real HTTP stack. Validate all path IDs. All state changes must be checked server-side, including direct hand-crafted API requests. Add sensible request size validation and response no-store/caching policy for private tenant data.

## 6. Frontend routes, behavior and art direction

Preserve the Phase 01/02 design exactly as a coherent product identity: **deep burgundy + vivid RED**, warm ivory contrast, oversized Anton only for expressive headings, IBM Plex Sans for dense UI. Do not drift into pink, navy/blue, glassmorphism, template-like gradient cards or generic stock illustrations. No unnecessary design overhaul.

Implement / complete the private Assets page within the established `/app` navigation (prefer existing route, typically `/app/assets`):

**Asset overview**
- A real list/table connected to the authenticated API, never hard-coded sample organizations or verified badges.
- Columns/cards as appropriate: domain, status, first-added date, verification freshness/expiry, action. Show counts derived from server data, not fictional live risk metrics.
- Filters or search only if trivial and functional. Treat a zero-domain organization as an intentional guided empty state.
- Show clear ‘Security scanning arrives in Phase 04’ notice; do not enable a Scan button.

**Add domain flow**
- An accessible, focused form with label/example and inline server validation, loading/error/success states.
- An unchecked-by-default, explicit authorization checkbox with readable language (e.g., “I control this domain or have written permission to request ShieldMate’s limited external checks.”). Do not claim the checkbox proves legal ownership.
- Never accept or silently trim a pasted full URL into a domain. Reject and explain the correct domain-only format.
- On success, take the user directly to clear DNS TXT instructions.

**DNS TXT instructions/detail**
- Exact TXT type, full hostname, intended value, creation timestamp, expiration, typical propagation caveat (no invented propagation-time guarantee), copy buttons with appropriate feedback, separate relative-host tip.
- A single primary **Verify ownership** action, with robust pending state and a clear result message. Warn when the record is missing without implying an outage or a security breach.
- Expired/rotated token is clearly identified; “Generate new challenge” is explicitly separate from “Verify”.
- For successful verification show the precise ‘verified at’ timestamp and distinguish “domain control verified” from “infrastructure is secure”.
- For operational failures show retry guidance, not raw exception messages.
- Accessible delete confirmation that states the irreversible scope; use existing dialog primitives where practical.

**UX requirements**
- Browser refresh maintains state; handle unauthorized/expired sessions and failed requests consistently.
- Keyboard navigation and visible focus, proper aria labels and live announcements, no keyboard trap, clear status text in addition to color. Honor prefers-reduced-motion.
- Mobile 360px / tablet 768px / desktop 1280px / large 1920px without broken code blocks or copyable DNS values causing horizontal overflow. Full record strings must be copyable even on narrow screens.
- Ensure no enabled dead navigation, fabricated tooltips, fake checks or undisclosed mock results.
- Preserve landing, public preview, login, onboarding, settings, 404, and UI kit with no regression.
- Explain limited MVP scope in product copy: **“ShieldMate Starter performs limited external configuration checks. It does not guarantee security or detect all vulnerabilities.”** If checks aren't built yet, say so accurately.

## 7. Security adversarial scenarios and test plan

Add meaningful tests with **isolated test database and mocked DNS resolution** (not tests that depend on public resolvers). At least the following scenarios must be covered:

### Backend validation / ownership / persistence
1. Valid canonical ASCII FQDN; mixed-case normalizes identically; trailing dot handled consistently; valid authorized subdomain accepted.
2. Invalid: URL, IP v4/v6, localhost, `.local`, special-use, public-suffix-only, wildcard, path, port, userinfo, underscore, invalid DNS length, injected newline/control characters, empty or oversized input, and malformed IDNA.
3. Duplicate domain in same org rejected; independent orgs may add same domain without learning about each other.
4. Organization membership and ownership derive only from current session; malicious `organization_id` and `verified=true` fields cannot bypass authorization.
5. Missing authorization acknowledgment rejected; consent timestamp/version persisted correctly.
6. Asset quota enforced server-side; malformed requests never emit DNS queries.
7. DB migration of actual Phase 02 tables + preexisting sessions; clean migration; reload persists assets/challenges.

### Challenge and DNS correctness
8. Challenge contains secure random token; expected hostname/value are correct and persisted/retrievable by the owner.
9. Correct exact TXT record marks verified; incorrect TXT value, wrong hostname or substring containing token do not.
10. Multiple TXT records and multi-string TXT chunks handled without false positives; DNS values never used as markup.
11. Missing/NXDOMAIN/NoAnswer returns pending/not found; timeout/SERVFAIL returns temporary error; no false verified state.
12. Challenge expiry is enforced against mocked clock without sleeps; an old published token cannot verify newly regenerated challenge.
13. Regeneration issues a different token and invalidates prior generation; stale in-flight verification cannot verify after rotation, deletion or expiration (test race/compare-and-set where feasible).
14. Verified state/freshness survives reload and backend restart; stale verified asset becomes ineligible for future scan authorization.
15. Deleting a domain removes visibility and future eligibility; records are not revived by an in-flight verification.
16. DNS lookup uses only exact derived TXT names with strict timeout and no arbitrary type/hostname/user-supplied resolver.

### Authentication, cross-tenant isolation and abuse
17. Unauthenticated access: 401; organization A cannot GET/POST/verify/regenerate/DELETE organization B's asset by guessed ID; consistent 404/denied semantics.
18. Missing/invalid session, CSRF token or Origin on modifying endpoints are rejected. Only authorized owner sessions can reveal active challenge details.
19. Domain create/verification/reissue limits tested; expected enforcement under single process is explicit and honest.
20. API never includes passwords, session cookie contents, private stacks, secrets or unrelated-org asset data.

### UI / full path
21. New account → organization → add authorized domain → see copyable TXT challenge → refresh → challenge persists → mocked/sandbox-owned TXT successful verification → list/detail shows actual verified status → delete with confirmation.
22. User-visible missing DNS, temporary DNS error, expired challenge, duplicate domain, quota exceeded, failed session and failed CSRF are handled without blank screens.
23. Asset URLs, nav, page states and copy button work on 360/768/1280/1920. Check contrast, keyboard navigation, overflow and screen-reader names via available tools.
24. Re-run all Phase 02 auth/isolation tests and Phase 01 landing/preview/browser tests; the backend health endpoint and Docker startup persist.
25. No active security-scan endpoint is operational and no external HTTPS/TCP probe is emitted in Phase 03.

Tests should mock the resolver at a seam, not patch random library internals across files. Tests must assert real DB/API state changes and not only mocked frontend rendering. Use UTC fake clock injection where practical. Be explicit about any test not executed.

## 8. Quality gates, operations and documentation

Run, at minimum (adapt based on actual repo scripts):

```bash
npm test --prefix frontend
npm run lint --prefix frontend
npm run format:check --prefix frontend
npm run typecheck --prefix frontend
npm run build --prefix frontend
# In backend venv / container:
pytest -q
ruff check .
ruff format --check .
mypy app
# Also:
python -m alembic upgrade head
# Actual DB migration / schema drift check using repo convention
npm audit --audit-level=low
pip-audit
docker compose config --quiet
docker compose up --build --wait
git diff --check
```

- Use actual existing virtualenv paths and migration commands; do not report a command as executed if you couldn't run it.
- Verify that a **backend container restart** preserves domain and challenge state, without committed DB artifacts.
- For real DNS verification, if a team-controlled domain is unavailable, mark public-DNS E2E as **NOT TESTED** and document manual instructions; all automated DNS tests must be mock-based. Never “prove” verification by creating fictitious records against a random external domain.
- Update `.env.example` with necessary resolver timeout, challenge TTL, verification freshness and quotas; include secure values, no secrets. Note limitations of single-process throttling and DNS records remaining publicly visible after verification.
- Update README with exact domain-only syntax, challenge-record creation steps, common DNS-hostname duplication pitfall, how to retry, ownership-vs-authorization limitation, tests and restart instructions.
- Add `docs/phase-03-results.md`: architecture, data model and Alembic revision, API request/response/error examples, exact challenge state machine, concurrency safeguards, security boundaries, screenshots / commands, limitations and Phase 04 handoff.
- Preserve or extend existing docs rather than replacing them wholesale.
- Do not use fake operational statistics or screenshots that aren't from an actual running build. If test-only records are shown, label the environment and data correctly.
- No external deployment, Git push, app-secret publication, DNS-provider modifications on the user's behalf, new cloud accounts or paid purchases. Local commit is allowed if repository convention and working tree permit; report hash/status.

## 9. Hard acceptance criteria — all must be addressed

Report Phase 03 as complete **only if** these gates actually pass; else clearly report partial completion and the specific blockers:

- [ ] Existing Phase 02 authentication and org isolation are preserved.
- [ ] Domain input is strictly normalized/validated, and dangerous/non-domain inputs are rejected.
- [ ] Tenant-scoped persistent domain CRUD works, including after restart.
- [ ] Enrollment authorization acknowledgement is required and recorded.
- [ ] Per-domain unique strong DNS TXT challenge is generated, displayed and retrievable.
- [ ] Verification uses real backend DNS TXT resolution (with controlled mock seam for tests).
- [ ] Only exact, fresh, current-generation matches mark an asset verified.
- [ ] Failures, timeouts, expiry, reissue, concurrency and deletion cannot create false verification.
- [ ] All endpoints enforce session, org ownership, CSRF/origin checks and sensible abuse limits.
- [ ] Unverified or stale assets are **not** scan-eligible; no actual scanner exists yet.
- [ ] Mobile/desktop verification UX, copy states and error messages are usable and accessible.
- [ ] Migrations, tests, frontend build, Docker restart and dependency audits are actually run and results recorded.
- [ ] Documentation reflects reality, including manual DNS setup and untested external-provider behavior.
- [ ] Phase 04 has NOT been started, nothing was pushed, and no public scanning/deployment occurred.

## 10. Required handoff response — precise and auditable

Use this exact structure:

```text
Phase: 03 — Authorized Assets & DNS TXT Verification
Branch / initial and final commit:
Baseline checks before changes:
Design and security decisions (short):
Data schema and migration revision:
Implemented frontend pages / flows:
Implemented API routes (method + path):
Verification mechanics (record format, issuance, expiry, reissue, freshness):
Files changed:
Not implemented (Phase 04+):
Commands executed and ACTUAL results (with counts):
Security tests (tenant isolation, CSRF, DNS negative cases, expiry, rotation, races):
Screenshots / browser checks at 360 / 768 / 1280 / 1920 (if actually run):
Acceptance gates: PASS / FAIL / NOT TESTED per item:
Open issues and manual DNS/provider setup:
How to start locally and demonstrate the ownership flow:
Git status / commit, no push or deploy:
Next phase: 04 — NOT STARTED
```

**Do the actual engineering work now. Preserve the existing product, respect the original BURGUNDY + RED visual identity, build a genuinely secure and testable asset verification flow, and stop at the end of Phase 03.**
