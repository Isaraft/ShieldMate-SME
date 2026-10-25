# Phase 10 publication audit — upload blocked pending decisions

Baseline: clean `main` at `8040755`, 13 reachable commits, only `refs/heads/main`, no tags/remote refs/remotes. No upload, remote creation, tag/release, history rewrite, author rewrite, ref deletion or credential rotation was performed. See [results](phase-10-results.md) for final local commits and reproducible checks.

## Read-only methods and scope

The standard-library [audit tool](../scripts/publication/audit.py) enumerates `git rev-list --all`, `rev-list --objects --all`, all commit trees/aliases via `ls-tree -rz`, and every unique blob via `cat-file --batch`. It scans current tracked bytes separately. Baseline: **2,019 objects, 1,766 blobs, 151,027,426 blob bytes**, including 1,051 unique PNG, 29 JPEG, 37 PDF and four other binary objects. History is scanned regardless of deletion/renaming. Only .env.example and .env.local.example match risky historical path rules; no committed SQLite magic/database, real .env, browser storage-state or participant-storage tree was found. Modes are ordinary Git regular-file modes; no historical symlink/submodule was found.

`gitleaks` is unavailable and was **NOT RUN**. The alternative detects private-key/cloud/GitHub/Slack/OpenAI signatures, credential-bearing URLs, quoted credential literals, Argon2 hashes, JWT/cookie/auth-header forms, emails, DNS challenge literals and personal home paths; output contains categories/locations/object IDs, never matched bytes. Focused tests prove deleted-history and alias coverage and redacted output with internal markers. This is not equivalent to every established secret detector, entropy scan or credential validity check. Unreachable/reflog-only objects, ignored operator databases and private research folders are outside upload history and were not ingested. No absence-of-all-secrets claim is made.

PDF text extraction and image OCR cover reachable unique binary objects separately. OCR is heuristic, not a privacy guarantee or a substitute for native-language/manual review. No raw extracted/OCR text, actual author email, secret value or ignored runtime evidence is committed. Redacted reports inventory exact outcomes and failures. Existing screenshots were checked against synthetic fixture source and phase labels; README selects two known developer captures with LOCAL QA/DEMO context.

## Classified findings and required action

| ID | Category / affected paths or commits | Result / disposition |
|---|---|---|
| P01 | Personal author/committer metadata throughout initial 13 commits | **BLOCKED pending author's explicit consent.** One identity includes a personal email; value withheld. Choosing a no-reply email for future commits does not remove earlier metadata. Do not rewrite without separate approval. |
| P02 | Supplied `docs/design-references/brand-slide-0{1,2,3}.png`, introduced at `60c1b2b` | **BLOCKED:** provenance/redistribution rights unconfirmed. Retain locally; obtain permission or approve removal from an alternative publication history. Deleting HEAD files alone would not solve exposure. No incompatible license is asserted without evidence. |
| P03 | Team names/contributions in supplied specification and research mapping; supplied QA-reference images | **BLOCKED pending team publication/privacy/IP approval.** The first supplied slide also contains an instructor name (value withheld). Names are intentional attribution, not evidence of contribution ownership/consent. No license selected or ownership assigned. |
| P04 | Personal checkout/home prefixes in 19 current documentation/log files; earlier versions remain reachable | Current text prefixes replaced with portable placeholders, outcomes retained. **Historical exposure remains BLOCKED pending consent/remediation decision.** Redaction manifest lists paths only; no destructive rewrite. |
| P05 | Credential-bearing URL candidates in config/network tests; email candidates in backend/frontend tests and QA scripts; challenge literal in Assets test | Inspected UI labels and synthetic rejection/auth fixtures using reserved names, not operator credentials. No matching real credential or active external challenge confirmed. Test passwords/markers have no external identity/service access. No rotation indicated from these fixture matches alone. |
| P06 | Engineering screenshot/PDF/domain/resource IDs | Artifact and source-provenance review identifies QA/DEMO/reserved-domain material, not customer/participant evidence. OCR/manual limits remain explicit; independent final binary review required before publication. Any newly identified private artifact is a hard stop. |
| P07 | Historical `.env`/storage/backups/hash/session patterns | Only intentionally safe example environment files found; no real DB/key/cookie storage artifact confirmed by targeted scan. High-confidence scanner absence/heuristic limits prevent a universal clean guarantee. |

No actual leaked credential requiring rotation was confirmed in this review. If a real secret is later identified, stop all uploads (including private), rotate/revoke at the source and agree a history-remediation strategy before proceeding. Private visibility is not sufficient remediation. Do not run filter-repo/BFG/gc/rebase/force-push or delete refs under this phase's authorization.

## Supply chain and rights

See [third-party notices](../THIRD_PARTY_NOTICES.md): web-font OFL notices are shipped; print derivative source hashes, renamed internal family and OFL are recorded. npm lock inventory and installed Python metadata contain license declarations; no license was chosen for the project. Mutable Docker base tags and complete-image dependencies are not cleared by app package audits. No new fonts/images/dependencies were added.

Official GitHub action release SHAs were resolved read-only from their source repositories. Workflow permissions are `contents: read`, checkout credential persistence is disabled, action references are immutable, jobs have timeouts, no privileged PR target workflow, secrets, deployment, write permission or artifact upload is configured. Advisory checks require package network access; no real owned target/participant/private instructor resource is required.

## Publication decision

**Local preparation can complete; first private push and public publication are NOT CLEARED.** Resolve P01–P04 and final binary-review limits, confirm team/IP/license decisions, then approve the exact GitHub account/repository name/private visibility. Only after that approval should a private repository be created/pushed and independently re-audited. Public visibility needs separate explicit approval. There is currently no `origin` to change and no GitHub URL to advertise.
