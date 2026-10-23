import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.findings.reconcile import reconcile, reconcile_pending
from app.main import create_app
from app.models import (
    DomainAsset,
    Finding,
    FindingEvaluation,
    FindingEvent,
    ScanRun,
)
from tests.test_auth import account, auth_client, mutate  # noqa: F401
from tests.test_finding_rules import TIME, row, source


@pytest.fixture
def workspace(auth_client):  # noqa: F811
    c = auth_client
    account(c)
    org = mutate(c, "/organizations", {"name": "QA finding workspace"}).json()["id"]
    asset = mutate(
        c, "/domains", {"fqdn": "qa.example.com", "authorization_acknowledged": True}
    ).json()["id"]
    return c, org, asset


def saved(workspace, issues=True, at=TIME, status="completed", overrides=None):
    c, org, asset = workspace
    run, observations = source()
    run.id = str(uuid4())
    run.asset_id, run.organization_id = asset, org
    run.requested_by = c.get("/api/v1/auth/me").json()["id"]
    run.hostname = "qa.example.com"
    run.proof_generation, run.proof_verified_at = 1, at - 1
    run.created_at, run.started_at, run.finished_at = at, at, at + 2
    run.status, run.completed_checks = status, len(observations)
    if issues:
        for observation in observations:
            if observation.check_id == "TLS_CERTIFICATE":
                observation.evidence["not_after"] = at + 5 * 86400
            elif observation.check_id in {"HTTPS_HSTS", "HTTPS_NOSNIFF"}:
                observation.outcome = "attention"
                observation.evidence["observation"] = "missing"
            elif observation.check_id == "HTTP_REDIRECT":
                observation.evidence = {"status": 200, "method": "HEAD", "path": "/"}
            elif observation.check_id == "DNS_SPF_PRESENT":
                observation.outcome, observation.evidence = "attention", {"record_count": 2}
            elif observation.check_id == "DNS_DMARC_PRESENT":
                observation.outcome, observation.evidence = (
                    "attention",
                    {"policy": "malformed", "record_count": 1},
                )
    for observation in observations:
        observation.scan_id, observation.observed_at = run.id, at
        if observation.check_id == "TLS_CERTIFICATE":
            observation.evidence["not_before"] = at - 86400
            if not issues:
                observation.evidence["not_after"] = at + 90 * 86400
    if overrides is not None:
        observations = overrides(observations)
    for observation in observations:
        observation.scan_id, observation.observed_at = run.id, at
    with c.app.state.database.sessions() as db:
        db.add(run)
        db.flush()
        db.add_all(observations)
        db.commit()
    return run.id


def process(workspace, identifier):
    c, org, _ = workspace
    return reconcile(c.app.state.database, identifier, org)


def test_detection_dedup_severity_resolution_reopening_and_provenance(workspace):
    c, _, _ = workspace
    first = saved(workspace)
    assert process(workspace, first)
    original = c.get("/api/v1/findings").json()
    assert original["total"] == 6
    assert [r["rule_id"] for r in original["priorities"]] == [
        "TLS_CERTIFICATE_ACTION",
        "DNS_SPF_MULTIPLE",
        "DNS_DMARC_POLICY",
    ]
    identifiers = {r["rule_id"]: r["id"] for r in original["items"]}
    assert not process(workspace, first)
    repeated = saved(workspace, at=TIME + 10)
    process(workspace, repeated)
    assert {r["rule_id"]: r["id"] for r in c.get("/api/v1/findings").json()["items"]} == identifiers
    clean = saved(workspace, issues=False, at=TIME + 20)
    process(workspace, clean)
    page = c.get("/api/v1/findings").json()
    assert page["priorities"] == [] and page["summary"]["counts_by_status"] == {"resolved": 6}
    tls_id = identifiers["TLS_CERTIFICATE_ACTION"]
    detail = c.get("/api/v1/findings/" + tls_id).json()
    assert detail["resolved_at"] == TIME + 20 and detail["first_seen_at"] == TIME
    assert detail["source_scan_id"] == clean
    again = saved(workspace, at=TIME + 30)
    process(workspace, again)
    detail = c.get("/api/v1/findings/" + tls_id).json()
    assert detail["status"] == "open" and detail["resolved_at"] is None
    assert detail["first_seen_at"] == TIME and detail["last_seen_at"] == TIME + 30
    assert {event["kind"] for event in detail["history"]} == {
        "detected",
        "confirmed",
        "resolved",
        "reopened",
    }
    assert all(
        event["snapshot"]["policy_version"] == "starter-risk-1" for event in detail["history"]
    )

    # Same rule, new supported expiry evidence can change urgency/severity without duplication.
    def less_urgent(rows):
        for r in rows:
            if r.check_id == "TLS_CERTIFICATE":
                r.evidence["not_after"] = TIME + 40 + 20 * 86400
        return rows

    process(workspace, saved(workspace, at=TIME + 40, overrides=less_urgent))
    assert c.get("/api/v1/findings/" + tls_id).json()["severity"] == "medium"


@pytest.mark.parametrize("status", ["partial", "failed", "interrupted"])
def test_incomplete_missing_or_error_never_resolves(workspace, status):
    c, _, _ = workspace
    process(workspace, saved(workspace))

    def incomplete(rows):
        return [row("TLS_CERTIFICATE", "inconclusive", error_code="network_timeout")]

    identifier = saved(workspace, issues=False, at=TIME + 10, status=status, overrides=incomplete)
    process(workspace, identifier)
    page = c.get("/api/v1/findings").json()
    assert page["summary"]["counts_by_status"] == {"open": 6}
    assert all(
        f["recheck_status"] == "not_rechecked" and f["last_seen_at"] == TIME for f in page["items"]
    )
    assert len(c.get("/api/v1/findings?freshness=not_rechecked").json()["items"]) == 6


def test_partial_can_resolve_only_comparable_rule(workspace):
    c, _, _ = workspace
    process(workspace, saved(workspace))
    process(
        workspace,
        saved(
            workspace,
            issues=False,
            at=TIME + 10,
            status="partial",
            overrides=lambda rows: [r for r in rows if r.check_id == "DNS_SPF_PRESENT"],
        ),
    )
    page = c.get("/api/v1/findings").json()
    assert page["summary"]["counts_by_status"] == {"open": 5, "resolved": 1}
    assert (
        next(r for r in page["items"] if r["rule_id"] == "DNS_SPF_MULTIPLE")["status"] == "resolved"
    )


def test_concurrent_processing_backfill_idempotency_and_restart(workspace):
    c, org, _ = workspace
    identifier = saved(workspace)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: process(workspace, identifier), range(2)))
    assert sorted(results) == [False, True]
    assert reconcile_pending(c.app.state.database, org) == 0
    before = c.get("/api/v1/findings").json()
    with TestClient(create_app(c.app.state.settings)) as restarted:
        restarted.cookies.update(c.cookies)
        assert restarted.get("/api/v1/findings").json() == before
    with c.app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(Finding)) == 6
        assert db.scalar(select(func.count()).select_from(FindingEvent)) == 6
        assert db.scalar(select(func.count()).select_from(FindingEvaluation)) == 1


def test_out_of_order_cannot_resurrect_resolved_or_clean_latest_state(workspace):
    c, _, _ = workspace
    older = saved(workspace, at=TIME)
    newer = saved(workspace, issues=False, at=TIME + 10)
    process(workspace, newer)
    process(workspace, older)
    assert c.get("/api/v1/findings").json()["total"] == 0
    with c.app.state.database.sessions() as db:
        previous = db.scalar(select(FindingEvaluation).where(FindingEvaluation.scan_id == older))
        assert previous.applied is False
        assert any(r["decision"] == "issue" for r in previous.assessment["rules"])


def test_scans_inflight_unsupported_versions_and_pending_summary(workspace):
    c, _, _ = workspace
    identifier = saved(workspace, status="running")
    assert not process(workspace, identifier)
    assert c.get("/api/v1/findings").json()["summary"]["assessment"]["in_flight_scans"] == 1
    with c.app.state.database.sessions() as db:
        run = db.get(ScanRun, identifier)
        run.status, run.engine_version = "completed", "unrecognized-version"
        db.commit()
    assert c.get("/api/v1/findings").json()["summary"]["assessment"]["pending_evaluations"] == 1
    process(workspace, identifier)
    page = c.get("/api/v1/findings").json()
    assert page["total"] == 0
    assert page["summary"]["assessment"]["rule_counts"] == {"not_evaluable": 6}


def test_api_scope_filters_counts_and_no_mutation(workspace):
    c, org, asset = workspace
    first = saved(workspace)
    process(workspace, first)
    page = c.get("/api/v1/findings?limit=2&severity=low").json()
    assert len(page["items"]) == 2 and page["total"] == 3
    assert page["summary"]["total"] == 3
    assert c.get("/api/v1/findings?offset=999").json()["items"] == []
    for query in [
        "limit=51",
        "sort=sql",
        "organization_id=" + org,
        "severity=critical",
        "status=deleted",
    ]:
        assert c.get("/api/v1/findings?" + query).status_code == 422
    own = c.get("/api/v1/findings").json()["items"][0]["id"]
    assert c.post("/api/v1/findings/" + own, json={"severity": "high"}).status_code == 405
    account(c, "foreign@example.com")
    mutate(c, "/organizations", {"name": "Other tenant"})
    assert c.get("/api/v1/findings").json()["total"] == 0
    for route in [
        "/findings/" + own,
        "/findings?domain_id=" + asset,
        "/findings?scan_id=" + first,
        "/findings/assessments/" + first,
    ]:
        assert c.get("/api/v1" + route).status_code == 404
    assert not reconcile(
        c.app.state.database, first, c.get("/api/v1/auth/me").json()["organization"]["id"]
    )
    c.cookies.clear()
    for route in ["/findings", "/findings/" + own, "/findings/assessments/" + first]:
        assert c.get("/api/v1" + route).status_code == 401


def test_source_retention_keeps_bounded_provenance_and_asset_delete_cascades(workspace):
    c, _, asset = workspace
    first = saved(workspace)
    process(workspace, first)
    finding_id = c.get("/api/v1/findings").json()["items"][0]["id"]
    with c.app.state.database.sessions() as db:
        db.execute(delete(ScanRun).where(ScanRun.id == first))
        db.commit()
    detail = c.get("/api/v1/findings/" + finding_id).json()
    assert not detail["source_scan_available"]
    assert detail["history"][0]["snapshot"]["evidence"]
    assert detail["source_scan_id"] == first
    assert mutate(c, "/domains/" + asset, method="DELETE").status_code == 200
    assert c.get("/api/v1/findings").json()["total"] == 0


def test_migration_from_phase04_preserves_scans_and_proofs(workspace, monkeypatch):
    c, _, asset = workspace
    identifier = saved(workspace)
    url = c.app.state.settings.database_url
    monkeypatch.setenv("SHIELDMATE_DATABASE_URL", url)
    config = Config("alembic.ini")
    before = c.get(f"/api/v1/domains/{asset}/scans/{identifier}").json()
    identity = c.get("/api/v1/auth/me").json()
    command.downgrade(config, "1806ce4b7076")
    command.upgrade(config, "head")
    command.check(config)
    assert c.get(f"/api/v1/domains/{asset}/scans/{identifier}").json() == before
    assert c.get("/api/v1/auth/me").json() == identity
    assert process(workspace, identifier)


def test_no_network_from_offline_evaluator(workspace, monkeypatch):
    import socket

    identifier = saved(workspace)
    monkeypatch.setattr(socket, "socket", lambda *a, **kw: pytest.fail("Network prohibited"))
    assert process(workspace, identifier)


def test_same_second_scan_order_uses_persisted_insertion_not_random_uuid(workspace, monkeypatch):
    import tests.test_findings as module

    identifiers = iter(
        ["ffffffff-ffff-4fff-8fff-ffffffffffff", "00000000-0000-4000-8000-000000000001"]
    )
    monkeypatch.setattr(module, "uuid4", lambda: next(identifiers))
    older = saved(workspace, at=TIME)
    newer = saved(workspace, issues=False, at=TIME)
    process(workspace, older)
    process(workspace, newer)
    assert workspace[0].get("/api/v1/findings").json()["summary"]["counts_by_status"] == {
        "resolved": 6
    }
    selected = workspace[0].get("/api/v1/findings").json()["items"][0]["id"]
    history = workspace[0].get("/api/v1/findings/" + selected).json()["history"]
    assert [event["kind"] for event in history] == ["resolved", "detected"]


def test_reconciliation_rollback_then_retry_has_no_half_published_state(workspace, monkeypatch):
    import app.findings.reconcile as module

    identifier = saved(workspace)
    original = module.evaluate

    def crash_mid_transaction(run, observations):
        assessment = original(run, observations)
        assessment.rules[1].severity = "invalid"
        return assessment

    monkeypatch.setattr(module, "evaluate", crash_mid_transaction)
    with pytest.raises(KeyError):
        process(workspace, identifier)
    with workspace[0].app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(Finding)) == 0
        assert db.scalar(select(func.count()).select_from(FindingEvaluation)) == 0
    monkeypatch.setattr(module, "evaluate", original)
    assert process(workspace, identifier)
    assert workspace[0].get("/api/v1/findings").json()["total"] == 6


def test_bounded_history_preserves_first_and_latest_resolution_reopening(workspace):
    c, _, _ = workspace
    process(workspace, saved(workspace))
    process(workspace, saved(workspace, issues=False, at=TIME + 1))
    process(workspace, saved(workspace, at=TIME + 2))
    early_confirmation = saved(workspace, at=TIME + 3)
    process(workspace, early_confirmation)
    for index in range(4, 54):
        process(workspace, saved(workspace, at=TIME + index))
    identifier = c.get("/api/v1/findings").json()["items"][0]["id"]
    detail = c.get("/api/v1/findings/" + identifier).json()
    assert detail["history_truncated"] and len(detail["history"]) == 50
    assert c.get("/api/v1/findings?scan_id=" + early_confirmation).json()["total"] == 6
    assert {"detected", "resolved", "reopened"} <= {event["kind"] for event in detail["history"]}


def test_configured_staleness_and_proof_expiry_preserve_findings(workspace):
    c, _, asset = workspace
    old = int(time.time()) - 604900
    process(workspace, saved(workspace, at=old))
    with c.app.state.database.sessions() as db:
        domain = db.get(DomainAsset, asset)
        domain.verification_valid_until = old
        db.commit()
    page = c.get("/api/v1/findings?freshness=stale").json()
    assert page["total"] == 6 and all(f["stale"] for f in page["items"])
    assert page["summary"]["assessment"]["stale_assessments"] == 1
    assert page["summary"]["counts_by_status"] == {"open": 6}


def test_concurrent_read_bundle_is_one_consistent_snapshot(workspace):
    c, _, _ = workspace
    identifier = saved(workspace)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(process, workspace, identifier)
        for _ in range(10):
            page = c.get("/api/v1/findings").json()
            assert page["total"] == len(page["items"]) == page["summary"]["total"]
            assert len(page["priorities"]) == min(3, page["total"])
        assert future.result()
