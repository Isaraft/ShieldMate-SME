# Phase 10 — local release / publication decision

Proposed version: **v0.1.0-mvp**, unreleased and untagged. Baseline `8040755`. Local implementation is being verified; final outcomes are recorded in [Phase 10 results](phase-10-results.md).

**Uploading any existing history is BLOCKED pending privacy/asset/team approval.** Public hosting is separately unapproved and unsuitable for this localhost profile. [Redacted audit](phase-10-publication-audit.md), [third-party notices](../THIRD_PARTY_NOTICES.md).

| Gate | Status | Evidence / boundary |
|---|---|---|
| G01 Baseline/branch/HEAD/status | PASS | Clean main,8040755,13 commits,one ref,no remote |
| G02 Current tracked scan | PASS | Targeted read-only categories/paths; no high-confidence real credential confirmed; heuristic limits disclosed |
| G03 Reachable history | PASS | All refs/13 commits/1766 unique blobs enumerated; no unreachable/ref-log guarantee; gitleaks unavailable |
| G04 Private artifacts/PII/account metadata | BLOCKED | Author email, historical home prefixes, team/instructor attribution and binary approval limits |
| G05 Asset/font/software rights | BLOCKED | OFL/metadata reviewed; supplied slides/QA-image redistribution and project rights unconfirmed |
| G06 Ignore/packaging safety | NOT TESTED | Await final ignored-path/context verification |
| G07 Safe environment/local start | NOT TESTED | Safe examples reviewed; awaiting clean Docker check |
| G08 Professional README | PASS | Current scope,actual captures,architecture,setup,limits,team and unselected-license status |
| G09 Security/scanner guidance | PASS | SECURITY.md and existing scanner/risk/recovery boundaries |
| G10 Portable documentation | PASS | Current personal home/checkout prefixes redacted; history exposure separately blocked |
| G11 Restricted reproducible CI | NOT TESTED | Read-only pinned workflow prepared; portable commands/definition verification pending; hosted GitHub run not performed |
| G12 Regression/build/i18n/tools | PASS |325 backend,98 frontend,54 internal tooling,3 Node; static/build/catalog checks logged |
| G13 Migration/Docker/smoke | NOT TESTED | Await clean isolated local release check |
| G14 Dependency/supply-chain review | PASS | App advisories/lock metadata/OFL/action SHAs reviewed; mutable image/CVE/legal limits explicit |
| G15 Clean committed checkout | NOT TESTED | Await local-only clone of candidate commit |
| G16 Demo/research truth | PASS | Read-only synthetic demo; H13–H18 pending; proposed hypothesis is not a result |
| G17 Release/audit documents | PASS | Proposed changelog plus audit/readiness/results documents; no tag/release |
| G18 Rights/account/publication decisions | BLOCKED | Team/license/identity/slide permissions,GitHub account/name/private-first approval required |
| G19 No external modification/rewrite | PASS | No remote creation/push/deployment/release/tag/history rewrite |
| G20 Final local commit/tree | NOT TESTED | Final evidence/handoff commit pending |

## Approval-gated private-first procedure

Do not execute uploads now. First resolve audit P01–P04 and final binary review. Team must confirm contribution/IP rights, names/email exposure, reference-slide permissions and license choice. If history cleanup is needed, propose the exact non-destructive alternative or separately approved rewrite; do not assume that deleting HEAD files suffices. Credentials, if ever found, must be rotated/revoked before upload, including private upload.

Then obtain explicit approval for an authenticated GitHub account, exact repository name and **private** visibility. Recheck clean Git state, all reachable refs, redacted audit, branch and intended commits. Create an empty private repository only under that approval; inspect any existing origin rather than overwriting it. With the approved private URL, add origin only if absent, review the exact destination and push only main (no --mirror/--all/--tags/force). Do not publish a tag/release automatically.

Independently inspect the remote copy, default branch, files, metadata, permissions, secret scan and actual Actions runs. Conditionally enable private vulnerability reporting if supported and approved. Public visibility, hosted deployment and release publication each require separate approval. Localhost is not a remotely usable prototype URL.

Human Phase 09 H13–H18 remain pending until real evidence is collected; a private GitHub repository will not complete the academic testing requirement.
