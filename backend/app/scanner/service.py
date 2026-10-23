"""Organization-scoped durable queue and read contracts. No network I/O in API requests."""

import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.auth import DB, Mutation, Owner, owned
from app.domains import asset_for, event, locked
from app.errors import PublicError
from app.models import CheckObservation, ScanRun
from app.scanner.contracts import ACTIVE, CHECKS, Observation, State
from app.scanner.policy import eligible

router = APIRouter(prefix="/domains/{domain_id}/scans")


class EmptyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    asset_id: str
    hostname: str
    status: State
    created_at: int
    started_at: int | None
    finished_at: int | None
    error_code: str | None
    completed_checks: int
    total_checks: int = len(CHECKS)
    engine_version: str


class ObservationOut(Observation):
    asset_id: str
    engine_version: str


class ScanDetail(ScanOut):
    observations: list[ObservationOut]


class History(BaseModel):
    items: list[ScanOut]
    offset: int
    limit: int
    total: int


def recover(db: Session, moment: int) -> None:
    db.execute(
        update(ScanRun)
        .where(ScanRun.status == "running", ScanRun.lease_until <= moment)
        .values(status="interrupted", finished_at=moment, error_code="worker_interrupted")
    )
    db.execute(
        update(ScanRun)
        .where(ScanRun.status == "queued", ScanRun.created_at <= moment - 900)
        .values(status="failed", finished_at=moment, error_code="queue_expired")
    )


@router.post("", status_code=202, response_model=ScanOut)
def enqueue(
    domain_id: UUID,
    request: Request,
    user: Owner,
    db: DB,
    _: Mutation,
    body: EmptyRequest | None = None,
) -> ScanOut:
    org_id, user_id = owned(user, db).id, user.id
    locked(db)
    moment = int(time.time())
    recover(db, moment)
    asset = asset_for(db, org_id, domain_id)
    if not eligible(asset, moment):
        raise PublicError(409, "Fresh DNS verification and recorded authorization are required.")
    if db.scalar(
        select(ScanRun.id).where(ScanRun.asset_id == asset.id, ScanRun.status.in_(ACTIVE))
    ):
        raise PublicError(409, "A scan is already queued or running for this domain.")
    settings = request.app.state.settings
    recent = ScanRun.created_at > moment - 3600
    for scope, maximum in (
        (ScanRun.requested_by == user_id, settings.scan_user_hourly),
        (ScanRun.organization_id == org_id, settings.scan_org_hourly),
        (ScanRun.asset_id == asset.id, settings.scan_domain_hourly),
    ):
        if db.scalar(select(func.count()).select_from(ScanRun).where(scope, recent)) >= maximum:
            raise PublicError(429, "Scan quota reached. Retry after the hourly window.")
    if (
        db.scalar(select(func.count()).select_from(ScanRun).where(ScanRun.status.in_(ACTIVE)))
        >= settings.scan_queue_limit
    ):
        raise PublicError(429, "The scan queue is full. Retry later.")
    # Bounded stored history per organization. Never remove recent quota accounting or active work.
    history = list(
        db.scalars(
            select(ScanRun)
            .where(ScanRun.organization_id == org_id)
            .order_by(ScanRun.created_at, ScanRun.id)
        )
    )
    if len(history) >= settings.scan_history_limit:
        removable = next(
            (r for r in history if r.status not in ACTIVE and r.created_at <= moment - 3600), None
        )
        if removable is None:
            raise PublicError(429, "Scan history capacity reached. Retry after one hour.")
        db.execute(delete(ScanRun).where(ScanRun.id == removable.id))
    run = ScanRun(
        organization_id=org_id,
        requested_by=user_id,
        asset_id=asset.id,
        hostname=asset.canonical_fqdn,
        proof_generation=asset.challenge_generation,
        proof_verified_at=asset.verified_at,
        status="queued",
        created_at=moment,
    )
    db.add(run)
    db.flush()
    event(db, org_id, asset.id, "scan_queued")
    db.commit()
    return ScanOut.model_validate(run)


@router.get("", response_model=History)
def history(
    domain_id: UUID,
    user: Owner,
    db: DB,
    offset: Annotated[int, Query(ge=0, le=100000)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> History:
    org_id = owned(user, db).id
    asset_for(db, org_id, domain_id)
    recover(db, int(time.time()))
    scope = (ScanRun.organization_id == org_id, ScanRun.asset_id == str(domain_id))
    count = db.scalar(select(func.count()).select_from(ScanRun).where(*scope)) or 0
    rows = db.scalars(
        select(ScanRun)
        .where(*scope)
        .order_by(ScanRun.created_at.desc(), ScanRun.id.desc())
        .offset(offset)
        .limit(limit)
    )
    result = History(
        items=[ScanOut.model_validate(row) for row in rows], total=count, offset=offset, limit=limit
    )
    db.commit()
    return result


@router.get("/{scan_id}", response_model=ScanDetail)
def detail(domain_id: UUID, scan_id: UUID, user: Owner, db: DB) -> ScanDetail:
    org_id = owned(user, db).id
    asset_for(db, org_id, domain_id)
    recover(db, int(time.time()))
    run = db.scalar(
        select(ScanRun).where(
            ScanRun.id == str(scan_id),
            ScanRun.asset_id == str(domain_id),
            ScanRun.organization_id == org_id,
        )
    )
    if run is None:
        raise PublicError(404, "Scan not found")
    observations = db.scalars(
        select(CheckObservation)
        .where(CheckObservation.scan_id == run.id)
        .order_by(CheckObservation.observed_at, CheckObservation.check_id)
        .limit(len(CHECKS))
    )
    result = ScanDetail(
        **ScanOut.model_validate(run).model_dump(),
        observations=[
            ObservationOut(
                **{key: getattr(row, key) for key in Observation.model_fields},
                asset_id=run.asset_id,
                engine_version=run.engine_version,
            )
            for row in observations
        ],
    )
    db.commit()
    return result
