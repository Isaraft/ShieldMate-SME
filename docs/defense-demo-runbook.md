# University defense rehearsal — 5–8 minutes

Use the localhost release at <http://127.0.0.1:8080>. Start/check it with `local-release-runbook.md`. Open EN, RU and KK PDFs ahead of time. Rehearse in a dedicated browser profile so parallel QA cookies do not overwrite the session. This is a university-stage MVP, not an independently certified assessment or a penetration-test service.

## Honest presentation sequence

| Time | Action | Explanation |
|---|---|---|
| 0:00–0:45 | Landing page; switch English / Русский / Қазақша | Risk-to-action for small teams; bounded external configuration checks, no safety guarantee. Burgundy/red identity and three-language support. |
| 0:45–1:30 | Register, sign in, create a company workspace | Real persistent account/session/tenant; no password reset, billing or multi-member roles. Use a fresh account only if needed; real auth quotas apply. |
| 1:30–2:30 | Add a domain **only if authorized**, acknowledge scope, show TXT challenge | Proof applies to that exact hostname. Pending/expired ownership cannot be scanned. Never demonstrate an arbitrary university/business domain without its owner's permission. |
| 2:30–3:30 | Verify TXT and enqueue a bounded scan, or switch to the labeled fixture/demo fallback | Real owned-domain propagation can take longer than a defense. Explain queued/running/partial/failed states honestly. Do not claim that fixture evidence was collected externally. |
| 3:30–4:45 | Dashboard Top 3 → finding → technical observations | Ranking comes from the shared deterministic engine; evidence IDs, timestamps, scope and limitations are visible. No fabricated CVEs or numerical safety score. |
| 4:45–5:45 | Create/open task; owner label, note, status done; reload | Work persists with history. **Task done does not resolve the finding**; a later conclusive observation must confirm technical resolution. |
| 5:45–6:45 | Reports → save/download snapshot; EN/RU/KK samples | Server-produced immutable PDF from persisted authorized observations. Scope/exclusions and evidence inventory remain visible. Private notes are omitted. |
| 6:45–7:30 | Logout; private route redirects; explain tested recovery | Session revoked, other tab cleared, IDOR/CSRF tests, online backup/isolated restore. Avoid calling tests a guarantee of internet-exposure security. |

## Safe offline fallback

Public `/demo` is fictional, read-only and marked DEMO in the UI and on every PDF page. Its four interactive steps and EN/RU/KK PDF exports require no account or target traffic. It does not create company records or run scanners.

For a complete interactive saved-work demonstration use the separate **LOCAL QA** stack at port 15873, built with `scripts/qa/phase08.override.yaml`. It injects DNS TXT and socket responses, while registration, cookies, authorization, queue persistence, finding reconciliation, task updates, and PDF generation use the real application. Present its organization names, screenshots and reports explicitly as synthetic. The override is not present in the normal RC. The QA run has consumed some scan/report quotas; prefer existing saved histories rather than bypassing limits. Never copy synthetic evidence into an actual company workspace.

The automated Phase 08 rehearsal exercises the complete browser journey and actual SIGKILL/lease recovery. A second human presenter/university rehearsal has **not** been performed; follow this checklist before the defense. Live owned-domain DNS TXT plus external TLS/HTTPS E2E is **NOT TESTED** in Phase 08 because no authorized real target was supplied. External Safari/Firefox/Edge and assistive-technology testing are also **NOT TESTED**.

## Evidence and recovery

- `docs/evidence/phase-08/checks/workflow.json`: actual workflow assertions/browser version.
- `docs/evidence/phase-08/checks/browser-matrix.json`: widths 360, 390, 768, 1024, 1280, 1440, 1920 × EN/RU/KK.
- `docs/evidence/phase-08/screenshots/`: real screenshots, including task done/finding open and restored task.
- `docs/evidence/phase-08/pdfs/`: short, long, edge and DEMO samples in each language; all fictional.
- `docs/evidence/phase-08/pdf-pages/`: every rasterized page and review sheets.
- `docs/evidence/phase-08/checks/operations.json`: consistent backup/restore manifests.

If Docker is down, restart the matching project and check readiness. If a scan was interrupted, show its retained partial evidence and interrupted label; do not repeatedly requeue it. If DNS is slow or the network fails, use Sample Demo or already saved LOCAL QA history. PDF files and screenshots are a clearly labeled last-resort presentation aid, not proof of a fresh scan. Do not start a tunnel or publish the application for the defense without separate approval.

Before any external exposure: obtain an authorized owned target and run the real TXT/TLS journey; obtain independent native RU/KK language review; test supported external browsers/assistive tools; plan HTTPS/proxy/cookie/origin settings, OS/container egress restrictions, operator backup encryption/retention and monitoring. No Phase 09 work is authorized by this runbook.
