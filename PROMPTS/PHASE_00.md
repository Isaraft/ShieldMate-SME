# CODEX EXECUTION PROMPT — PHASE 00 ONLY

You are taking ownership of the initial engineering foundation for **ShieldMate SME Starter**, a real B2B cybersecurity risk-to-action MVP built for the university's Technological Entrepreneurship Assignment 5. Act as a disciplined senior full-stack engineer and security-minded product designer, not a one-shot scaffold generator.

**Before changing any code, read ALL of:**
1. `AGENTS.md` — mandatory repository-wide engineering, security and brand requirements.
2. `SHIELDMATE_MVP_SPEC.md` — complete MVP scope and safety boundaries.
3. `PHASES.md` — exact development order and acceptance gates.
4. The three images in `docs/design-references/` — visual identity **only**, not functional specs or layouts to copy.

Then inspect the repository, branch, git status, existing code, tooling and documentation. Preserve existing useful implementation and unrelated work. If the repo is empty, create the smallest maintainable foundation that can grow into the MVP.

## Product understanding

ShieldMate SME targets Kazakhstan SMEs of approximately 10–100 staff lacking their own security department. It will eventually let a user register a company, verify a company domain via DNS TXT, run **authorized and bounded read-only** DNS/TLS/HTTPS checks, see evidence-backed priorities, assign remediation tasks and export a management report. Its core competitive idea is converting technical findings into a short, understandable weekly action list. It is NOT a SOC, SIEM, EDR, penetration-testing platform or vulnerability exploit scanner.

The **brand must be Burgundy + RED**. Visual direction: confident editorial/brutalist, condensed oversized headlines, graphic scale and asymmetry on public-facing pages; high-clarity and usable data presentation inside the app. Light neutrals support contrast but do not make this a pink website. Absolutely no generic blue cybersecurity palette, purple gradients, neon, glassmorphism, default AI landing-page composition, fake stats, stock testimonials or emoji-icon cards.

## Your task — PHASE 00 FOUNDATION ONLY

1. Write a concise initial repository assessment: what exists, what should be preserved, and your choice of a minimal architecture. Do not ask routine questions that can be answered from these documents.
2. Establish an understandable structure: `frontend/`, `backend/`, `docs/`, root configuration and tests. Reuse valid existing structure if present.
3. Frontend: React + TypeScript + Vite + Tailwind CSS (or equivalent existing stack). Provide client-side routing, a minimal accessible app shell, not-yet-live route placeholders, 404 state and reusable layout foundations. Define centralized design tokens with deep burgundy, crimson RED and warm readable neutral surfaces. Use deliberate type families (maximum two) and fallback stacks. **Do not build the full landing page or dashboard in this phase.**
4. Backend: FastAPI with Pydantic configuration, SQLAlchemy 2-style models foundation, SQLite and Alembic migration infrastructure. Implement `GET /api/v1/health` returning a simple stable response. Keep routers, configuration, DB session and exception handling modular. Do not add functional account or domain models until their phases unless migration/bootstrap needs a minimal placeholder.
5. Docker Compose: local `frontend` and `backend` services, persistent database volume, restricted ports, explicit health/startup instructions. Avoid adding Redis, Kafka, Elasticsearch, Celery, Kubernetes, hosted paid services, cloud API dependencies or any LLM.
6. Tooling: minimal backend test for health endpoint; minimal frontend render/routing smoke tests; lint, format and type-check configurations where appropriate. Pin dependencies using each ecosystem's normal lockfiles; avoid blind latest-edge dependency choices. Configure `.gitignore` (exclude `.env`, SQLite/volume files, cache, secrets, build artifacts), safe `.env.example` with descriptive placeholders only, no secrets or production tokens.
7. Document local run, manual and Docker commands, project architecture and test commands in `README.md`. State prominently that external scanning, authentication, reports and paid subscriptions **are not implemented yet**.
8. Never fabricate security findings, chart values, clients, fake user reviews or demo scan results. Do not add links/buttons that falsely claim to scan domains or authenticate users; future actions must be disabled or transparently labeled as planned.
9. Consider secure defaults from day one: input validation patterns, safe configuration loading, no permissive credentialed CORS, env-based secrets, no stack trace exposure, no remote check endpoints before Phase 03/04. Avoid overengineering controls belonging to later phases while ensuring the foundation does not make them difficult.
10. Run the actual relevant checks available in the environment: backend tests, frontend tests, build, lint/typecheck and `docker compose config` where Docker is available. Fix errors caused by this phase. If a command cannot run (e.g. missing dependency/network/service), report that fact with exact reason; never invent successful results.

## Design quality rules

At the beginning, write a **3–4 sentence visual concept** explaining mood, typography, color and the intentional difference between expressive marketing design and restrained internal tooling. Follow the user-provided visual direction exactly; do not copy the slideshow structure. Include thoughtfully designed initial empty/loading/not-yet-implemented states and visible keyboard focus. Respect `prefers-reduced-motion` and accessibility.

## Scope boundaries

**STOP after Phase 00.** Do not implement login, organization onboarding, domain verification, DNS/TLS/HTTP checks, vulnerability findings, risk scoring, remediation tasks, PDFs, a fully detailed landing page, deployment or beta test results. These belong to later phases and require independent verification. Never push to remote or deploy without explicit authorization. Do not overwrite uncommitted work.

## Response format after implementation

1. **Repository assessment and decisions** — existing architecture, what was kept, selected stack, concise visual concept.
2. **Files created/modified** — meaningful summary, not an enormous source code dump.
3. **Commands and actual results** — build, lint, typecheck, tests and Docker validation; show failures if any.
4. **Security and quality checklist** — what exists now, what is intentionally deferred, config the owner must supply.
5. **Phase 00 acceptance** — each objective PASS / FAIL / NOT TESTED with a reason.
6. **Run locally** — exact reproducible commands.
7. **Next phase** — short handoff to Phase 01. **Do not start it.**

If a requirement conflicts with another, identify the conflict and choose the safer, simpler maintainable approach without silently discarding product requirements. If absolutely blocked, ask only essential questions (at most five); otherwise proceed with documented conservative assumptions.
