"""Read-only organization overview; ranking is exclusively the Phase 05 query policy."""

import time

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import and_, func, select, text

from app.auth import DB, OrganizationOut, Owner, owned
from app.findings.queries import finding_page
from app.findings.schemas import Filters, FindingPage
from app.models import CheckObservation, DomainAsset, Finding, RemediationTask, ScanRun, TaskEvent
from app.scanner.contracts import ENGINE
from app.scanner.policy import eligible
from app.tasks.schemas import TaskOut
from app.tasks.service import task_outputs, task_query

router = APIRouter(prefix="/dashboard")


class RecentScan(BaseModel):
    id: str
    asset_id: str
    hostname: str
    status: str
    created_at: int
    finished_at: int | None
    completed_checks: int


class Activity(BaseModel):
    task_id: str
    title: str
    kind: str
    version: int
    created_at: int
    actor_label: str = "Workspace owner"


class DashboardOut(BaseModel):
    organization: OrganizationOut
    generated_at: int
    asset_count: int
    verified_assets: int
    eligible_assets: int
    task_counts: dict[str, int]
    done_unverified: int
    recent_scan_count: int
    last_useful_observation_at: int | None
    findings: FindingPage
    tasks: list[TaskOut]
    scans: list[RecentScan]
    activity: list[Activity]


@router.get("/summary", response_model=DashboardOut)
def summary(request: Request, user: Owner, db: DB) -> DashboardOut:
    org = owned(user, db).id
    db.rollback()
    db.execute(text("BEGIN"))
    organization = owned(user, db)
    moment = int(time.time())
    assets = list(db.scalars(select(DomainAsset).where(DomainAsset.organization_id == org)))
    tasks = task_query(org)
    counts: dict[str, int] = {
        key: value
        for key, value in (
            db.execute(
                select(RemediationTask.status, func.count())
                .join(
                    Finding,
                    and_(
                        Finding.id == RemediationTask.finding_id,
                        Finding.organization_id == RemediationTask.organization_id,
                    ),
                )
                .join(
                    DomainAsset,
                    and_(
                        DomainAsset.id == Finding.asset_id,
                        DomainAsset.organization_id == Finding.organization_id,
                    ),
                )
                .where(RemediationTask.organization_id == org)
                .group_by(RemediationTask.status)
            ).all()
        )
    }
    scans = (
        select(ScanRun)
        .join(
            DomainAsset,
            and_(
                DomainAsset.id == ScanRun.asset_id,
                DomainAsset.organization_id == ScanRun.organization_id,
            ),
        )
        .where(ScanRun.organization_id == org)
    )
    latest = db.scalars(
        scans.order_by(ScanRun.created_at.desc(), text("scan_runs.rowid DESC")).limit(5)
    )
    useful = db.scalar(
        select(func.max(CheckObservation.observed_at))
        .join(ScanRun, ScanRun.id == CheckObservation.scan_id)
        .join(
            DomainAsset,
            and_(
                DomainAsset.id == ScanRun.asset_id,
                DomainAsset.organization_id == ScanRun.organization_id,
            ),
        )
        .where(
            ScanRun.organization_id == org,
            ScanRun.engine_version == ENGINE,
            (ScanRun.error_code.is_(None)) | (ScanRun.error_code != "authorization_changed"),
            CheckObservation.outcome.in_(["pass", "attention", "informational"]),
        )
    )
    done_unverified = (
        db.scalar(
            select(func.count()).select_from(
                tasks.where(RemediationTask.status == "done", Finding.status == "open").subquery()
            )
        )
        or 0
    )
    activity = db.execute(
        select(TaskEvent, Finding.title)
        .join(
            RemediationTask,
            and_(
                RemediationTask.id == TaskEvent.task_id,
                RemediationTask.organization_id == TaskEvent.organization_id,
            ),
        )
        .join(
            Finding,
            and_(
                Finding.id == RemediationTask.finding_id,
                Finding.organization_id == RemediationTask.organization_id,
            ),
        )
        .where(TaskEvent.organization_id == org)
        .order_by(TaskEvent.created_at.desc(), text("task_events.rowid DESC"))
        .limit(5)
    ).all()
    return DashboardOut(
        organization=OrganizationOut.model_validate(organization),
        generated_at=moment,
        asset_count=len(assets),
        verified_assets=sum(
            a.verified_at is not None and (a.verification_valid_until or 0) > moment for a in assets
        ),
        eligible_assets=sum(eligible(a, moment) for a in assets),
        task_counts=counts,
        done_unverified=done_unverified,
        recent_scan_count=db.scalar(select(func.count()).select_from(scans.subquery())) or 0,
        last_useful_observation_at=useful,
        findings=finding_page(
            db,
            org,
            Filters(status="open", limit=1),
            request.app.state.settings.finding_stale_seconds,
        ),
        tasks=task_outputs(
            db,
            org,
            db.execute(
                tasks.order_by(RemediationTask.updated_at.desc(), RemediationTask.id).limit(5)
            ).all(),
            request.app.state.settings.finding_stale_seconds,
        ),
        scans=[
            RecentScan(**{key: getattr(run, key) for key in RecentScan.model_fields})
            for run in latest
        ],
        activity=[
            Activity(
                task_id=e.task_id,
                title=title,
                kind=e.kind,
                version=e.version,
                created_at=e.created_at,
            )
            for e, title in activity
        ],
    )
