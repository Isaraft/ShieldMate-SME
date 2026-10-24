import hashlib
import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response
from sqlalchemy import func, select, text

from app.auth import DB, Mutation, Owner, owned
from app.domains import locked
from app.errors import PublicError
from app.models import SecurityReport
from app.reports.pdf import MAX_BYTES
from app.reports.schemas import CreateReport, HistoryFilter, ReportHistory, ReportMeta, Snapshot
from app.reports.service import audit, generate
from app.reports.snapshot import collect

router = APIRouter(prefix="/reports")


@router.get("/overview", response_model=Snapshot)
def overview(request: Request, user: Owner, db: DB) -> Snapshot:
    org = owned(user, db).id
    db.rollback()
    db.execute(text("BEGIN"))
    return collect(
        db, org, "preview", "en", int(time.time()), request.app.state.settings.finding_stale_seconds
    )


@router.get("", response_model=ReportHistory)
def history(filters: Annotated[HistoryFilter, Query()], user: Owner, db: DB) -> ReportHistory:
    org = owned(user, db).id
    db.rollback()
    db.execute(text("BEGIN"))
    query = select(SecurityReport).where(SecurityReport.organization_id == org)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(SecurityReport.created_at.desc(), SecurityReport.id)
        .offset(filters.offset)
        .limit(filters.limit)
    )
    return ReportHistory(
        items=[ReportMeta.model_validate(r) for r in rows],
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.post("", response_model=ReportMeta)
def create(body: CreateReport, request: Request, user: Owner, db: DB, _: Mutation) -> ReportMeta:
    org, actor = owned(user, db).id, user.id
    db.rollback()
    request.app.state.report_limiter.check("create:" + org, 30)
    return generate(
        request.app.state.database,
        org,
        actor,
        body,
        request.app.state.settings.finding_stale_seconds,
    )


@router.get("/{report_id}", response_model=ReportMeta)
def metadata(report_id: UUID, user: Owner, db: DB) -> ReportMeta:
    record = db.scalar(
        select(SecurityReport).where(
            SecurityReport.id == str(report_id),
            SecurityReport.organization_id == owned(user, db).id,
        )
    )
    if record is None:
        raise PublicError(404, "Report not found")
    return ReportMeta.model_validate(record)


@router.get("/{report_id}/download")
def download(report_id: UUID, request: Request, user: Owner, db: DB) -> Response:
    org, actor = owned(user, db).id, user.id
    request.app.state.report_limiter.check("download:" + org, 180)
    locked(db)
    record = db.scalar(
        select(SecurityReport).where(
            SecurityReport.id == str(report_id), SecurityReport.organization_id == org
        )
    )
    if record is None:
        raise PublicError(404, "Report not found")
    if record.status != "ready":
        audit(db, record, actor, "download_failed")
        db.commit()
        raise PublicError(409, "This report is not ready for download.")
    data = record.pdf
    if (
        not data
        or len(data) > MAX_BYTES
        or len(data) != record.byte_count
        or hashlib.sha256(data).hexdigest() != record.sha256
    ):
        audit(db, record, actor, "download_failed")
        db.commit()
        raise PublicError(409, "Report integrity check failed. This artifact is unavailable.")
    audit(db, record, actor, "downloaded")
    db.commit()
    return Response(
        data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="shieldmate-{record.id}-{record.locale}.pdf"'
            ),
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
