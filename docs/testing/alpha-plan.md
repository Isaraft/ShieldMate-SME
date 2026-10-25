# Alpha plan — shieldmate-alpha-1

**HUMAN ALPHA: NOT CONDUCTED.** Engineering automation is recorded separately in the Phase 09 report; it does not fill the human result cells below. The specification proposes at least three structured internal sessions; Assignment 5 specifies internal/close-to-team testers but does not prescribe that number. Confirm the team plan before recruitment. Each genuine session gets an A-code and session ID, build, chosen language, exact environment, consent and local timestamp with UTC offset.

Use the translated participant consent explanation plus the matching `materials/alpha-task-sheet-*.md`. Populate `alpha-results-template.csv` only after actual observation. Record one row per check/session; link dated notes and, if separately consented, media in the manifest. Never save passwords, actual challenge tokens or sensitive business details. Do not put human artifacts in Git. Copy this checklist into a private note before testing; blank cells intentionally await real evidence.

| ID | Steps | Expected behavior | Actual observation | Severity / issue | Evidence ID/file | Tester code | Local date/time |
|---|---|---|---|---|---|---|---|
| AL01 | Start compiled local release; check readiness; sign in/create a disposable company; reload; restart services using runbook | Loopback8080 only; real session/company persist; no Vite or public tunnel; errors safe | | | | | |
| AL02 | Add an explicitly authorized domain; acknowledge scope; inspect current DNS TXT instructions. Publish/check TXT **only with owner permission** | Exact current challenge, expiry and consent required. Unverified/private/expired assets cannot run. Without a supplied real domain record live proof **NOT TESTED** | | | | | |
| AL03 | In a separately named QA project, use the existing injected DNS/socket harness; enqueue and inspect stored progress/observations. In normal release show public DEMO separately | QA data is visibly synthetic; real queue/persistence/worker, no arbitrary target; no fixture in normal image or live-assessment claim | | | | | |
| AL04 | Open dashboard/findings; compare Top 3 and evidence IDs; inspect severity explanation and a partial/inconclusive source | Shared deterministic ranking, usable provenance; errors/absence never imply secure; fixed demo Top 1 matches frozen rubric | | | | | |
| AL05 | In isolated QA create/open a task, edit owner label/note/status, save, reload; inspect activity. Mark Done; inspect original finding | Task changes/history persist; Done alone does not resolve technical finding; version conflict handled. Public demo remains read-only | | | | | |
| AL06 | Generate/download EN/RU/KK report in isolated QA; open actual PDF pages; compare hash/history; open DEMO export separately | Readable glyphs/tables/labels; QA/DEMO context intact, private tenant access and immutable bytes; insufficient data stated honestly | | | | | |
| AL07 | Landing/private/demo at360/768/1280/1920; keyboard menu/dialog; switch language with an unsaved form; sign out across tabs; attempt foreign fixture IDs using approved harness | No overflow/overlap; visible focus; values retained for same identity; old tenant data cleared; server denies foreign resources | | | | | |
| AL08 | Clean start in a **new disposable project**; readiness; restart; online backup; restore into a new volume; check saved accounts/assets/scans/findings/tasks/PDF hashes | Existing valuable volumes untouched; private files; source/restore consistent; failed migration never starts HTTP; recovery stays truthful | | | | | |

## Environment and safety

Default human beta uses the public read-only demo. Full-function alpha may use a fresh isolated QA project, **not a shared company workspace**. Existing `scripts/qa/phase08.override.yaml` supplies synthetic TXT/socket responses and is absent from release images. Use `local-environment.md`; do not relax CSRF/Host/CORS/cookies/network validation or raise quotas to make a session succeed. The real scanner is never used on an unverified/third-party target. Existing Phase 08 risk register remains applicable.

Record `environment=public_demo|isolated_qa|localhost_rc`, `data_context=synthetic|real_authorized|not_applicable`. QA/demo must be synthetic. AL02's real target can remain NOT_TESTED without pretending fixture TXT is live proof. A missing real target is a known limitation, not a bug to disguise.

## Defect triage and retest

Use `issue-template.md`: actual steps/build/environment/language/viewport, expected vs observed, consented redacted evidence, severity and owner decision. Critical/high security or data-isolation issues stop testing; preserve private evidence, isolate service, repair and regress before resuming. Medium workflow failures are fixed before beta if reproducible; low cosmetic issues are logged honestly. Do not silently replace a failed first observation with a passing retest. Give the retest a separate session ID and link the issue/build. No discovered-human-defect claims may be made without real notes.

A participant may stop. Keep only consented minimal notes and disposition, follow withdrawal/deletion agreement, and record missing evidence explicitly. Do not publish raw audio/screenshots or confidential content. Automated fixtures may prefill **AUTOMATED_ENGINEERING** rows in a separate engineering ledger, with `tester_code=AUTOMATION`; the CLI never counts them as human alpha sessions.
