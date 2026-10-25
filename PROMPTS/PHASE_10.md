# SHIELDMATE SME — PHASE 10
## GitHub Publication Readiness, Repository Audit & Release Engineering

**Execution language:** English
**Baseline:** `main` at `8040755` (Phase 09 engineering complete; reportedly clean working tree).
**Target:** A professionally documented, secure, reproducible, **GitHub-ready** ShieldMate SME repository.
**Publication rule:** Prepare and verify everything locally. **Do not create a remote repository, push, make anything public, publish a release, or rewrite Git history without my explicit approval.**

---

## 1. Context and non-negotiable product truths

ShieldMate SME is a Kazakhstan-focused, cybersecurity SaaS **Starter MVP**, not a production SOC, SIEM, EDR, penetration-testing platform, or security guarantee. The application currently includes a burgundy-and-red branded landing page; EN/RU/KK localization; authentication and organization workspaces; domain authorization and DNS TXT verification; tightly restricted DNS/TLS/HTTP checks for verified assets; evidence-based findings; contextual prioritization; remediation tasks; immutable PDF reports; and a clearly separated synthetic public demonstration.

Development phases 00–08 and the **engineering portion** of Phase 09 were completed locally. Phase 09 explicitly reports `E01–E12: PASS`, but real-human `H13–H18` testing remains **PENDING**. There are no verified real beta measurements, accepted commercial customers, proven real-world scanning outcomes, paid pilots, or public deployment. Never imply otherwise in GitHub materials. The proposed 80%/120-second usability hypothesis is not yet an observed result.

The work should represent a serious, independently understandable engineering portfolio project while respecting the original three-person university team and its intellectual-property rights. Do not unilaterally choose an open-source license or publish others' contributions; flag team/lecturer permissions that need confirmation before public release.

## 2. Working method

1. Inspect the entire repository first, including `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, the previous phase completion reports, architecture and scanner documentation, testing kit, Git state/remotes, existing license metadata, and current CI files.
2. Confirm the actual baseline with `git status`, `git branch --show-current`, `git rev-parse HEAD`, `git log`, and a safe listing of Git remotes. If the repository is not at the expected state, state the discrepancy; do not reset, checkout, force, rebase, or discard changes.
3. Preserve application behavior, the three-language UI, and the burgundy/red visual identity. This is a **release-engineering and publication-safety phase**, not a new product-feature sprint or visual redesign.
4. Make minimal justified changes, with focused regression tests. Reuse repository tooling; avoid adding large dependencies solely for this phase.
5. Do not fabricate clean results or confuse `NOT TESTED` with `PASS`. If a release blocker requires user action, document it and stop before any irreversible or external operation.

## 3. Audit the complete Git history for publication risks

Examine both the **current tracked tree** and **all reachable Git history/refs**. Do not assume that deleting a sensitive file from the current HEAD makes its past contents safe to publish.

At minimum, investigate:

- `.env`, `.env.*` other than intentionally safe examples, auth/signing/session keys, credentials, cloud tokens, webhook secrets, private keys/certificates, API access keys, password hashes, session cookies, CSRF tokens, real DNS TXT challenges and sensitive configuration values.
- SQLite databases, database journals, WAL/SHM files, backups, migration snapshots containing application data, Docker volumes, persistent artifacts, private PDF reports, logs, raw error dumps, coverage outputs, package caches, temporary QA output and actual research/consent files.
- Screenshots and documents that accidentally expose usernames, email addresses, passwords, organization names, verified domains, internal paths or private identifiers. Differentiate clearly marked synthetic fixtures from actual people/data.
- Hard-coded local absolute paths, machine usernames, personal home directories and internal-only links in README, docs, screenshots, config and tests.
- Git author/committer email exposure inherent in the planned history, as well as unexpected branches/tags/remote refs.
- Third-party visual assets, font binaries, presentation screenshots and packaged PDF fonts: identify original source, license and redistribution permission. Do not infer permission from successful local use. Do not copy font binaries into new outputs merely to satisfy documentation.

Use established scanners such as `gitleaks` if available, plus targeted Git and filesystem inspection. If a scanner is absent, use a defensible alternative without reporting that the absent scanner passed. Distinguish actual secrets from test fixtures to avoid misleading findings.

**Never print a discovered secret into the completion report, test logs, README, patches shown to the user, or a Git commit message.** Redact and report only the affected path/commit/category and recommended action.

**HARD STOP:** If any real secret, private report, unapproved private data, or incompatible binary license exists anywhere in history intended for publication, mark public publication **BLOCKED**. Propose remediation and necessary credential rotation. Do not silently run `git filter-repo`, BFG, `git gc`, force-push, delete refs, or rewrite author metadata. Obtain approval before any history rewrite or destructive operation.

## 4. Repository hygiene and data protection

- Inspect and improve `.gitignore`, `.dockerignore`, and related packaging rules based on the actual project. Exclude local secrets, runtime storage, SQLite files/backups, generated private reports, QA participant responses/consent records, transient images and artifacts, coverage/build outputs, caches and virtual environments.
- Keep only safe, necessary, intentionally versioned examples and synthetic fixtures. Validate that `.env.example` contains **no valid credentials** and accurately documents required variables; avoid defaults that accidentally enable insecure public production.
- Check `git ls-files`, `git check-ignore`, and a clean check-out/clone to ensure ignored secrets are not already tracked.
- Ensure all committed source and executable scripts have sensible permissions, paths are portable, and README instructions don't depend on the original machine.
- Keep genuine beta evidence outside the public source tree by default. Human-testing templates may remain in the repository if entirely blank and safe.
- Confirm the repository does not accidentally configure the localhost-only app to listen publicly or relax scanner/network/auth restrictions in a new default profile.

## 5. Professional GitHub README and supporting documentation

Write a polished, factual `README.md` in clear English. Optional concise localized overview sections can be added if they improve accessibility, but avoid duplicated inaccurate translations or bloated prose. The README must read like a serious developer-maintained project—not AI-generated marketing copy.

Include:

1. Product name and a one- or two-sentence problem statement rooted in SME security prioritization.
2. A restrained, honest explanation of what the **Starter MVP actually supports**; clearly distinguish planned/Plus-only capabilities.
3. Key architecture and technology stack, matching the repository and Docker configuration.
4. A simple architecture diagram if helpful (Markdown/Mermaid is fine), without inventing components.
5. Accurate prerequisites and reproducible **localhost-only** startup using the actual release profile, including first-run migrations/env steps and `docker compose -f compose.local.yaml up --build -d --wait` if verified.
6. Authentication/onboarding, verified-domain consent and safe scanning workflow, including safe boundaries and explicit ownership requirement.
7. The existing synthetic `/demo`, visibly identified as synthetic. Provide a usable path for reviewers who lack an owned domain.
8. Available UI/report languages: English, Russian, Kazakh.
9. Tests, quality checks, local backup/restore, and how to stop/reset the app without deleting production or user data by accident.
10. Screenshots only if they're actually in the repository, sanitized, representative and properly attributed. Use correct **relative paths**.
11. Honest current maturity: local MVP, no independent production security certification, no real beta outcomes yet, no public hosted instance.
12. Non-sensitive limitations, what was intentionally excluded, and a clear collaboration/acknowledgment section reflecting the project's three-person team.
13. Licensing status accurately stated. **Do not claim MIT/Apache-2.0 or invent a LICENSE file without the team's explicit decision.** If rights are unresolved, say `License: not yet selected; all rights reserved unless otherwise specified` or equivalent, without pretending the repository is open source.

Review `docs/architecture.md`, `docs/scanner.md`, `docs/local-release-runbook.md`, and security/testing documents for contradictions or unnecessary exposure. Add a concise `SECURITY.md` describing responsible vulnerability reporting **without inventing a contact email**, and the difference between reportable bugs and authorized scanning. If an official private security-reporting mechanism exists in repo settings, document it conditionally; do not assert it has been enabled.

## 6. CI and reproducible release verification

Build or improve GitHub Actions **only if appropriate to this repository**, using minimal permissions (`contents: read` unless more are justified), predictable environment setup and dependency caching where useful. Review any existing workflows first; don't duplicate them. Pin third-party actions to reviewed immutable commit SHAs where feasible and avoid executing privileged workflows on untrusted code.

CI should run the checks that are actually portable:

- Python backend unit/security tests, Ruff, mypy and migration/schema checks.
- Frontend test suite, ESLint, TypeScript typecheck, formatting, i18n consistency and production build.
- Evidence-tool tests and repository QA configuration checks, if documented and executable without private data.
- Dependency audits if network/tooling policy permits; report `NOT RUN` rather than fabricating results when unavailable.

Do not require real DNS control, externally reachable scan targets, private API keys, access to instructor resources, a GPU, actual beta participants, or persistent local app data in CI. Use explicitly labeled synthetic fixtures for deterministic network-layer testing.

Perform a clean-checkout verification using committed project files and documented commands. Make sure the build does not accidentally depend on untracked `.env` secrets or local Docker volumes. Do not publish test fixtures as live assessments.

## 7. Release notes, changelog and publication decision

Prepare an honest initial release candidate: `v0.1.0-mvp` **as a proposed version only**, not an actual tag/release until approval. Draft release notes listing implemented Starter MVP functionality and the known limitations, including that the product is not a replacement for SOC/EDR/SIEM and that human beta gates remain pending.

Create or update:

- `docs/phase-10-publication-audit.md`: tracked-tree AND complete-history audit, methods, classifications, blocked items and evidence without secret values.
- `docs/phase-10-release-readiness.md`: precise PASS/FAIL/NOT TESTED gates, link to reproducible commands, manual approvals and publish checklist.
- `docs/phase-10-results.md`: detailed actual implementation, tests, changed files and Git status.
- `CHANGELOG.md` or a concise release-notes draft, if none exists.

Review whether there is already an `origin`; never overwrite or change the remote URL without consent. If publishing readiness passes and the user's GitHub identity/repo name/permission are not known, provide clear next-step choices rather than inventing an owner account.

**Publication is a distinct approval gate.** The intended order is: (1) finish local audit/cleanup, (2) show redacted evidence and recommend private/public readiness, (3) receive explicit approval for GitHub account, name and visibility, (4) create/push to a **private** GitHub repository first, (5) independently audit the remote copy and seek separate approval before making it public. Never claim a private repo can contain historical secrets safely simply because it is private.

## 8. Explicitly forbidden shortcuts

- No fake GitHub URL, badges, stars, customers, uptime, security scores, research statistics or hosted demo links.
- No publishing `127.0.0.1` as a publicly accessible URL.
- No copying real reports, login cookies, consent sheets, credentials or private QA artifacts to public examples.
- No license selection or copyright assignment on behalf of teammates.
- No unilateral rewrite/deletion of Git history, force push or remote creation.
- No disabling app security for easier local tests, broadening scan targets, enabling unrestricted redirects, relaxing verification requirements or weakening tenant boundaries.
- No rewriting the frontend design or implementing Phase 09 human testing as synthetic human evidence.
- No stopping after a plan; implement all **locally safe, authorized** Phase 10 improvements.

## 9. Required acceptance gates

Mark each gate **PASS, FAIL, BLOCKED or NOT TESTED**, with supporting evidence.

- **G01** Baseline, local branch, HEAD and pre-change status independently verified.
- **G02** Current tracked-tree secret/private-data scan performed.
- **G03** Full reachable Git history/ref scan performed, and any limitations clearly stated.
- **G04** Private artifacts, PII, owned domains and account metadata reviewed/redacted.
- **G05** Fonts, assets, borrowed visuals and software license rights assessed; unresolved approvals surfaced.
- **G06** `.gitignore`/`.dockerignore` protect future local data without hiding needed source files.
- **G07** Safe `.env.example` and localhost-only run instructions verified.
- **G08** Professional README is accurate, portable and consistent with the shipped MVP.
- **G09** Security/scanner limitations and disclosure guidance are explicit.
- **G10** All documentation uses stable relative paths, not private absolute file paths.
- **G11** CI workflows (if added/modified) are minimally privileged and run reproducibly or untested status is honest.
- **G12** Backend, frontend, i18n, evidence tooling and production builds show real command results.
- **G13** Database migration, Docker startup and local release smoke checks are verified.
- **G14** Dependency and supply-chain review performed with tools and limits stated.
- **G15** Clean-checkout test succeeds using only committed files and safe supplied configuration.
- **G16** Synthetic demo and academic testing statuses are clearly distinguished from real outcomes.
- **G17** Proposed release notes, version and publication-audit documents exist.
- **G18** Team/publication/licensing approvals and any blocking issues are explicitly documented.
- **G19** No public/private remote repo creation, push, release, tag publication or history rewrite occurred without approval.
- **G20** Final working tree is clean after a local commit, or the exact reason it is not is documented.

Do not declare GitHub publication ready when a blocking audit/license/permission gate has failed.

## 10. Final response contract

At completion provide:

1. Baseline and new local commit, branch, and clean/dirty tree status.
2. Short summary of the README/docs/CI/hygiene changes with concrete paths.
3. A redacted public-exposure/security/history audit summary with blockers clearly identified.
4. Exact commands executed and actual counts/results, with `NOT TESTED` where appropriate.
5. All 20 acceptance gates with evidence.
6. Outstanding human permissions: team agreement, license decision, GitHub account/repo name, private-first approval, then optional public approval.
7. A minimal next-step **private GitHub push procedure** to execute **only after explicit approval**.
8. Confirmation that Phase 09 H13–H18 remain pending absent real human testing.

**Implement Phase 10 publication readiness now. Stop before any GitHub upload, deployment, external network action that modifies a service, or destructive history rewrite. Do not merely provide a plan.**
