# ruff: noqa: F811
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import DomainAsset, Finding, Organization, RemediationTask, TaskEvent, User
from tests.test_auth import ORIGIN, PASSWORD, account, auth_client, mutate  # noqa: F401
from tests.test_findings import process, saved, workspace  # noqa: F401


def start(workspace):
    c, _, _ = workspace
    process(workspace, saved(workspace, at=int(time.time()) - 100))
    finding = c.get("/api/v1/findings").json()["priorities"][0]
    response = mutate(c, f"/findings/{finding['id']}/task", {})
    assert response.status_code == 200, response.text
    return finding, response.json()


def test_task_workflow_is_not_technical_resolution(workspace):
    c, _, _ = workspace
    finding, task = start(workspace)
    assert task["status"] == "todo" and task["version"] == 1
    original = c.get("/api/v1/findings/" + finding["id"]).json()
    for status in ["in_progress", "done", "in_progress", "done"]:
        task = mutate(
            c,
            "/tasks/" + task["id"],
            {
                "version": task["version"],
                "status": status,
                "owner_label": "Внешний IT",
                "note": "<script>alert(1)</script>\nRecheck required",
            },
            "PATCH",
        ).json()
        assert task["status"] == status
        assert task["finding"]["status"] == "open"
        assert (task["completed_at"] is not None) == (status == "done")
    after = c.get("/api/v1/findings/" + finding["id"]).json()
    for key in original.keys() - {"task_id", "task_status"}:
        assert original[key] == after[key]
    assert len(task["history"]) == 5
    assert [e["version"] for e in task["history"]] == [5, 4, 3, 2, 1]
    assert all(e["actor_id"] == c.get("/api/v1/auth/me").json()["id"] for e in task["history"])
    assert "csrf" not in str(task["history"])
    assert c.get("/api/v1/tasks/" + task["id"]).json() == task
    dashboard = c.get("/api/v1/dashboard/summary").json()
    assert dashboard["task_counts"] == {"done": 1} and dashboard["done_unverified"] == 1
    assert dashboard["findings"]["total"] == 6
    assert dashboard["findings"]["priorities"][0]["task_id"] == task["id"]
    assert [f["id"] for f in dashboard["findings"]["priorities"]] == [
        f["id"] for f in c.get("/api/v1/findings").json()["priorities"]
    ]


def test_idempotent_create_edit_and_conflict(workspace):
    c, _, _ = workspace
    finding, task = start(workspace)
    assert mutate(c, f"/findings/{finding['id']}/task", {}).json()["id"] == task["id"]
    changed = mutate(
        c, "/tasks/" + task["id"], {"version": 1, "note": "Contacted host"}, "PATCH"
    ).json()
    assert changed["version"] == 2
    replay = mutate(c, "/tasks/" + task["id"], {"version": 1, "note": "Contacted host"}, "PATCH")
    assert replay.json() == changed
    assert (
        mutate(c, "/tasks/" + task["id"], {"version": 1, "note": "Overwrite"}, "PATCH").status_code
        == 409
    )
    assert len(c.get("/api/v1/tasks/" + task["id"]).json()["history"]) == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"version": 1, "status": "fixed"},
        {"version": True, "note": "x"},
        {"version": 1},
        {"version": 1, "note": "x" * 2001},
        {"version": 1, "owner_label": "x" * 81},
        {"version": 1, "note": None},
        {"version": 1, "status": None},
        {"version": 1, "note": "bad\x00"},
        {"version": 1, "organization_id": str(uuid4())},
        {"version": 1, "finding_id": str(uuid4())},
    ],
)
def test_patch_validation(workspace, payload):
    c, _, _ = workspace
    _, task = start(workspace)
    assert mutate(c, "/tasks/" + task["id"], payload, "PATCH").status_code == 422


@pytest.mark.parametrize(
    "query",
    [
        "limit=51",
        "offset=-1",
        "status=fixed",
        "severity=critical",
        "domain_id=no",
        "organization_id=forged",
        "sort=random",
    ],
)
def test_list_validation(workspace, query):
    assert workspace[0].get("/api/v1/tasks?" + query).status_code == 422


def test_scope_session_csrf_and_forged_inputs(workspace):
    c, _, _ = workspace
    finding, task = start(workspace)
    assert mutate(c, f"/findings/{finding['id']}/task", {"actor_id": "forged"}).status_code == 422
    for origin, token in [(ORIGIN, ""), ("https://evil.example", "invalid")]:
        assert (
            c.patch(
                "/api/v1/tasks/" + task["id"],
                json={"version": 1, "note": "bad"},
                headers={"Origin": origin, "X-CSRF-Token": token},
            ).status_code
            == 403
        )
        assert (
            c.post(
                f"/api/v1/findings/{finding['id']}/task",
                json={},
                headers={"Origin": origin, "X-CSRF-Token": token},
            ).status_code
            == 403
        )
    cookie = c.cookies.get("shieldmate_session")
    account(c, "other@example.com")
    mutate(c, "/organizations", {"name": "Other tenant"})
    for path in ["/tasks/" + task["id"], "/tasks?domain_id=" + finding["asset_id"]]:
        assert c.get("/api/v1" + path).status_code == 404
    assert (
        mutate(c, "/tasks/" + task["id"], {"version": 1, "note": "foreign"}, "PATCH").status_code
        == 404
    )
    assert mutate(c, f"/findings/{finding['id']}/task", {}).status_code == 404
    assert c.get("/api/v1/tasks").json()["total"] == 0
    assert c.get("/api/v1/dashboard/summary").json()["findings"]["total"] == 0
    c.cookies.clear()
    for path in ["/tasks", "/tasks/" + task["id"], "/dashboard/summary"]:
        assert c.get("/api/v1" + path).status_code == 401
    c.cookies.set("shieldmate_session", cookie)
    assert c.get("/api/v1/tasks/" + task["id"]).status_code == 401
    c.cookies.clear()
    assert (
        mutate(c, "/auth/login", {"email": "owner@example.com", "password": PASSWORD}).status_code
        == 200
    )
    assert c.get("/api/v1/tasks/" + task["id"]).status_code == 200
    assert c.delete("/api/v1/tasks/" + task["id"]).status_code == 405


def test_dashboard_empty_coverage_verified_and_filters(workspace):
    c, _, asset = workspace
    empty = c.get("/api/v1/dashboard/summary").json()
    assert empty["asset_count"] == 1 and empty["verified_assets"] == 0
    assert empty["recent_scan_count"] == 0 and empty["findings"]["total"] == 0
    assert empty["last_useful_observation_at"] is None and empty["task_counts"] == {}
    with c.app.state.database.sessions() as db:
        domain = db.get(DomainAsset, asset)
        domain.verified_at = int(time.time()) - 10
        domain.verification_valid_until = int(time.time()) + 1000
        db.commit()
    finding, task = start(workspace)
    dashboard = c.get("/api/v1/dashboard/summary").json()
    assert dashboard["verified_assets"] == dashboard["eligible_assets"] == 1
    assert dashboard["recent_scan_count"] == 1 and dashboard["scans"][0]["status"] == "completed"
    assert dashboard["last_useful_observation_at"]
    assert c.get("/api/v1/tasks?status=done").json()["total"] == 0
    assert c.get("/api/v1/tasks?severity=high&domain_id=" + asset).json()["total"] == 1
    assert c.get("/api/v1/tasks?limit=1&offset=1").json()["items"] == []


def test_recurrence_incomplete_and_stale_do_not_rewrite_human_work(workspace):
    c, _, _ = workspace
    finding, task = start(workspace)
    task = mutate(
        c,
        "/tasks/" + task["id"],
        {"version": 1, "status": "done", "note": "Keep this note"},
        "PATCH",
    ).json()
    moment = int(time.time())
    process(workspace, saved(workspace, at=moment + 10, issues=False))
    clean = c.get("/api/v1/tasks/" + task["id"]).json()
    assert clean["finding"]["status"] == "resolved" and clean["status"] == "done"
    process(workspace, saved(workspace, at=moment + 20))
    recurrence = c.get("/api/v1/tasks/" + task["id"]).json()
    assert recurrence["reopened_at"] == moment + 20 and recurrence["finding"]["status"] == "open"
    assert recurrence["note"] == "Keep this note" and recurrence["version"] == 2

    def missing(rows):
        return []

    process(workspace, saved(workspace, at=moment + 30, status="failed", overrides=missing))
    assert (
        c.get("/api/v1/tasks/" + task["id"]).json()["finding"]["recheck_status"] == "not_rechecked"
    )
    with c.app.state.database.sessions() as db:
        f = db.get(Finding, finding["id"])
        f.observed_at = moment - 8 * 86400
        db.commit()
    assert c.get("/api/v1/tasks/" + task["id"]).json()["finding"]["stale"]


def test_concurrent_create_and_update(workspace):
    c, _, _ = workspace
    process(workspace, saved(workspace))
    finding = c.get("/api/v1/findings").json()["items"][0]
    csrf = c.get("/api/v1/auth/csrf").json()["csrf_token"]
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}

    def create(_):
        return c.post(f"/api/v1/findings/{finding['id']}/task", json={}, headers=headers)

    with ThreadPoolExecutor(max_workers=4) as pool:
        replies = list(pool.map(create, range(4)))
    assert {r.status_code for r in replies} == {200}
    assert len({r.json()["id"] for r in replies}) == 1
    task = replies[0].json()

    def change(i):
        return c.patch(
            "/api/v1/tasks/" + task["id"], json={"version": 1, "note": str(i)}, headers=headers
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(change, range(2)))
    assert sorted(r.status_code for r in replies) == [200, 409]
    assert len(c.get("/api/v1/tasks/" + task["id"]).json()["history"]) == 2


def test_database_tenant_constraints_and_delete_cascade(workspace):
    c, _, asset = workspace
    _, task = start(workspace)
    other_finding = next(
        f["id"] for f in c.get("/api/v1/findings").json()["items"] if f["id"] != task["finding_id"]
    )
    with c.app.state.database.sessions() as db:
        other_user = User(email="db-constraint@example.com", password_hash="QA unused hash")
        db.add(other_user)
        db.flush()
        other_org = Organization(owner_id=other_user.id, name="QA other database tenant")
        db.add(other_org)
        db.flush()
        db.add(
            RemediationTask(
                organization_id=other_org.id,
                finding_id=other_finding,
                created_at=1,
                updated_at=1,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
    assert mutate(c, "/domains/" + asset, {}, "DELETE").status_code == 200
    assert c.get("/api/v1/tasks/" + task["id"]).status_code == 404
    with c.app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(TaskEvent)) == 0


def test_budget_and_history_bounds(workspace, monkeypatch):
    c, org, _ = workspace
    _, task = start(workspace)
    moment = int(time.time())
    for i in range(59):
        task = mutate(
            c, "/tasks/" + task["id"], {"version": task["version"], "note": str(i)}, "PATCH"
        ).json()
    assert (
        mutate(
            c, "/tasks/" + task["id"], {"version": task["version"], "note": "limit"}, "PATCH"
        ).status_code
        == 429
    )
    # Advance each group beyond the persistent rate window; keep total history bounded.
    monkeypatch.setattr("app.tasks.api.time.time", lambda: moment + 1000)
    for i in range(50):
        task = mutate(
            c,
            "/tasks/" + task["id"],
            {"version": task["version"], "note": "later" + str(i)},
            "PATCH",
        ).json()
    assert task["history_truncated"] and len(task["history"]) == 100
    assert task["history"][-1]["kind"] == "created"


def test_task_migration_preserves_phase05_sources(workspace, monkeypatch):
    c, _, _ = workspace
    finding, task = start(workspace)
    # Downgrade only the newly added task schema, preserving Phase 05 content.
    config = Config("alembic.ini")
    command.downgrade(config, "9752376ee8f2")
    assert c.get("/api/v1/auth/me").status_code == 200
    with c.app.state.database.sessions() as db:
        assert db.get(Finding, finding["id"]).status == "open"
    command.upgrade(config, "head")
    command.check(config)
    assert c.get("/api/v1/findings").json()["total"] == 6
    assert c.get("/api/v1/tasks").json()["total"] == 0


def test_resolved_creation_nonexistent_ids_and_atomic_rollback(workspace, monkeypatch):
    c, _, _ = workspace
    process(workspace, saved(workspace, at=int(time.time()) - 50))
    finding = c.get("/api/v1/findings").json()["items"][0]
    assert mutate(c, "/findings/" + str(uuid4()) + "/task", {}).status_code == 404
    # Force an event failure after the task insert; the request session must roll back both.
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    def crash(session, *args):
        if any(isinstance(row, TaskEvent) for row in session.new):
            raise RuntimeError("QA event failure")

    event.listen(Session, "before_flush", crash)
    try:
        with pytest.raises(RuntimeError):
            mutate(c, "/findings/" + finding["id"] + "/task", {})
    finally:
        event.remove(Session, "before_flush", crash)
    assert c.get("/api/v1/tasks").json()["total"] == 0
    task = mutate(c, "/findings/" + finding["id"] + "/task", {}).json()
    process(workspace, saved(workspace, at=int(time.time()) - 20, issues=False))
    assert mutate(c, "/findings/" + finding["id"] + "/task", {}).json()["id"] == task["id"]
    other = next(f for f in c.get("/api/v1/findings").json()["items"] if f["id"] != finding["id"])
    assert mutate(c, "/findings/" + other["id"] + "/task", {}).status_code == 409


def test_dashboard_and_tasks_do_not_probe_network(workspace, monkeypatch):
    c, _, _ = workspace
    _, task = start(workspace)
    import socket

    monkeypatch.setattr(socket, "socket", lambda *a, **kw: pytest.fail("No network permitted"))
    assert c.get("/api/v1/dashboard/summary").status_code == 200
    assert c.get("/api/v1/tasks/" + task["id"]).status_code == 200
    assert (
        mutate(
            c, "/tasks/" + task["id"], {"version": 1, "note": "Offline work"}, "PATCH"
        ).status_code
        == 200
    )


def test_dashboard_inflight_partial_clean_and_no_org(auth_client):  # noqa: F811
    c = auth_client
    account(c)
    assert c.get("/api/v1/dashboard/summary").status_code == 404
    org = mutate(c, "/organizations", {"name": "QA state coverage"}).json()["id"]
    empty = c.get("/api/v1/dashboard/summary").json()
    assert (
        empty["asset_count"] == 0
        and empty["recent_scan_count"] == 0
        and empty["findings"]["priorities"] == []
    )
    asset = mutate(
        c, "/domains", {"fqdn": "state.example.com", "authorization_acknowledged": True}
    ).json()["id"]
    ws = (c, org, asset)
    from app.models import ScanRun

    identifier = saved(ws, status="queued", at=int(time.time()) - 20)
    summary = c.get("/api/v1/dashboard/summary").json()
    assert summary["findings"]["summary"]["assessment"]["in_flight_scans"] == 1
    assert summary["findings"]["total"] == 0
    with c.app.state.database.sessions() as db:
        run = db.get(ScanRun, identifier)
        run.status = "partial"
        db.commit()
    process(ws, identifier)
    assert c.get("/api/v1/dashboard/summary").json()["scans"][0]["status"] == "partial"
    process(ws, saved(ws, issues=False, at=int(time.time()) - 10))
    clean = c.get("/api/v1/dashboard/summary").json()
    assert clean["findings"]["total"] == 0 and clean["findings"]["priorities"] == []
    assert clean["findings"]["summary"]["assessment"]["rule_counts"]["clear"] == 6
