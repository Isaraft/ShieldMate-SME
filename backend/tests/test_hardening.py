"""Adversarial request/session cases; no external target traffic."""

import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.scanner.policy import public_ip
from tests.test_auth import ORIGIN, account, auth_client  # noqa: F401


def test_other_tab_csrf_read_does_not_revoke_inflight_mutation(auth_client):  # noqa: F811
    c = auth_client
    account(c)
    first = c.get("/api/v1/auth/csrf").json()["csrf_token"]
    second = c.get("/api/v1/auth/csrf").json()["csrf_token"]
    assert first == second
    response = c.post(
        "/api/v1/organizations",
        json={"name": "Two tabs"},
        headers={"Origin": ORIGIN, "X-CSRF-Token": first},
    )
    assert response.status_code == 201
    assert (
        c.post(
            "/api/v1/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": second}
        ).status_code
        == 200
    )
    assert (
        c.post(
            "/api/v1/organizations",
            json={"name": "Stale"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": first},
        ).status_code
        == 401
    )


def test_actual_body_bound_and_safe_asgi_exception(caplog):
    app = create_app(
        Settings(_env_file=None, database_url="sqlite:///:memory:", allowed_hosts=["testserver"])
    )
    called = []

    @app.post("/controlled-body")
    def body(data: dict):
        called.append(data)
        return {"ok": True}

    @app.get("/controlled-error")
    def broken():
        raise RuntimeError("PRIVATE-QA-EXCEPTION-MARKER")

    with TestClient(app) as c:  # Exceptions must not escape to Uvicorn's traceback logger.
        r = c.post(
            "/controlled-body",
            content=json.dumps({"text": "x" * 20000}),
            headers={"Content-Type": "application/json", "Content-Length": "2"},
        )
        assert r.status_code == 413 and called == []
        assert (
            c.post("/controlled-body", content="{}", headers={"Content-Length": "1"}).status_code
            == 400
        )
        assert c.post("/controlled-body", json={}).status_code == 200
        error = c.get("/controlled-error")
        assert error.status_code == 500 and error.headers["x-frame-options"] == "DENY"
        assert "PRIVATE-QA" not in error.text + caplog.text


def test_explicit_recent_special_prefixes():
    for address in ["100:0:0:1::1", "3fff::1", "5f00::1"]:
        assert not public_ip(address)


def test_readiness_detects_missing_or_stale_schema(auth_client):  # noqa: F811
    c = auth_client
    assert c.get("/api/v1/health/ready").json() == {"status": "ready"}
    from sqlalchemy import text

    with c.app.state.database.sessions() as db:
        db.execute(text("UPDATE alembic_version SET version_num='outdated'"))
        db.commit()
    assert c.get("/api/v1/health").status_code == 200
    assert c.get("/api/v1/health/ready").status_code == 503


def test_local_release_is_strict_and_cookie_namespaced(tmp_path, monkeypatch):
    import pytest
    from pydantic import ValidationError

    for change in [
        {"cookie_secure": True},
        {"cors_origins": ["http://localhost:8080"]},
        {"trusted_origins": ["http://evil.example:8080"]},
        {"trusted_origins": []},
        {"database_url": "sqlite:///:memory:"},
    ]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, environment="local_release", **change)
    for origin in ["http://localhost:bad", "http://localhost:0", "http://localhost:8080\n"]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, trusted_origins=[origin])
    settings = Settings(
        _env_file=None,
        environment="local_release",
        database_url=f"sqlite:///{tmp_path / 'release.db'}",
        allowed_hosts=["127.0.0.1", "backend"],
        trusted_origins=["http://127.0.0.1:8080"],
    )
    with TestClient(create_app(settings), base_url="http://127.0.0.1:8080") as c:
        # A missing migrated DB is not healthy readiness, while liveness remains honest.
        assert c.get("/api/v1/health/ready").status_code == 503


def test_anonymous_bootstrap_cannot_create_unbounded_sessions(auth_client):  # noqa: F811
    c = auth_client
    first = c.get("/api/v1/auth/csrf")
    cookie = c.cookies.get("shieldmate_session")
    assert first.status_code == 200
    for _ in range(99):
        c.cookies.clear()
        assert c.get("/api/v1/auth/csrf").status_code == 200
    c.cookies.clear()
    blocked = c.get("/api/v1/auth/csrf")
    assert blocked.status_code == 429 and blocked.headers["retry-after"] == "900"
    c.cookies.set("shieldmate_session", cookie)
    assert c.get("/api/v1/auth/csrf").status_code == 200


def test_local_release_cookie_does_not_overwrite_standard_profile(auth_client):  # noqa: F811
    settings = auth_client.app.state.settings.model_copy(
        update={
            "environment": "local_release",
            "allowed_hosts": ["127.0.0.1", "backend"],
            "trusted_origins": ["http://127.0.0.1:8080"],
        }
    )
    with TestClient(create_app(settings), base_url="http://127.0.0.1:8080") as c:
        c.cookies.set("shieldmate_session", "unrelated-standard-profile")
        response = c.get("/api/v1/auth/csrf")
        assert response.status_code == 200
        assert c.cookies.get("shieldmate_session") == "unrelated-standard-profile"
        assert c.cookies.get("shieldmate_rc_session")
        assert "HttpOnly" in response.headers["set-cookie"]


def test_sqlite_full_error_is_safe_and_rolls_back(auth_client, caplog):  # noqa: F811
    from sqlalchemy import text

    from app.auth import DB

    c = auth_client
    with c.app.state.database.engine.connect() as db:
        db.exec_driver_sql("CREATE TABLE qa_full(value BLOB)")
        db.commit()
        pages = db.exec_driver_sql("PRAGMA page_count").scalar()
        db.exec_driver_sql(f"PRAGMA max_page_count={pages}")

    @c.app.post("/controlled-full")
    def full(db: DB):
        db.execute(
            text("INSERT INTO qa_full(value) VALUES (:value)"),
            {"value": "PRIVATE-STORAGE-MARKER" * 20000},
        )
        db.commit()

    response = c.post("/controlled-full", json={})
    assert response.status_code == 500
    assert "PRIVATE-STORAGE-MARKER" not in response.text + caplog.text
    with c.app.state.database.sessions() as db:
        assert db.scalar(text("SELECT count(*) FROM qa_full")) == 0
