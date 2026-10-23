# ShieldMate SME — Phase 02: Authentication & Organization Workspace

## Role and execution mandate

You are acting as a senior full-stack engineer, application-security engineer, and design-conscious product developer. **Implement Phase 02 now** in the existing ShieldMate SME repository. Do not stop after generating a plan. Ship working, testable code and perform actual verification before declaring completion.

**Current verified handoff (as reported by the previous Codex run):** Phase 01 was completed on local `main` at commit `a2fca5d`. React/TypeScript UI, FastAPI health API, SQLite/Alembic, Docker Compose, design tokens, public landing, workspace preview, UI kit, and tests already exist. The previous run reported 22 passing frontend tests, 12 passing backend tests, clean build/lint/typecheck/dependency audits, browser checks at 360/768/1280/1920, and an accessible UI. **Independently inspect the current repository and re-run the actual baseline checks. Do not assume this report is proof of the current working tree.**

## 0. Read first; preserve existing work

Read and follow, in order:
1. `AGENTS.md` (permanent engineering and security rules).
2. `SHIELDMATE_MVP_SPEC.md` (authoritative product scope and safety boundaries).
3. `PHASES.md`, specifically Phase 02 and the future Phase 03–04 boundaries.
4. `docs/design-system.md` and the existing frontend design tokens/components.
5. `docs/phase-01-results.md`, if available.
6. The current frontend routes/components/tests, backend routes/models/migrations/config/tests, Compose files, lockfiles, `.env.example`, and README.

Report any material conflict between these instructions and the existing repository. Follow the safer/more restrictive constraint, and document the resolution. Do not overwrite unrelated changes, recreate the repository, discard migrations, replace existing architecture, or break the Phase 01 marketing site. Avoid adding large authentication frameworks when the existing stack can support a small secure implementation.

## 1. Product outcome / definition of done

Implement a **real user-account and organization-onboarding flow**, so a new ShieldMate user can:

1. Open the existing branded public site.
2. Choose a functional **Create account** call to action.
3. Register with a valid email address and password.
4. Log in using real backend authentication.
5. Create a company workspace (organization name; optionally one small useful field such as business sector).
6. Enter `/app` as an authenticated user with an active organization.
7. See their actual account and organization identity in the application shell and organization settings.
8. Refresh the browser and stay signed in until session expiry or logout.
9. Log out; lose access to private pages and authenticated API resources.
10. See correct loading, invalid-input, already-registered, unauthenticated, expired-session, and error states.

There is **no security scanning, domain onboarding, vulnerability data, or reports in this phase**. Dashboard cards and controls for later phases must remain clearly planned/disabled, with no fake operational data. Preserve the Phase 01 look and feel.

## 2. Scope and deliberate simplifications

### Must implement
- Real register/login/logout/current-user endpoints.
- Strong password hashing and safe password verification.
- Stateful, server-managed authenticated sessions, persistent across reloads.
- CSRF defense appropriate for cookie-based authentication.
- User and organization schema changes via Alembic migrations.
- Organization creation and retrieval/editing for the authenticated owner.
- Simple, secure organization ownership and server-side authorization.
- Protected frontend routes and auth-aware navigation.
- Functional, accessible login, registration, first-time organization setup, and basic organization settings UI.
- Real tests covering authentication, persistence, authorization, and security boundaries.
- README/config/documentation updates.

### Explicitly do **not** implement
- Domain verification, DNS queries, external HTTP/TLS requests, scanners or vulnerability findings.
- Invitations, team administration, granular RBAC, SSO/OAuth, MFA, email-verification delivery, password-reset email workflows, or a multi-organization switcher.
- Subscription billing, pricing checkout, phishing simulations, management PDF reports, analytics, or production deployment.
- Fake demo accounts with predictable shipped passwords, seeded claims about customers, or a simulated authentication state in localStorage.

For this MVP, a new account owns **one** organization workspace. Keep the schema clean enough to support future membership/roles, but **do not build complex multi-tenant RBAC prematurely**. Use a simple and consistently enforced user↔organization ownership model. If a small membership table is already required by the existing architecture, implement only the minimal safe owner relationship. Document what can be expanded in a future phase.

## 3. Backend data model and migrations

Inspect existing tables first. Evolve them with **non-destructive Alembic migrations**, following current SQLAlchemy conventions.

At minimum, the persisted schema needs:

**User**
- UUID or safe opaque primary key consistent with the project.
- Unique, normalized email address with server-side duplicate checks and database uniqueness.
- Password hash (never plaintext or reversible encryption).
- Creation timestamp and necessary status fields.
- Organization association/ownership defined unambiguously.

**Organization**
- Safe opaque identifier.
- Display name, normalized/validated and length-limited.
- Owner ID or equivalent minimal authorization relationship.
- Creation/update timestamps.
- No fictional security score, scan state, risk metrics, or subscription activity.

**Session** (if implementing the recommended database-backed opaque-session design)
- Session identifier stored as a **cryptographic hash** or similarly safe server-side representation; raw bearer secret appears only in the HttpOnly cookie.
- Associated user ID; expiry; revocation; creation timestamps; optional rotation/last-used metadata when justified.
- Indexed expiry and a documented cleanup strategy; no unsafe in-memory-only sessions.

Preferred session architecture: high-entropy opaque random tokens (at least 256 bits), server-side persistence, token hashing at rest, proper expiry, invalidation on logout, no access tokens or session secrets in localStorage, sessionStorage, browser-visible JS, URLs, logs, or response JSON.

Keep migrations deterministic and compatible with the SQLite database and Docker persistence from Phase 00. Confirm upgrade from the previous schema **and** initialization from a clean database. Do not delete user data or reset the database to make tests pass.

## 4. Authentication and API behavior

Preserve existing API versioning conventions; do not create a parallel incompatible routing system. Suggested logical contracts (adapt paths to actual project conventions and document final routes):

| Method | Logical endpoint | Behavior |
|---|---|---|
| POST | `/api/v1/auth/register` | Validate and create user; choose and document whether login is automatic |
| POST | `/api/v1/auth/login` | Validate credentials, rotate/create new session cookie |
| POST | `/api/v1/auth/logout` | Revoke current session and clear cookie |
| GET | `/api/v1/auth/me` | Return authenticated identity and current organization state, without secrets |
| GET | `/api/v1/auth/csrf` | Supply a CSRF value or equivalent mechanism where needed |
| POST | `/api/v1/organizations` | Create the current user's organization; reject unauthorized/duplicate attempts |
| GET | `/api/v1/organizations/current` | Return only the authenticated user's organization |
| PATCH | `/api/v1/organizations/current` | Update allowed organization fields with server-side authorization |

Do not create generic `GET /organizations/{id}` endpoints that expose unrelated tenant records just because an attacker guesses an ID. If legacy routes require IDs, always prove membership/ownership server-side. Future assets/findings/tasks must resolve tenant scope from the authenticated principal, not from a user-supplied `organization_id`.

**Validation and error handling**
- Email: normalized consistently, practical length limits, reject malformed input; avoid unusual provider-specific transformations.
- Password: minimum 12 characters, reasonable documented maximum, support passphrases and Unicode, no arbitrary forced symbol requirements; prevent denial-of-service inputs.
- Organization name: trim/normalize, reject empty/whitespace-only names, limit size, escape when rendered.
- Use Pydantic input/output schemas; explicit response shape and status codes; no password/hash/session fields in serializers.
- Invalid login returns a generic response that does not disclose whether the email exists.
- Duplicate registration should be clearly handled without stack traces; document the account-enumeration trade-off if returning a specific already-registered message.
- Return 401 for unauthenticated, 403 for unauthorized, 409 for conflicting state, and appropriate validation responses (as consistent with the current project's error conventions).
- Handle simultaneous duplicate creates and database constraints safely.

**Password security**
- Prefer Argon2id with a maintained library, configured to realistic memory/time costs; document chosen parameters and safe future rehash-on-login handling.
- Never log, print, echo, transmit back, or include plaintext passwords in exceptions, traces or persisted test fixtures.
- Do not use hand-rolled crypto or insecure SHA-256 password storage.

## 5. Security controls — mandatory, not cosmetic

**Sessions and cookies**
- `HttpOnly`, explicit `SameSite=Lax` or stronger based on tested navigation requirements, path scoping, sane expiry/max-age, and `Secure=true` behind production HTTPS.
- For local `http://127.0.0.1` development, a clearly labeled dev-only configuration may disable Secure; **fail closed** rather than silently allowing insecure cookies in production.
- Logout revokes the active session server-side, not just clearing client UI.
- Expired, revoked, random, corrupted, and forged session cookies must be rejected consistently.
- Session fixation resistance (fresh session after login; do not reuse an attacker-controlled pre-auth session).
- Keep auth responses non-cacheable where appropriate.

**CSRF / origin and CORS**
- Because browser authentication uses cookies, implement and **test** a concrete CSRF defense for state-changing endpoints, including logout, organization creation/editing, and session-creating login flows as appropriate.
- A defensible approach is a server-bound CSRF token passed as a custom header, combined with verified Origin/Referer and SameSite cookies. Pick one consistent design and explain how the frontend receives and attaches tokens. Merely setting CORS or SameSite is not a complete CSRF plan.
- Restrict allowed origins explicitly; credentialed CORS must never use wildcard origins.
- Test missing/invalid CSRF, disallowed origin, and same-origin valid requests.

**Authorization and privacy**
- Every organization read/write must derive identity from the verified server-side session.
- Test 2 independently registered users and organizations. Neither can query, update, or access the other's data, even by direct API request or modified IDs.
- Never serialize password hashes, cookie tokens, CSRF secrets, or internal error traces.
- Apply sensible login and registration rate limiting. Prefer per-IP with additional account-level resistance where practical. Choose a well-scoped, documented, testable limiter; acknowledge multi-worker limitations if using in-memory storage rather than presenting it as production-grade shared protection.
- Keep generic security headers and CSP from Phase 01 working; prevent credentials or tenant data from being cached inappropriately.
- Avoid unsafe HTML injection and SQL string concatenation.
- Use explicit environment variables for secrets and trusted origins. Keep `.env.example` placeholders only, and ensure real values never enter Git.
- Treat company/account data as private; collect only what Phase 02 needs.

## 6. Frontend functionality and design

Keep the existing distinctive **burgundy + strong red** ShieldMate identity, Anton display accents, IBM Plex Sans interface text, warm ivory contrast, and the established UI kit. Follow `docs/design-system.md`. The attached presentation screenshots are *style references only*, not layouts to copy. No blue cyber theme, pink-dominant site, violet neon, generic gradient login template, glassmorphism, excessive rounded cards or fake marketing metrics.

Implement, using existing routes where possible:

**Registration**
- Accessible email/password form, optional confirm-password field, meaningful labels and autocomplete attributes.
- Client validation for usability, with authoritative backend validation.
- Loading/disabled submit state, field/error messaging, success navigation.
- Suitable plain-language text for a real SME owner/IT generalist; no fake assurances about verified email or protected infrastructure.

**Login**
- Real call to backend, cookie handling with the existing API base URL and `credentials: 'include'` where required.
- Safe inline errors, successful redirect, no exposed sensitive tokens.
- A clear route to registration; do not add an inert password-reset button. If reset is not implemented, show honest explanatory text or omit the action.

**Organization onboarding**
- After first login, if no organization exists, show an intentional “Create your workspace” flow.
- Form for real company name and only necessary metadata, persistent backend creation.
- One workspace per user during the MVP; repeat creation must be blocked and produce an appropriate error.

**Authenticated `/app` shell**
- Route guard based on real `GET /auth/me`, not a localStorage Boolean.
- Correct loading screen while auth state is being checked (avoid brief flashes of private content).
- Navigation and redirects: signed-out users attempting `/app` go to login; signed-in users without org go to onboarding; signed-in users with org reach the workspace.
- Account/organization name visible, accessible user menu and working logout.
- Public landing remains accessible without authentication.
- Keep Phase 01 preview/UI-kit behavior honest and testable: if it is a publicly accessible design preview, separate it clearly from the real private workspace and ensure it never uses private data without authentication. Do not break its previous verification scripts unnecessarily.

**Organization settings**
- Display persisted organization identity; allow safe rename for the owner.
- Give success and error feedback; refresh reflects saved changes.
- No unimplemented delete-account, invite, billing, scan, domain-management or report buttons masquerading as functional controls.

**State and UX quality**
- Preserve responsive layouts for 360, 768, 1280 and 1920 CSS px.
- Real pending/success/failure states, keyboard navigation and visible focus, helpful empty states, correct aria descriptions and labels, accessible field error relationships, reduced-motion support.
- Avoid hard-coded “Welcome, Admin” and placeholder organizations where actual data should render.
- Do not add a large state-management library unless the existing architecture truly needs one.

## 7. Test plan and acceptance cases

Before changes, run and record the Phase 01 baseline. After changes, implement appropriate unit, integration, API and browser/E2E tests **using local test databases and no external services**.

At minimum automate cases covering:

### Backend/API
1. Successful registration persists a new user with a password hash, not plaintext.
2. Duplicate email and malformed email are handled safely.
3. Password boundaries are validated and documented.
4. Correct login creates a valid cookie-backed session; incorrect credentials fail generically.
5. Unauthenticated `/me` and organization routes return 401.
6. `/me` returns the correct authenticated user and organization status.
7. Organization creation persists and rejects invalid names/duplicate creation.
8. Organization rename persists; missing/invalid session cannot rename.
9. User A cannot see or alter User B's organization; try guessed IDs and malicious `organization_id` payloads.
10. Logout revokes session; reusing the old cookie fails.
11. Expired/revoked/invalid tokens fail.
12. Missing/wrong CSRF token and disallowed Origin fail on state changes; valid token works.
13. Login/registration rate limiting is exercised under controlled settings.
14. Password hash, raw session token, secrets and stack traces never appear in expected API output.
15. Alembic migrations work on an existing Phase 01 database **and** on a clean SQLite database; existing health endpoint remains operational.

### Frontend / browser
1. Register → login → onboarding → create company → private workspace → reload → logout.
2. An unauthenticated deep link to `/app` is redirected properly.
3. Expired sessions show a clean re-login flow without losing site navigation.
4. All forms handle disabled/loading/errors/success correctly.
5. Real organization rename survives refresh.
6. New UI is responsive at 360 / 768 / 1280 / 1920.
7. Keyboard, focus, contrast and basic automated accessibility checks pass.
8. Landing page, FAQ, navigation, 404, workspace preview, UI-kit and health endpoint do not regress.

Use real HTTP integration tests with a test client when feasible. Do not treat browser screenshots or a mocked `fetch` unit test as proof that backend authorization and CSRF work. Record commands executed and real outcomes. Run `npm audit` / `pip-audit` or equivalent existing checks; explain any findings. If environment lacks a browser/test tool, mark those items **NOT TESTED** instead of claiming PASS.

## 8. Local configuration, deployment readiness and documentation

- Preserve the existing `docker compose up --build --wait` workflow.
- Confirm frontend/backend cookie, CSRF and CORS behavior on localhost (including port differences) using documented dev origin settings.
- Preserve database data across container restart; do not commit local DB files or credentials.
- Add only the necessary settings to `.env.example` with clearly safe placeholders, comments and dev-vs-production guidance.
- Explain production requirements: HTTPS termination, `Secure` cookies, trusted origins, secret rotation, migration execution, session cleanup, backups and proper multi-worker rate-limit backend if needed. **Do not deploy in this phase.**
- Update README with register/login/org-onboarding workflow, exact startup/tests, troubleshooting, scope limitations, and clear “not yet implemented” items.
- Add `docs/phase-02-results.md` documenting decisions, API contracts, security controls, migration IDs, tests and known limitations.
- Avoid unnecessary new packages; keep lockfiles accurate and verify dependency compatibility.

## 9. Definition of done: non-negotiable gates

Do not report Phase 02 as completed unless all of the following actually hold:

- [ ] Sign up, sign in, session reload and logout operate against persistent backend storage.
- [ ] Server-side sessions use high-entropy tokens, safe hashed storage, expiry and revocation.
- [ ] Passwords are hashed securely and never exposed.
- [ ] Frontend private routes and backend private endpoints reject unauthenticated access.
- [ ] Every organization operation is scoped by the authenticated user; cross-tenant access tests pass.
- [ ] CSRF protection is implemented and tested on cookie-authenticated mutations.
- [ ] Registration/login abuse protections exist with documented limitations.
- [ ] Existing landing and brand system remain intact; UI interactions are real, responsive and accessible.
- [ ] No invented security findings, scan runs, reports, billing or fake organization data.
- [ ] Existing tests remain passing; new backend/frontend tests and production build pass.
- [ ] Database migration/clean start and Docker persistence are verified.
- [ ] Documentation and environment samples are updated without exposing secrets.

If a criterion cannot be completed safely, explicitly label it **FAIL / BLOCKED**, explain why, and stop short of claiming completion. Fix your own regressions before handing off.

## 10. Execution and final report format

1. **Inspect first**: check branch/status, existing routes, dependency strategy, session/cookie architecture, design system and baseline tests. State a short implementation plan; then implement.
2. Keep implementation narrowly scoped to Phase 02; favor a straightforward maintainable system over an elaborate auth framework.
3. Run actual backend/frontend test, lint, format, type-check, audit, build, Compose and browser checks. Record precise commands and pass/fail counts; do not invent outcomes.
4. Where the current repo workflow permits, create a **local** commit containing only your verified Phase 02 changes; report commit hash and clean/dirty status. Never push, deploy or publish secrets. Do not commit or stage unrelated pre-existing edits.
5. Deliver the exact handoff structure:

```text
Phase: 02 — Authentication & Organization Workspace
Design/architecture decisions:
API routes and data/migration changes:
Files changed:
Implemented:
Explicitly NOT implemented:
Verification commands and actual results:
Auth/session/CSRF/authorization test results:
Responsive/accessibility verification:
Security and regression findings:
Acceptance criteria: PASS / FAIL / NOT TESTED (each gate)
Local startup + manual signup walkthrough:
Manual environment/production steps:
Open issues/limitations:
Git status and local commit:
Next phase: 03 — NOT STARTED
```

**Execute Phase 02 now. Do not start DNS/domain verification, security scanning, finding prioritization, or any later phase without my explicit approval.**
