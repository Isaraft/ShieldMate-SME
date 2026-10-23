"""Scoped projections of human work and its independently evaluated finding."""

from collections.abc import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.errors import PublicError
from app.findings.queries import available, output
from app.models import DomainAsset, Finding, FindingEvent, RemediationTask, TaskEvent
from app.tasks.schemas import EventOut, TaskDetail, TaskOut


def task_query(org: str) -> Select[tuple[RemediationTask, Finding, str]]:
    return (
        select(RemediationTask, Finding, DomainAsset.canonical_fqdn)
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
    )


def task_outputs(
    db: Session, org: str, rows: Sequence[Row[tuple[RemediationTask, Finding, str]]], stale: int
) -> list[TaskOut]:
    live = available(db, org, {finding.source_scan_id for _, finding, _ in rows})
    reopened: dict[str, int] = {
        key: value
        for key, value in (
            db.execute(
                select(FindingEvent.finding_id, func.max(FindingEvent.occurred_at))
                .join(Finding, Finding.id == FindingEvent.finding_id)
                .where(
                    Finding.organization_id == org,
                    FindingEvent.kind == "reopened",
                    Finding.id.in_([f.id for _, f, _ in rows]),
                )
                .group_by(FindingEvent.finding_id)
            ).all()
        )
    }
    return [
        TaskOut(
            **{key: getattr(task, key) for key in TaskOut.model_fields if hasattr(task, key)},
            reopened_at=reopened.get(finding.id),
            finding=output(finding, host, live, stale),
        )
        for task, finding, host in rows
    ]


def task_detail(db: Session, org: str, identifier: str, stale: int) -> TaskDetail:
    row = db.execute(task_query(org).where(RemediationTask.id == identifier)).first()
    if row is None:
        raise PublicError(404, "Task not found")
    events = db.scalars(
        select(TaskEvent)
        .where(TaskEvent.task_id == identifier, TaskEvent.organization_id == org)
        .order_by(TaskEvent.version.desc())
        .limit(100)
    )
    return TaskDetail(
        **task_outputs(db, org, [row], stale)[0].model_dump(),
        history=[
            EventOut(
                **{
                    field: getattr(event, field)
                    for field in EventOut.model_fields
                    if hasattr(event, field)
                }
            )
            for event in events
        ],
    )
