"""Bounded consistent-snapshot aggregation of authorized, persisted evidence only."""

from collections import Counter

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.errors import PublicError
from app.findings.adapter import normalize
from app.findings.contracts import POLICY
from app.findings.queries import finding_page
from app.findings.schemas import Filters
from app.models import (
    CheckObservation,
    DomainAsset,
    Finding,
    FindingEvaluation,
    Organization,
    RemediationTask,
    ScanRun,
)
from app.reports.schemas import Locale, ReportAsset, ReportTask, SavedObservation, Snapshot
from app.scanner.contracts import ENGINE
from app.scanner.policy import eligible

MAX_ASSETS, MAX_FINDINGS, MAX_TASKS = 20, 120, 120


def collect(
    db: Session, org: str, identifier: str, locale: Locale, moment: int, stale: int
) -> Snapshot:
    organization = db.get(Organization, org)
    if organization is None:
        raise PublicError(404, "Workspace not found")
    domains = list(
        db.scalars(
            select(DomainAsset)
            .where(DomainAsset.organization_id == org)
            .order_by(DomainAsset.canonical_fqdn)
            .limit(MAX_ASSETS + 1)
        )
    )
    if len(domains) > MAX_ASSETS:
        raise PublicError(409, "Snapshot limit is 20 domains. No records were silently omitted.")
    runs = list(
        db.scalars(
            select(ScanRun)
            .where(ScanRun.organization_id == org, ScanRun.asset_id.in_([a.id for a in domains]))
            .order_by(ScanRun.created_at.desc(), text("scan_runs.rowid DESC"))
            .limit(1000)
        )
    )
    latest: dict[str, ScanRun] = {}
    for run in runs:
        latest.setdefault(run.asset_id, run)
    rows = list(
        db.scalars(
            select(CheckObservation)
            .where(CheckObservation.scan_id.in_([r.id for r in latest.values()]))
            .limit(MAX_ASSETS * 13)
        )
    )
    observations: dict[str, list[CheckObservation]] = {}
    for row in rows:
        observations.setdefault(row.scan_id, []).append(row)
    evaluated = set(
        db.scalars(
            select(FindingEvaluation.scan_id).where(
                FindingEvaluation.organization_id == org,
                FindingEvaluation.policy_version == POLICY,
                FindingEvaluation.scan_id.in_([r.id for r in runs]),
            )
        )
    )
    assets: list[ReportAsset] = []
    safe_runs: list[str] = []
    for asset in domains:
        for run in runs:
            if (
                run.asset_id == asset.id
                and run.id in evaluated
                and eligible(asset, moment, run)
                and run.engine_version == ENGINE
                and run.status in {"completed", "partial", "failed", "interrupted"}
                and run.error_code != "authorization_changed"
            ):
                safe_runs.append(run.id)
        current = latest.get(asset.id)
        source = observations.get(current.id, []) if current else []
        assessed = bool(
            current
            and current.id in safe_runs
            and any(o.outcome in {"pass", "attention", "informational"} for o in source)
        )
        old = bool(current and moment - (current.finished_at or current.created_at) > stale)
        counts = dict(Counter(o.outcome for o in source)) if assessed else {}
        if assessed:
            counts["not_checked"] = max(0, 13 - len(source))
        reason = (
            "Evidence available"
            if assessed
            else (
                "Current ownership proof required"
                if not eligible(asset, moment)
                else "No saved scan"
                if not current
                else "Collection or evaluation still processing"
                if current.status in {"queued", "running"} or current.id not in evaluated
                else "No qualifying authorized evidence"
            )
        )
        assets.append(
            ReportAsset(
                id=asset.id,
                hostname=asset.canonical_fqdn,
                currently_authorized=eligible(asset, moment),
                verification_valid_until=asset.verification_valid_until,
                assessed=assessed,
                reason=reason,
                stale=old,
                scan_id=current.id if current else None,
                scan_status=current.status if current else None,
                scan_finished_at=current.finished_at if current else None,
                observation_counts=counts,
                observations=[
                    SavedObservation(
                        id=o.id,
                        check_id=o.check_id,
                        outcome=o.outcome,
                        observed_at=o.observed_at,
                        values=n.values if (n := normalize(o)) else {},
                    )
                    for o in sorted(source, key=lambda o: o.check_id)
                ]
                if assessed
                else [],
            )
        )
    included = [a.id for a in assets if a.assessed]
    page = finding_page(db, org, Filters(limit=50), stale, included, safe_runs)
    if page.total > MAX_FINDINGS:
        raise PublicError(409, "Snapshot finding limit exceeded. No records were silently omitted.")
    findings = page.items
    while len(findings) < page.total:
        findings.extend(
            finding_page(
                db, org, Filters(limit=50, offset=len(findings)), stale, included, safe_runs
            ).items
        )
    allowed = {f.id for f in findings}
    task_rows = db.execute(
        select(RemediationTask, Finding, DomainAsset.canonical_fqdn)
        .join(
            Finding,
            (Finding.id == RemediationTask.finding_id)
            & (Finding.organization_id == RemediationTask.organization_id),
        )
        .join(
            DomainAsset,
            (DomainAsset.id == Finding.asset_id)
            & (DomainAsset.organization_id == Finding.organization_id),
        )
        .where(RemediationTask.organization_id == org, Finding.id.in_(allowed))
        .order_by(RemediationTask.updated_at.desc(), RemediationTask.id)
        .limit(MAX_TASKS + 1)
    ).all()
    if len(task_rows) > MAX_TASKS:
        raise PublicError(409, "Snapshot task limit exceeded. No records were silently omitted.")
    tasks = [
        ReportTask(
            id=t.id,
            finding_id=f.id,
            title=f.title,
            hostname=host,
            status=t.status,
            owner_label=t.owner_label,
            updated_at=t.updated_at,
            completed_at=t.completed_at,
            finding_status=f.status,
            finding_stale=next(x.stale for x in findings if x.id == f.id),
            recommendation=f.recommendation,
        )
        for t, f, host in task_rows
    ]
    assessed_count = sum(a.assessed for a in assets)
    pending = any(
        a.scan_status in {"queued", "running"}
        or a.reason == "Collection or evaluation still processing"
        for a in assets
    )
    incomplete = any(
        a.assessed
        and (
            a.scan_status != "completed"
            or any(a.observation_counts.get(k, 0) for k in ["error", "inconclusive", "not_checked"])
        )
        for a in assets
    )
    state = (
        "no_assets"
        if not assets
        else "unverified"
        if not any(a.currently_authorized for a in assets)
        else "processing"
        if pending
        else "no_evidence"
        if not assessed_count
        else "stale"
        if any(a.stale for a in assets if a.assessed)
        else "incomplete"
        if incomplete or assessed_count < len(assets)
        else "ready"
    )
    total_findings = (
        db.scalar(select(func.count()).select_from(Finding).where(Finding.organization_id == org))
        or 0
    )
    return Snapshot(
        id=identifier,
        organization_id=org,
        organization_name=organization.name,
        created_at=moment,
        locale=locale,
        policy_version=POLICY,
        readiness=state,
        can_generate=assessed_count > 0,
        counts={
            "enrolled_domains": len(assets),
            "authorized_domains": sum(a.currently_authorized for a in assets),
            "unverified_domains": sum(not a.currently_authorized for a in assets),
            "assessed_domains": assessed_count,
            "without_usable_evidence": len(assets) - assessed_count,
            "stale_domains": sum(a.assessed and a.stale for a in assets),
            "excluded_historical_findings": total_findings - len(findings),
        },
        finding_counts=dict(Counter(f"{f.status}:{f.severity}" for f in findings)),
        task_counts=dict(Counter(t.status for t in tasks)),
        assets=assets,
        findings=findings,
        priorities=page.priorities,
        tasks=tasks,
    )
