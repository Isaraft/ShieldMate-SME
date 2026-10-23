"""Allowlisted normalized evidence only. No raw text/headers/tokens copied from storage."""

from app.findings.contracts import Evidence
from app.models import CheckObservation

SOURCES = {
    "TLS_CERTIFICATE": "TLS 443",
    "HTTPS_RESPONSE": "HTTPS /",
    "HTTP_REDIRECT": "HTTP /",
    "DNS_SPF_PRESENT": "DNS TXT",
    "DNS_DMARC_PRESENT": "DNS TXT _dmarc",
    "DNS_MX_PRESENT": "DNS MX",
    "HTTPS_HSTS": "HTTPS headers",
    "HTTPS_NOSNIFF": "HTTPS headers",
}
VALUES = {
    "error_code": {
        "tls_expired",
        "tls_hostname_mismatch",
        "tls_invalid_chain",
        "tls_validity_error",
        "network_timeout",
        "connection_refused",
        "network_failure",
        "tls_failure",
        "tls_certificate_unavailable",
        "dns_unavailable",
        "dns_limit",
        "dns_alias_unsupported",
        "dns_ambiguous",
        "dns_malformed",
        "no_public_addresses",
        "unsafe_destination",
        "peer_mismatch",
        "http_header_limit",
        "http_invalid_response",
        "http_invalid_headers",
        "http_ambiguous_headers",
        "http_incomplete_headers",
        "overall_timeout",
        "authorization_changed",
        "redirect_not_followed",
        "engine_failure",
        "worker_interrupted",
    },
    "policy": {"none", "quarantine", "reject", "missing", "malformed", "ambiguous"},
    "observation": {"missing", "needs review", "positive max-age", "nosniff", "unexpected value"},
    "header": {"strict-transport-security", "x-content-type-options"},
    "method": {"HEAD", "GET"},
    "path": {"/"},
    "redirect": {
        "same_host_https_not_followed",
        "same_host_not_followed",
        "outside_exact_host",
        "unsupported_port",
        "unsupported_destination",
    },
    "protocol": {"TLSv1.2", "TLSv1.3"},
}
BOUNDS = {
    "not_before": (0, 7258118400),
    "not_after": (0, 7258118400),
    "record_count": (0, 32),
    "status": (200, 599),
}


def normalize(row: CheckObservation) -> Evidence | None:
    if (
        row.check_id not in SOURCES
        or row.outcome not in {"pass", "attention", "informational", "inconclusive", "error"}
        or not isinstance(row.evidence, dict)
        or type(row.observed_at) is not int
    ):
        return None
    values: dict[str, str | int] = {}
    for key, value in row.evidence.items():
        if key in VALUES and isinstance(value, str) and value in VALUES[key]:
            values[key] = value
        elif key in BOUNDS and type(value) is int:
            lower, upper = BOUNDS[key]
            if lower <= value <= upper:
                values[key] = value
    if "error_code" in row.evidence and "error_code" not in values:
        values["error_code"] = "unrecognized_error"
    return Evidence(
        observation_id=row.id,
        check_id=row.check_id,
        observed_at=row.observed_at,
        outcome=row.outcome,
        source=SOURCES[row.check_id],
        values=values,
    )


def integer(row: Evidence | None, key: str) -> int | None:
    value = row.values.get(key) if row else None
    return value if type(value) is int else None


def conclusive(row: Evidence | None) -> bool:
    return (
        row is not None
        and "error_code" not in row.values
        and row.outcome in {"pass", "attention", "informational"}
    )
