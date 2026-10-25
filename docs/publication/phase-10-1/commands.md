> Historical Phase 10.1 proposal, retained for provenance. Clone-only sanitization was subsequently approved and completed; see [current sanitization status](../sanitization-results.md). Upload permission is still pending.

# Proposed command procedure — NOT EXECUTED

These blocks are a reviewable procedure, **not authorization**. Do not run history filtering, account configuration or GitHub mutations until the human decisions in README.md are approved. All variable values below are operator-selected placeholders; no identity, private source path or GitHub owner/name is guessed.

## 1. Freeze the approved baseline and verify private backup

Keep this original repository intact. Current source HEAD is `ce2f8df`; Phase10.1 documents are uncommitted. Decide whether to commit them under an approved noreply identity before making a candidate; if so, record the new approved source tip and create/verify an updated backup. Do not discard them or silently use a stale backup.

```sh
umask 077
: "${ORIGINAL:?absolute original repository path required}"
: "${BACKUP:?new private backup directory required}"
: "${SOURCE_TIP:?explicit approved source commit required}"
: "${POLICY:?private approved-policy directory required}"
: "${PUB:?new independent publication clone path required}"
test "$(git -C "$ORIGINAL" rev-parse HEAD)" = "$SOURCE_TIP"
test -z "$(git -C "$ORIGINAL" status --porcelain)"
test ! -e "$BACKUP"
mkdir -m 700 "$BACKUP"
git -C "$ORIGINAL" bundle create "$BACKUP/original.bundle" --all
git -C "$ORIGINAL" bundle verify "$BACKUP/original.bundle" > "$BACKUP/verify-private.log" 2>&1
git clone --no-checkout "$BACKUP/original.bundle" "$BACKUP/restore-check"
test "$(git -C "$BACKUP/restore-check" rev-parse HEAD)" = "$SOURCE_TIP"
git -C "$BACKUP/restore-check" fsck --full > "$BACKUP/fsck-private.log" 2>&1
```

Also archive the complete Git directory privately and compare every archived regular-file hash, as already demonstrated in this phase. Compare reachable object sets between original and restored clone; verify bundle/archive SHA256 and protect an independent offline copy. Bundle alone excludes reflogs/unreachable objects/local configuration. Neither Git backup includes live Docker volumes or ignored operator files: retain the original worktree and use the existing private SQLite backup runbook if protecting runtime data too. Do not upload any original bundle/archive/private policy.

## 2. Prepare policy privately; review exact diff scope

Before filtering, create/review these files in `$POLICY` with 0700 directory/0600 files:

- `exclude-paths.txt`: the **exact five lines** in `exclude-paths.proposed.txt`, or a newly approved list. No blanket application/localization/font/notice removal.
- `mailmap`: actual old identity read privately from the source and approved new display/noreply identity. Apply to author **and** committer; never print old values. Do not use a committed `.mailmap` to claim old commit objects are sanitized: it changes display, not stored metadata.
- `replacements.txt`: only approved literal private prefix/address replacements. Do not redact synthetic `/home/fixture`, reserved fixture emails or required upstream license contacts. Current source text is already home-redacted; historical versions need cleanup. `--replace-text` skips binary content: excluded slide/QA image copies must be removed by paths and any additional sensitive binary must stop the process.

Copy the exact noreply address shown in GitHub Settings → Emails; do not construct a guessed user ID. Modern format is `ID+USERNAME@users.noreply.github.com`; older accounts may differ. Noreply still identifies the chosen public account. Decide any remaining team/instructor attribution separately. No permission is inferred from an alias or a license label.

## 3. Clone-only filtering — requires separate explicit approval

Install a reviewed pinned git-filter-repo from its official source into isolated tooling after approval. Record version/source/checksum. **No --force, no working in the original checkout.** The filter tool may remove origin, expire reflogs, prune objects and invalidate signatures in this disposable copy; those are reasons the original/backup must remain untouched. Current baseline has no tags/signatures, but recheck if baseline changes.

```sh
: "${HISTORY_REWRITE_APPROVED:?STOP: human approval required}"
test "$HISTORY_REWRITE_APPROVED" = yes
test ! -e "$PUB"
git clone --no-local --single-branch --branch main "$ORIGINAL" "$PUB"
test "$(git -C "$PUB" rev-parse HEAD)" = "$SOURCE_TIP"
test "$(git -C "$PUB" rev-parse --absolute-git-dir)" != "$(git -C "$ORIGINAL" rev-parse --absolute-git-dir)"
git -C "$PUB" filter-repo \
  --invert-paths --paths-from-file "$POLICY/exclude-paths.txt" \
  --mailmap "$POLICY/mailmap" \
  --replace-text "$POLICY/replacements.txt" \
  --replace-message "$POLICY/replacements.txt" \
  --prune-empty never --prune-degenerate never \
  > "$POLICY/filter-private.log" 2>&1
```

Preserve/review `.git/filter-repo/commit-map` privately; require one mapped surviving commit per approved source milestone, same order/dates unless separately approved, and original repository HEAD/refs/object set unchanged. All author/committer rewrites change descendant hashes. An origin removal in **this clone** is expected; do not recreate a remote until upload approval. A sanitized child branch with old parents is insufficient.

## 4. Candidate documentation and future-author configuration

After identity approval, configure **locally in the publication clone**, not globally:

```sh
: "${APPROVED_NOREPLY:?copy exact address from GitHub Settings}"
: "${APPROVED_DISPLAY_NAME:?approved attribution required}"
git -C "$PUB" config --local user.email "$APPROVED_NOREPLY"
git -C "$PUB" config --local user.name "$APPROVED_DISPLAY_NAME"
git -C "$PUB" config --local user.useConfigOnly true
```

Separately choose whether to apply this to the original repository for future work. No original config is changed by this proposal. GitHub's “keep email private” and “block command line pushes that expose my email” are useful additional account options; they do not repair old commits.

In the candidate, update current AGENTS/README/architecture/reference-source notes so excluded images are described as retained privately, not broken public links. Retain approved team credit and third-party notices. Explain pre-publication phase hashes and commit-map provenance. Review legacy specs/prompts separately rather than pretending current features or academic results changed. Commit only reviewed documentation under the approved identity. No open-source license is required just to label an authorized private repository; grant reuse rights only after owners agree.

## 5. Mandatory candidate checks before GO

Capture outputs privately/redacted. Treat nonzero audit exits as findings requiring review, not automatic success. Do not feed the raw Gitleaks JSON into public artifacts: secret redaction does not strip author/email fields.

```sh
cd "$PUB"
git status --porcelain
git for-each-ref --format='%(refname)'
python scripts/publication/audit.py --output "$POLICY/candidate-history.json"
gitleaks git --log-opts='--all --full-history' --redact=100 \
  --report-format=json --report-path="$POLICY/candidate-gitleaks-private.json" --exit-code=10 .
gitleaks dir --redact=100 --report-format=json \
  --report-path="$POLICY/candidate-tree-private.json" --exit-code=10 .
```

Run the dir scan on a clean tracked-only checkout (before installing dependencies/creating runtime data). Review raw output privately, verify every author/committer email equals the approved noreply identity, and search **all unique reachable blobs** for exact old email/private prefixes and the five removed asset object IDs/aliases. Scan author/committer headers and commit/tag messages too. Re-run binary extraction/OCR and targeted manual privacy review; Gitleaks is not a PII/copyright scanner. Review future false positives individually; do not blanket-allow test or prompt folders. Verify no old/backup refs or original branch ancestry remains reachable in the candidate.

Compare runtime/security/migration/lock/catalog/font files byte-for-byte against the approved original, allowing only explicitly approved changes. Verify all private image paths are absent from every commit and originals still match backup hashes. Check current Markdown/image links after exclusion. Keep evidence-tool frozen files intact; `scenario` must match the approved definition.

```sh
cd "$PUB/backend"
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run alembic upgrade head
uv run alembic check
uv run pip-audit
cd "$PUB/frontend"
npm ci
npm test
npm run lint
npm run typecheck
npm run format:check
npm run i18n:check
npm run build
npm audit
cd "$PUB"
backend/.venv/bin/pytest scripts/tests -q
backend/.venv/bin/mypy --strict scripts/research scripts/research_evidence.py scripts/publication
node --test --test-reporter=tap scripts/tests/qa-runtime.test.cjs
python -S scripts/research_evidence.py scenario
actionlint -color=false .github/workflows/ci.yml
SHIELDMATE_RC_PORT=16273 docker compose -p shieldmate-publication-check -f compose.local.yaml up --build -d --wait
curl --fail http://127.0.0.1:16273/api/v1/health/ready
node scripts/verify-publication-smoke.cjs
SHIELDMATE_RC_PORT=16273 docker compose -p shieldmate-publication-check -f compose.local.yaml stop
```

Use free port 16273 and a fresh isolated project/volume; the optional browser requires installed Playwright Chromium/axe as in the testing guide. Do not touch valuable volumes or add `-v`. Check real session/CSRF/tenant and scanner fixture regressions, three-language PDFs/demo isolation, build-context privacy and backup/restore behavior as in Phase10/08 runbooks. Live external owned-domain checks remain separately NOT TESTED without authorization. Hosted Actions stays NOT TESTED until an actual approved upload and run. Document every failure/limitation honestly.

## 6. Fresh transport clone and approved private-first push

This stage is unexecuted and requires a **new explicit upload approval** after remediation. Confirm team/asset rights, metadata decisions, approved exact account/name/private visibility and a GO checklist. The approved source may remain all-rights-reserved; private storage does not waive ownership or third-party obligations.

```sh
: "${UPLOAD_APPROVED:?STOP: explicit upload approval required}"
test "$UPLOAD_APPROVED" = yes
: "${TRANSPORT:?new independent transport clone path required}"
: "${APPROVED_REPO:?exact approved OWNER/NAME required}"
test ! -e "$TRANSPORT"
git clone --no-local --single-branch --branch main "$PUB" "$TRANSPORT"
```

Re-audit the transport clone before any remote mutation: hashes/tree/commit map, all reachable refs/blobs/metadata, Gitleaks, no original ancestry/private data, and clean checkout. A local origin pointing at `$PUB` is expected from cloning. Inspect it privately; only with approval remove **that clone-local source remote** before adding the explicitly approved GitHub destination. Never change the original repository remote.

```sh
gh auth status
# MUTATES GITHUB: execute only under the explicit private-upload approval above.
gh repo create "$APPROVED_REPO" --private
test "$(gh repo view "$APPROVED_REPO" --json visibility --jq .visibility)" = PRIVATE
git -C "$TRANSPORT" remote remove origin
git -C "$TRANSPORT" remote add origin "https://github.com/${APPROVED_REPO}.git"
test "$(git -C "$TRANSPORT" remote get-url origin)" = "https://github.com/${APPROVED_REPO}.git"
git -C "$TRANSPORT" -c push.followTags=false push --set-upstream origin refs/heads/main:refs/heads/main
```

Do not upload to a pre-existing repository without re-review; do not overwrite origins, mirror, push all refs/tags, force, publish a release or change public visibility. If creation succeeds but a later check fails, stop and inspect rather than retrying blindly or deleting the remote. Verify GitHub owner/name/PRIVATE before push; authentication must use an approved helper, not embedded credentials.

After push, independently clone the private remote into a new directory, compare the exact intended reachable refs/objects and scan it again. Inspect hosted Actions, access/collaborators and settings; only then describe the private publication result. Public visibility, tags/releases, tunnels and deployment require separate approval. H13–H18 remain pending.
