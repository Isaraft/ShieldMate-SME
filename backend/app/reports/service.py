"""Atomic SQLite BLOB publication eliminates filesystem paths, symlinks and orphan files."""

import hashlib
import logging
import time
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import Database
from app.domains import locked
from app.errors import PublicError
from app.models import ReportEvent, SecurityReport
from app.reports import pdf
from app.reports.schemas import SCHEMA, CreateReport, ReportMeta
from app.reports.snapshot import collect

logger = logging.getLogger("shieldmate.reports")


def generate(
    database: Database, org: str, actor: str, body: CreateReport, stale: int
) -> ReportMeta:
    moment = int(time.time())
    with database.sessions() as db:
        locked(db)
        recovered = False
        for expired in db.scalars(
            select(SecurityReport).where(
                SecurityReport.status == "generating",
                SecurityReport.organization_id == org,
                SecurityReport.created_at < moment - 300,
            )
        ):
            expired.status, expired.error_code = "failed", "generation_interrupted"
            audit(db, expired, actor, "failed")
            recovered = True
        if recovered:
            db.commit()
            locked(db)
        previous = db.scalar(
            select(SecurityReport).where(
                SecurityReport.organization_id == org,
                SecurityReport.request_key == str(body.request_key),
            )
        )
        if previous:
            if previous.locale != body.locale:
                raise PublicError(409, "This request key was already used for another language.")
            return ReportMeta.model_validate(previous)
        count = (
            db.scalar(
                select(func.count())
                .select_from(SecurityReport)
                .where(SecurityReport.organization_id == org)
            )
            or 0
        )
        if count >= 20:
            raise PublicError(
                429, "Report history limit is 20 snapshots. Existing reports remain available."
            )
        for field, value in [
            (SecurityReport.organization_id, org),
            (SecurityReport.created_by, actor),
        ]:
            if (
                db.scalar(
                    select(func.count())
                    .select_from(SecurityReport)
                    .where(field == value, SecurityReport.created_at > moment - 3600)
                )
                or 0
            ) >= 5:
                raise PublicError(
                    429,
                    "At most five report attempts per hour. Retry later.",
                    headers={"Retry-After": "3600"},
                )
        if db.scalar(
            select(SecurityReport.id).where(
                SecurityReport.organization_id == org, SecurityReport.status == "generating"
            )
        ):
            raise PublicError(409, "A report is already being generated for this workspace.")
        if (
            db.scalar(
                select(func.count())
                .select_from(SecurityReport)
                .where(
                    SecurityReport.status == "generating", SecurityReport.created_at >= moment - 300
                )
            )
            or 0
        ) >= 2:
            raise PublicError(429, "Report service is busy. Retry shortly.")
        identifier = str(uuid4())
        snapshot = collect(db, org, identifier, body.locale, moment, stale)
        if not snapshot.can_generate:
            raise PublicError(
                409,
                "No qualifying authorized evidence is available. "
                "Review domain verification and scans.",
            )
        if len(snapshot.model_dump_json().encode()) > 2 * 1024 * 1024:
            raise PublicError(
                409, "Snapshot size limit exceeded. No records were silently omitted."
            )
        record = SecurityReport(
            id=identifier,
            organization_id=org,
            created_by=actor,
            request_key=str(body.request_key),
            locale=body.locale,
            created_at=moment,
            status="generating",
            schema_version=SCHEMA,
            snapshot=snapshot.model_dump(),
        )
        db.add(record)
        db.flush()
        audit(db, record, actor, "requested")
        db.commit()
    try:
        data = pdf.render(snapshot)
        if not data.startswith(b"%PDF-") or len(data) > pdf.MAX_BYTES:
            raise ValueError("Invalid output")
        with database.sessions() as db:
            locked(db)
            row = db.get(SecurityReport, identifier)
            if row is None or row.status != "generating":
                raise ValueError("Generation lease expired")
            row.pdf, row.byte_count, row.sha256, row.status = (
                data,
                len(data),
                hashlib.sha256(data).hexdigest(),
                "ready",
            )
            audit(db, row, actor, "ready")
            db.commit()
            return ReportMeta.model_validate(row)
    except Exception as exc:
        logger.warning(
            "report_failed report_id=%s exception_type=%s", identifier, type(exc).__name__
        )
        with database.sessions() as db:
            locked(db)
            row = db.get(SecurityReport, identifier)
            if row is None:
                raise PublicError(503, "The report could not be generated. Retry later.") from None
            if row.status == "generating":
                row.status, row.error_code = "failed", "generation_failed"
                audit(db, row, actor, "failed")
                db.commit()
            return ReportMeta.model_validate(row)


def audit(db: Session, report: SecurityReport, actor: str, kind: str) -> None:
    db.add(
        ReportEvent(
            organization_id=report.organization_id,
            report_id=report.id,
            actor_id=actor,
            kind=kind,
            created_at=int(time.time()),
        )
    )
    db.flush()
    identifiers = list(
        db.scalars(
            select(ReportEvent.id)
            .where(ReportEvent.report_id == report.id)
            .order_by(ReportEvent.created_at.desc(), ReportEvent.id.desc())
        )
    )
    if len(identifiers) > 100:
        db.execute(delete(ReportEvent).where(ReportEvent.id.in_(identifiers[100:])))
