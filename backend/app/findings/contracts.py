"""Offline finding policy contracts, separate from scanner collection outcomes."""

from typing import Literal

from pydantic import BaseModel, Field

POLICY = "starter-risk-1"
Severity = Literal["high", "medium", "low", "info"]
Category = Literal["tls", "https", "http_headers", "dns_email"]
Decision = Literal["issue", "clear", "not_evaluable", "not_applicable"]
SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1, "info": 0}


class Evidence(BaseModel):
    observation_id: str
    check_id: str
    observed_at: int
    outcome: str
    source: str
    values: dict[str, str | int]


class Evaluation(BaseModel):
    rule_id: str
    policy_version: str = POLICY
    decision: Decision = "not_evaluable"
    reason: str = "Comparable, conclusive evidence is unavailable."
    category: Category
    title: str
    severity: Severity = "low"
    urgency: int = Field(default=0, ge=0, le=3)
    relevance: int = Field(default=1, ge=0, le=2)
    confidence: Literal["conclusive", "contextual"] = "contextual"
    impact: str
    recommendation: str
    rationale: str
    limitation: str
    evidence: list[Evidence] = Field(default_factory=list)


class Assessment(BaseModel):
    policy_version: str = POLICY
    scan_id: str
    source_engine: str
    scan_status: str
    observed_checks: int
    observation_counts: dict[str, int]
    expected_checks: int = 13
    rules: list[Evaluation]
    coverage: dict[str, int]
