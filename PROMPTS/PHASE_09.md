# SHIELDMATE SME — PHASE 09
## Alpha & Beta Testing, MVP Validation, Evidence Package and University Defense Readiness

**Execution language:** English. **User-facing application languages:** English, Russian, Kazakh.
**Starting commit:** `e9c7db4` on `main` (Phase 08). **Project:** ShieldMate SME Starter MVP.
**Strict scope:** Phase 09 only. **Do not push, publish, expose a public tunnel, purchase services or start an unrelated Phase 10.**

### 0. Your role and non-negotiable working standards

Act as a senior software engineer, QA lead, security engineer and product researcher preparing a defensible, evidence-based university MVP validation. This is not a generic chatbot-produced portfolio case study. Read the full repository first, including `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, the Phase 08 risk register, release/restore runbook, defense runbook, scanner documentation, test harnesses, and the actual Assignment 5 brief if accessible in the workspace. The course requirements below are transcribed into this prompt so that you can work even if the assignment PDF is not in the repo. When the actual assignment source differs, report the conflict rather than silently replacing either source.

Preserve the existing burgundy-and-red editorial identity, clean architecture, application security, database contents, migrations, immutable reporting artifacts, existing demo-data isolation and EN/RU/KK localization. Prefer small verified improvements to expansive refactors or speculative new features. All generated text should be clear, credible, practical and non-promotional.

**Fundamental integrity rule:** Software tests, injected QA fixtures, screenshots of a seeded demo, and simulated participant answers are NOT evidence that real people tested the MVP. Never fabricate participants, interview notes, session dates, task durations, quotes, survey responses, real business ownership, commercial interest or conversion numbers. Do not silently count your own automated Playwright interactions as alpha or beta sessions. Mark unavailable observations `NOT CONDUCTED`, `NOT TESTED`, or `PENDING MANUAL EVIDENCE`, with an exact explanation. Never pretend to have contacted or observed participants.

### 1. Assignment 5 criteria to support

The assignment continues ShieldMate from Assignments 1–4. The team must plan and build a **working** MVP, alpha-test internally, beta-test with real users from its target market, analyze results, and defend the live prototype. The report is a 1,500–2,000-word PDF, excluding cover/tables/figures/references/appendix, with numbered sections: Introduction, Literature Review, User's Path Map (at least four stages and insights), Feature List & Prioritization (at least eight features and an explicit MoSCoW/RICE or other justified method), MVP Scope (included/excluded features, a one-sentence hypothesis and a numeric criterion), MVP Management & Development Method (alternatives, justification, team roles and plan), Alpha & Beta Testing, Conclusion, References (APA 7), and Appendix. The appendix must contain dated testing proof, individual contribution table and AI-tools disclosure. The prototype requires **three to six screenshots** and a live demonstration. Presentation: **maximum ten slides**, PDF, with questions. Report and slides must be PDF; the prototype link is a separate LMS field. No testing evidence means no credit for unsupported results.

**Your Phase 09 responsibility:** Make the actual application and its validation process reliable, instrumentable, reproducible, easy to test, privacy-aware and accompanied by evidence templates and truthful analysis utilities. Do not autonomously invent the academic report's findings, literature references, claimed pilot adoption or external tester results. Prepare usable structured material that the human team can incorporate into the report after actual sessions.

### 2. Establish an independently verified Phase 08 baseline

Before modification:
- Confirm branch, HEAD, clean/dirty status; do not discard user changes.
- Run existing backend/frontend tests, lint/type/format/build, migration drift, Docker local release and health/readiness checks.
- Inspect actual `/demo`, authenticated application, reports and EN/RU/KK rendering.
- Review any known issues from Phase 08. Record genuine defects and critical blockers, particularly anything that would invalidate a usability session or expose private data.
- Determine whether a **documented test mode** can support a local user session safely, without altering production code paths or claiming synthetic results are real assessments.
- Produce a dated baseline entry in `docs/phase-09-results.md` showing commands and factual results.

### 3. Explicit product hypothesis and measurement definitions

Treat the following as a **proposed** measurable usability hypothesis aligned with earlier ShieldMate product decisions, pending team adoption:

> At least 80% of target-user beta participants will be able to identify the highest-priority security issue and explain its recommended next action in no more than 120 seconds using ShieldMate's clearly identified test scenario, without moderator hints.

This does **not** establish that ShieldMate reduces real-world breaches, accurately detects all vulnerabilities, or that participants will pay for a subscription.

Recommend at least **five distinct beta participants** from the intended audience (SME owners, operations leads, IT generalists or people genuinely responsible for SME security decisions). This is a pragmatic proposed sample, not a requirement stated in Assignment 5; do not label it a course-mandated minimum. For n=5, meeting an 80% threshold requires **4/5** successful participants. Preserve denominator and explain small-sample limitations. Recruitment must be actual and documented by the team; avoid classifying only developer teammates as beta users. Beta users may test a clearly labeled synthetic demonstration *for usability* without consenting to access or scanning a real organization's assets. Mark this distinction clearly.

Define:
- Primary task success: correct identification of the scenario's designated Top 1 issue **AND** a sensible next action, no hint, elapsed time <=120 seconds.
- Elapsed time: monotonic timer from the moment the task is read/shown until the answer is submitted; manual stopwatch is acceptable if recorded consistently. Pause/aborted handling must be documented.
- Hinted responses: record separately and count as primary-task failure.
- Incomplete/withdrawn tests: preserve outcome and document the denominator policy; do not quietly drop unfavorable records.
- Secondary usability metrics: unaided completion of navigation to finding evidence; ability to distinguish a remediation task marked Done from an evidence-confirmed resolved finding; clarity rating (1–5); usefulness rating (1–5); friction issues, error count and qualitative verbatim feedback when consented.
- Do not calculate an unsubstantiated business ROI, actual risk reduction, NPS or paid demand.

Use a single reproducible scenario with a predeclared correct issue/next action and a **fixed scenario version**, preventing outcome manipulation after tests. If the current demo contains ambiguous Top 1 priorities, improve scenario description or write a grading rubric that reflects its actual deterministic server results; do not invent hidden findings.

### 4. Alpha test: internal functionality + guided human checks

Build `docs/testing/alpha-plan.md` with an executable checklist of the real flows:
1. Start/restart local release, login and organization setup.
2. Enroll an explicitly owned/test domain, show DNS TXT instructions; if actual domain unavailable, mark live verification as not tested, do not fake it.
3. Existing scanned-observation pipeline using explicitly synthetic QA data only in an isolated test context; verify no real-scan claims are made.
4. Inspect Top 3 evidence, check severity rationale and inconclusive states.
5. Create/update task and demonstrate that task completion does not resolve a technical finding.
6. Render and inspect EN/RU/KK report, keeping any `LOCAL QA`/`DEMO` indicators.
7. Exercise navigation, keyboard focus, resize, localization switches, form preservation, session/logout and isolation.
8. Test Docker clean start, ready health, backup/restore and artifact checks.

For each item include steps, expected behavior, actual result to be filled, issue severity, evidence filename, tester initials/code and local date/time. Running automation can prefill **automated** checks only; human observation fields must stay empty until someone actually tests.

Identify and fix actual reproducible bugs arising during this phase, with regression tests. Avoid unrelated design rewrites and unapproved product features.

### 5. Beta protocol: realistic, repeatable and ethically sound

Create `docs/testing/beta-protocol.md` with:
- One short invitation script in EN, RU and KK, accurately describing an academic cybersecurity interface usability test and the use of synthetic data.
- A consent explanation: voluntary participation, approximate session steps (no promises about time if unknown), no access to actual company secrets, permission separately requested for screenshots/audio/quotes, withdrawal option, study-only purpose and local retention/deletion instructions.
- Anonymous IDs such as `B01`, `B02`; optional broad role/industry categories (no names/emails/phone numbers required), language and familiarity category, documented date, moderator and scenario version.
- A standardized opening explanation that **does not reveal the correct answer**.
- A task sheet: reach the primary issue, identify risk/action, inspect evidence, navigate to tasks, explain difference between Done and Resolved, review reporting clarity.
- Neutral moderator prompts and clearly prohibited hints.
- A closing survey of 4–6 short questions, combining measurable and open-ended answers. In addition, include a question testing perceived value without framing it as actual willingness to pay unless a real, appropriately worded question is asked.
- Accessibility alternatives to accommodate participants without excluding them or changing scores silently.
- A defined stop/rollback procedure if the local machine, browser or demo fails.
- Data-handling guardrails: never collect passwords or confidential company data, disable third-party analytics by default, avoid logging the tester's raw input unnecessarily and keep proof local and access-controlled.

Translate the participant-facing materials to natural EN, RU and KK; use existing localization conventions or clearly separate study documents from app translation catalogs. Flag language copy requiring independent native-speaker validation.

### 6. Evidence collection and analysis tooling

Provide a small, low-dependency, offline-friendly evidence kit under `docs/testing/` plus scripts under `scripts/` (names may adapt to repo conventions):
- `alpha-results-template.csv` and `beta-results-template.csv` with documented, stable columns.
- A participant note template containing consent state, date/time, role segment, scenario version, observed actions, ratings and comment provenance.
- `evidence-manifest-template.csv` linking anonymized participant/session IDs to dated screenshots, survey exports and notes, with SHA-256 checksums if supporting files exist.
- A practical `README.md`: how to conduct tests, where to store private artifacts (ignored by Git), how to create redacted submission-safe proof and how to run analysis.
- An analysis/validator CLI that consumes *real filled-in CSVs*, validates types/IDs/duplicates/date format/consent and denominators, and produces a clearly labeled outcome summary. Empty templates must generate `NO REAL BETA RESULTS YET`, not 0% success or a passing score. It must never create plausible-looking synthetic participants or fill empty fields. Script may write report-ready summary tables to a chosen output path but must not impersonate a study or generate forged evidence.
- Unit tests for evidence validation, threshold calculation (including 4/5 passing, 3/5 failing), missing data, duplicates, hinted completions, withdrawn sessions, mixed languages and malformed input.

Prefer Python standard library (csv, argparse, hashlib, pathlib, datetime) and avoid introducing networked databases or user telemetry unless clearly justified. If any new API/form is necessary, it must be private, security-reviewed and explicitly documented; a file-based kit may be more proportionate.

**Data protection:** Never commit participant answers, names, personal contacts, raw screenshots containing private data, recordings, secrets, live company domain records or interview identifiers beyond anonymized codes. Keep private evidence in gitignored local folders, provide export/sanitization directions and do not send anything externally. Do not silently purge pre-existing files.

### 7. User's Path Map, feature priorities and contribution support

Prepare a source-linked *draft support* file `docs/testing/assignment-05-mapping.md` with:
- At least four actual product journey stages (discovery/onboarding, authorized enrollment, scan/findings interpretation, action/recheck, report/return), grounded in what exists.
- At least eight candidate features prioritized with a consistently applied MoSCoW method. Clearly distinguish live Starter MVP features from excluded Plus/future features such as phishing campaigns, managed response, full SIEM integrations and billing.
- A one-sentence proposed hypothesis and numeric criterion consistent with Section 3; mark them as team-proposed until confirmed.
- Concise explanation and alternative comparison for MVP type (e.g., functional concierge-supported pilot vs fully automated product) and development method (e.g., iterative increments vs waterfall), carefully separating observed history from rationale.
- A blank team contribution matrix naming actual three members only if names are already present in the repository/documentation; otherwise leave editable fields. Do not assign fictional work or invent contribution percentages.
- An AI-assistance disclosure template naming Codex/ChatGPT or the tools actually used and their roles, without hiding AI contributions.
- A short checklist for Part B: 3–6 genuine screenshots, feature coverage explanation, live demo and LMS prototype-link field. Do not claim the localhost URL is remotely usable; document the potential issue and a question to confirm with the lecturer.
- A short checklist for Part C: <=10 slides in PDF, live walkthrough, individual Q&A; **do not** generate a 10-slide artifact or 2,000-word report unless separately requested.

Do not manufacture peer-reviewed sources for the literature review. Identify the academic-citation requirement and leave verified sourcing and final report writing to a later, explicitly requested step.

### 8. Stable demonstration and test environment

Keep the currently verified **local-only** release profile at `http://127.0.0.1:8080` (or its actual configured replacement). Verify:
- Reproducible `docker compose -f compose.local.yaml up --build -d --wait` startup and `/ready` behavior.
- Clearly labeled synthetic demo stays isolated from authenticated real organization data and cannot bypass scanner authorization.
- A fresh, deterministic demo state for every research session, without deleting legitimate persisted organization data.
- Participant sessions cannot modify another team's real data or persist accidental private data into screenshots/reports.
- Form/locale navigation is robust, and all buttons in the tested workflow work as indicated.
- PDF export is legible and correctly labeled in all three languages; inspect a manageable set of representative pages, not merely extract text.
- A nontechnical lecturer can follow `docs/testing/defense-checklist.md` with preflight, click path, fallback demonstration plan and simple recovery steps.

If actual domain ownership is still not available, keep that limitation prominent, demonstrate the **real code path** from tests/fixtures without claiming a live external scan, and recommend a separate owned-domain test when possible. Do not configure public tunnels, remove `localhost` binding or weaken CSRF/Host/CORS/cookie or scanner protections for convenience.

### 9. Independent quality and security checks

After changes execute and record the **real** results of:
- Backend and frontend unit/integration suites;
- Python Ruff, format, mypy; TypeScript typecheck, ESLint, formatting, build;
- Alembic migration upgrade/history/drift;
- npm and Python dependency audit (do not describe zero known CVEs as an absolute security guarantee);
- Docker build, readiness, restart and persistence checks;
- Browser smoke checks for marketing page, `/demo`, sign-in, private Dashboard, Assets, Findings, Action Plan and Reports in EN/RU/KK at 360/768/1280/1920 widths;
- PDF generation and rendered-page inspection;
- CSRF/session/tenant isolation, no unintended external outbound requests and no QA fixture contamination of production-like state;
- Evidence CLI with deterministic unit test fixtures clearly marked **INTERNAL TEST DATA** and entirely separated from human beta evidence.

Where actual browser/device/screen-reader/native-language testing is unavailable, mark it `NOT TESTED`. Never report screenshot counts without describing what was inspected and whether it was automated or human.

### 10. Delivery structure and acceptance gates

Update `docs/phase-09-results.md` (or equivalent) with truthful status. Divide acceptance gates into **ENGINEERING READY** and **HUMAN EVIDENCE PENDING**; a complete code change does not mean the university assignment has been beta-tested.

**Engineering gates (can be marked PASS through actual implementation):**
1. Phase 08 baseline preserved.
2. Safe, documented alpha plan and pass/fail records.
3. Beta protocol with eligible target participants and neutral instructions.
4. Consent, participant anonymity and private evidence storage safeguards.
5. Reproducible scenario and declared success rubric/denominators.
6. CSV templates, evidence manifest and analysis validator, including tests.
7. Assignment 5 source-aligned mapping and honesty about excluded functions.
8. Stable and isolated local demo/release workflow.
9. Natural EN/RU/KK study support with translation uncertainty labeled.
10. Product/security regressions passed with exact results.
11. Evidence-ready screenshot instructions, defense preflight and recovery.
12. No push, remote exposure or fabricated study results; clean documented Git state.

**Human evidence gates (MUST remain PENDING until the team actually completes them):**
13. Dated internal alpha sessions with participants, observations and reproducible evidence.
14. Actual beta sessions with target-audience participants and recorded consent/outcomes.
15. Computed hypothesis criterion from the collected real beta evidence, with denominator.
16. Evidence-linked conclusion and changes, validated with the team.
17. Complete academic report appendix: test materials, dated evidence, contribution table and accurate AI-tool statement.
18. Lecturer-compatible prototype access/defense logistics confirmed.

Report blocked/not-done items explicitly. If you can perform an **internal technical alpha-style walkthrough** yourself, label it as developer/automated QA rather than human alpha or external beta research.

### 11. Final Codex response format

1. Starting/ending commit and Git status; working tree and push/deployment status.
2. What changed, organized by application vs research/evidence tooling vs documentation.
3. Confirmed and proposed research hypothesis and exact definitions, including why results cannot yet be claimed.
4. Actual commands and results (test counts, audit results, browser/PDF QA, Docker).
5. Files/links for alpha protocol, beta protocol, evidence templates, CLI, assignment mapping and demo runbook.
6. Engineering gates PASS/FAIL/NOT TESTED and human-evidence gates PENDING/COMPLETED WITH REAL PROOF.
7. Real remaining constraints, including live owned-domain end-to-end and independent language verification.
8. Short **HUMAN NEXT ACTIONS** guide describing exactly how the team should recruit participants, run alpha/beta, collect consent/evidence, calculate results and prepare the submission.

**Start implementing Phase 09 now.** Do not stop at planning. Do not claim complete beta testing without real human participants. Do not deploy publicly or push anything without explicit approval.
