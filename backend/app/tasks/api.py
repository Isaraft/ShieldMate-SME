import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.auth import DB, Mutation, Owner, owned
from app.domains import locked
from app.errors import PublicError
from app.findings.queries import PRIORITY
from app.findings.schemas import DomainOption
from app.models import DomainAsset, Finding, RemediationTask, TaskEvent
from app.tasks.schemas import EmptyInput, TaskDetail, TaskFilters, TaskPage, TaskPatch
from app.tasks.service import task_detail, task_outputs, task_query

router = APIRouter()


def budget(request: Request, db: Session, org: str) -> None:
    try:
        request.app.state.task_limiter.check(org, 180)
    except PublicError:
        raise PublicError(429, "Too many task requests. Retry in 15 minutes.") from None
    count = (
        db.scalar(
            select(func.count())
            .select_from(TaskEvent)
            .where(TaskEvent.organization_id == org, TaskEvent.created_at > int(time.time()) - 900)
        )
        or 0
    )
    if count >= 60:
        raise PublicError(
            429, "Task change limit reached. Retry in 15 minutes.", headers={"Retry-After": "900"}
        )


@router.get("/tasks", response_model=TaskPage)
def listing(
    filters: Annotated[TaskFilters, Query()], request: Request, user: Owner, db: DB
) -> TaskPage:
    org = owned(user, db).id
    db.rollback()
    db.execute(text("BEGIN"))
    query = task_query(org)
    if filters.domain_id:
        if not db.scalar(
            select(DomainAsset.id).where(
                DomainAsset.id == str(filters.domain_id), DomainAsset.organization_id == org
            )
        ):
            raise PublicError(404, "Domain not found")
        query = query.where(Finding.asset_id == str(filters.domain_id))
    if filters.status != "all":
        query = query.where(RemediationTask.status == filters.status)
    if filters.severity != "all":
        query = query.where(Finding.severity == filters.severity)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    order = {
        "updated": (RemediationTask.updated_at.desc(), RemediationTask.id),
        "oldest": (RemediationTask.created_at, RemediationTask.id),
        "priority": PRIORITY,
    }[filters.sort]
    rows = db.execute(query.order_by(*order).offset(filters.offset).limit(filters.limit)).all()
    return TaskPage(
        items=task_outputs(db, org, rows, request.app.state.settings.finding_stale_seconds),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
        domains=[
            DomainOption(id=d.id, hostname=d.canonical_fqdn)
            for d in db.scalars(
                select(DomainAsset)
                .where(DomainAsset.organization_id == org)
                .order_by(DomainAsset.canonical_fqdn)
            )
        ],
    )


@router.get("/tasks/{task_id}", response_model=TaskDetail)
def detail(task_id: UUID, request: Request, user: Owner, db: DB) -> TaskDetail:
    org = owned(user, db).id
    db.rollback()
    db.execute(text("BEGIN"))
    return task_detail(db, org, str(task_id), request.app.state.settings.finding_stale_seconds)


@router.post("/findings/{finding_id}/task", response_model=TaskDetail)
def create(
    finding_id: UUID, body: EmptyInput, request: Request, user: Owner, db: DB, _: Mutation
) -> TaskDetail:
    org, actor = owned(user, db).id, user.id
    locked(db)
    finding = db.scalar(
        select(Finding)
        .join(DomainAsset, DomainAsset.id == Finding.asset_id)
        .where(
            Finding.id == str(finding_id),
            Finding.organization_id == org,
            DomainAsset.organization_id == org,
        )
    )
    if finding is None:
        raise PublicError(404, "Finding not found")
    existing = db.scalar(
        select(RemediationTask).where(
            RemediationTask.finding_id == finding.id, RemediationTask.organization_id == org
        )
    )
    if existing:
        # Per-process request budget also covers idempotent reads through this POST.
        try:
            request.app.state.task_limiter.check(org, 180)
        except PublicError:
            raise PublicError(429, "Too many task requests. Retry in 15 minutes.") from None
        return task_detail(db, org, existing.id, request.app.state.settings.finding_stale_seconds)
    if finding.status != "open":
        raise PublicError(409, "This finding is resolved. A new task is not needed.")
    budget(request, db, org)
    moment = int(time.time())
    task = RemediationTask(
        organization_id=org, finding_id=finding.id, created_at=moment, updated_at=moment
    )
    db.add(task)
    db.flush()
    db.add(
        TaskEvent(
            organization_id=org,
            task_id=task.id,
            actor_id=actor,
            version=1,
            kind="created",
            created_at=moment,
            changes={"status": {"old": "", "new": "todo"}},
        )
    )
    identifier = task.id
    db.commit()
    db.expire_all()
    db.execute(text("BEGIN"))
    return task_detail(db, org, identifier, request.app.state.settings.finding_stale_seconds)


@router.patch("/tasks/{task_id}", response_model=TaskDetail)
def edit(
    task_id: UUID, body: TaskPatch, request: Request, user: Owner, db: DB, _: Mutation
) -> TaskDetail:
    org, actor = owned(user, db).id, user.id
    locked(db)
    row = db.execute(task_query(org).where(RemediationTask.id == str(task_id))).first()
    if row is None:
        raise PublicError(404, "Task not found")
    task = row[0]
    budget(request, db, org)
    changes = {
        key: {"old": getattr(task, key), "new": getattr(body, key)}
        for key in body.model_fields_set - {"version"}
        if getattr(task, key) != getattr(body, key)
    }
    if not changes:
        return task_detail(db, org, task.id, request.app.state.settings.finding_stale_seconds)
    if task.version != body.version:
        raise PublicError(
            409, "This task changed elsewhere. Reload the latest version before saving."
        )
    for key, value in changes.items():
        setattr(task, key, value["new"])
    moment = int(time.time())
    if "status" in changes:
        task.completed_at = moment if task.status == "done" else None
    task.updated_at, task.version = moment, task.version + 1
    db.add(
        TaskEvent(
            organization_id=org,
            task_id=task.id,
            actor_id=actor,
            version=task.version,
            kind="updated",
            created_at=moment,
            changes=changes,
        )
    )
    db.flush()
    events = list(
        db.scalars(
            select(TaskEvent.id)
            .where(TaskEvent.task_id == task.id)
            .order_by(TaskEvent.version.desc())
        )
    )
    if len(events) > 100:
        db.execute(delete(TaskEvent).where(TaskEvent.id.in_(events[99:-1])))
        task.history_truncated = True
    identifier = task.id
    db.commit()
    db.expire_all()
    db.execute(text("BEGIN"))
    return task_detail(db, org, identifier, request.app.state.settings.finding_stale_seconds)
