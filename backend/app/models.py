import time
import uuid

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
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


class ScanRun(Base):
    __tablename__ = "scan_runs"
    __table_args__ = (
        Index(
            "one_active_scan_per_asset",
            "asset_id",
            unique=True,
            sqlite_where=text("status IN ('queued', 'running')"),
        ),
        CheckConstraint(
            "status IN ('queued','running','completed','partial','failed','interrupted')"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    # Keep a minimal audit/history snapshot after Phase 03 physical asset deletion.
    asset_id: Mapped[str] = mapped_column(String(36), index=True)
    hostname: Mapped[str] = mapped_column(String(253))
    proof_generation: Mapped[int]
    proof_verified_at: Mapped[int]
    status: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[int] = mapped_column(index=True)
    started_at: Mapped[int | None]
    finished_at: Mapped[int | None]
    lease_until: Mapped[int | None]
    error_code: Mapped[str | None] = mapped_column(String(40))
    completed_checks: Mapped[int] = mapped_column(default=0)
    engine_version: Mapped[str] = mapped_column(String(32), default="starter-checks-1")


class CheckObservation(Base):
    __tablename__ = "check_observations"
    __table_args__ = (UniqueConstraint("scan_id", "check_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scan_runs.id", ondelete="CASCADE"), index=True)
    check_id: Mapped[str] = mapped_column(String(40))
    observed_at: Mapped[int]
    outcome: Mapped[str] = mapped_column(String(16))
    summary: Mapped[str] = mapped_column(String(240))
    source: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[str] = mapped_column(String(600))
    evidence: Mapped[dict[str, str | int | list[str]]] = mapped_column(JSON)


class FindingEvaluation(Base):
    __tablename__ = "finding_evaluations"
    __table_args__ = (UniqueConstraint("scan_id", "policy_version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scan_runs.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), index=True)
    policy_version: Mapped[str] = mapped_column(String(32))
    evaluated_at: Mapped[int]
    scan_created_at: Mapped[int]
    applied: Mapped[bool]
    assessment: Mapped[dict[str, object]] = mapped_column(JSON)


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("organization_id", "fingerprint"),
        Index("finding_identity_org", "id", "organization_id", unique=True),
        CheckConstraint("status IN ('open','resolved')"),
        CheckConstraint("severity IN ('high','medium','low','info')"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    rule_id: Mapped[str] = mapped_column(String(40))
    policy_version: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(24), index=True)
    status: Mapped[str] = mapped_column(String(12), index=True)
    severity: Mapped[str] = mapped_column(String(8), index=True)
    severity_rank: Mapped[int]
    urgency: Mapped[int]
    relevance: Mapped[int]
    confidence: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(180))
    impact: Mapped[str] = mapped_column(String(600))
    recommendation: Mapped[str] = mapped_column(String(800))
    rationale: Mapped[str] = mapped_column(String(600))
    limitation: Mapped[str] = mapped_column(String(600))
    first_seen_at: Mapped[int]
    last_seen_at: Mapped[int]
    resolved_at: Mapped[int | None]
    observed_at: Mapped[int]
    source_scan_id: Mapped[str] = mapped_column(String(36))
    evidence: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    last_evaluation_at: Mapped[int]
    last_scan_created_at: Mapped[int]
    last_scan_id: Mapped[str] = mapped_column(String(36))
    recheck_status: Mapped[str] = mapped_column(String(20))
    history_truncated: Mapped[bool] = mapped_column(default=False)


class FindingEvent(Base):
    __tablename__ = "finding_events"
    __table_args__ = (UniqueConstraint("finding_id", "source_scan_id", "policy_version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), index=True
    )
    source_scan_id: Mapped[str] = mapped_column(String(36), index=True)
    policy_version: Mapped[str] = mapped_column(String(32))
    occurred_at: Mapped[int]
    kind: Mapped[str] = mapped_column(String(24))
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON)


class RemediationTask(Base):
    __tablename__ = "remediation_tasks"
    __table_args__ = (
        UniqueConstraint("finding_id"),
        UniqueConstraint("id", "organization_id"),
        ForeignKeyConstraint(
            ["finding_id", "organization_id"],
            ["findings.id", "findings.organization_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("status IN ('todo','in_progress','done')"),
        CheckConstraint("version >= 1"),
        CheckConstraint("length(owner_label) <= 80 AND length(note) <= 2000"),
        Index("task_org_status_updated", "organization_id", "status", "updated_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    finding_id: Mapped[str] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(16), default="todo")
    owner_label: Mapped[str] = mapped_column(String(80), default="")
    note: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[int]
    updated_at: Mapped[int]
    completed_at: Mapped[int | None]
    version: Mapped[int] = mapped_column(default=1)
    history_truncated: Mapped[bool] = mapped_column(default=False)


class TaskEvent(Base):
    __tablename__ = "task_events"
    __table_args__ = (
        UniqueConstraint("task_id", "version"),
        ForeignKeyConstraint(
            ["task_id", "organization_id"],
            ["remediation_tasks.id", "remediation_tasks.organization_id"],
            ondelete="CASCADE",
        ),
        Index("task_event_org_time", "organization_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    task_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int]
    kind: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[int]
    changes: Mapped[dict[str, dict[str, str]]] = mapped_column(JSON)
