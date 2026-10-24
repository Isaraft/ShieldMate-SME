# Security Snapshot reports — Phase 07

Reports are accounts of **saved, authorized external-configuration evidence**, not certificates, live scans, monthly trends or compliance audits. The protected `/app/reports` route uses actual organization records. A zero finding count never establishes that a domain is secure.

## Source contract

`app/reports/schemas.py` defines `security-snapshot-1`: opaque report/organization IDs, display name, UTC creation time, requested locale, `real`/`demo` kind, policy version, readiness, coverage, assets/observations, findings, shared Top 3, and scoped remediation work. Snapshot creation uses a consistent SQLite transaction. Dates remain Unix UTC; UI formats in `Asia/Almaty` with the date's actual GMT offset; PDFs print explicit UTC.

`app/reports/snapshot.py` reads organization/domain/scan/observation/finding/evaluation/task tables. Inclusion requires current ownership authorization, matching scan proof generation and verification timestamp, supported scanner/policy versions and a persisted terminal evaluation. The latest scan must contain at least one usable observation; errors/inconclusive checks alone cannot authorize generation. Queued/running/unevaluated scans do not imply clean results. An expired/rotated proof excludes the asset's evidence. Pruned source runs exclude unsupported historical findings rather than inventing provenance.

The existing `finding_page` service supplies finding states, counts and Top 3 using optional internal scope filters. Its risk rubric is unchanged. Report counts describe the **assessed subset**, so the screen explicitly explains exclusions when the dashboard retains older findings. The finding lifecycle remains owned by Phase 05; a human task marked done does not resolve it. Reports include task status, owner label, recommendation, timestamps and references; freeform private work notes are deliberately omitted.

Readiness: `no_assets`, `unverified`, `no_evidence`, `processing`, `incomplete`, `stale`, `ready`. An assessed subset can produce a prominently scoped partial or stale report; missing/failed/not-checked observations and excluded domains remain visible. `can_generate` requires usable authorized persisted evidence, never a fabricated clean result.

## Persistence and lifecycle

Additive Alembic revision `f34f9df9b6a4` follows `e53b215e4b66` and adds `security_reports` and `report_events`; previous migrations remain unchanged. JSON snapshot and PDF BLOB live together in the existing SQLite database/Docker database volume. There is no filesystem artifact path, symlink, public bucket or static customer PDF. History queries defer BLOB loading.

Generation reserves a row (`generating`) and commits the consistent snapshot, renders outside the DB lock, then atomically publishes bytes, size, SHA-256 and `ready`. Failures persist `failed` with a fixed error code and no downloadable broken PDF. Same-organization request UUIDs are idempotent; reusing a UUID with another locale fails. A partial unique index prevents simultaneous generation per organization. Requests recover their own interrupted reservations after five minutes; they cannot modify another organization's row. A completed snapshot is never re-rendered or overwritten after source records change.

SQLite backup must include the reports as sensitive customer data; use SQLite's online backup API or stop services before a consistent volume backup, not an arbitrary live database-file copy. No report deletion UI, scheduled retention or cleanup job is introduced. Domain deletion does not rewrite existing report artifacts. The conservative lifetime limit requires an explicit future retention policy before higher-volume use.

## APIs and controls

All customer routes require the existing authenticated owner and organization checks:

- `GET /api/v1/reports/overview`: current readiness and scoped snapshot.
- `GET /api/v1/reports?offset=0&limit=10`: own metadata history, bounded pagination.
- `POST /api/v1/reports`: strict `{locale: "en"|"ru"|"kk", request_key: UUID}`; existing CSRF and Origin checks.
- `GET /api/v1/reports/{UUID}`: own metadata.
- `GET /api/v1/reports/{UUID}/download`: own saved PDF, checked size/SHA-256, attachment, `private, no-store`, `nosniff`.

No caller-supplied organization, risk, evidence, file path or render URL is accepted. Invalid/foreign IDs fail independently of UI visibility. Download access is checked afresh even if logout occurs while rendering; late completion grants no bearer URL. Requested/ready/failed/downloaded/download-failed audit events contain actor, organization, report ID and time, not secrets or source text. At most 100 events remain per report; this is a bounded operational record, not an immutable forensic audit ledger.

Limits: 20 enrolled domains, 120 findings, 120 tasks, 1,000 retained scan rows (existing scanner ceiling), 2 MiB snapshot JSON, 2 MiB PDF, 80 pages; reject excess rather than truncate a claimed complete assessment. Five creation attempts/hour per organization and creator, 20 lifetime report attempts/organization, one active render/organization and two active global reservations. Sensitive route request budgets are process-local (30 create/15 minutes and 180 download/15 minutes); durable attempt/concurrency limits are in SQLite. Existing auth/scanner restrictions remain unchanged.

## PDF implementation

ReportLab renders selectable text into A4 pages with burgundy rules, restrained red, wrapped paragraphs and page numbers. Embedded, licensed Plex-derived print regular/semibold supports Cyrillic and Kazakhstan company-name characters; the license is in `app/reports/fonts/`. Both UI and print retain the same Plex typography, with Anton reserved for Latin display text. The renderer HTML-escapes text, removes bidi/control characters and never loads remote images/URLs, executes HTML, invokes a browser/subprocess or calls the scanner. Evidence values come through the existing allowlisting normalizer; raw DNS proof, cookies, session material and work notes never enter the PDF.

Contents: organization/report/version/timestamps, limitations, explicit denominators/coverage, lifecycle/severity and task counts, authoritative Top 3 with rationale, all scoped findings/evidence, remediation work and asset/check detail. Source IDs and app-relative references contain no tokens. These are readable references rather than externally hosted access links.

## Reproduction

Run `docker compose up --build -d --wait`, open `http://localhost:5173`, register/sign in and create a workspace. Enroll only a domain you control, publish its exact current TXT challenge, verify it, run the bounded checks and wait for evaluation. Open `/app/reports`, review coverage, choose EN/RU, generate and download from history. Refresh/restart and download again: the checksum and bytes must match.

A genuinely owned-domain assessment remains **NOT TESTED** until the owner provides a domain and authorization. `scripts/verify-phase-07.cjs` instead uses an isolated QA stack with injected TXT and persisted synthetic observations, visibly labeled in screenshots; it is not live security-assessment evidence.

## Phase 07.1 print template

Newly generated snapshots carry `template_version: assessment-2`; the evidence schema remains `security-snapshot-1`. This optional metadata field requires no schema migration. Existing database rows, immutable JSON and PDF BLOBs are never rewritten. Downloads continue returning the stored bytes. The old-template EN/RU artifacts were downloaded before and after the new images started, and after a database/container restart; SHA-256 comparisons are recorded under `evidence/phase-07-1/checks/`.

The renderer uses an A4 frame with zero implicit padding and explicit 18mm side / 27mm top / 23mm bottom margins. Print styles separate narrative, labels, evidence and tables. Section headings stay with introductory content; tables repeat headings across page breaks. Executive coverage, authoritative Top 3, methodology, finding evidence, remediation work, definitions and the observation appendix form one reading sequence. Ordering and finding lifecycles remain Phase 05 service outputs. UTC is printed explicitly; no CVSS, certification or new security score is computed.

Every DEMO page retains the DEMO marker; explicitly named LOCAL QA organizations receive a visible test-data header. Other reports carry confidentiality/authorized-scope context. Raw evidence values and identifiers wrap without truncation. User notes remain excluded. The bounded offline renderer still enforces 80 pages / 2MiB, strips unsafe controls and escapes markup. It cannot fetch remote resources. Font binaries stay inside the repository and application image, accompanied by OFL and source hashes. Print TTFs are reproducibly assembled from locked Plex subsets; the missing right arrow is rotated from Plex's own vertical-arrow outline and the derivative is internally renamed ShieldMate Plex Print.

`verify-phase-071-pdfs.py` uses Poppler to rasterize all nine final API-generated fixtures and check text extraction, page bounds and context on every page. Visual contact-sheet/full-page review supplements those checks. This is not PDF/UA certification; screen reader reading order and non-Chromium viewers require manual follow-up.
