# Phase 10 — local release / publication decision

Proposed version: **v0.1.0-mvp**, unreleased and untagged. Baseline `8040755`; final tested application/packaging candidate `4964696`. The subsequent handoff commit adds documentation and redacted evidence. [Exact results](phase-10-results.md), [publication audit](phase-10-publication-audit.md), [third-party notices](../THIRD_PARTY_NOTICES.md).

**Local preparation is complete. Uploading the existing history, including a first private push, is BLOCKED pending privacy/asset/team decisions.** Public hosting is separately unapproved and unsuitable for this localhost profile.

| Gate | Status | Evidence / boundary |
|---|---|---|
| G01 Baseline/branch/HEAD/status | PASS | Clean main at8040755;13 baseline commits; one ref; no remote; `evidence/phase-10/baseline.json` |
| G02 Current tracked scan | PASS | Read-only targeted scan plus current staged files; no real credential confirmed; heuristic limits explicit |
| G03 Reachable history | PASS | All baseline refs/13 commits/1766 blobs; repeated through 17 candidate commits/1814 blobs; final post-commit scan retained locally; gitleaks unavailable |
| G04 Private artifacts/PII/account metadata | BLOCKED | Personal author email, historical home prefixes, team/instructor attribution and final binary-consent review |
| G05 Asset/font/software rights | BLOCKED | OFL/notices/hash/name/history reviewed; supplied slide/QA-image redistribution and project rights unconfirmed |
| G06 Ignore/packaging safety | PASS | 21 ignore assertions; harmless nested env markers included before fix and excluded after in both Docker contexts; production builds still pass |
| G07 Safe environment/local start | PASS | Safe examples reviewed; clean locked install and isolated16273 startup without secret env/seed volume; localhost8080 remains healthy |
| G08 Professional README | PASS | Actual supported scope, two developer screenshots, architecture, setup, limits, team and unselected-license status |
| G09 Security/scanner guidance | PASS | SECURITY.md with conditional private reporting/no invented contact; scanner/risk/backup boundaries preserved |
| G10 Portable documentation | PASS | Current identifying home/checkout prefixes redacted; no private absolute path remains in current documentation; history separately blocked |
| G11 Restricted reproducible CI | PASS | SHA-pinned read-only workflow, credential persistence off, no privileged PR event, secrets or deployment; actionlint 1.7.12 and local commands pass. Hosted Actions run NOT TESTED |
| G12 Regression/build/i18n/tools | PASS |325 backend, 101 frontend, 55 internal-tool, 3 Node tests; lint/format/type/catalog/build checks; three new logo regressions failed before fix |
| G13 Migration/Docker/smoke | PASS | Headf34f9df9b6a4/no drift; clean compiled Docker profile; 12 localized axe/layout views, private redirect/401,3 demo PDFs/18 labeled pages |
| G14 Dependency/supply-chain review | PASS |68 Python/347 npm advisory records:0 known advisories; license inventories, OFL and official action SHA/checksum review; base-image CVE/legal limits explicit |
| G15 Clean committed checkout | PASS | Local no-hardlink clone of committed candidate; fresh uv/npm dependencies; 325/101 tests; final tools55; safe empty storage; candidate 4964696 builds/starts with notices served |
| G16 Demo/research truth | PASS | Read-only synthetic demo; H13–H18 pending; proposed 80%/120s hypothesis is not a result |
| G17 Release/audit documents | PASS | Proposed changelog, audit, readiness and results; no tag/release |
| G18 Rights/account/publication decisions | BLOCKED | Team/lecturer/IP/license/identity/slide permissions; GitHub account/name and explicit private-first approval required |
| G19 No external modification/rewrite | PASS | No remote creation/push/deployment/release/tag/history rewrite; read-only source/package downloads only |
| G20 Final local commit/tree | PASS | Handoff commit contains this report; `git log -1` identifies it; post-commit status checked clean; no human evidence tracked |

**17 PASS, 3 BLOCKED.** PASS on an audit-execution gate does not clear findings from that audit. No claim of GitHub publication readiness while G04/G05/G18 are blocked.

## Approval-gated private-first procedure

Do not execute uploads now. First resolve audit P01–P04 and final binary review. Team must confirm contribution/IP rights, names/email exposure, reference-slide permissions and license choice. If history cleanup is needed, propose the exact non-destructive alternative or separately approved rewrite; deleting HEAD files alone is insufficient. Credentials, if ever found, must be rotated/revoked before any upload, including private.

Then obtain explicit approval for an authenticated GitHub account, exact repository name and **private** visibility. Recheck clean Git state, all reachable refs, audit, branch and intended commits. Create an empty private repository only under that approval. Inspect any existing origin rather than overwriting it. Add the approved private URL only if origin is absent, review the destination, then push **main only**. Do not use --mirror/--all/--tags/force or publish a tag/release automatically.

Independently inspect the remote copy, default branch, files, metadata, permissions, secret scan and actual Actions runs. Conditionally enable private vulnerability reporting if supported and approved. Public visibility, hosted deployment and release publication each require separate approval. Localhost is not a remotely usable prototype URL.

Human Phase 09 H13–H18 remain pending until real evidence is collected; a private GitHub repository does not complete academic testing.
