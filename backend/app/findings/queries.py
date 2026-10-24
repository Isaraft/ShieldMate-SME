"""Read-only, owner-scoped finding review. No endpoint accepts evidence or severity writes."""

import time
from collections import Counter

from sqlalchemy import and_, case, exists, func, literal_column, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.errors import PublicError
from app.findings.contracts import POLICY, Assessment
from app.findings.schemas import (
    Coverage,
    DomainOption,
    Filters,
    FindingOut,
    FindingPage,
    Summary,
)
from app.models import (
    DomainAsset,
    Finding,
    FindingEvaluation,
    FindingEvent,
    RemediationTask,
    ScanRun,
)
from app.scanner.contracts import ENGINE

PRIORITY = (
    Finding.severity_rank.desc(),
    Finding.urgency.desc(),
    Finding.relevance.desc(),
    case((Finding.confidence == "conclusive", 1), else_=0).desc(),
    Finding.last_seen_at.desc(),
    Finding.fingerprint,
)


def scopes(db: Session, org: str, filters: Filters) -> Select[tuple[Finding, str]]:
    query = (
        select(Finding, DomainAsset.canonical_fqdn)
        .join(
            DomainAsset,
            (DomainAsset.id == Finding.asset_id)
            & (DomainAsset.organization_id == Finding.organization_id),
        )
        .where(Finding.organization_id == org)
    )
    if filters.domain_id:
        if not db.scalar(
            select(DomainAsset.id).where(
                DomainAsset.id == str(filters.domain_id), DomainAsset.organization_id == org
            )
        ):
            raise PublicError(404, "Domain not found")
        query = query.where(Finding.asset_id == str(filters.domain_id))
    if filters.scan_id:
        run = db.scalar(
            select(ScanRun).where(
                ScanRun.id == str(filters.scan_id), ScanRun.organization_id == org
            )
        )
        if run is None or (filters.domain_id and run.asset_id != str(filters.domain_id)):
            raise PublicError(404, "Scan not found")
        saved = db.scalar(
            select(FindingEvaluation).where(
                FindingEvaluation.scan_id == run.id,
                FindingEvaluation.organization_id == org,
                FindingEvaluation.policy_version == POLICY,
            )
        )
        supported = (
            [
                r.rule_id
                for r in Assessment.model_validate(saved.assessment).rules
                if r.decision == "issue"
            ]
            if saved
            else []
        )
        query = query.where(
            or_(
                exists(
                    select(FindingEvent.id).where(
                        FindingEvent.finding_id == Finding.id,
                        FindingEvent.source_scan_id == str(filters.scan_id),
                    )
                ),
                and_(Finding.asset_id == run.asset_id, Finding.rule_id.in_(supported)),
            )
        )
    for field in ("status", "severity", "category"):
        if (value := getattr(filters, field)) != "all":
            query = query.where(getattr(Finding, field) == value)
    if filters.freshness == "not_rechecked":
        query = query.where(Finding.recheck_status == "not_rechecked")
    return query


def available(db: Session, org: str, identifiers: set[str]) -> set[str]:
    return set(
        db.scalars(
            select(ScanRun.id).where(ScanRun.organization_id == org, ScanRun.id.in_(identifiers))
        )
    )


def output(row: Finding, hostname: str, live: set[str], stale_seconds: int) -> FindingOut:
    values = {
        field: getattr(row, field) for field in FindingOut.model_fields if hasattr(row, field)
    }
    return FindingOut(
        **values,
        hostname=hostname,
        source_scan_available=row.source_scan_id in live,
        stale=int(time.time()) - row.observed_at > stale_seconds,
        ranking_reason=(
            f"{row.severity.title()} severity; urgency {row.urgency}/3; "
            f"observed relevance {row.relevance}/2; {row.confidence} evidence. "
            "Ties use newest issue observation, then stable fingerprint. These"
            " are ordering labels, not a risk score."
        ),
    )


def coverage(db: Session, org: str, filters: Filters, stale_seconds: int) -> Coverage:
    rank = (
        select(
            ScanRun.id,
            func.row_number()
            .over(
                partition_by=ScanRun.asset_id,
                order_by=(ScanRun.created_at.desc(), literal_column("scan_runs.rowid").desc()),
            )
            .label("rank"),
        )
        .where(ScanRun.organization_id == org)
        .subquery()
    )
    query = (
        select(ScanRun)
        .join(
            DomainAsset,
            (DomainAsset.id == ScanRun.asset_id)
            & (DomainAsset.organization_id == ScanRun.organization_id),
        )
        .where(ScanRun.organization_id == org)
    )
    if filters.scan_id:
        query = query.where(ScanRun.id == str(filters.scan_id))
    else:
        query = query.where(ScanRun.id.in_(select(rank.c.id).where(rank.c.rank == 1)))
    if filters.domain_id:
        query = query.where(ScanRun.asset_id == str(filters.domain_id))
    runs = list(db.scalars(query.limit(100)))
    evaluations = list(
        db.scalars(
            select(FindingEvaluation).where(
                FindingEvaluation.organization_id == org,
                FindingEvaluation.policy_version == POLICY,
                FindingEvaluation.scan_id.in_([run.id for run in runs]),
            )
        )
    )
    counts: Counter[str] = Counter()
    rules: Counter[str] = Counter()
    for evaluation in evaluations:
        counts.update(Assessment.model_validate(evaluation.assessment).observation_counts)
        rules.update(Assessment.model_validate(evaluation.assessment).coverage)
    pending = sum(run.status not in {"queued", "running"} for run in runs) - len(evaluations)
    return Coverage(
        policy_version=POLICY,
        source_scans=len(runs),
        evaluated_scans=len(evaluations),
        pending_evaluations=pending,
        in_flight_scans=sum(run.status in {"queued", "running"} for run in runs),
        stale_assessments=sum(
            int(time.time()) - (run.finished_at or run.created_at) > stale_seconds for run in runs
        ),
        unsupported_scans=sum(run.engine_version != ENGINE for run in runs),
        observation_counts=dict(counts),
        rule_counts=dict(rules),
        last_scan_at=max((run.finished_at or run.created_at for run in runs), default=None),
        notes=(
            "Latest scan per selected asset, or the selected source scan. "
            "Observation counts describe collection; six rule decisions describe "
            "this limited policy. "
            "CSP/HTML policy effectiveness, outbound mail use and whole-company security "
            "are not assessed. No numerical score is calculated."
        ),
    )


def attach_tasks(db: Session, org: str, records: list[FindingOut]) -> list[FindingOut]:
    links = {
        t.finding_id: t
        for t in db.scalars(
            select(RemediationTask).where(
                RemediationTask.organization_id == org,
                RemediationTask.finding_id.in_([f.id for f in records]),
            )
        )
    }
    for record in records:
        if task := links.get(record.id):
            record.task_id, record.task_status = task.id, task.status
    return records


def finding_page(
    db: Session,
    org: str,
    filters: Filters,
    stale: int,
    asset_ids: list[str] | None = None,
    evidence_scan_ids: list[str] | None = None,
) -> FindingPage:
    query = scopes(db, org, filters)
    if asset_ids is not None:
        query = query.where(Finding.asset_id.in_(asset_ids))
    if evidence_scan_ids is not None:
        query = query.where(Finding.source_scan_id.in_(evidence_scan_ids))
    if filters.freshness == "stale":
        query = query.where(Finding.observed_at < int(time.time()) - stale)
    subquery = query.subquery()
    total = db.scalar(select(func.count()).select_from(subquery)) or 0
    states: dict[str, int] = {
        key: count
        for key, count in db.execute(
            select(subquery.c.status, func.count()).group_by(subquery.c.status)
        ).all()
    }
    severities: dict[str, int] = {
        key: count
        for key, count in db.execute(
            select(subquery.c.severity, func.count()).group_by(subquery.c.severity)
        ).all()
    }
    categories: dict[str, int] = {
        key: count
        for key, count in db.execute(
            select(subquery.c.category, func.count()).group_by(subquery.c.category)
        ).all()
    }
    order = {
        "priority": PRIORITY,
        "newest": (Finding.last_seen_at.desc(), Finding.fingerprint),
        "oldest": (Finding.first_seen_at, Finding.fingerprint),
        "domain": (DomainAsset.canonical_fqdn, *PRIORITY),
    }[filters.sort]
    rows = list(db.execute(query.order_by(*order).offset(filters.offset).limit(filters.limit)))
    top = list(db.execute(query.where(Finding.status == "open").order_by(*PRIORITY).limit(3)))
    live = available(db, org, {row.source_scan_id for row, _ in [*rows, *top]})
    return FindingPage(
        domains=[
            DomainOption(id=asset.id, hostname=asset.canonical_fqdn)
            for asset in db.scalars(
                select(DomainAsset)
                .where(DomainAsset.organization_id == org)
                .order_by(DomainAsset.canonical_fqdn)
            )
        ],
        items=attach_tasks(db, org, [output(row, host, live, stale) for row, host in rows]),
        priorities=attach_tasks(db, org, [output(row, host, live, stale) for row, host in top]),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
        summary=Summary(
            total=total,
            counts_by_status=states,
            counts_by_severity=severities,
            counts_by_category=categories,
            assessment=coverage(db, org, filters, stale),
        ),
    )
