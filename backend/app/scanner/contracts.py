"""Versioned, bounded technical observations; no business risk classification."""

import time
from typing import Literal

from pydantic import BaseModel, Field

ENGINE = "starter-checks-1"
State = Literal["queued", "running", "completed", "partial", "failed", "interrupted"]
Outcome = Literal["pass", "attention", "informational", "inconclusive", "error"]
ACTIVE = ("queued", "running")
CHECKS = (
    "DNS_ADDRESS",
    "DNS_MX_PRESENT",
    "DNS_SPF_PRESENT",
    "DNS_DMARC_PRESENT",
    "TLS_CERTIFICATE",
    "HTTPS_RESPONSE",
    "HTTP_REDIRECT",
    "HTTPS_HSTS",
    "HTTPS_CSP",
    "HTTPS_NOSNIFF",
    "HTTPS_REFERRER",
    "HTTPS_PERMISSIONS",
    "HTTPS_FRAME",
)


class ScanFailure(Exception):
    """Only a fixed machine code crosses the network/persistence boundary."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class Observation(BaseModel):
    check_id: str
    observed_at: int = Field(default_factory=lambda: int(time.time()))
    outcome: Outcome
    summary: str = Field(max_length=240)
    source: str = Field(max_length=40)
    explanation: str = Field(max_length=600)
    evidence: dict[str, str | int | list[str]] = Field(default_factory=dict)


def clean(value: str, limit: int = 256) -> str:
    return "".join(c for c in value if 32 <= ord(c) < 127)[:limit]


def observation(
    check: str,
    outcome: Outcome,
    summary: str,
    source: str,
    evidence: dict[str, str | int | list[str]],
    explanation: str,
) -> Observation:
    return Observation(
        check_id=check,
        outcome=outcome,
        summary=summary,
        source=source,
        evidence=evidence,
        explanation=explanation,
    )
