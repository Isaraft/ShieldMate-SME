# Limited External Configuration Assessment — policy starter-risk-1

Phase 05 interprets **saved** Phase 04 observations. Evaluation is offline and deterministic:
the same source records, source version and policy produce the same six rule decisions.
It does not crawl, resolve DNS, connect sockets, expand scope or change ownership proofs.
No numerical posture/security score, CVSS, exploit probability or company-wide safety verdict
is calculated. No Critical finding is warranted by this deliberately narrow catalog.

## Evidence contract and applicability

Only `starter-checks-1` observations from terminal `completed`, `partial`, `failed` or
`interrupted` runs are eligible. `authorization_changed` invalidates the run for assertions.
Queued/running runs are never evaluated definitively. A partial/interrupted run can support
only rules whose required observations are present and conclusive. Failed network operations
never demonstrate the absence of a policy or service. An unknown engine version produces six
`not_evaluable` decisions. Duplicate check IDs, missing fields and malformed values cannot
be used to assert or clear their conditions.

The adapter allowlists check IDs, integer bounds, fixed policy/header/error enums and root
method/path/status fields. It discards source prose, raw TXT, HTTP policies, cookies, challenge
values, certificate names, arbitrary headers/bodies and unknown fields. Evidence snapshots
include original observation ID, method/source, check ID, collection outcome, observed epoch
and the minimal normalized values. Original scanner records remain unchanged. React displays
values as escaped text. No endpoint accepts an observation, severity or lifecycle mutation.

A collection outcome and a rule decision are distinct. For example, Phase 04 records TLS
validation rejection as `inconclusive` with a precise fixed error code. That code can support
a trust issue, while an unspecified TLS failure cannot. Conversely, SPF record count zero is
an `attention` collection outcome but conclusively demonstrates the absence of **multiple**
SPF policies. It can clear the multiplicity rule without claiming SPF correctness or safety.
This rule-specific comparison follows the authoritative Phase 05 brief rather than treating
all Phase 04 `attention` values identically.

## Decision vocabulary

- `issue`: the documented condition is supported; create/update/reopen the logical finding.
- `clear`: a comparable conclusive observation did not exhibit this **specific** condition.
- `not_evaluable`: unavailable, missing, ambiguous, unsupported or failed evidence. Preserve
  the previous lifecycle and annotate `not_rechecked`; never mark resolved.
- `not_applicable`: the necessary context was not established. It also cannot resolve a
  previous issue. This means insufficient applicable context, not a passed security check.

The UI separately shows source collection counts and these six policy decisions. Latest
source coverage is per selected asset, or a specifically selected scan. It does not sum old
runs to imply more coverage. Priority/status/category counters describe the filtered finding
set; coverage describes the selected asset/scan scope independently of finding severity.

## Rule registry (immutable version 1)

### TLS_CERTIFICATE_ACTION — tls

Source: `TLS_CERTIFICATE`.

- Precise `tls_expired`, `tls_hostname_mismatch`, `tls_invalid_chain`, or
  `tls_validity_error` with an error/inconclusive collection outcome supports a **High**
  issue, urgency 3, relevance 2, conclusive confidence. The last code means outside the
  validity window; it is not automatically called expired.
- A `pass` with integer `not_before <= observed_at < not_after` is a verified certificate.
  Remaining time is computed from **source observed_at**, never today's clock or the
  rounded `remaining_days` display field. <=7 days: High/urgency 2; >7–30 days:
  Medium/urgency 1. >30 days: clear. Missing/inconsistent dates are not evaluable.
- Generic timeout, refusal, chain-unspecified TLS failure or unknown error cannot establish
  expiry, hostname mismatch or lack of HTTPS. No insecure verification fallback is used.
- Impact: trust errors/expiry can interrupt access to this exact public endpoint.
- Action: hosting contact checks renewal, names and full trusted chain, installs the correct
  certificate, then requests an authorized recheck. No application-wide TLS guarantee.
- One fingerprint covers trust and renewal concerns, avoiding duplicate certificate alerts.

### HTTP_ROOT_REDIRECT — https

Sources: a trusted certificate, `HTTPS_RESPONSE` with inspected root HEAD/GET and status 2xx,
and a conclusive `HTTP_REDIRECT` for root HEAD/GET.

HTTP 2xx supports **Low**, urgency 0, relevance 1, contextual confidence: the observed root did
not immediately redirect to HTTPS. A 3xx with `same_host_https_not_followed` clears this
condition. Other redirects, unknown scope, errors and unsupported statuses are not evaluable.
No redirect is followed and no later hop/path behavior is inferred. No assertion that HTTPS
is absent, credentials were exposed, or interception occurred. Ask hosting to review the
root HTTP→same-host HTTPS redirect and run a new authorized check.

### HTTPS_HSTS — http_headers

Requires the same trusted/inspected HTTPS 2xx context, plus `HTTPS_HSTS` with the expected
header and normalized condition. `attention` + missing/needs-review supports **Low**,
urgency 0, relevance 1, contextual confidence. `pass` + positive max-age clears this simple
condition. Missing/uninspected/redirected HTTPS is unknown, not missing HSTS. Action:
review a suitable positive max-age; check subdomain coverage before includeSubDomains or
preload. The policy does not prove exploitation, full HSTS validity or preload eligibility.

### HTTPS_NOSNIFF — http_headers

Requires inspected/trusted HTTPS 2xx and the expected nosniff observation. Missing or
unexpected value with `attention` supports **Low**, urgency 0, relevance 1, contextual
confidence; `pass` + nosniff clears it. The body/content type was not collected, so this is
a conditional browser-hardening review, not an XSS finding. Ask the application contact to
check MIME types and nosniff applicability before changing configuration, then recheck.

### DNS_SPF_MULTIPLE — dns_email

Source: conclusive `DNS_SPF_PRESENT.record_count`, integer 0–32. More than one exact SPF
version record supports **Medium**, urgency 1, relevance 1, conclusive confidence in record
multiplicity. Zero/one clears multiplicity only. Invalid/missing count is unknown. Impact:
mail-authentication evaluation errors **if** this exact domain sends mail. Action: consolidate
intended senders into one policy with the mail administrator, preserving other TXT records.
No parsing of SPF mechanisms/includes, outgoing-mail proof or compromise detection exists.
Missing SPF alone never creates an unconditional finding.

### DNS_DMARC_POLICY — dns_email

Source: conclusive `DNS_DMARC_PRESENT.policy` + count. `reject`/`quarantine` with one record
clears this basic review condition. A single basic `malformed` policy supports **Medium**,
urgency 1, relevance 1, contextual confidence. Missing(count 0) or monitor-only none(count 1)
supports a **Low** contextual review only when a conclusive MX count>0 provides limited
mail context. Without that context it is not applicable and cannot clear an existing finding.
Ambiguous/multiple/inconsistent/unknown policy data are not evaluable.

MX count is weak context: inbound handling does not prove outgoing mail use, and the Phase 04
count cannot distinguish a Null MX. These are known possible false positives, explicitly low
priority and conditional. `p=none` may be an intentional monitoring stage. Ask the mail
administrator to establish actual use, review alignment/syntax, monitor senders and stage
policy enforcement. No claim of phishing compromise, delivery success or full RFC validation.

## Deliberate non-rules

Missing MX remains informational context, never a vulnerability. Missing SPF without proven
outgoing-mail use is not asserted. Phase 04 did not collect content types or safe raw policy
syntax; CSP/frame/referrer/permissions observations cannot establish policy effectiveness or
HTML applicability. No CSP/XSS/clickjacking vulnerability is manufactured. Generic transport
failures do not establish unavailable HTTPS. No DNSSEC/DKIM/OS/CVE/reputation/internal-network
rules, LLM recommendations or fabricated company criticality are present.

## Reproducible ordering and worked examples

Open findings sort by the following tuple, evaluated on the server:

1. Severity descending: High 3, Medium 2, Low 1, Informational 0.
2. Urgency descending: 3 explicit trust error; 2 renewal<=7 days; 1 renewal<=30 days or supported
   medium email-configuration issue; 0 contextual hardening.
3. Observed relevance descending: 2 directly verified TLS endpoint; 1 observed root/mail context.
4. Confidence: conclusive before contextual.
5. Latest **issue** observation time descending.
6. Stable SHA256 fingerprint of `(asset UUID, rule ID)` ascending.

Numbers are bounded ordinal sorting components, **not a security score**. Severity reasoning,
confidence, evidence date and limitations remain visible. No more than three actual open
findings are returned; resolved findings cannot fill the priority list. Filters apply to
both the list and its priority selection. Changing table sort does not change the rubric.

Examples: a certificate due in 5 days ranks High before multiple SPF records (Medium).
A certificate due in 20 days (Medium/relevance 2) ranks before multiple SPF (Medium/relevance 1)
when urgency ties. Multiple SPF ranks before a contextual malformed DMARC when severity,
urgency and relevance tie, because SPF multiplicity is conclusive. Identical findings after
reruns retain the same fingerprint/DB identity and stable final tie-breaker. Stale dates stay
visible; a source-time deadline is never silently promoted into a current expiry claim.

## Transactional lifecycle and history

The worker reconciles retained terminal scans in created-time/insertion order, up to 5 per
iteration. Explicit local backfill uses the same service. A short SQLite BEGIN IMMEDIATE
transaction covers evaluation uniqueness, finding upserts and events. `(scan ID,policy)`
uniqueness and `(organization,fingerprint)` uniqueness make retries/concurrent processing
idempotent. A crash rolls back the entire evaluation, so a later pass safely retries.
No API read performs evaluation or network activity.

A confirmed issue preserves first_seen, advances last_seen/evidence and may change supported
severity. A comparable clear resolves it with source provenance. Repeated clear checks do
not reset the original resolution time. An issue after resolution reopens the same ID and
retains prior resolution history. Unknown/not-applicable/missing checks leave status and
last-known evidence intact with `not_rechecked`. User/task completion cannot change findings.

SQLite insertion order breaks same-second source ties; random UUID lexical order is not
chronology. Out-of-order older sources are evaluated and archived with `applied=false`, but
cannot overwrite newer state or resurrect issues against a newer clean assessment. Normal
backfill is chronological; explicit out-of-order archives are visible through assessment
provenance rather than rewriting current lifecycle. The source-order implementation is
SQLite-specific and must be reviewed with any future database migration.

Freshness defaults to 7 days (`SHIELDMATE_FINDING_STALE_SECONDS`, validated 60–7776000s).
It is a read-time annotation, distinct from open/resolved and not-rechecked. Expired DNS proof
does not erase historical findings; Phase 04 still requires fresh proof before another scan.

Six rules bound current findings to six per enrolled asset. Asset deletion explicitly removes
derived findings, evaluations and events; the UI discloses this before confirmation. Original
Phase 04 scan-history retention stays unchanged. Evaluation rows cascade when source scans
are pruned (default 100/org, validated maximum 1000). Finding/event evidence snapshots remain
usable after source pruning, with links marked unavailable. Event history is capped 50/finding:
first detection, latest resolution/reopening and recent events are retained, with an explicit
history-compacted flag. This bounds storage and discloses older event removal. Retain/export
necessary research evidence before intentionally removing assets or pruning history.

Every snapshot records policy version. Compatible future policy revisions require explicit
version changes/backfill; incompatible rule semantics require a new immutable rule ID.
There is no user-controlled policy override, fake-resolution endpoint or automatic rewriting
of old observation records. No Phase 06 task/dashboard workflow is implemented.
