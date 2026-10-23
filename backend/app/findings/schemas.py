from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.findings.contracts import Assessment, Category, Evaluation, Evidence, Severity


class Filters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["all", "open", "resolved"] = "all"
    severity: Literal["all", "high", "medium", "low", "info"] = "all"
    category: Literal["all", "tls", "https", "http_headers", "dns_email"] = "all"
    freshness: Literal["all", "stale", "not_rechecked"] = "all"
    domain_id: UUID | None = None
    scan_id: UUID | None = None
    sort: Literal["priority", "newest", "oldest", "domain"] = "priority"
    offset: int = Field(default=0, ge=0, le=10000)
    limit: int = Field(default=20, ge=1, le=50)


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    asset_id: str
    hostname: str
    fingerprint: str
    rule_id: str
    policy_version: str
    category: Category
    status: Literal["open", "resolved"]
    severity: Severity
    urgency: int
    relevance: int
    confidence: str
    title: str
    impact: str
    recommendation: str
    rationale: str
    limitation: str
    first_seen_at: int
    last_seen_at: int
    observed_at: int
    resolved_at: int | None
    last_evaluation_at: int
    recheck_status: str
    stale: bool
    history_truncated: bool
    source_scan_id: str
    source_scan_available: bool
    evidence: list[Evidence]
    ranking_reason: str


class HistoryOut(BaseModel):
    kind: str
    source_scan_id: str
    source_scan_available: bool
    policy_version: str
    occurred_at: int
    snapshot: Evaluation


class FindingDetail(FindingOut):
    history: list[HistoryOut]


class Coverage(BaseModel):
    policy_version: str
    source_scans: int
    evaluated_scans: int
    pending_evaluations: int
    in_flight_scans: int
    stale_assessments: int
    unsupported_scans: int
    observation_counts: dict[str, int]
    rule_counts: dict[str, int]
    last_scan_at: int | None
    notes: str


class Summary(BaseModel):
    total: int
    counts_by_status: dict[str, int]
    counts_by_severity: dict[str, int]
    counts_by_category: dict[str, int]
    assessment: Coverage


class DomainOption(BaseModel):
    id: str
    hostname: str


class FindingPage(BaseModel):
    domains: list[DomainOption]
    items: list[FindingOut]
    priorities: list[FindingOut]
    total: int
    offset: int
    limit: int
    summary: Summary


class AssessmentOut(BaseModel):
    scan_id: str
    asset_id: str
    status: Literal["pending", "evaluated", "in_flight"]
    assessment: Assessment | None
