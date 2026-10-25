# ShieldMate Phase 09 — local evidence kit

**ENGINEERING READINESS ≠ HUMAN TESTING.** Human alpha/beta sessions are **NOT CONDUCTED**. Templates contain headers/blank fields only. No recruitment, interviews, answers, dates, timings, quotations, adoption or conclusions are generated. The standard-library CLI validates declared records and file integrity; it cannot authenticate people, verify consent truth, replace a moderator or certify translation quality.

Start with `alpha-plan.md`, `beta-protocol.md`, `assignment-05-mapping.md` and `defense-checklist.md`. Participant-facing invitations/consent/tasks/six questions are in `materials/participant-{en,ru,kk}.md`; internal alpha instructions have matching `alpha-task-sheet-{en,ru,kk}.md`. All language drafts require independent native-speaker review. The CSV/CLI uses stable English machine codes; moderators use the participant's chosen language.

## Safe workflow

1. Agree team responsibilities and actual eligible recruitment. Confirm local lecturer/LMS access expectations. Do not send invitations from this tool.
2. Check/freeze the scenario with `python scripts/research_evidence.py scenario`. Moderator-only `scenario.json` contains the answer key; **do not show it to participants**. Its SHA256 covers rubric, protocol, fixed fixture, demo UI/catalog and three participant-wording hashes. Use one clean committed application build per beta analysis; mixed builds are rejected.
3. Initialize a **new** ignored local folder (Python3.13+, no packages/network needed):

```sh
python scripts/research_evidence.py init research-private/phase09
```

Within the repository, init refuses destinations outside the ignored `research-private/` boundary. It creates 0700 folders and 0600 header-only CSVs/declaration, refuses existing directories/files, and never deletes anything. `/research-private/` is Git-ignored. Do not move raw evidence outside that boundary or `git add -f` it. Local OS permissions are not encryption; restrict device/backup access and arrange approved retention.

4. Complete the private `study-declaration.json`: actual adoption time if adopted **before trials**, custodian moderator code, agreed deletion date in Asia/Almaty, and actual aggregate count of removed started withdrawals (0 only if none). Until adopted, state remains PROPOSED; no confirmation may be claimed. Five is a proposed planning minimum, not an Assignment 5 mandate.
5. Take consent before collecting observations. Use anonymous codes and the note template. Record only actual first attempts, measured times, observed errors and consented feedback. Keep any contact/code mapping separate; never ask for passwords/company secrets. Use a fresh guest `/demo` context for beta; no real-domain authorization or account is required. Actual alpha mutations belong in separate synthetic QA.
6. Put notes/media in the private folder. Hash **existing consented files**; the command does not create or validate their historical authenticity:

```sh
python scripts/research_evidence.py hash research-private/phase09/notes/B01-01.md
```

Add a real manifest row with relative path, actual capture time, classification, owner/session, kind, consent review, redaction status and returned digest. Every started nonwithdrawn beta trial needs its own dated notes reference. Hashes change if redaction/editing changes bytes; create a new reviewed redacted artifact and manifest entry, do not pretend it is the original.

7. Validate/compute from filled-in records:

```sh
python scripts/research_evidence.py alpha --csv research-private/phase09/alpha-results.csv --manifest research-private/phase09/evidence-manifest.csv --evidence-root research-private/phase09
python scripts/research_evidence.py beta --csv research-private/phase09/beta-results.csv --manifest research-private/phase09/evidence-manifest.csv --evidence-root research-private/phase09 --study research-private/phase09/study-declaration.json
python scripts/research_evidence.py beta --csv research-private/phase09/beta-results.csv --manifest research-private/phase09/evidence-manifest.csv --evidence-root research-private/phase09 --study research-private/phase09/study-declaration.json --format markdown --output research-private/phase09/summary-01.md
```

Use a **separate manifest per alpha/beta CSV**, containing only sessions in that input. Duplicate the blank manifest under descriptive filenames before recording both studies; the commands above illustrate one study at a time. Unknown/withdrawn owners are rejected, not silently ignored. Output is aggregate-only and refuses overwrite. Empty beta gives **NO REAL BETA RESULTS YET**, null percentage and pending criterion; empty alpha gives **NO HUMAN ALPHA SESSIONS CONDUCTED**. These are not 0% findings or passes. JSON and Markdown retain n/N, dispositions and explicit withdrawal sensitivity. Missing values are not imputed.

8. A team member checks raw observations, eligibility, consent, grading, clock handling, duplicates and omissions. The proposed threshold is assessed only with adopted-before-testing declaration and planned N≥5; sample limitations remain. Code cannot turn a declared record into verified human evidence. Exact quotations and qualitative themes are selected/interpreted by the team, not generated by the CLI.
9. Manually redact submission-safe evidence: remove identifiers, browser profiles, contacts, account emails, tabs, secrets, real asset names and unrelated content; inspect every pixel/text layer. Cropping/blur alone may miss text/metadata. Retain only permission-approved, explicitly labeled proof; use a new manifest entry/hash and a team redaction signoff. No automatic sanitizer claims to remove every private detail. Do not publish/upload anything automatically. Before sharing through LMS, confirm participant permission and lecturer audience.
10. On withdrawal, stop using responses/media. The team removes relevant data as agreed; the tool does not purge files. Retain only permitted minimal disposition or anonymous aggregate count, disclose exclusion and conservative bound, and avoid double counting. Delete backups/copies under the agreed retention procedure too. The CLI blocks beta processing after the declared local retention date; alpha retention must also be checked manually against consent notes. Never silently purge pre-existing files.

## Stable CSV contract

UTF-8 (optional BOM), comma-delimited, exact header/order; no extra identity/contact/password/free-answer columns. Use decimal point seconds, not locale decimal commas; booleans are `yes|no`. ISO timestamps require `T` and explicit offset, e.g. the actual observed time in `+05:00` (do not copy an example as evidence). Build is the actual Git commit, 7–40 lowercase hex digits. IDs identify records, not real people automatically. At most5000 rows /2MB per CSV; artifacts≤128MB, confined relative paths, no symlinks or URL reads. Errors never echo responses or OS paths. Retention dates are YYYY-MM-DD in the team's agreed Asia/Almaty context.

### Beta columns

| Columns | Meaning / allowed values |
|---|---|
| evidence_class | `HUMAN_BETA` only in real mode; `INTERNAL_TEST_DATA` only with explicit test flag |
| participant_id, session_id | B +2–4 digits; session is that code + `-` +2 digits. One primary record per person/code; follow-ups are separate, not best-attempt replacement |
| local_datetime, language, moderator_code | Actual session time with offset; `en|ru|kk`; M +2–4 digits |
| role_segment, target_eligible, relationship, eligibility_reason | `sme_owner|operations|it_generalist|outsourced_it|other`; yes/no; `team|close|other`; `sme_decision_responsibility|not_target|team_member|declined_screening`. Team members cannot be eligible beta; genuine nonteam target friends are disclosed |
| familiarity | `none|some|regular`, self-described |
| consent, screenshot_consent, audio_consent, quote_consent | Core `yes|no|withdrawn`; media/quote independent yes/no. Withdrawal/decline requires no retained answers/media references |
| scenario_id, scenario_sha256, build_id | Frozen study version, **complete scenario-definition file** hash (not just fixture), actual app build |
| session_status, primary_started | `completed|incomplete|aborted|withdrawn|declined|not_started`; yes/no. This column records the primary-trial disposition; started incomplete/aborted stays in denominator. Skipping later optional tasks does not undo a completed primary answer |
| timing_method, protocol_variant | `monotonic|manual_stopwatch|not_recorded`; `standard|accessible` (no medical details) |
| elapsed_seconds, paused, hint_given | Observed finite nonnegative seconds (≤86400 input sanity bound), pause yes/no, hint yes/no (primary task only). Pauses/timing also refer to the primary task. Completed trial needs time; unknown time blank; pause/hint/time>120 cannot succeed |
| top_issue_correct, next_action_correct | Human rubric decisions yes/no, both required for completed trial; unknown remains blank in incomplete/aborted |
| evidence_navigation_unaided, done_vs_resolved_correct | Observed secondary yes/no; unknown or skipped stays blank, including after a completed primary task |
| clarity_rating, usefulness_rating, error_count | Optional ratings1–5; observed nonnegative integer errors or blank. No inferred ratings/errors |
| notes_evidence_id | Existing own-session `E` +3–6 digits notes entry; blank for withdrawn/declined/not_started |

### Alpha and manifest columns

Alpha: `evidence_class` = HUMAN_ALPHA or AUTOMATED_ENGINEERING (never interchangeable); `tester_code` = A-code or AUTOMATION; `session_id`, `local_datetime`, `language`, `build_id`, `scenario_id=shieldmate-alpha-1`, `environment=localhost_rc|isolated_qa|public_demo`, `data_context=real_authorized|synthetic|not_applicable`, `check_id=AL01..AL08`, core/media/quote consent, `result=PASS|FAIL|NOT_TESTED`, severity/issue reference and manifest `evidence_id`. Automated consent is `not_applicable`, media flags no. Failures need severity and actual issue reference; retests keep a separate session. Repeated session identity/consent must agree. Human sessions and distinct testers are reported separately from automation.

Manifest: `evidence_id`, `evidence_class`, `participant_id`, `session_id`, `kind=notes|screenshot|survey|audio|quote|engineering_log`, `captured_at`, `relative_path`, `sha256`, `redaction_status=private_raw|redacted`. Engineering logs cannot impersonate human notes. Human media/quotes require corresponding separate consent **before file contents are hashed**. Human artifact roots must be private; use init-created folders. Human inputs inside this checkout are accepted only under ignored `research-private/`. A redacted flag is a team declaration, not automatic proof of successful redaction.

## Tool tests and integrity boundary

```sh
backend/.venv/bin/pytest scripts/tests -q
backend/.venv/bin/mypy --strict scripts/research scripts/research_evidence.py
backend/.venv/bin/ruff check --config backend/pyproject.toml scripts/research scripts/research_evidence.py scripts/tests
```

The tests use temporary **INTERNAL TEST DATA**, synthetic IDs and timing constants solely to exercise calculations. `--internal-test-data` rejects human-classified rows, labels output INTERNAL TEST ONLY, and cannot produce a real human criterion result. Real mode rejects test-classified rows. Neither mode generates participant rows or answers. Do not copy unit fixtures, automation logs, seed screenshots or old discovery interviews into human records. No network calls, new application APIs, analytics SDKs, dependencies or database migrations are added for this kit.
