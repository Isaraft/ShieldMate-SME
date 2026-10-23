"""Explicit isolated QA fixtures only. Never imported or copied into application images."""

import argparse
import json
import time
from uuid import UUID, uuid4

from app.config import Settings
from app.db import Database
from app.models import CheckObservation, DomainAsset, Organization, ScanRun
from app.scanner.contracts import observation


def seed(asset_id: str, scenario: str) -> str:
    database = Database(Settings().database_url)
    try:
        with database.sessions() as db:
            asset = db.get(DomainAsset, asset_id)
            if asset is None:
                raise ValueError("QA asset missing")
            org = db.get(Organization, asset.organization_id)
            if org is None or not org.name.startswith("LOCAL QA"):
                raise ValueError(
                    "Fixture seeding requires an explicitly isolated LOCAL QA workspace"
                )
            moment = int(time.time()) - (8 * 86400 if scenario == "stale" else 0)
            # Ensure reproducible chronology even if several QA calls occur in one second.
            run = ScanRun(
                id=str(uuid4()),
                organization_id=org.id,
                requested_by=org.owner_id,
                asset_id=asset.id,
                hostname=asset.canonical_fqdn,
                proof_generation=asset.challenge_generation,
                proof_verified_at=asset.verified_at or moment - 1,
                engine_version="starter-checks-1",
                status="partial" if scenario == "unknown" else "completed",
                created_at=moment,
                started_at=moment,
                finished_at=moment + 1,
                completed_checks=13,
                error_code="checks_incomplete" if scenario == "unknown" else None,
            )
            db.add(run)
            db.flush()
            issue = scenario in {"issues", "stale"}
            values = [
                ("DNS_ADDRESS", "informational", {"addresses": ["8.8.8.8"]}),
                ("DNS_MX_PRESENT", "informational", {"record_count": 1}),
                (
                    "DNS_SPF_PRESENT",
                    "attention" if issue else "informational",
                    {"record_count": 2 if issue else 1},
                ),
                (
                    "DNS_DMARC_PRESENT",
                    "attention" if issue else "informational",
                    {"policy": "malformed" if issue else "reject", "record_count": 1},
                ),
                (
                    "TLS_CERTIFICATE",
                    "pass",
                    {
                        "not_before": moment - 86400,
                        "not_after": moment + (5 if issue else 90) * 86400,
                        "remaining_days": 5 if issue else 90,
                        "issuer": "LOCAL QA fixture issuer",
                        "subject": asset.canonical_fqdn,
                        "protocol": "TLSv1.3",
                    },
                ),
                (
                    "HTTPS_RESPONSE",
                    "informational",
                    {"status": 200, "method": "HEAD", "path": "/"},
                ),
                (
                    "HTTP_REDIRECT",
                    "informational",
                    {
                        "status": 200 if issue else 301,
                        "method": "HEAD",
                        "path": "/",
                        **(
                            {}
                            if issue
                            else {"redirect": "same_host_https_not_followed"}
                        ),
                    },
                ),
            ]
            for check, header, positive in [
                ("HTTPS_HSTS", "strict-transport-security", "positive max-age"),
                ("HTTPS_NOSNIFF", "x-content-type-options", "nosniff"),
                (
                    "HTTPS_CSP",
                    "content-security-policy",
                    "present; policy needs review",
                ),
                ("HTTPS_REFERRER", "referrer-policy", "present; policy needs review"),
                (
                    "HTTPS_PERMISSIONS",
                    "permissions-policy",
                    "present; policy needs review",
                ),
                ("HTTPS_FRAME", "x-frame-options", "DENY"),
            ]:
                values.append(
                    (
                        check,
                        "attention"
                        if issue
                        else (
                            "pass"
                            if check in {"HTTPS_HSTS", "HTTPS_NOSNIFF", "HTTPS_FRAME"}
                            else "informational"
                        ),
                        {
                            "header": header,
                            "observation": "missing" if issue else positive,
                        },
                    )
                )
            for check, outcome, evidence in values:
                if scenario == "unknown" and check != "DNS_ADDRESS":
                    outcome, evidence = (
                        "inconclusive",
                        {"error_code": "network_timeout"},
                    )
                result = observation(
                    check,
                    outcome,
                    "LOCAL QA fixture observation",
                    "LOCAL QA fixture",
                    evidence,
                    "Injected fixture; no live security assessment.",
                )
                result.observed_at = moment
                db.add(CheckObservation(scan_id=run.id, **result.model_dump()))
            db.commit()
            return run.id
    finally:
        database.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-id", required=True, type=UUID)
    parser.add_argument(
        "--scenario", choices=["issues", "clean", "unknown", "stale"], required=True
    )
    args = parser.parse_args()
    print(
        json.dumps(
            {"scan_id": seed(str(args.asset_id), args.scenario), "fixture": True}
        )
    )
