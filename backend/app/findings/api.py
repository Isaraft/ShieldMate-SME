"""Read-only organization-scoped finding review."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import Integer, literal_column, select, text

from app.auth import DB, Owner, owned
from app.errors import PublicError
from app.findings.contracts import POLICY, Assessment, Evaluation
from app.findings.queries import attach_tasks, available, finding_page, output
from app.findings.schemas import AssessmentOut, Filters, FindingDetail, FindingPage, HistoryOut
from app.models import DomainAsset, Finding, FindingEvaluation, FindingEvent, ScanRun

router = APIRouter(prefix="/findings")


@router.get("", response_model=FindingPage)
def listing(
    filters: Annotated[Filters, Query()], request: Request, user: Owner, db: DB
) -> FindingPage:
    org = owned(user, db).id
    db.rollback()
    db.execute(text("BEGIN"))
    return finding_page(db, org, filters, request.app.state.settings.finding_stale_seconds)


@router.get("/assessments/{scan_id}", response_model=AssessmentOut)
def assessment(scan_id: UUID, user: Owner, db: DB) -> AssessmentOut:
    org = owned(user, db).id
    # One read snapshot keeps totals, rows, priorities and provenance mutually consistent.
    db.rollback()
    db.execute(text("BEGIN"))
    run = db.scalar(
        select(ScanRun)
        .join(
            DomainAsset,
            (DomainAsset.id == ScanRun.asset_id)
            & (DomainAsset.organization_id == ScanRun.organization_id),
        )
        .where(ScanRun.id == str(scan_id), ScanRun.organization_id == org)
    )
    if run is None:
        raise PublicError(404, "Scan not found")
    saved = db.scalar(
        select(FindingEvaluation).where(
            FindingEvaluation.scan_id == run.id,
            FindingEvaluation.organization_id == org,
            FindingEvaluation.policy_version == POLICY,
        )
    )
    return AssessmentOut(
        scan_id=run.id,
        asset_id=run.asset_id,
        status="evaluated"
        if saved
        else "in_flight"
        if run.status in {"queued", "running"}
        else "pending",
        assessment=Assessment.model_validate(saved.assessment) if saved else None,
    )


@router.get("/{finding_id}", response_model=FindingDetail)
def detail(finding_id: UUID, request: Request, user: Owner, db: DB) -> FindingDetail:
    org = owned(user, db).id
    # One read snapshot keeps totals, rows, priorities and provenance mutually consistent.
    db.rollback()
    db.execute(text("BEGIN"))
    selected = db.execute(
        select(Finding, DomainAsset.canonical_fqdn)
        .join(
            DomainAsset,
            (DomainAsset.id == Finding.asset_id)
            & (DomainAsset.organization_id == Finding.organization_id),
        )
        .where(Finding.id == str(finding_id), Finding.organization_id == org)
    ).first()
    if selected is None:
        raise PublicError(404, "Finding not found")
    row, host = selected
    events = list(
        db.scalars(
            select(FindingEvent)
            .where(FindingEvent.finding_id == row.id)
            .order_by(
                FindingEvent.occurred_at.desc(),
                literal_column("finding_events.rowid", Integer).desc(),
            )
            .limit(50)
        )
    )
    live = available(db, org, {row.source_scan_id, *(event.source_scan_id for event in events)})
    return FindingDetail(
        **attach_tasks(
            db, org, [output(row, host, live, request.app.state.settings.finding_stale_seconds)]
        )[0].model_dump(),
        history=[
            HistoryOut(
                kind=event.kind,
                source_scan_id=event.source_scan_id,
                source_scan_available=event.source_scan_id in live,
                policy_version=event.policy_version,
                occurred_at=event.occurred_at,
                snapshot=Evaluation.model_validate(event.snapshot),
            )
            for event in events
        ],
    )
