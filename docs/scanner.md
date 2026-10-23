# Phase 04 scanner design and threat model

The Phase 04 implementation brief is preserved unchanged in `PROMPTS/PHASE_04.md`.
The starting tree was clean at `f7f33b2`. No architecture replacement or new dependency
was necessary. The brief explicitly permits an optional, bounded TCP 80 observation;
this supplements the original specification's HTTPS443 scope without adding other ports.

## Pipeline and trust boundaries

1. Cookie authentication derives the owner and organization. Start requires the existing
   exact Origin/session-bound CSRF check and accepts only an empty body, never a target.
2. A short SQLite `BEGIN IMMEDIATE` serializes eligibility, quotas, capacity and insertion.
   A unique partial index independently prevents two queued/running jobs for an asset.
3. The job snapshots exact canonical hostname, asset/org/requester IDs and proof generation/
   verified timestamp. Phase 03 consent policy and freshness rules remain authoritative:
   challenge expiration does not revoke an earlier still-fresh proof; rotation does.
4. One global DB worker slot claims the oldest queued job. Independent worker processes
   serialize claims through SQLite. Network work never holds a SQLite write transaction.
5. Before DNS, after acquiring the job, before every policy lookup, after resolving each
   destination and before requests/completion, the worker checks the current asset and proof.
   Deletion, policy/consent revocation, rotation or expiry fails closed. Already in-flight
   I/O cannot be retracted, but is bounded and grants no new authorization or final success.
6. DNS uses the OS-configured recursive resolver, UDP only, bounded deadline/count/bytes.
   Queries are exact A/AAAA, apex MX/TXT and `_dmarc.<exact-host>` TXT. No DKIM selector,
   SPF include traversal, MX-host probing, sibling/subdomain expansion or challenge queries.
7. Every HTTP/TLS connection freshly resolves A **and** AAAA. Any query error, alias,
   ambiguous answer, no address or any unsafe address blocks that connection. Mixed sets
   are rejected. One vetted numeric IP is selected; no fallback address amplification.
8. `socket.socket(...).connect((pinned_ip, 80|443))` never receives a hostname. The peer IP
   is compared to the pin. There is no general URL client, proxy discovery or hostname
   re-resolution by a HTTP library. Host and TLS SNI use the exact canonical domain.
9. `ssl.create_default_context()` keeps CERT_REQUIRED and hostname checking. No unverified
   retry exists. Certificate/hostname/chain failures prevent HTTPS observations. TLS evidence
   is committed before HTTP collection, so malformed HTTP cannot erase a valid handshake.
10. HEAD `/` uses an identifiable User-Agent and Connection: close. Only 405/501 permits one
    fresh, reauthorized/pinned GET `/` fallback. Reading stops at the header terminator:
    zero application body bytes are read or persisted, even if Content-Length is enormous.
11. No redirects are followed, including same-host redirects or loops. Location is parsed
    only into a safe scope category; no raw path/query/credentials are retained. HTTPS
    redirect destinations have inconclusive header observations and yield partial execution.
12. Each observation commits incrementally. Terminal status describes collection coverage,
    never overall site safety. Technical results feed a future phase; no finding/score exists.

## Network policy

`ipaddress` public classification plus explicit special-use checks rejects private,
loopback, link-local, multicast, reserved, unspecified, carrier-grade NAT, documentation
ranges, IPv4-mapped IPv6 (including mapped-public), 6to4, Teredo, known NAT64 prefixes,
and zone identifiers. Explicit exclusions also cover protocol-assignment ranges and the
Azure platform virtual endpoint 168.63.129.16, which can otherwise be classified public.
See [Microsoft’s platform-address documentation](https://learn.microsoft.com/en-us/azure/virtual-network/what-is-ip-address-168-63-129-16). Every returned A/AAAA address must pass, even if another is public.
IPv4 and IPv6 sockets connect numerically with correct address family. Numeric pinning
prevents DNS rebinding from switching a validated connection to a later private answer.
Tests replace getaddrinfo with a failure and assert the exact socket destination and SNI.
Direct transport calls independently reject noncanonical/unsafe hostname syntax.

DNS infrastructure is operator-configured and trusted; the resolver may itself be on a
private network. It is not a user-selectable probe destination. DNS queries may cause
ordinary recursive infrastructure traffic. Resolver answers are not DNSSEC-validated by
the application. Refusing CNAME chains is a deliberate fail-closed MVP limitation, so
many CDN/alias configurations will remain inconclusive. UDP truncation never falls back
to unbounded DNS/TCP. Operating-system routing, CA store and application runtime are trusted.
A malicious operator routing public IPs internally is outside application IP classification.
A deployment-level denylist/egress firewall remains a defense-in-depth prerequisite for a
later public deployment; the local bridge does not claim network namespace enforcement.

## Bounds and lifecycle

| Resource                                             | Default / fixed bound                                     |
| ---------------------------------------------------- | --------------------------------------------------------- |
| User / organization / exact asset start quotas       | 6 / 6 / 2 in a rolling hour, persisted                    |
| Active run per domain                                | 1, unique SQLite partial index                            |
| Global queued + running jobs                         | 20                                                        |
| Active workers / per-check concurrency               | One global DB slot / sequential                           |
| Network budget / DNS-connect-TLS-read operation      | 45s overall / min(3s, remaining)                          |
| Worker lease / queued job expiration                 | 90s / 15 minutes                                          |
| DNS records / value / total collected text per query | 32 / 1024 bytes / 4096 bytes                              |
| Addresses per resolution                             | 32, all vetted                                            |
| HTTP response headers / one line / header lines      | 16KiB / 2048 bytes / <=101 fields                         |
| Application body bytes read                          | 0                                                         |
| HEAD-to-GET fallback                                 | At most once per port, only 405/501                       |
| Network application ports / paths / redirects        | TCP 80,443 / `/` only / 0 followed                        |
| Observations / evidence per observation              | 13 / serialized JSON <=4096 bytes                         |
| Stored run history                                   | At most 100 runs/org, configurable validated ceiling 1000 |

The overall budget governs network operations; short SQLite commits and cleanup add local
wall-clock overhead. A process blocked/crashed outside network code cannot continue owning
the global slot indefinitely: after the lease the job becomes `interrupted`. No job is
silently retried. The previous worker checks status/lease before later probes and writes.
API history/detail polling and worker acquisition both perform stale-job recovery. A queued
job remains durable across API restarts and is only executed after current eligibility checks.
A queued job older than 15 minutes is failed rather than unexpectedly running later.

Allowed transitions: queued→running→completed/partial/failed; queued→failed on queue expiry;
running→interrupted on lease expiry. Any new attempt creates a new ID. Useful technical
outcomes are pass/attention/informational; unavailable checks are inconclusive/error.
Completed means13 useful observations; partial preserves useful observations with missing/
failed checks; no useful observations means failed. Revoked authorization always ends failed.

Retention evicts the oldest terminal run older than an hour when the organization reaches
capacity; it cannot erase recent quota accounting or active jobs. If none can be evicted,
start returns429. Observations cascade with eviction. Asset deletion keeps minimal historical
scan snapshots, without a domain FK, so delayed workers cannot recreate deleted assets.
Deleted-asset endpoints return404. New enrollment has a new identity. Audit DomainEvents
contain request/outcome kinds and IDs, never evidence/tokens. They retain the existing Phase 03
retention limitation: operators must plan an audit retention policy before production.

## Catalog and evidence interpretation

| Stable check      | Interpretation / limitation                                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| DNS_ADDRESS       | All exact-host A/AAAA addresses public; no guarantee for future answers                                                                     |
| DNS_MX_PRESENT    | Record count only; missing MX is context, not vulnerability                                                                                 |
| DNS_SPF_PRESENT   | Exact `v=spf1` record count; 0/multiple attention, one informational; no mechanisms/includes evaluation                                     |
| DNS_DMARC_PRESENT | Basic first version tag + unique p=none/quarantine/reject; missing/malformed/ambiguous distinguished; no deliverability/alignment guarantee |
| TLS_CERTIFICATE   | Verified chain/hostname handshake; validity window/days/issuer/subject/protocol; one destination, no cipher/protocol enumeration            |
| HTTPS_RESPONSE    | Root response status, method, redirect scope; no security verdict from status                                                               |
| HTTP_REDIRECT     | Port80 status/safe redirect category; no follow-up or inference about absent HTTP service                                                   |
| HTTPS_HSTS        | Positive max-age simple check; does not assess coverage or preload                                                                          |
| HTTPS_CSP         | Presence only, needs human policy review                                                                                                    |
| HTTPS_NOSNIFF     | Exact case-insensitive nosniff value                                                                                                        |
| HTTPS_REFERRER    | Presence only, not full policy validation                                                                                                   |
| HTTPS_PERMISSIONS | Presence only, not full policy validation                                                                                                   |
| HTTPS_FRAME       | DENY/SAMEORIGIN or CSP frame-ancestors presence; CSP effectiveness unassessed                                                               |

Each API observation includes asset ID, UTC epoch timestamp, stable check ID, source,
outcome, summary, explanation, safe structured evidence and engine version `starter-checks-1`.
No cookies, full headers, challenge values, raw TXT contents, HTML bodies or arbitrary
Location URLs enter persistence. CSP/nonces/report URIs and raw header policies are omitted;
only deterministic summaries are retained. Certificate names are ASCII sanitized/limited.
React renders evidence as text. Exceptions are fixed codes; unexpected logs contain only
exception type and scan ID. API errors preserve the existing safe envelope/no-store headers.

## Local QA and what remains unverified

All automated checks use injected DNS/socket fixtures, never random external sites. The
browser fixture modules live under scripts/qa, outside application Docker COPY paths.
`phase04.compose.yaml` mounts them **only** into a separately named local QA stack/volume.
Screenshots state LOCAL QA and must not be presented as live results. The production entry
remains `app.main:app`, production worker `app.scanner.worker`, with actual UDP/socket/TLS.

No team-controlled domain was supplied. LIVE owned-domain/provider/TLS end-to-end remains
NOT TESTED. To exercise it, explicitly authorize the exact name, publish the current real
TXT challenge, verify it, then start a bounded check in the normal local stack. Do not use
third-party targets to replace that missing acceptance evidence. Screen readers, physical
mobile devices and non-Chromium engines also remain untested. Public deployment is unapproved.
