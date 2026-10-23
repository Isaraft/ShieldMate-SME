"""Immutable policy-v1 editorial catalog. Never derived from untrusted response prose."""

from app.findings.contracts import Evaluation

CATALOG: tuple[Evaluation, ...] = (
    Evaluation(
        rule_id="TLS_CERTIFICATE_ACTION",
        category="tls",
        title="Review certificate trust or renewal",
        confidence="conclusive",
        relevance=2,
        impact=(
            "Certificate problems can stop customers or staff reaching this "
            "exact website over trusted HTTPS."
        ),
        recommendation=(
            "Ask the hosting contact to check renewal, the certificate names "
            "and full trusted chain. Install the correct certificate, then run"
            " an authorized scan again."
        ),
        rationale=(
            "An explicit trust error or a measured renewal deadline supports a"
            " transport maintenance priority."
        ),
        limitation=(
            "One exact hostname and pinned endpoint was checked. This does not"
            " enumerate every certificate, cipher or supported protocol."
        ),
    ),
    Evaluation(
        rule_id="HTTP_ROOT_REDIRECT",
        category="https",
        title="HTTP root does not immediately redirect to HTTPS",
        impact=(
            "The observed HTTP root can be reached without the HTTPS redirect "
            "expected for this site's public entry point."
        ),
        recommendation=(
            "Ask the hosting contact to redirect the HTTP root to HTTPS on the"
            " same exact hostname. Recheck both root responses with an "
            "authorized scan."
        ),
        rationale=(
            "A successful HTTP root response alongside inspected HTTPS "
            "supports a low-priority entry-point hardening recommendation."
        ),
        limitation=(
            "Only HEAD/GET at / was observed. No credentials, other paths or "
            "later redirect hops were tested; this is not proof of "
            "interception."
        ),
    ),
    Evaluation(
        rule_id="HTTPS_HSTS",
        category="http_headers",
        title="Review the HTTPS transport policy",
        impact=(
            "The inspected HTTPS root did not demonstrate the limited HSTS "
            "condition used by this policy."
        ),
        recommendation=(
            "Have the hosting contact review Strict-Transport-Security and "
            "deploy a suitable positive max-age after checking HTTPS coverage."
            " Do not enable includeSubDomains or preload without checking "
            "their scope. Rerun the authorized check."
        ),
        rationale=(
            "A missing or unrecognized HSTS value on an inspected HTTPS "
            "response is contextual, low-priority hardening."
        ),
        limitation=(
            "Only the root response and a simple max-age condition were "
            "checked. No exploitation or whole-origin coverage is established."
        ),
    ),
    Evaluation(
        rule_id="HTTPS_NOSNIFF",
        category="http_headers",
        title="Review the response content-type safeguard",
        impact=(
            "The inspected response did not demonstrate nosniff, a browser "
            "content-type hardening control."
        ),
        recommendation=(
            "Ask the application contact to review MIME types and set "
            "X-Content-Type-Options: nosniff where appropriate, then rerun an "
            "authorized scan."
        ),
        rationale=(
            "Missing or unexpected nosniff is low-priority contextual "
            "hardening, never proof of XSS."
        ),
        limitation=(
            "Response content type and body were not collected. Browser "
            "applicability needs review; API or non-browser services may have "
            "different requirements."
        ),
    ),
    Evaluation(
        rule_id="DNS_SPF_MULTIPLE",
        category="dns_email",
        title="Multiple SPF policies were observed",
        severity="medium",
        urgency=1,
        confidence="conclusive",
        impact=(
            "Multiple SPF policies at the same name can cause "
            "mail-authentication evaluation errors if this domain sends mail."
        ),
        recommendation=(
            "Ask the mail administrator to consolidate intended senders into "
            "one SPF policy at this exact name. Do not overwrite the DNS "
            "ownership challenge. Rerun the authorized DNS check."
        ),
        rationale=(
            "The persisted exact v=spf1 record count identifies multiplicity; "
            "medium priority reflects configuration correctness, not "
            "compromise."
        ),
        limitation=(
            "Outbound email use and SPF mechanisms/includes are unknown. One "
            "record or no record is not proof that outbound email is correctly"
            " authorized."
        ),
    ),
    Evaluation(
        rule_id="DNS_DMARC_POLICY",
        category="dns_email",
        title="Review the email-domain policy",
        impact=(
            "The saved basic DMARC observation warrants a mail-policy review; "
            "it does not establish email compromise."
        ),
        recommendation=(
            "Ask the mail administrator to confirm whether this exact domain "
            "sends mail, review DMARC syntax and alignment, and stage "
            "enforcement after monitoring legitimate senders. Rerun the "
            "authorized DNS check."
        ),
        rationale=(
            "Missing or monitor-only policy with inbound-mail context is low "
            "priority. A single basic malformed policy is medium priority for "
            "configuration review."
        ),
        limitation=(
            "MX suggests inbound handling only. Outbound email, alignment, "
            "reporting and full DMARC syntax were not assessed; p=none can be "
            "intentional."
        ),
    ),
)
