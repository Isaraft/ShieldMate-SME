# Assignment 5 support — draft, not a completed academic report

Human testing, conclusions, contribution confirmation and submission logistics are **PENDING MANUAL EVIDENCE**. This file maps the implemented product and prepared instruments to course requirements; it does not manufacture study findings, academic sources or a final report/deck.

## Source and precedence

Original course source inspected completely: `<operator-home>/Downloads/Telegram Desktop/Assignment 5 MVP (2).pdf`, “Technological Entrepreneurship — Assignment 5: Creating an MVP”, SHA256 `e68301c18942bcb47afb65337b90a35676978bc546c6bc358b6f0dbbebd79636` (3 pages). Local authoritative Phase 09 implementation brief is preserved in `PROMPTS/PHASE_09.md`. The two agree on the ten numbered sections, real alpha/beta evidence, working prototype, PDF-only report/slides,3–6 screenshots,≤10 slides and separate LMS prototype field. The actual source additionally specifies **at least three literature sources: two academic + one course lecture**, and **Times New Roman12pt,1.5 spacing, justified,2.5cm margins**, with course/title/group/member names on the cover. Apply those requirements to the eventual report; no fictional references are supplied here.

Repository product sources: `SHIELDMATE_MVP_SPEC.md` sections0–3,10–11; `PHASES.md`; current `docs/architecture.md`, `scanner.md`, `risk-methodology.md`, `remediation-workflow.md`, `reports.md`, `demo.md`, Phase08 results/risk register. Source links below are repository-relative and identify real behavior, not human-research proof.

Clarifications/conflicts to disclose: the older spec calls the usability target “prespecified” and proposes≥3 alpha sessions/≥5 beta people. There is no actual team adoption/recruitment proof, and the course source sets no numerical sample minimum; current Phase09 treats those as **project proposals pending adoption**. The older UC09/demo acceptance mentions editable sample tasks; approved Phase07/08 public `/demo` is intentionally **read-only**, while real task persistence is implemented in authenticated isolated workspaces. Do not claim a mutable public demo or redesign it to mask that distinction. The old Phase08 roadmap heading mentions public deployment; the actual approved Phase08/09 scope is local-only, not a deployed URL.

## User's Path Map (draft design rationale)

| Stage | User goal / channel / actual action | Implemented support and source | Possible friction to investigate (not observed results) |
|---|---|---|---|
| Discover / enter | Understand scope on `/`; choose account or `/demo` | `frontend/src/pages/Landing.tsx`, `Demo.tsx`; explicit synthetic/limited-check notices | Can an SME owner distinguish bounded assessment from a security guarantee? |
| Onboard / authorize | Sign in/create company; add exact authorized domain and DNS TXT | `Account.tsx`, `Assets.tsx`; `backend/app/auth.py`, `domains.py`, `domain_dns.py` | DNS access may require an IT provider; measure separately from demo comprehension |
| Collect / interpret | Enqueue authorized check; review persisted observations and Top3 | `backend/app/scanner/`, `findings/`, `Dashboard.tsx`, `Findings.tsx`; `docs/scanner.md`, `risk-methodology.md` | Does priority + plain next action reduce interpretation effort in a fixed scenario? |
| Act / recheck | Open a finding, create task, owner label/note/status; later authorized recheck | `tasks/`, `TaskDetail.tsx`; `docs/remediation-workflow.md` | Do users understand Done is human work while technical resolution needs conclusive evidence? |
| Share / return | View report readiness/scope, save/download immutable PDF, revisit history | `reports/`, `Reports.tsx`; `docs/reports.md` | Are exclusions, timestamps, source provenance and stale/incomplete states understood? |

Three **design inferences for validation**, not user findings: (1) proof-first enrollment prevents unauthorized scanning but can create a provider dependency, so beta uses a read-only scenario and alpha covers proof separately; (2) evidence-linked priorities and task/finding separation need explicit comprehension measurement rather than a fabricated safety score; (3) frozen demo + marked immutable PDFs support offline defense, but cannot validate live DNS/provider reliability or business adoption. Team must replace or qualify these with actual session insights where appropriate.

## Feature priorities — consistent MoSCoW

Must = necessary for safe core risk-to-action validation; Should = useful enhancement after core stability; Could = optional future benefit; Won't = excluded from this MVP. This uses scope/deadline constraints rather than inventing RICE reach/impact estimates. Priorities are product decisions, not measured customer demand.

| Feature | Priority | Actual state / rationale |
|---|---|---|
| Account/company isolation | Must | Implemented; persists owner scope, prerequisite for private data (`auth.py`) |
| Exact-domain consent + DNS TXT proof | Must | Implemented; prerequisite for probes; live owned-provider E2E still NOT TESTED (`domains.py`) |
| Bounded DNS/TLS/HTTP checks + scan history | Must | Implemented/safety-tested; only authorized public exact hosts, no exploit scanner (`scanner/`) |
| Evidence-backed findings and shared Top3 | Must | Implemented deterministic rules/queries, no fabricated CVEs/score (`findings/`) |
| Plain impact/action + technical evidence detail | Must | Implemented for supported observations, inconclusive states preserved (`registry.py`, finding UI) |
| Persistent remediation task/status/owner label/history | Must | Implemented; owner label is not a user role; Done does not resolve finding (`tasks/`) |
| Immutable private PDF/report history | Must | Implemented EN/RU/KK with scope/provenance; insufficient data stays explicit (`reports/`) |
| Isolated clearly marked public sample | Must | Implemented read-only `/demo`; safe testing without company access (`demo.py`) |
| Business/technical presentation choice | Should | Implemented view density, no authorization effect |
| English/Russian/Kazakh localization | Should | Implemented; native external review pending (`backend/app/locales/`) |
| Historical progress trends | Could | Per-scan history exists; no invented longitudinal security trend |
| CSV finding import / weekly email | Could | Not implemented; not required for this usability hypothesis |
| Phishing campaigns, managed response, SIEM/EDR integrations | Won't | Excluded Plus/future scope and operational/legal burden |
| Billing/subscriptions or paid-demand claims | Won't | Not implemented; proposed pricing is unvalidated |
| Exploitation, arbitrary ports/internal scans, full security guarantee | Won't | Explicitly excluded; unsafe/unsubstantiated |

## Scope, hypothesis and proposed criterion

Included: working owner-isolated application, authorized bounded checks, evidence/risk-to-action workflow, task persistence, immutable reports, honest read-only demo, EN/RU/KK. Excluded: public deployment in this phase, multi-member RBAC, payment/Plus services, continuous monitoring and unrestricted scanners. No claim of comprehensive vulnerability coverage.

**PROPOSED, team adoption pending:** At least80% of distinct target-user beta participants identify the highest-priority issue and explain a sensible next action in≤120 seconds without hints in the fixed test scenario. Recommend≥5 analyzed participants (4/5 succeeds;3/5 fails); not a course minimum. `beta-protocol.md` defines timer start/stop, missing/hinted/aborted/withdrawn handling and sensitivity denominators. User-entered grades/times require actual observation. `scenario.json` binds the actual fixed Top1 and rubric. No participant result exists yet.

## MVP type and management method

Observed implementation: a functional software MVP with real private backend workflows, plus a clearly synthetic read-only illustration and moderator-supported sessions. Proposed positioning for the report: **functional MVP with assisted pilot onboarding/testing**, not a concierge service that manually manufactures security results. Compare with a landing-page/clickable mockup (insufficient working features for PartB), Wizard-of-Oz manual results (would not verify implemented engine), and fully self-service public SaaS (would require deployment/operations work outside approved scope). The team must confirm the rationale; do not claim a pilot customer or automated public deployment.

Observed Git/doc history is phased incremental engineering through the Phase08 `e9c7db4` baseline. Proposed management explanation: iterative, risk-first increments with regression gates, versus waterfall (integration/safety feedback arrives late). This is rationale grounded in source history, not evidence that the human team held specific sprints/meetings. Do not invent sprint dates, daily stand-ups or deadlines.

| Next milestone | Human-agreed owner | Planned actual date | Required proof |
|---|---|---|---|
| Confirm protocol/sample/retention/language review | | | Adopted declaration, reviewed handouts |
| Internal alpha and defect triage/retests | | | Dated actual sessions/issues and consented notes |
| Recruit and run eligible beta sessions | | | Real consent, timings/answers and manifest |
| Validate/compute and agree interpretations | | | CLI aggregate + team review of primary evidence |
| Write referenced report and appendix | | |1500–2000 words, actual evidence, APA7 |
| Prepare≤10 PDF slides and rehearse live | | | Genuine3–6 screenshots, logistics confirmed |

## Contribution matrix — names sourced, work unassigned/unconfirmed

Names are present in `SHIELDMATE_MVP_SPEC.md` section11. Its old proposed responsibility split is not proof of completed work. Do not fill hours/percentages or attribute Codex's implementation to a person without review.

| Actual named member | Confirmed role | Actual tasks/contribution | Dated commit/evidence | Review/signoff |
|---|---|---|---|---|
| Muratbay Bekzat | | | | |
| Aisagaliev Islam | | | | |
| Taubayeva Aina | | | | |

## AI-tools disclosure template

Confirmed for this implementation: **Codex** assisted with repository review, programming, engineering tests, study-template/CLI preparation, translation drafts and technical documentation. Automated browser/fixture runs are engineering QA, not participants. The human team remains responsible for consent, recruitment, observation, language/source review, grading, analysis interpretation and submission accuracy; those activities are pending here. Add actual dates, scope, reviewed outputs and each member's verification. List ChatGPT or other tools only if actually used, with truthful purposes; do not hide AI assistance or assert that no AI was used. No participant quotations or interview evidence were generated.

## Submission checklists (team work remaining)

PartA numbered sections:1Introduction;2Literature Review;3User's Path Map (≥4stages +2–3insights);4Feature Prioritization (≥8features/method/justification);5MVP Scope (included/excluded + one-sentence hypothesis/numeric criterion);6MVP type + management method, each compared with an alternative, real plan/roles;7Alpha/Beta (who/why/metrics/results linked to appendix);8Conclusion (criterion evaluated only from real data);9References APA7;10Appendix (dated proof, actual contributions, accurate AI statement). Source at least two real academic publications/books and one real course lecture; verify bibliographic details later. This phase does not fabricate literature or write the final1500–2000-word report.

PartB: select3–6 **genuine rendered prototype screenshots**, explain implemented/excluded scope and distinguish engineering synthetic screenshots from dated human-session proof. The working private product must support the real main flow; public read-only demo is an illustration, not a mock replacement. The prototype link goes in the separate LMS field. **127.0.0.1 is accessible only on the operator's machine**; ask the lecturer whether an in-person local demonstration is acceptable or a separately approved accessible deployment is required. Do not claim a localhost link is remotely usable or configure a tunnel here.

PartC:≤10 slides exported as PDF, actual live walkthrough/fallback, individual Q&A about product/method/security/evidence/limits. Confirm real LMS deadline/group/full names and demonstration machine/connectivity with the lecturer. No slide deck or final academic PDF has been requested/generated in Phase09. Unknown logistics stay pending.
