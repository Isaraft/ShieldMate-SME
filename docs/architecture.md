# Phase 00 architecture

## Initial assessment

The supplied archive contains five Markdown documents and three PNG design references.
All eight were read or visually inspected before implementation and are preserved unchanged.
The source folder contains only the archive; there is no previous application, dependency
lock, branch, commit history or user code to reuse. Implementation lives in this extracted
project. Slide text is not a functional instruction: subscription, continuous monitoring
and safety claims in the old presentation are not implemented or repeated as achieved facts.

## Boundaries

React + TypeScript + Vite render a small welcome screen, accessible layout, future-route
placeholders and a 404. React Router handles navigation. Tailwind v4 provides the token
and utility foundation; component CSS carries the restrained layout. A same-origin
`GET /api/v1/health` is the only application request. The UI reports connection status,
not security status, with loading, timeout, error and retry states.

FastAPI serves a typed `{ "status": "ok" }` liveness response. Settings, exception handling,
routers and database sessions are separate modules. SQLAlchemy 2 uses SQLite, enables
foreign keys on every connection and exposes a session dependency for future routes.
There are no account, organization, domain, finding or task models. Alembic's initial
revision is intentionally empty; only its version table is created. Application startup
does not call `create_all`; the documented migration step owns schema changes.

The local Vite server proxies `/api` to loopback port 8000. Compose builds static assets,
serves them through unprivileged Nginx, and proxies `/api` to the backend. Compose binds
both published ports to loopback, uses one backend worker, a persistent named database
volume, read-only container filesystems and a standard bridge network. Docker's internal
network mode suppressed the published ports in runtime testing, so the local setup uses a
normal bridge with loopback-only publication. Outbound networking is not firewall-blocked;
there is no scanner or domain request endpoint. No external domain is probed. Future scanning
phases must implement the specified egress constraints before enabling checks.

## Configuration and safety

Pydantic Settings reads the root `.env`; process environment takes precedence. SQLite
relative paths resolve from `backend/`, regardless of the process working directory.
CORS is off by default; explicit origins may be configured for GET only without cookies.
Hostnames must be explicit. No secrets, sessions or browser storage are needed yet.
Errors use `error: {code, message}` without submitted input or exception details.
Application error logging records exception type, not payload. Access logging is disabled
in documented commands to avoid recording query strings. Standard server/startup diagnostics
remain local operational output; never add secret-bearing exception messages in later code.

The health endpoint is liveness, not database readiness. It does not query SQLite or
certify that a future workflow can complete. Container startup runs migrations first.
TrustedHostMiddleware rejects invalid host headers with Starlette's fixed plain-text 400;
application API errors use the JSON envelope. There are no modifying public API routes.

## Visual concept and initial choices

Deep burgundy, vivid red and warm ivory establish a confident, editorial identity.
Anton provides a condensed display voice; IBM Plex Sans makes supporting copy and
navigation readable. Large type is confined to the small welcome panel; the workspace
uses compact navigation and quiet, explicit planned states. Expressive public-page design
and the full component system belong to Phase 01, which has not started.

Central tokens live in `frontend/src/styles.css`, including semantic success/warning/error
colors, visible focus, reduced-motion rules and responsive spacing. All state colors have
text labels. Only Latin font subsets and the four used weights are imported from Fontsource
and bundled locally; there is no Google Fonts request or remote image dependency. Both
families use the SIL Open Font License; notices are included in `frontend/public/licenses/`
and copied into the build. Only WOFF2 is shipped, without duplicate legacy WOFF assets.
Broader Cyrillic coverage and final typography decisions belong to the relevant design and
localization phases. Fallback stacks remain usable without fonts.

## Dependency decisions

Use stable release lines, not prereleases: React 19, Vite 7, TypeScript 5.9, Tailwind 4.1,
Vitest 4.1 and SQLAlchemy 2.0. `package-lock.json` and `uv.lock` pin resolved versions and
hashes. Python 3.13 is the container baseline; Python 3.14 is also accepted. Node 24 is
the container baseline, with Node 22.12+ supported by the frontend configuration.
Container image tags follow their named release lines; they are not digest-pinned.
Rebuild and audit before any later deployment; this is a local foundation.

The backend image exports hashed requirements from the frozen uv lock and installs them
with pip's `--require-hashes`. This retains the same versions and integrity checks while
avoiding the uv download step that stalled in the container build environment.

Official implementation references: [Vite requirements](https://vite.dev/guide/),
[Tailwind's Vite integration](https://tailwindcss.com/docs/installation/using-vite),
[FastAPI settings](https://fastapi.tiangolo.com/advanced/settings/).

## Deferred work

Authentication, organization authorization, CSRF, sensitive-action rate limiting,
domain verification, SSRF protections, checks, findings, tasks, PDF, sample demo,
subscriptions, production TLS and deployment are absent. Do not expose the local services
publicly. The frontend is a client-rendered SPA with noindex metadata, not a public
marketing release; social previews, sitemap and a documented SEO strategy belong to Phase 01.
