"""Explicit offline maintainer command. Produces the single reserved-name synthetic fixture."""

import json
from collections import Counter
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.findings.adapter import normalize
from app.findings.contracts import POLICY
from app.findings.engine import evaluate
from app.findings.schemas import FindingOut
from app.models import CheckObservation, ScanRun
from app.reports.schemas import ReportAsset, ReportTask, SavedObservation, Snapshot

TIME = 1790812800  # 2026-10-01 00:00 UTC. Fixed scenario, never a current customer timestamp.


def uid(value):
    return str(uuid5(NAMESPACE_URL, "shieldmate-demo-v1:" + value))


run = ScanRun(
    id=uid("scan"),
    asset_id=uid("asset"),
    organization_id=uid("org"),
    hostname="merchant.example",
    status="completed",
    engine_version="starter-checks-1",
    created_at=TIME,
    finished_at=TIME + 2,
    error_code=None,
)
values = [
    ("DNS_ADDRESS", "informational", {}),
    ("DNS_MX_PRESENT", "informational", {"record_count": 1}),
    ("DNS_SPF_PRESENT", "attention", {"record_count": 2}),
    ("DNS_DMARC_PRESENT", "attention", {"policy": "malformed", "record_count": 1}),
    (
        "TLS_CERTIFICATE",
        "pass",
        {"not_before": TIME - 86400, "not_after": TIME + 5 * 86400, "protocol": "TLSv1.3"},
    ),
    ("HTTPS_RESPONSE", "informational", {"status": 200, "method": "HEAD", "path": "/"}),
    (
        "HTTP_REDIRECT",
        "informational",
        {"status": 301, "method": "HEAD", "path": "/", "redirect": "same_host_https_not_followed"},
    ),
    (
        "HTTPS_HSTS",
        "pass",
        {"header": "strict-transport-security", "observation": "positive max-age"},
    ),
    ("HTTPS_NOSNIFF", "pass", {"header": "x-content-type-options", "observation": "nosniff"}),
    ("HTTPS_CSP", "informational", {}),
    ("HTTPS_FRAME", "pass", {}),
    ("HTTPS_REFERRER", "informational", {}),
    ("HTTPS_PERMISSIONS", "informational", {}),
]
rows = [
    CheckObservation(
        id=uid(check),
        scan_id=run.id,
        check_id=check,
        outcome=outcome,
        observed_at=TIME,
        evidence=evidence,
        summary="SYNTHETIC",
        source="SYNTHETIC",
        explanation="No network check performed",
    )
    for check, outcome, evidence in values
]
assessment = evaluate(run, rows)
findings = []
for r in assessment.rules:
    if r.decision != "issue":
        continue
    findings.append(
        FindingOut(
            **{
                k: getattr(r, k)
                for k in [
                    "rule_id",
                    "category",
                    "severity",
                    "urgency",
                    "relevance",
                    "confidence",
                    "title",
                    "impact",
                    "recommendation",
                    "rationale",
                    "limitation",
                    "evidence",
                ]
            },
            id=uid(r.rule_id),
            asset_id=run.asset_id,
            hostname=run.hostname,
            fingerprint=uid("fingerprint:" + r.rule_id),
            policy_version=POLICY,
            status="open",
            first_seen_at=TIME,
            last_seen_at=TIME,
            observed_at=TIME,
            resolved_at=None,
            last_evaluation_at=TIME + 3,
            recheck_status="confirmed",
            stale=False,
            history_truncated=False,
            source_scan_id=run.id,
            source_scan_available=False,
            ranking_reason=(
                "Synthetic scenario uses the documented Phase 05 ordering; no security score."
            ),
        )
    )
# Fixed fixture ordering checked against the real ranking rubric by tests; not a second live engine.
order = ["TLS_CERTIFICATE_ACTION", "DNS_SPF_MULTIPLE", "DNS_DMARC_POLICY"]
findings.sort(key=lambda f: order.index(f.rule_id))
tasks = []
for f, status in zip(findings, ["todo", "in_progress", "done"], strict=True):
    f.task_id, f.task_status = uid("task:" + f.rule_id), status
    tasks.append(
        ReportTask(
            id=f.task_id,
            finding_id=f.id,
            title=f.title,
            hostname=f.hostname,
            status=status,
            owner_label="Sample IT contact",
            updated_at=TIME + 100,
            completed_at=TIME + 100 if status == "done" else None,
            finding_status="open",
            finding_stale=False,
            recommendation=f.recommendation,
        )
    )
asset = ReportAsset(
    id=run.asset_id,
    hostname=run.hostname,
    currently_authorized=False,
    verification_valid_until=None,
    assessed=True,
    reason="Synthetic scenario only; no ownership proof or network check",
    stale=False,
    scan_id=run.id,
    scan_status="completed",
    scan_finished_at=TIME + 2,
    observation_counts=dict(Counter(o.outcome for o in rows)),
    observations=[
        SavedObservation(
            id=o.id,
            check_id=o.check_id,
            outcome=o.outcome,
            observed_at=o.observed_at,
            values=n.values if (n := normalize(o)) else {},
        )
        for o in rows
    ],
)
snapshot = Snapshot(
    id=uid("report"),
    kind="demo",
    organization_id=run.organization_id,
    organization_name="Sample Merchant KZ",
    created_at=TIME + 120,
    locale="en",
    policy_version=POLICY,
    readiness="ready",
    can_generate=False,
    counts={
        "enrolled_domains": 1,
        "authorized_domains": 0,
        "assessed_domains": 1,
        "without_usable_evidence": 0,
        "unverified_domains": 1,
        "stale_domains": 0,
        "excluded_historical_findings": 0,
    },
    finding_counts=dict(Counter("open:" + f.severity for f in findings)),
    task_counts=dict(Counter(t.status for t in tasks)),
    assets=[asset],
    findings=findings,
    priorities=findings[:3],
    tasks=tasks,
)
Path("app/reports/demo_snapshot.json").write_text(
    json.dumps(snapshot.model_dump(), ensure_ascii=False, indent=2) + "\n"
)
