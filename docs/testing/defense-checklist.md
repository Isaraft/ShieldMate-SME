# Lecturer-friendly local defense checklist

**Engineering demonstration only until real sessions are collected.** Confirm in-person/localhost acceptance with the lecturer; this URL cannot be opened remotely from another computer. No tunnel/public deployment is configured. Report/slides must be PDFs, prototype URL is a separate LMS field;≤10 slides,3–6 genuine prototype screenshots. Final academic report, human appendix and individual contributions remain team work.

## Before the appointment

- Agree the actual deadline, group/member names, audience and who operates the machine. Confirm local presentation is accepted or request a separate authorized access plan.
- Open terminal in the ShieldMate repository. Run:

```sh
docker compose -f compose.local.yaml up --build -d --wait
curl --fail http://127.0.0.1:8080/api/v1/health/ready
```

Expected: `{"status":"ready"}`. Open <http://127.0.0.1:8080>. A technician can use `local-environment.md` / `../local-release-runbook.md` if startup fails. No need to edit ports or disable security controls.
- Use a fresh guest browser for public demo/research, not the operator's real authenticated workspace. Check EN/RU/KK and keyboard/text size. Have the fixed scenario/rubric version recorded privately; do not show answer key to a timed participant.
- Open the saved **DEMO** PDFs in all languages and select3–6 actual screenshots with captions. They demonstrate product behavior and synthetic data; they are not participant evidence. Check every chosen page/image, marker and redaction permission.
- If displaying actual alpha/beta results, first validate the real records and appendix permissions. Otherwise show “NOT CONDUCTED / PENDING MANUAL EVIDENCE”; do not substitute this phase's automated tests.

## Click path — adaptable proposed5–8 minute rehearsal, not a recorded duration

1. Landing: explain SME risk-to-action purpose and bounded scope. Switch language using native names.
2. **Sample Demo**: show persistent synthetic/read-only notice and fixed date. It requires no account/company secrets and makes no external scan.
3. Findings/priorities step: explain Top1, next action and expand technical evidence. No fabricated safety score/CVE or live-date claim.
4. Example work: show todo/in-progress/done examples. Done does not prove technical resolution. This public page does not edit tasks.
5. Sample report: download/open actual PDF; show DEMO on pages, scope, observation dates and limitations. Inspect one page in Russian/Kazakh too.
6. If full private functionality is being demonstrated, a technician opens a **separate synthetic QA workspace**, labeled LOCAL QA, to show real persisted task edit/reload/history and report history. Keep its synthetic network answers explicit. Never use another company's data or remove labels.
7. Explain actual engineering checks and remaining manual research/live-owned-domain limits. Show real human results only after collected/consented; acknowledge uncertainty and sample size.

## If something fails

- Page/network error: stop the timer if a session is underway and record aborted/not_started honestly. Refresh/restart readiness with technician support. Do not replace first trial with a later success.
- DNS/provider unavailable: use marked Sample Demo. A live authorized asset remains NOT TESTED; do not invent TXT proof or try an unrelated domain.
- PDF unavailable: show a saved marked sample, explicitly say it is saved; do not call it a fresh generation. Technician checks logs/space and retries safely.
- Docker unavailable: disclose the interruption and use labeled screenshots/PDFs as an explanatory fallback. A screenshot is not a working live demonstration; rearrange the live portion with the lecturer.
- Privacy/security issue: stop, close participant context, preserve only consented private evidence, contact the human team, repair and regress before resuming. Do not bypass controls.

Afterward, close guest contexts, retain only agreed consented artifacts, perform scheduled manual deletion/backup cleanup, and record actual contributions/Q&A notes. Do not claim a second human rehearsal or lecturer approval unless it happened.
