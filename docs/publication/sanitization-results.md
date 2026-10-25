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
