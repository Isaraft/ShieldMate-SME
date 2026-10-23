import secrets
import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import DB, Mutation, Owner, owned
from app.domain_validation import canonical_domain
from app.errors import PublicError
from app.models import DomainAsset, DomainEvent

router = APIRouter(prefix="/domains")
POLICY = "starter-authorization-v1"


class Enrollment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fqdn: str = Field(min_length=1, max_length=254)
    authorization_acknowledged: StrictBool

    @field_validator("authorization_acknowledged")
    @classmethod
    def consent(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Explicit authorization is required")
        return value

    @field_validator("fqdn")
    @classmethod
    def validate_fqdn(cls, value: str) -> str:
        return canonical_domain(value)


class DomainOut(BaseModel):
    id: str
    canonical_fqdn: str
    status: str
    created_at: int
    authorization_attested_at: int
    authorization_policy_version: str
    challenge_generation: int
    challenge_issued_at: int
    challenge_expires_at: int
    verified_at: int | None
    verification_valid_until: int | None
    last_verification_checked_at: int | None
    last_verification_error_code: str | None
    record_type: str = "TXT"
    record_hostname: str
    relative_hostname: str = "_shieldmate-challenge"
    record_value: str
    scan_available: bool = False


def now() -> int:
    return int(time.time())


def output(asset: DomainAsset) -> DomainOut:
    moment = now()
    status = "pending"
    if asset.verified_at:
        status = "verified" if (asset.verification_valid_until or 0) > moment else "stale"
    elif asset.challenge_expires_at <= moment:
        status = "expired"
    return DomainOut(
        id=asset.id,
        canonical_fqdn=asset.canonical_fqdn,
        status=status,
        created_at=asset.created_at,
        authorization_attested_at=asset.authorization_attested_at,
        authorization_policy_version=asset.authorization_policy_version,
        challenge_generation=asset.challenge_generation,
        challenge_issued_at=asset.challenge_issued_at,
        challenge_expires_at=asset.challenge_expires_at,
        verified_at=asset.verified_at,
        verification_valid_until=asset.verification_valid_until,
        last_verification_checked_at=asset.last_verification_checked_at,
        last_verification_error_code=asset.last_verification_error_code,
        record_hostname="_shieldmate-challenge." + asset.canonical_fqdn,
        record_value="shieldmate-verification=" + asset.challenge_token,
    )


def event(db: Session, org: str, asset: str, kind: str) -> None:
    db.add(DomainEvent(organization_id=org, asset_id=asset, event=kind, occurred_at=now()))


def limit(db: Session, request: Request, org: str) -> None:
    request.app.state.domain_limiter.check(
        request.client.host if request.client else "unknown",
        request.app.state.settings.domain_ip_rate_limit,
    )
    # Persisted per-org budget survives restart; SQLite write lock serializes quota and limits.
    count = db.scalar(
        select(func.count())
        .select_from(DomainEvent)
        .where(DomainEvent.organization_id == org, DomainEvent.occurred_at > now() - 900)
    )
    if count >= request.app.state.settings.domain_rate_limit:
        raise PublicError(429, "Too many asset actions. Retry in 15 minutes.")


def locked(db: Session) -> None:
    db.rollback()  # End the authentication read transaction before acquiring the write lock.
    db.execute(text("BEGIN IMMEDIATE"))


def asset_for(db: Session, org: str, domain_id: UUID) -> DomainAsset:
    asset = db.scalar(
        select(DomainAsset).where(
            DomainAsset.id == str(domain_id), DomainAsset.organization_id == org
        )
    )
    if asset is None:
        raise PublicError(404, "Domain not found")
    return asset


@router.get("", response_model=list[DomainOut])
def list_domains(user: Owner, db: DB) -> list[DomainOut]:
    org = owned(user, db)
    return [
        output(a)
        for a in db.scalars(
            select(DomainAsset)
            .where(DomainAsset.organization_id == org.id)
            .order_by(DomainAsset.created_at, DomainAsset.id)
        )
    ]


@router.post("", status_code=201, response_model=DomainOut)
def enroll(body: Enrollment, request: Request, user: Owner, db: DB, _: Mutation) -> DomainOut:
    org_id = owned(user, db).id
    locked(db)
    limit(db, request, org_id)
    if (
        db.scalar(
            select(func.count())
            .select_from(DomainAsset)
            .where(DomainAsset.organization_id == org_id)
        )
        >= request.app.state.settings.domain_quota
    ):
        raise PublicError(
            409, "Workspace domain quota reached. Remove an asset before adding another."
        )
    moment = now()
    asset = DomainAsset(
        organization_id=org_id,
        canonical_fqdn=body.fqdn,
        created_at=moment,
        updated_at=moment,
        authorization_attested_at=moment,
        authorization_policy_version=POLICY,
        challenge_token=secrets.token_urlsafe(32),
        challenge_generation=1,
        challenge_issued_at=moment,
        challenge_expires_at=moment + request.app.state.settings.challenge_seconds,
    )
    db.add(asset)
    try:
        db.flush()
        event(db, org_id, asset.id, "enrolled")
        db.commit()
    except IntegrityError:
        db.rollback()
        raise PublicError(409, "This domain is already in your workspace") from None
    return output(asset)


@router.get("/{domain_id}", response_model=DomainOut)
def detail(domain_id: UUID, user: Owner, db: DB) -> DomainOut:
    return output(asset_for(db, owned(user, db).id, domain_id))


@router.delete("/{domain_id}")
def remove(domain_id: UUID, user: Owner, db: DB, _: Mutation) -> dict[str, str]:
    org_id = owned(user, db).id
    locked(db)
    asset = asset_for(db, org_id, domain_id)
    db.delete(asset)
    event(db, org_id, str(domain_id), "removed")
    db.commit()
    return {"message": "Domain removed"}


@router.post("/{domain_id}/verification/request", response_model=DomainOut)
def reissue(domain_id: UUID, request: Request, user: Owner, db: DB, _: Mutation) -> DomainOut:
    org_id = owned(user, db).id
    locked(db)
    asset = asset_for(db, org_id, domain_id)
    limit(db, request, org_id)
    moment = now()
    asset.challenge_token = secrets.token_urlsafe(32)
    asset.challenge_generation += 1
    asset.challenge_issued_at = asset.updated_at = moment
    asset.challenge_expires_at = moment + request.app.state.settings.challenge_seconds
    asset.verified_at = asset.verification_valid_until = None
    asset.last_verification_error_code = None
    event(db, org_id, asset.id, "challenge_rotated")
    db.commit()
    return output(asset)


@router.post("/{domain_id}/verification/check")
def verify(domain_id: UUID, request: Request, user: Owner, db: DB, _: Mutation) -> dict[str, Any]:
    org_id = owned(user, db).id
    locked(db)
    asset = asset_for(db, org_id, domain_id)
    limit(db, request, org_id)
    initial = output(asset)
    generation = asset.challenge_generation
    event(db, org_id, asset.id, "verification_requested")
    db.commit()  # Never hold a database write lock across network I/O.
    if initial.challenge_expires_at <= now():
        return {"code": "challenge_expired", "domain": initial}
    result = request.app.state.check_txt(
        initial.record_hostname, initial.record_value, request.app.state.settings.dns_timeout
    )
    moment = now()
    values: dict[str, Any] = {
        "last_verification_checked_at": moment,
        "last_verification_error_code": None if result == "match" else result,
        "updated_at": moment,
    }
    if result == "match":
        values.update(
            verified_at=moment,
            verification_valid_until=moment + request.app.state.settings.verification_seconds,
        )
    # Compare current generation, owner and expiry atomically, including after network I/O.
    changed = db.execute(
        update(DomainAsset)
        .where(
            DomainAsset.id == str(domain_id),
            DomainAsset.organization_id == org_id,
            DomainAsset.challenge_generation == generation,
            DomainAsset.challenge_expires_at > moment,
        )
        .values(**values)
    )
    if getattr(changed, "rowcount", 0) != 1:
        db.rollback()
        raise PublicError(
            409, "Challenge changed, expired or domain removed. Reload before verifying."
        )
    event(db, org_id, str(domain_id), "verified" if result == "match" else result)
    db.commit()
    db.expire_all()
    return {
        "code": "verified" if result == "match" else result,
        "domain": output(asset_for(db, org_id, domain_id)),
    }
