> Historical Phase 10.1 proposal, retained for provenance. Clone-only sanitization was subsequently approved and completed; see [current sanitization status](../sanitization-results.md). Upload permission is still pending.

# Phase 10.1 — blocker resolution proposal

**Decision: NO-GO for the first private GitHub push.** Non-destructive preparation is complete; no publication consent, history rewrite or upload is authorized or claimed.

Baseline remains `ce2f8df` on `main`: 18 reachable commits, one local branch, no tags/remotes. Original history, assets, Git configuration and application source remain intact. This package is deliberately uncommitted: the exact approved GitHub noreply identity has not been supplied, and no additional commit with the old personal email is necessary for this planning task.

Read the Phase 10 readiness assessment and publication audit in full. Their G04/G05/G18 conditions remain unresolved, but this review distinguishes essential permissions from optional privacy/license choices more precisely.

## Remaining blockers and proportional remedies

| Item | Assessment | Recommended action / required decision |
|---|---|---|
| Historical author email | One identity appears as author and committer in all 18 commits. Actual value is withheld. No email/home candidate was found in commit messages. | Privacy decision, not a confirmed credential leak. Approve retention or replacement in a separate publication copy. Recommend GitHub's exact account-provided noreply address; approve display name too. No config has been changed. |
| Historical home paths | 19 documentation/log files across 20 blob versions contain actual identifying home paths. A separate generic test-fixture path is not private and must remain untouched. Current documentation was already redacted in Phase 10. | Recommend replacing only reviewed identifying prefixes throughout history in the separate copy. Do not globally scrub every email, `/home` or `/tmp` string: that would damage fixtures/notices. Locations are in the redacted inventory; values stay private. |
| Three supplied presentation slides | All 18 commits contain the three tracked brand-reference paths. Source/redistribution permission is unconfirmed; the first slide includes instructor/team attribution. | Exclude their five-path policy subset (three slides plus two QA screenshots) from **every reachable publication commit**, or obtain explicit permission covering the intended upload. Original files stay local. Removing HEAD files or adding a child branch alone does not remove ancestry. |
| Two supplied QA-reference screenshots | Present in eight commits; user-supplied defect references, unconfirmed repository redistribution permission. | Recommend exclusion alongside slides. They are not application dependencies. Permission can instead be recorded if the actual rights holder agrees. |
| Core code, original UI and team documents | Actual IP/contribution/permission agreement has not been supplied. A Git author identity does not establish sole ownership. | Essential approval for third-party GitHub storage. Confirm rights holders and team agreement; check any applicable university/course obligations rather than assuming university ownership or that lecturer approval is always required. Removing names does not resolve code ownership. |
| Team/instructor names and attribution | Intentional attribution in supplied source materials/README/research mapping, plus slide text. No independent consent is claimed. | Approve appropriate attribution/privacy treatment. Preserve accurate credit under approved names/aliases. Instructor text leaves the candidate if the slides are excluded; team text still needs a reviewed decision. Do not invent contributions or erase ownership. |
| Open-source license | No project license selected. This alone is not an inherent blocker to a rights-authorized **private** source repository. | Private-first can retain accurate all-rights-reserved status if owners authorize storage. An MIT/Apache/etc. choice is optional now and needs rights-holder agreement before granting reuse rights. No LICENSE is created. Third-party license obligations still apply. |
| Secret scanner findings | Gitleaks 8.30.1 returns exit 10 with two findings, both reviewed false positives. | Do not claim a zero-finding scan or add broad exclusions. Keep reviewed rule/path/commit records; approve narrow handling if a later CI scan requires a strict pass. Any newly confirmed real credential blocks upload and requires rotation/revocation. |
| Technical limitations | Real owned-domain external E2E, independent language/privacy/legal review and hosted CI remain unverified. Human H13–H18 remain pending. | Disclose these honestly. They do not by themselves prove source cannot be stored privately, but they prevent stronger production/research claims. Public runtime deployment is separately unauthorized. |

Privacy improvements are optional **only if the affected person knowingly approves exposure**. Until decisions are recorded, the current privacy objectives keep them pending. Asset exclusion can resolve the reference-copy issue without obtaining redistribution permission for those excluded files; it cannot grant permission for the remaining project.

## Evidence gathered now

- Repeated read-only audit: all 18 commits, 2,173 reachable objects and 1,875 unique blobs, including renamed/deleted aliases. One identity, 36 author/committer occurrences; no extra refs/remotes. Raw identity/path values exist only in protected private work storage.
- Installed **Gitleaks 8.30.1** from the official release; downloaded archive SHA256 matches the same-release official checksums. No independent signature attestation is claimed. Full-history command: `gitleaks git --log-opts='--all --full-history' --redact=100 --report-format=json --report-path=<private-report> --exit-code=10 .`. No repository content was uploaded.
- Finding 1: `private-key`, `scripts/tests/test_publication_audit.py`, commit `580c4cb`, lines 15–37. Deliberately incomplete INTERNAL test marker, not a usable key. Finding 2: `generic-api-key`, `PROMPTS/PHASE_07.md`, commit `8f295fa`, line 18. Ordinary architecture instructions, no credential assignment. Raw output remains private because Gitleaks includes author metadata even with secret redaction. The safe findings file omits Match/Secret/Author/Email.
- Verified bundle containing all refs; restored an independent clone, matched HEAD and all 2,173 reachable object records, and passed `git fsck --full`. Also archived the complete `.git` directory and byte-verified every regular file against the original. A HEAD file archive retains original tracked files, including all five references. These private same-host backups are not encrypted/off-host disaster recovery and do not include live Docker volumes/ignored operator files. No destructive operation is permitted merely because a backup exists.
- Temporary **filesystem-only dependency probe**: exported baseline tracked files excluding exactly five references; all remaining **1,906 files match original bytes**. Both frontend/backend Docker images build from that export. No `.git`, branch, rewritten history or publication candidate was created in it. Missing reference links in documentation remain a later approved edit, not a claim that the export is publishable.
- Actual regression rerun: backend 325, frontend 101, offline tooling 55, Node 3 passed; static/frontend locale/build checks pass; actionlint passes; Compose config passes; existing localhost 8080 readiness is healthy. Current application/CI/Docker files are unchanged. No scan against a real target, human research or fresh deployment was performed.

[Redacted evidence](evidence.json), [metadata/asset locations](metadata-inventory.json), [Gitleaks findings](gitleaks-review.json), [backup verification](backup-verification.json), [command procedure](commands.md).

## What is essential to keep

| Files | Reason |
|---|---|
| `backend/app/**`, migrations, pyproject/uv lock, Alembic config, Dockerfile and deploy entrypoint | API/auth/scanner/evidence/tasks/reports, schema and reproducible backend build |
| `frontend/src/**`, index/config/manifests/lock, public favicon/robots/licenses, Dockerfile/Nginx | Real interface, localization imports, compiled build and same-origin routing |
| `backend/app/locales/**`, report fonts/LICENSE/sources and web-font notices | EN/RU/KK and licensed PDF/UI assets; do not remove copyright notices or substitute unlicensed fonts |
| `.github/workflows/ci.yml`, tests, QA runtime, scripts/research and publication tooling | CI and verification contracts; no new dependency or security relaxation required |
| `docs/testing/scenario.json`, beta protocol, participant materials and related templates | Evidence-tool scenario hashes bind specific files; deleting/editing them invalidates the existing study definition |
| Current architecture, scanner/risk/recovery docs, README, SECURITY and notices | Understandability, accurate limits, safe operations and third-party obligations |

Exactly five proposed exclusions are in `exclude-paths.proposed.txt`; no runtime/build/CI code references these image paths. Legacy phase reports, prompts, supplied source specs and most engineering captures are not needed by the application, but remain useful provenance. Approximately 164 MB of engineering evidence can be trimmed later if approved; keep the two README images and repair documentation links if doing so. This optional size reduction is not a prerequisite for private storage. No broad documentation/evidence deletion is proposed by default.

## Recommended strategy and alternatives

**Recommend:** after explicit approval, rewrite **only a fresh, independent, no-hardlink publication clone** with a reviewed private mailmap, exact text replacements and the five-path removal list. Keep all 18 milestone commits, their order/messages/dates and useful engineering history where feasible; use no-prune options to retain empty milestones. All author/committer replacements change commit IDs and therefore descendant IDs. Verify a commit map, app-tree identity and every reachable ref before any upload. New documentation must explain that old phase-report hashes refer to the private pre-publication lineage; old hashes alone do not retain that ancestry.

The original repository, full Git snapshot and bundle remain untouched and must never become the upload source. After sanitization, make a fresh independent transport clone of the sanitized main branch; audit it again and push **only main** after separate account/name/private-visibility approval. Do not push original branches/tags/bundles or use --mirror/--all/--force.

Alternatives: (a) preserve original history only if actual affected people and rights holders approve its exposure/asset redistribution; (b) approve a new curated root commit if selective rewriting proves unreliable. A new root loses useful history and still needs core-code permission. Both alternatives require approval; neither is executed now. Merely adding a “sanitized” child branch with original parents is ineffective.

## Decisions for the user

1. Approve or reject clone-only history sanitization; original repository stays unchanged. Choose the five proposed removals versus obtaining reference-image permission, and whether to retain all other engineering evidence.
2. Supply the exact GitHub-provided noreply address and approved display name; approve mapping this single historical identity in both roles. Decide treatment of home paths, team/instructor names and any additional private content.
3. Confirm who owns/authorizes the remaining code/UI/materials and the relevant team/course requirements. Confirm permitted private GitHub storage/audience. No teammate or university permission is presumed.
4. Choose whether to defer an open-source license (recommended until agreed) or arrange a rights-holder-approved license decision. Approve only narrow false-positive handling if desired.
5. After the sanitized candidate passes all post-remediation checks, approve the exact GitHub account, repository name and **private** visibility. Public visibility/release/deployment need later separate approval.

Stop here: no history/config/assets were rewritten, no branch created, no remote changed and no upload occurred. The proposed command blocks are intentionally unexecuted.

References: [GitHub commit email guidance](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address?platform=linux), [noreply formats](https://docs.github.com/en/account-and-profile/reference/email-addresses-reference), [GitHub licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository), [upstream filter-repo manual](https://github.com/newren/git-filter-repo/blob/main/Documentation/git-filter-repo.txt). Repository facts are verified locally; these sources do not establish anyone's project-specific permission.
