import hashlib
import hmac
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_session
from app.errors import PublicError as HTTPException
from app.models import LoginSession, Organization, User

router = APIRouter()
DB = Annotated[Session, Depends(get_session)]
hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))
COOKIE = "shieldmate_session"
# Single-process local MVP limiter; bounded keys, monotonic expiry, never stores email/password.
_attempts: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def csrf_value(token: str) -> str:
    """Session-bound, domain-separated token; stable across tabs, never persisted raw."""
    return hmac.new(token.encode(), b"shieldmate-csrf-v1", hashlib.sha256).hexdigest()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def email_valid(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(
            r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,63}", value
        ):
            raise ValueError("Enter a valid email address")
        local, domain = value.rsplit("@", 1)
        if (
            local.startswith(".")
            or local.endswith(".")
            or ".." in local
            or any(
                not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
                for label in domain.split(".")
            )
        ):
            raise ValueError("Enter a valid email address")
        return value


class OrganizationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value or any(ord(c) < 32 for c in value):
            raise ValueError("Enter a company name")
        return value


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    created_at: int
    updated_at: int


class Identity(BaseModel):
    id: str
    email: str
    organization: OrganizationOut | None


def cookie_name(request: Request) -> str:
    # Cookies are not port-scoped; parallel local profiles must not overwrite each other.
    return (
        "shieldmate_rc_session"
        if request.app.state.settings.environment == "local_release"
        else COOKIE
    )


def session_for(request: Request, db: Session) -> LoginSession:
    token = request.cookies.get(cookie_name(request), "")
    session = db.get(LoginSession, digest(token)) if 20 <= len(token) <= 128 else None
    if session is None or session.revoked or session.expires_at <= int(time.time()):
        raise HTTPException(401, "Your session has ended. Sign in again.")
    return session


def principal(request: Request, db: DB) -> User:
    session = session_for(request, db)
    user = db.get(User, session.user_id) if session.user_id else None
    if user is None:
        raise HTTPException(401, "Sign in to continue")
    return user


Owner = Annotated[User, Depends(principal)]


def mutation(request: Request, db: DB) -> LoginSession:
    if request.headers.get("origin") not in request.app.state.settings.trusted_origins:
        raise HTTPException(403, "Request origin is not permitted")
    session = session_for(request, db)
    csrf = request.headers.get("x-csrf-token", "")
    if len(csrf) > 128 or not secrets.compare_digest(session.csrf_hash, digest(csrf)):
        raise HTTPException(403, "Refresh the page and try again")
    return session


Mutation = Annotated[LoginSession, Depends(mutation)]


def issue(request: Request, response: Response, db: Session, user_id: str | None) -> str:
    db.execute(delete(LoginSession).where(LoginSession.expires_at < int(time.time()) - 86400))
    token = secrets.token_urlsafe(32)
    csrf = csrf_value(token)
    lifetime = request.app.state.settings.session_seconds if user_id else 1800
    db.add(
        LoginSession(
            token_hash=digest(token),
            csrf_hash=digest(csrf),
            user_id=user_id,
            expires_at=int(time.time()) + lifetime,
        )
    )
    response.set_cookie(
        cookie_name(request),
        token,
        max_age=lifetime,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="lax",
        path="/api",
    )
    return csrf


def throttle(request: Request, email: str) -> None:
    now = time.monotonic()
    keys = [
        "ip:" + (request.client.host if request.client else "unknown"),
        "account:" + digest(email),
    ]
    with _lock:
        for key in list(_attempts):
            if not _attempts[key] or _attempts[key][-1] < now - 900:
                del _attempts[key]
        if len(_attempts) > 10000:
            raise HTTPException(429, "Try again later", headers={"Retry-After": "900"})
        for key in keys:
            queue = _attempts[key]
            while queue and queue[0] < now - 900:
                queue.popleft()
            if len(queue) >= request.app.state.settings.auth_rate_limit:
                raise HTTPException(
                    429, "Too many attempts. Try again later.", headers={"Retry-After": "900"}
                )
        for key in keys:
            _attempts[key].append(now)


@router.get("/auth/csrf")
def csrf(request: Request, response: Response, db: DB) -> dict[str, str]:
    try:
        current = session_for(request, db)
    except HTTPException:
        current = None
    # Stable per session: reading a token in another tab must not invalidate in-flight work.
    # Existing sessions adopt the derived token on their first refresh after this upgrade.
    if current:
        value = csrf_value(request.cookies[cookie_name(request)])
        if current.csrf_hash != digest(value):
            current.csrf_hash = digest(value)
    else:
        try:
            request.app.state.bootstrap_limiter.check(
                request.client.host if request.client else "unknown", 100
            )
        except HTTPException:
            raise HTTPException(
                429,
                "Too many session requests. Retry in 15 minutes.",
                headers={"Retry-After": "900"},
            ) from None
        value = issue(request, response, db, None)
    db.commit()
    return {"csrf_token": value}


@router.post("/auth/register", status_code=201)
def register(body: Credentials, request: Request, db: DB, _: Mutation) -> dict[str, str]:
    throttle(request, body.email)
    db.add(User(email=body.email, password_hash=hasher.hash(body.password)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists") from None
    return {"message": "Account created. Sign in to continue."}


@router.post("/auth/login")
def login(
    body: Credentials, request: Request, response: Response, db: DB, old: Mutation
) -> dict[str, str]:
    throttle(request, body.email)
    user = db.scalar(select(User).where(User.email == body.email))
    try:
        hasher.verify(user.password_hash if user else DUMMY_HASH, body.password)
    except (VerificationError, InvalidHashError):
        raise HTTPException(401, "Email or password is incorrect") from None
    if user is None:
        raise HTTPException(401, "Email or password is incorrect")
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hasher.hash(body.password)
    old.revoked = True
    issue(request, response, db, user.id)
    db.commit()
    return {"message": "Signed in"}


@router.post("/auth/logout")
def logout(request: Request, response: Response, db: DB, current: Mutation) -> dict[str, str]:
    current.revoked = True
    db.commit()
    response.delete_cookie(
        cookie_name(request),
        path="/api",
        secure=request.app.state.settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return {"message": "Signed out"}


@router.get("/auth/me", response_model=Identity)
def me(user: Owner, db: DB) -> Identity:
    org = db.scalar(select(Organization).where(Organization.owner_id == user.id))
    return Identity(
        id=user.id,
        email=user.email,
        organization=OrganizationOut.model_validate(org) if org else None,
    )


def owned(user: User, db: Session) -> Organization:
    org = db.scalar(select(Organization).where(Organization.owner_id == user.id))
    if org is None:
        raise HTTPException(404, "Create your workspace first")
    return org


@router.get("/organizations/current", response_model=OrganizationOut)
def get_organization(user: Owner, db: DB) -> Organization:
    return owned(user, db)


@router.post("/organizations", response_model=OrganizationOut, status_code=201)
def create_organization(body: OrganizationInput, user: Owner, db: DB, _: Mutation) -> Organization:
    org = Organization(owner_id=user.id, name=body.name)
    db.add(org)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Your account already owns a workspace") from None
    return org


@router.patch("/organizations/current", response_model=OrganizationOut)
def rename_organization(body: OrganizationInput, user: Owner, db: DB, _: Mutation) -> Organization:
    org = owned(user, db)
    org.name, org.updated_at = body.name, int(time.time())
    db.commit()
    return org
