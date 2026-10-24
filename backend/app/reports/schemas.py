from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.findings.schemas import FindingOut

Locale = Literal["en", "ru"]
SCHEMA = "security-snapshot-1"


class CreateReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locale: Locale = "en"
    request_key: UUID


class HistoryFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    offset: int = Field(default=0, ge=0, le=10000)
    limit: int = Field(default=10, ge=1, le=20)


class SavedObservation(BaseModel):
    id: str
    check_id: str
    outcome: str
    observed_at: int
    values: dict[str, str | int]


class ReportAsset(BaseModel):
    id: str
    hostname: str
    currently_authorized: bool
    verification_valid_until: int | None
    assessed: bool
    reason: str
    stale: bool
    scan_id: str | None
    scan_status: str | None
    scan_finished_at: int | None
    observation_counts: dict[str, int]
    observations: list[SavedObservation]


class ReportTask(BaseModel):
    id: str
    finding_id: str
    title: str
    hostname: str
    status: str
    owner_label: str
    updated_at: int
    completed_at: int | None
    finding_status: str
    finding_stale: bool
    recommendation: str


class Snapshot(BaseModel):
    schema_version: str = SCHEMA
    id: str
    kind: Literal["real", "demo"] = "real"
    organization_id: str
    organization_name: str
    created_at: int
    locale: Locale
    policy_version: str
    readiness: Literal[
        "no_assets", "unverified", "no_evidence", "processing", "incomplete", "stale", "ready"
    ]
    can_generate: bool
    counts: dict[str, int]
    finding_counts: dict[str, int]
    task_counts: dict[str, int]
    assets: list[ReportAsset]
    findings: list[FindingOut]
    priorities: list[FindingOut]
    tasks: list[ReportTask]


class ReportMeta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    locale: Locale
    created_at: int
    status: Literal["generating", "ready", "failed"]
    schema_version: str
    byte_count: int
    sha256: str | None
    error_code: str | None


class ReportHistory(BaseModel):
    items: list[ReportMeta]
    total: int
    offset: int
    limit: int
