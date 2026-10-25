# Sanitized publication copy

**Technical sanitization: completed. Upload decision: NO-GO pending team/rights-holder permission and explicit upload approval.** No GitHub repository, push, tag, release, visibility change, tunnel or deployment was performed.

The human authorized clone-only history sanitization and supplied the exact GitHub identity `Isaraft`, `147975507+Isaraft@users.noreply.github.com`. That approval does not establish permission from other contributors, an institution or a third-party asset owner. Appropriate team attribution and upstream copyright/license notices remain intact. No project open-source license is selected; private storage still requires authorization for the remaining code/UI/materials.

## What changed

- The private original remains at `ce2f8df`, including its pre-existing uncommitted Phase 10.1 proposal. Its full file-content/mode checkpoint and existing backup checksums are checked after work; no original configuration, reference asset, history or running database is changed.
- A fresh independent clone was filtered using pinned git-filter-repo 2.47.0. Both author and committer use the approved noreply identity. Exact documented private home/source prefixes and the former address were removed from historical text/messages. A known derived author fingerprint was also tested for absence; it existed in an older private audit artifact, not in the final publication history.
- Five reference paths and all their known image blob IDs were excluded from every commit: three `docs/design-references/brand-slide-0*.png` slides and `docs/qa-references/hero-overlap.png`, `russian-steps-alignment.png`. Their original files/backups are retained privately; missing images cannot be recovered from this copy's reachable objects.
- All **18 original milestone commits** survive in their original order with messages, author/committer dates and parent relationships preserved. All IDs changed through the identity rewrite. [Commit map](commit-map.tsv) records old→new provenance; old IDs in historical reports are not reachable commits in this copy. No original branch/tag/backup ref is retained here.
- Before adding these documentation updates, every remaining HEAD file was byte-identical to the original. Application/auth/scanner/network controls, migrations, dependency locks, catalogs, fonts, visual styles, tests and CI remain unchanged. Current documentation now identifies privately retained references and the separate ownership/upload gate. The original Phase 10.1 proposal is retained as historical context.

The approved noreply identity and existing team attribution are intentionally present: this is not an anonymous repository. Checks specifically cover the former personal email, documented identifying paths, derived fingerprint and excluded image data. They do not establish consent for other people's names or grant publication rights.

## Verification and limits

Read-only checks enumerate every reachable commit/tree/blob and compare the original lineage through the commit map. They require the former address/private prefixes and known removed image/commit object IDs to be absent, every author/committer email to match the approved identity, no additional refs/remotes, and a valid Git object graph. Git fsck, Gitleaks history/tree scans, clean-checkout builds/regressions and Docker verification are recorded in the final evidence summary.

Gitleaks 8.30.1 default rules report two reviewed false positives: an intentionally incomplete INTERNAL scanner-test key marker and ordinary architecture prose in `PROMPTS/PHASE_07.md`. Exit 10 is preserved as a finding result; no blanket allowlist or zero-finding claim is used. Raw scanner logs stay outside Git because they include metadata. Binary extraction/OCR limitations from Phase 10 remain; no scanner proves total privacy, ownership or security.

Only local technical checks are performed. Hosted Actions, independent legal/native-language review, live owned-domain external E2E and human Phase 09 H13–H18 remain pending. Neither a private visibility choice nor removal of reference images grants rights over the remaining project. Original verified backups are private, unencrypted same-host copies; they are not for upload or a substitute for offline disaster recovery.

## Connecting an empty private repository — only after approval

Stop until permission for the remaining project and the exact GitHub repository name/private visibility/upload are approved. No owner/name is invented beyond the user-supplied account identity. If the repository already exists, verify its ownership, empty state, private visibility and intended audience first; do not create/delete/overwrite a remote automatically.

In this sanitized copy, `origin` is intentionally absent. After approval, use the **exact approved empty private URL**:

```sh
: "${APPROVED_PRIVATE_URL:?explicitly approved empty private GitHub URL required}"
# Verify PRIVATE visibility, correct owner/name and no existing refs before continuing.
test -z "$(git remote)"
git remote add origin "$APPROVED_PRIVATE_URL"
git remote get-url origin
git -c push.followTags=false push --set-upstream origin refs/heads/main:refs/heads/main
```

Do not embed credentials in URLs, push original history/bundles, use --mirror/--all/--tags/force or publish releases. Prefer a freshly audited no-hardlink transport clone of this sanitized main branch for actual upload. Independently clone/audit the remote and inspect real Actions results afterward. Public visibility/release/deployment require separate approval.

## Final local verification results

- Working sanitized copy: **325 backend tests passed (66.60s)**, **101 frontend tests**, **55 tooling tests**, **3 Node configuration tests**. Ruff/format/mypy, ESLint/TypeScript/format,976×3 localization keys, production build and actionlint pass. Dependency audits: 68 Python packages/347 npm dependency records, zero known advisories. Existing Starlette/httpx deprecation and JS chunk-size warnings remain.
- Independent clean checkout of the documentation candidate: locked fresh dependencies, **325 backend tests passed (67.09s)**, **101 frontend tests**, **55 tooling tests**, **3 Node tests**, full static/catalog/build checks and frozen research scenario pass. Migration head `f34f9df9b6a4`, no schema drift.
- Clean Docker build and startup passed on isolated localhost 16273 with fresh volumes. Actual Chromium check: **12 views** (EN/RU/KK×360/768/1280/1920), zero axe violations,overflow or page errors; private login redirect/401 protection and **3 DEMO PDFs /18 marked pages** pass. The inherited browser helper writes to its fixed sibling work location; copied actual outputs were used for PDF inspection after correcting an inspection-path assumption. No app code or quotas changed.
- All **1,075 retained image blobs and 37 PDF blobs** are byte-identical to items in the prior full OCR/text extraction inventory; the five excluded image blobs are absent even from physically stored objects. No new exhaustive OCR or independent privacy/legal certification is claimed. Exact-byte privacy scans cover all reachable object types, including commit metadata/messages and historical blob bytes.
- Original repository checkpoint: **20,764 files/symlinks**, contents/modes/targets and original Git state match. Existing verified backup checksums match. No original tracked, untracked or ignored content was changed. The original remains at `ce2f8df`; the existing Phase 10.1 untracked review package remains untouched.

[Evidence summary](sanitization-evidence/summary.json), [object/privacy verification](sanitization-evidence/current-privacy-verification.json), [original preservation](sanitization-evidence/original-preservation.json), [clean-checkout command results](sanitization-evidence/clean-verification.json), [Gitleaks review](sanitization-evidence/gitleaks-reviewed.json), [PDF checks](sanitization-evidence/pdf-verification.json).

The final commit containing this report adds verification records and documentation only. All original milestone hashes map through `commit-map.tsv`; subsequent documentation commits use the approved noreply identity. Final clean Git/fsck/privacy checks are repeated after committing. No remote is configured. The isolated test containers are stopped with volumes retained; the original localhost 8080 app is left running unchanged.
