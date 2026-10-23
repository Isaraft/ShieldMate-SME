import time
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str]
    created_at: Mapped[int] = mapped_column(default=lambda: int(time.time()))


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[int] = mapped_column(default=lambda: int(time.time()))
    updated_at: Mapped[int] = mapped_column(default=lambda: int(time.time()))


class LoginSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[int] = mapped_column(index=True)
    created_at: Mapped[int] = mapped_column(default=lambda: int(time.time()))
    revoked: Mapped[bool] = mapped_column(default=False)


class DomainAsset(Base):
    __tablename__ = "domains"
    __table_args__ = (
        UniqueConstraint("organization_id", "canonical_fqdn"),
        CheckConstraint("challenge_generation >= 1"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    canonical_fqdn: Mapped[str] = mapped_column(String(253))
    created_at: Mapped[int]
    updated_at: Mapped[int]
    authorization_attested_at: Mapped[int]
    authorization_policy_version: Mapped[str] = mapped_column(String(32))
    challenge_token: Mapped[str] = mapped_column(String(64))
    challenge_generation: Mapped[int]
    challenge_issued_at: Mapped[int]
    challenge_expires_at: Mapped[int]
    verified_at: Mapped[int | None]
    verification_valid_until: Mapped[int | None]
    last_verification_checked_at: Mapped[int | None]
    last_verification_error_code: Mapped[str | None] = mapped_column(String(40))


class DomainEvent(Base):
    __tablename__ = "domain_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    asset_id: Mapped[str] = mapped_column(String(36))
    event: Mapped[str] = mapped_column(String(40))
    occurred_at: Mapped[int]
