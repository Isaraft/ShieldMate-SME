import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.main import create_app
from app.models import CheckObservation, DomainAsset, ScanRun
from app.scanner.contracts import CHECKS, ScanFailure, observation
from app.scanner.dns_checks import Records
from app.scanner.runner import Runner
from app.scanner.worker import work_once
from tests.test_auth import PASSWORD, account, auth_client, mutate  # noqa: F401


@pytest.fixture
def ready(auth_client):  # noqa: F811
    c = auth_client
    account(c)
    mutate(c, "/organizations", {"name": "QA isolated workspace"})
    asset = mutate(
        c, "/domains", {"fqdn": "qa.example.com", "authorization_acknowledged": True}
    ).json()
    c.app.state.check_txt = Mock(return_value="match")
    mutate(c, f"/domains/{asset['id']}/verification/check")
    return c, asset["id"]


def path(asset):
    return f"/domains/{asset}/scans"


class FixtureRunner:
    def run(self, host, budget, guard, emit):
        assert host == "qa.example.com"
        guard()
        for check in CHECKS:
            emit(
                observation(
                    check,
                    "informational",
                    "Controlled test evidence",
                    "QA fixture",
                    {"note": "Fixture, no network"},
                    "No external request was sent.",
                )
            )


def run_worker(c, runner=None):
    return work_once(c.app.state.database, c.app.state.settings, runner or FixtureRunner())


def test_lifecycle_durable_paginated_history_and_redaction(ready):
    c, asset = ready
    start = mutate(c, path(asset))
    assert start.status_code == 202
    job = start.json()
    assert job["status"] == "queued" and job["completed_checks"] == 0
    assert mutate(c, path(asset)).status_code == 409
    assert run_worker(c)
    assert not run_worker(c)
    with TestClient(create_app(c.app.state.settings)) as restarted:
        restarted.cookies.update(c.cookies)
        record = restarted.get("/api/v1" + path(asset) + "/" + job["id"]).json()
        assert record["status"] == "completed" and len(record["observations"]) == 13
        assert record["started_at"] and record["finished_at"]
        assert record["engine_version"] == "starter-checks-1"
        for secret in ["challenge_token", "csrf_hash", "token_hash", "proof_generation"]:
            assert secret not in str(record)
        history = restarted.get("/api/v1" + path(asset) + "?limit=1&offset=0").json()
        assert history["total"] == 1 and history["items"][0]["id"] == job["id"]
        assert restarted.get("/api/v1" + path(asset) + "?limit=51").status_code == 422
        assert restarted.get("/api/v1" + path(asset) + "?offset=1").json()["items"] == []


@pytest.mark.parametrize(
    "change", ["unverified", "stale", "consent", "policy", "deleted", "rotated"]
)
def test_authorization_before_enqueue_and_acquisition(ready, change):
    c, asset = ready
    # First enqueue before revocation, then the same asset becomes ineligible.
    job = mutate(c, path(asset)).json()
    with c.app.state.database.sessions() as db:
        row = db.get(DomainAsset, asset)
        if change == "unverified":
            row.verified_at = None
        elif change == "stale":
            row.verification_valid_until = int(time.time()) - 1
        elif change == "consent":
            row.authorization_attested_at = 0
        elif change == "policy":
            row.authorization_policy_version = "revoked"
        elif change == "deleted":
            db.delete(row)
        else:
            row.challenge_generation += 1
            row.verified_at = None
        db.commit()
    runner = Mock()
    assert run_worker(c, runner)
    runner.run.assert_not_called()
    with c.app.state.database.sessions() as db:
        assert db.get(ScanRun, job["id"]).status == "failed"
        assert db.get(ScanRun, job["id"]).error_code == "authorization_changed"
    assert mutate(c, path(asset)).status_code == (404 if change == "deleted" else 409)


def test_rotation_during_execution_stops_subsequent_network_work(ready):
    c, asset = ready
    job = mutate(c, path(asset)).json()

    class RevokingRunner:
        def run(self, host, budget, guard, emit):
            guard()
            emit(observation("DNS_ADDRESS", "informational", "Test", "QA", {}, "Fixture"))
            assert mutate(c, f"/domains/{asset}/verification/request").status_code == 200
            guard()  # Must fail before any further probe.
            raise AssertionError("Revocation was ignored")

    run_worker(c, RevokingRunner())
    detail = c.get("/api/v1" + path(asset) + "/" + job["id"]).json()
    assert detail["status"] == "failed" and detail["error_code"] == "authorization_changed"
    assert len(detail["observations"]) == 1


def test_scope_csrf_unknown_input_and_scan_idor(ready):
    c, asset = ready
    assert c.post("/api/v1" + path(asset), json={}).status_code == 403
    assert mutate(c, path(asset), {}, Origin="https://evil.com").status_code == 403
    for body in [
        {"url": "http://127.0.0.1"},
        {"organization_id": "other"},
        {"port": 22},
        {"headers": {}},
        {"path": "/admin"},
    ]:
        assert mutate(c, path(asset), body).status_code == 422
    job = mutate(c, path(asset), {}).json()
    account(c, "second@example.com")
    mutate(c, "/organizations", {"name": "Other owner"})
    own_asset = mutate(
        c, "/domains", {"fqdn": "other.example.com", "authorization_acknowledged": True}
    ).json()["id"]
    for route in [path(asset), path(asset) + "/" + job["id"], path(own_asset) + "/" + job["id"]]:
        assert c.get("/api/v1" + route).status_code == 404
    assert mutate(c, path(asset)).status_code == 404
    c.cookies.clear()
    assert c.get("/api/v1" + path(asset)).status_code == 401
    assert c.get("/api/v1" + path(asset) + "/" + job["id"]).status_code == 401
    assert mutate(c, path(asset)).status_code == 401


def test_atomic_duplicate_active_constraint_and_worker_slot(ready):
    c, asset = ready
    job = mutate(c, path(asset)).json()
    with c.app.state.database.sessions() as db:
        first = db.get(ScanRun, job["id"])
        db.add(
            ScanRun(
                organization_id=first.organization_id,
                requested_by=first.requested_by,
                asset_id=asset,
                hostname=first.hostname,
                proof_generation=1,
                proof_verified_at=first.proof_verified_at,
                status="queued",
                created_at=int(time.time()),
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run_worker(c), range(2)))
    assert sum(results) == 1
    with c.app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ScanRun)) == 1
        assert db.scalar(select(func.count()).select_from(CheckObservation)) == 13


@pytest.mark.parametrize("limit", ["scan_user_hourly", "scan_org_hourly", "scan_domain_hourly"])
def test_persisted_hourly_quotas(ready, limit):
    c, asset = ready
    setattr(c.app.state.settings, limit, 1)
    assert mutate(c, path(asset)).status_code == 202
    run_worker(c)
    assert mutate(c, path(asset)).status_code == 429


def test_queue_and_history_capacity(ready):
    c, asset = ready
    c.app.state.settings.scan_queue_limit = 1
    first = mutate(c, path(asset)).json()
    other = mutate(
        c, "/domains", {"fqdn": "other.example.com", "authorization_acknowledged": True}
    ).json()["id"]
    mutate(c, f"/domains/{other}/verification/check")
    assert mutate(c, path(other)).status_code == 429
    run_worker(c)
    c.app.state.settings.scan_history_limit = 1
    assert mutate(c, path(other)).status_code == 429
    with c.app.state.database.sessions() as db:
        db.get(ScanRun, first["id"]).created_at -= 3601
        db.commit()
    assert mutate(c, path(other)).status_code == 202
    with c.app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ScanRun)) == 1
        assert db.scalar(select(func.count()).select_from(CheckObservation)) == 0


def test_restart_closes_expired_running_lease_and_keeps_observations(ready):
    c, asset = ready
    first = mutate(c, path(asset)).json()
    with c.app.state.database.sessions() as db:
        job = db.get(ScanRun, first["id"])
        job.status, job.lease_until = "running", int(time.time()) - 1
        db.add(
            CheckObservation(
                scan_id=job.id,
                **observation(
                    "DNS_ADDRESS", "informational", "Fixture", "QA", {}, "No network"
                ).model_dump(),
            )
        )
        job.completed_checks = 1
        db.commit()
    with TestClient(create_app(c.app.state.settings)) as restarted:
        restarted.cookies.update(c.cookies)
        detail = restarted.get("/api/v1" + path(asset) + "/" + first["id"]).json()
        assert detail["status"] == "interrupted" and len(detail["observations"]) == 1
        assert detail["error_code"] == "worker_interrupted"
    assert mutate(c, path(asset)).status_code == 202


def test_partial_network_scan_and_unsafe_target(ready):
    c, asset = ready
    dns, transport = Mock(), Mock()
    dns.resolve.return_value = ["8.8.8.8"]
    dns.query.return_value = Records([], "dns_unavailable")
    transport.open.side_effect = ScanFailure("network_timeout")
    job = mutate(c, path(asset)).json()
    run_worker(c, Runner(dns, transport))
    row = c.get("/api/v1" + path(asset) + "/" + job["id"]).json()
    assert row["status"] == "partial" and len(row["observations"]) == 13
    assert row["observations"][0]["outcome"] == "informational"
    job = mutate(c, path(asset)).json()
    dns.resolve.side_effect = ScanFailure("unsafe_destination")
    transport.reset_mock()
    run_worker(c, Runner(dns, transport))
    row = c.get("/api/v1" + path(asset) + "/" + job["id"]).json()
    assert row["status"] == "failed" and row["error_code"] == "unsafe_destination"
    transport.open.assert_not_called()


def test_non_destructive_upgrade_from_phase03(ready, monkeypatch):
    # Preserve real Phase03 rows through the additive migration.
    from alembic import command
    from alembic.config import Config

    c, asset = ready
    url = c.app.state.settings.database_url
    config = Config("alembic.ini")
    monkeypatch.setenv("SHIELDMATE_DATABASE_URL", url)
    before = c.get("/api/v1/domains").json()
    identity = c.get("/api/v1/auth/me").json()
    command.downgrade(config, "90bff5eabc24")
    command.upgrade(config, "head")
    command.check(config)
    assert c.get("/api/v1/auth/me").json() == identity
    assert c.get("/api/v1/domains").json() == before
    assert mutate(c, path(asset)).status_code == 202


def test_concurrent_api_enqueues_are_serialized(ready):
    c, asset = ready
    token = c.get("/api/v1/auth/csrf").json()["csrf_token"]
    headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": token}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: c.post("/api/v1" + path(asset), json={}, headers=headers).status_code,
                range(2),
            )
        )
    assert sorted(results) == [202, 409]


def test_waiting_queue_expires_without_becoming_a_success(ready):
    c, asset = ready
    first = mutate(c, path(asset)).json()
    with c.app.state.database.sessions() as db:
        db.get(ScanRun, first["id"]).created_at -= 901
        db.commit()
    detail = c.get("/api/v1" + path(asset) + "/" + first["id"]).json()
    assert detail["status"] == "failed" and detail["error_code"] == "queue_expired"
    assert detail["observations"] == []


def test_evidence_limit_is_terminal_and_does_not_persist_oversized_data(ready):
    c, asset = ready
    job = mutate(c, path(asset)).json()

    class OversizedRunner:
        def run(self, host, budget, guard, emit):
            emit(
                observation(
                    "DNS_ADDRESS",
                    "informational",
                    "Fixture",
                    "QA",
                    {"untrusted": "x" * 5000},
                    "Fixture",
                )
            )

    run_worker(c, OversizedRunner())
    record = c.get("/api/v1" + path(asset) + "/" + job["id"]).json()
    assert record["status"] == "failed" and record["error_code"] == "evidence_limit"
    assert record["observations"] == []


def test_changed_organization_owner_revokes_acquired_job(ready):
    from app.models import Organization

    c, asset = ready
    job = mutate(c, path(asset)).json()
    account(c, "replacement@example.com")
    replacement = c.get("/api/v1/auth/me").json()["id"]
    with c.app.state.database.sessions() as db:
        run = db.get(ScanRun, job["id"])
        db.get(Organization, run.organization_id).owner_id = replacement
        db.commit()
    runner = Mock()
    run_worker(c, runner)
    runner.run.assert_not_called()
    record = c.get("/api/v1" + path(asset) + "/" + job["id"]).json()
    assert record["status"] == "failed" and record["error_code"] == "authorization_changed"


def test_revocation_between_last_guard_and_terminal_commit_is_atomic(ready, monkeypatch):
    import app.scanner.worker as worker

    c, asset = ready
    job = mutate(c, path(asset)).json()
    original = worker.locked
    calls = 0

    def revoke_before_final_lock(db):
        nonlocal calls
        calls += 1
        if calls == 15:  # claim + 13 incremental observations + terminal write
            with c.app.state.database.sessions() as other:
                other.get(DomainAsset, asset).authorization_attested_at = 0
                other.commit()
        original(db)

    monkeypatch.setattr(worker, "locked", revoke_before_final_lock)
    run_worker(c)
    record = c.get("/api/v1" + path(asset) + "/" + job["id"]).json()
    assert record["status"] == "failed" and record["error_code"] == "authorization_changed"
    assert len(record["observations"]) == 13
