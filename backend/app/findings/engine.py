"""Pure deterministic interpretation of persisted Phase04 contracts. No network or clock I/O."""

from collections import Counter

from app.findings.adapter import conclusive, integer, normalize
from app.findings.contracts import Assessment, Evaluation, Evidence
from app.findings.registry import CATALOG
from app.models import CheckObservation, ScanRun
from app.scanner.contracts import CHECKS, ENGINE


def trusted_certificate(row: Evidence | None) -> bool:
    if row is None or row.outcome != "pass" or "error_code" in row.values:
        return False
    start, end = integer(row, "not_before"), integer(row, "not_after")
    return start is not None and end is not None and start <= row.observed_at < end


def inspected_https(rows: dict[str, Evidence]) -> bool:
    response = rows.get("HTTPS_RESPONSE")
    status = integer(response, "status")
    return (
        trusted_certificate(rows.get("TLS_CERTIFICATE"))
        and conclusive(response)
        and status is not None
        and 200 <= status < 300
        and response is not None
        and response.values.get("path") == "/"
        and response.values.get("method") in {"HEAD", "GET"}
    )


def apply_rule(result: Evaluation, rows: dict[str, Evidence]) -> None:
    rule = result.rule_id
    if rule == "TLS_CERTIFICATE_ACTION":
        row = rows.get("TLS_CERTIFICATE")
        if row is None:
            return
        code = row.values.get("error_code")
        names = {
            "tls_expired": "The certificate was rejected as expired",
            "tls_hostname_mismatch": "The certificate did not match this hostname",
            "tls_invalid_chain": "The certificate chain was not trusted",
            "tls_validity_error": "The certificate was outside its validity period",
        }
        if (
            row.outcome in {"inconclusive", "error"}
            and code in names
            and set(row.values) == {"error_code"}
        ):
            result.decision, result.title = "issue", names[str(code)]
            result.severity, result.urgency = "high", 3
        elif trusted_certificate(row):
            end = integer(row, "not_after")
            assert end is not None
            remaining = end - row.observed_at
            if remaining <= 30 * 86400:
                result.decision = "issue"
                result.severity = "high" if remaining <= 7 * 86400 else "medium"
                result.urgency = 2 if result.severity == "high" else 1
                result.title = "Certificate renewal was due within " + (
                    "7 days" if result.severity == "high" else "30 days"
                )
            else:
                result.decision = "clear"
        if result.decision != "not_evaluable":
            result.evidence = [row]
    elif rule == "DNS_SPF_MULTIPLE":
        row = rows.get("DNS_SPF_PRESENT")
        count = integer(row, "record_count")
        if conclusive(row) and count is not None:
            result.decision = "issue" if count > 1 else "clear"
            result.evidence = [row] if row else []
    elif rule == "DNS_DMARC_POLICY":
        row, mx = rows.get("DNS_DMARC_PRESENT"), rows.get("DNS_MX_PRESENT")
        if not conclusive(row) or row is None:
            return
        policy, count = row.values.get("policy"), integer(row, "record_count")
        if policy in {"quarantine", "reject"} and count == 1:
            result.decision = "clear"
        elif policy == "malformed" and count == 1:
            result.decision, result.severity, result.urgency = "issue", "medium", 1
            result.title = "Review a basic DMARC policy format problem"
        elif (policy == "none" and count == 1) or (policy == "missing" and count == 0):
            mx_count = integer(mx, "record_count")
            if conclusive(mx) and mx_count is not None and mx_count > 0:
                result.decision = "issue"
                result.title = "Review " + (
                    "monitor-only DMARC" if policy == "none" else "missing DMARC"
                )
                result.evidence = [mx] if mx else []
            else:
                result.decision = "not_applicable"
                result.reason = (
                    "Outbound mail use is unknown; no sufficient mail context was saved."
                )
        if result.decision != "not_evaluable":
            result.evidence.append(row)
    elif rule in {"HTTPS_HSTS", "HTTPS_NOSNIFF"}:
        row = rows.get(rule)
        header = "strict-transport-security" if rule == "HTTPS_HSTS" else "x-content-type-options"
        if not inspected_https(rows) or row is None or row.values.get("header") != header:
            return
        detail = row.values.get("observation")
        positive = "positive max-age" if rule == "HTTPS_HSTS" else "nosniff"
        negative = (
            {"missing", "needs review"} if rule == "HTTPS_HSTS" else {"missing", "unexpected value"}
        )
        if row.outcome == "pass" and detail == positive:
            result.decision = "clear"
        elif row.outcome == "attention" and detail in negative:
            result.decision = "issue"
        if result.decision != "not_evaluable":
            result.evidence = [rows["TLS_CERTIFICATE"], rows["HTTPS_RESPONSE"], row]
    elif rule == "HTTP_ROOT_REDIRECT":
        row = rows.get("HTTP_REDIRECT")
        status = integer(row, "status")
        if not inspected_https(rows) or not conclusive(row) or row is None or status is None:
            return
        if row.values.get("path") != "/" or row.values.get("method") not in {"HEAD", "GET"}:
            return
        if 200 <= status < 300:
            result.decision = "issue"
        elif 300 <= status < 400 and row.values.get("redirect") == "same_host_https_not_followed":
            result.decision = "clear"
        if result.decision != "not_evaluable":
            result.evidence = [rows["TLS_CERTIFICATE"], rows["HTTPS_RESPONSE"], row]
    if result.decision in {"issue", "clear"}:
        result.reason = (
            "Supported by the documented source conditions."
            if result.decision == "issue"
            else "This specific rule condition was not observed in a comparable check."
        )


def evaluate(run: ScanRun, observations: list[CheckObservation]) -> Assessment:
    counts = Counter(row.check_id for row in observations)
    source_counts = dict.fromkeys(
        ["pass", "attention", "informational", "inconclusive", "error"], 0
    )
    known = set()
    for row in observations:
        if row.check_id in CHECKS and row.outcome in source_counts and counts[row.check_id] == 1:
            source_counts[row.outcome] += 1
            known.add(row.check_id)
    source_counts["not_checked"] = len(CHECKS) - len(known)
    source_counts["unsupported"] = sum(row.check_id not in CHECKS for row in observations)
    rows = {
        row.check_id: normalized
        for row in observations
        if counts[row.check_id] == 1
        and row.observed_at > 0
        and (normalized := normalize(row)) is not None
    }
    trusted = (
        run.engine_version == ENGINE
        and run.status in {"completed", "partial", "failed", "interrupted"}
        and run.error_code != "authorization_changed"
    )
    results = []
    for template in CATALOG:
        result = template.model_copy(deep=True)
        if trusted:
            apply_rule(result, rows)
        else:
            result.reason = "Unsupported engine, in-flight run or revoked scan authorization."
        if trusted and result.decision == "not_evaluable":
            dependencies = {
                "TLS_CERTIFICATE_ACTION": ["TLS_CERTIFICATE"],
                "HTTP_ROOT_REDIRECT": ["TLS_CERTIFICATE", "HTTPS_RESPONSE", "HTTP_REDIRECT"],
                "HTTPS_HSTS": ["TLS_CERTIFICATE", "HTTPS_RESPONSE", "HTTPS_HSTS"],
                "HTTPS_NOSNIFF": ["TLS_CERTIFICATE", "HTTPS_RESPONSE", "HTTPS_NOSNIFF"],
                "DNS_SPF_MULTIPLE": ["DNS_SPF_PRESENT"],
                "DNS_DMARC_POLICY": ["DNS_MX_PRESENT", "DNS_DMARC_PRESENT"],
            }[result.rule_id]
            result.evidence = [rows[check] for check in dependencies if check in rows]
            errors = sorted(
                {str(e.values["error_code"]) for e in result.evidence if "error_code" in e.values}
            )
            if errors:
                result.reason = (
                    "Check evidence was unavailable: "
                    + ", ".join(errors)
                    + ". No condition was established."
                )
        results.append(result)
    return Assessment(
        scan_id=run.id,
        source_engine=run.engine_version,
        scan_status=run.status,
        observed_checks=len(known),
        observation_counts=source_counts,
        rules=results,
        coverage=dict(Counter(result.decision for result in results)),
    )
