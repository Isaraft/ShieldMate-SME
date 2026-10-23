"""Pure policy tests use actual Phase04 field shapes, never network access."""

import copy
import uuid

import pytest

from app.findings.engine import evaluate
from app.models import CheckObservation, ScanRun

TIME = 1800000000


def row(check, outcome, **evidence):
    return CheckObservation(
        id=str(uuid.uuid4()),
        scan_id="fixture",
        check_id=check,
        observed_at=TIME,
        outcome=outcome,
        source="untrusted source ignored",
        summary="untrusted prose ignored",
        explanation="ignored",
        evidence=evidence,
    )


def source():
    run = ScanRun(
        id=str(uuid.uuid4()),
        engine_version="starter-checks-1",
        status="completed",
        error_code=None,
        created_at=TIME,
        started_at=TIME,
        finished_at=TIME + 2,
    )
    rows = [
        row("TLS_CERTIFICATE", "pass", not_before=TIME - 86400, not_after=TIME + 90 * 86400),
        row("HTTPS_RESPONSE", "informational", status=200, method="HEAD", path="/"),
        row(
            "HTTP_REDIRECT",
            "informational",
            status=301,
            method="HEAD",
            path="/",
            redirect="same_host_https_not_followed",
        ),
        row("DNS_MX_PRESENT", "informational", record_count=1),
        row("DNS_SPF_PRESENT", "informational", record_count=1),
        row("DNS_DMARC_PRESENT", "informational", policy="reject", record_count=1),
        row(
            "HTTPS_HSTS", "pass", header="strict-transport-security", observation="positive max-age"
        ),
        row("HTTPS_NOSNIFF", "pass", header="x-content-type-options", observation="nosniff"),
    ]
    return run, rows


def rule_result(check, outcome, evidence, rule):
    run, rows = source()
    rows = [r for r in rows if r.check_id != check] + [row(check, outcome, **evidence)]
    return next(result for result in evaluate(run, rows).rules if result.rule_id == rule)


@pytest.mark.parametrize(
    "code,decision",
    [
        ("tls_expired", "issue"),
        ("tls_hostname_mismatch", "issue"),
        ("tls_invalid_chain", "issue"),
        ("tls_validity_error", "issue"),
        ("network_timeout", "not_evaluable"),
        ("tls_failure", "not_evaluable"),
        ("connection_refused", "not_evaluable"),
        ("unknown", "not_evaluable"),
    ],
)
def test_precise_tls_failure_vs_generic_error(code, decision):
    result = rule_result(
        "TLS_CERTIFICATE", "inconclusive", {"error_code": code}, "TLS_CERTIFICATE_ACTION"
    )
    assert result.decision == decision
    if decision == "issue":
        assert result.severity == "high"


@pytest.mark.parametrize(
    "days,decision,severity",
    [
        (1, "issue", "high"),
        (7, "issue", "high"),
        (8, "issue", "medium"),
        (30, "issue", "medium"),
        (31, "clear", "low"),
        (0, "not_evaluable", "low"),
    ],
)
def test_expiry_uses_source_time_not_current_clock(days, decision, severity):
    result = rule_result(
        "TLS_CERTIFICATE",
        "pass",
        {"not_before": TIME - 100, "not_after": TIME + days * 86400, "remaining_days": 9999},
        "TLS_CERTIFICATE_ACTION",
    )
    assert result.decision == decision and result.severity == severity


@pytest.mark.parametrize(
    "count,decision",
    [
        (0, "clear"),
        (1, "clear"),
        (2, "issue"),
        (32, "issue"),
        (33, "not_evaluable"),
        (-1, "not_evaluable"),
        (True, "not_evaluable"),
        ("2", "not_evaluable"),
    ],
)
def test_spf_multiplicity_only(count, decision):
    result = rule_result(
        "DNS_SPF_PRESENT", "attention", {"record_count": count}, "DNS_SPF_MULTIPLE"
    )
    assert result.decision == decision


@pytest.mark.parametrize(
    "policy,count,decision",
    [
        ("reject", 1, "clear"),
        ("quarantine", 1, "clear"),
        ("none", 1, "issue"),
        ("missing", 0, "issue"),
        ("malformed", 1, "issue"),
        ("ambiguous", 2, "not_evaluable"),
        ("reject", 2, "not_evaluable"),
        ("none", 0, "not_evaluable"),
        ("bad", 1, "not_evaluable"),
    ],
)
def test_basic_dmarc(policy, count, decision):
    assert (
        rule_result(
            "DNS_DMARC_PRESENT",
            "attention",
            {"policy": policy, "record_count": count},
            "DNS_DMARC_POLICY",
        ).decision
        == decision
    )


def test_no_mx_does_not_invent_email_use_or_a_vulnerability():
    run, rows = source()
    rows = [
        r
        for r in rows
        if r.check_id not in {"DNS_MX_PRESENT", "DNS_DMARC_PRESENT", "DNS_SPF_PRESENT"}
    ]
    rows += [
        row("DNS_MX_PRESENT", "informational", record_count=0),
        row("DNS_DMARC_PRESENT", "attention", policy="missing", record_count=0),
        row("DNS_SPF_PRESENT", "attention", record_count=0),
    ]
    results = evaluate(run, rows)
    assert not any(result.decision == "issue" for result in results.rules)
    assert (
        next(r for r in results.rules if r.rule_id == "DNS_DMARC_POLICY").decision
        == "not_applicable"
    )


@pytest.mark.parametrize(
    "check,header,good,bad",
    [
        ("HTTPS_HSTS", "strict-transport-security", "positive max-age", "missing"),
        ("HTTPS_NOSNIFF", "x-content-type-options", "nosniff", "unexpected value"),
    ],
)
def test_headers_require_conclusive_inspected_https(check, header, good, bad):
    assert (
        rule_result(check, "attention", {"header": header, "observation": bad}, check).decision
        == "issue"
    )
    assert (
        rule_result(check, "pass", {"header": header, "observation": good}, check).decision
        == "clear"
    )
    assert (
        rule_result(check, "inconclusive", {"header": header, "observation": bad}, check).decision
        == "not_evaluable"
    )
    run, rows = source()
    rows = [r for r in rows if r.check_id != "HTTPS_RESPONSE"]
    rows += [row(check, "attention", header=header, observation=bad)]
    assert (
        next(r for r in evaluate(run, rows).rules if r.rule_id == check).decision == "not_evaluable"
    )


@pytest.mark.parametrize(
    "status,redirect,decision",
    [
        (200, None, "issue"),
        (301, "same_host_https_not_followed", "clear"),
        (302, "outside_exact_host", "not_evaluable"),
        (404, None, "not_evaluable"),
        (302, "same_host_not_followed", "not_evaluable"),
    ],
)
def test_http_only_observed_root_behavior(status, redirect, decision):
    evidence = {"status": status, "method": "HEAD", "path": "/"}
    if redirect:
        evidence["redirect"] = redirect
    assert (
        rule_result("HTTP_REDIRECT", "informational", evidence, "HTTP_ROOT_REDIRECT").decision
        == decision
    )


def test_version_inflight_duplicate_and_authorization_fail_closed():
    run, rows = source()
    rows[0].evidence = {"error_code": "tls_expired"}
    rows[0].outcome = "inconclusive"
    for attribute, value in [
        ("engine_version", "future-unsupported"),
        ("status", "running"),
        ("error_code", "authorization_changed"),
    ]:
        altered = copy.copy(run)
        setattr(altered, attribute, value)
        assert all(r.decision == "not_evaluable" for r in evaluate(altered, rows).rules)
    assert (
        next(
            r
            for r in evaluate(run, [*rows, rows[0]]).rules
            if r.rule_id == "TLS_CERTIFICATE_ACTION"
        ).decision
        == "not_evaluable"
    )


def test_determinism_and_evidence_redaction():
    run, rows = source()
    for source_row in rows:
        source_row.evidence.update(
            {
                "set-cookie": "secret",
                "authorization": "secret",
                "challenge_token": "secret",
                "body": "<script>secret</script>",
                "subject": "secret",
            }
        )
    first = evaluate(run, rows).model_dump()
    assert first == evaluate(run, list(reversed(rows))).model_dump()
    assert "secret" not in str(first) and "untrusted prose" not in str(first)
    assert not any("CSP" in r.rule_id for r in evaluate(run, rows).rules)
