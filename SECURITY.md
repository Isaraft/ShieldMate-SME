# Security policy

ShieldMate is a local university Starter MVP, not a certified security service. There is no published release, support SLA, official reporting email or enabled GitHub reporting channel yet.

## Report a suspected application bug privately

Do not place passwords, cookies, CSRF values, DNS challenges, company domains, private PDFs, database files, participant records or exploit payloads containing personal data in a public issue. Prepare a redacted report with affected build, expected/actual behavior, minimal reproducible steps, impact and synthetic evidence. Retain sensitive details privately until an authenticated maintainer agrees a secure channel.

If a future repository enables GitHub Private Vulnerability Reporting, use **Security → Report a vulnerability** there. This document does not claim that mechanism exists or is enabled. Otherwise arrange a private channel directly with the project team; no contact address is invented. Ordinary usability issues can be reported with synthetic examples once a repository/channel is approved.

## Authorized checks are a separate activity

Permission to report ShieldMate bugs does not authorize testing third-party assets, accessing another tenant, credential attacks, denial of service, exploitation or uploading real participant data. Use isolated local accounts and synthetic fixtures. Live checks require explicit authorization for the exact currently TXT-verified public hostname. Do not weaken SSRF policy, redirect restrictions or ownership controls to reproduce a finding.

## Current boundaries

Local HTTP cookies intentionally lack Secure only in validated development/local-release modes. Production requires HTTPS/Secure cookies and separate deployment design. Never expose the localhost profile through a tunnel or public bind. The API enforces organization scopes, session validity and CSRF; presentation switches are not permissions. Scanner errors/inconclusive results do not prove a target safe. Human task completion is distinct from evidence-backed resolution.

Dependency audits and regression tests are point-in-time checks, not guarantees. Real owned-domain external E2E, independent penetration testing, native-language validation, deployment-level egress policy, public TLS and distributed abuse controls are not certified or complete. See [scanner](docs/scanner.md), [risk register](docs/phase-08-risk-register.md), [backup/privacy runbook](docs/local-release-runbook.md) and [publication audit](docs/phase-10-publication-audit.md).
