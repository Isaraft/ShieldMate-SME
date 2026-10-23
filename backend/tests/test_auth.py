import secrets
import time

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth import COOKIE, _attempts, digest
from app.config import Settings
from app.main import create_app
from app.models import LoginSession, User

ORIGIN = "http://127.0.0.1:5173"
PASSWORD = secrets.token_urlsafe(24) + " Ж"


@pytest.fixture
def auth_client(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("SHIELDMATE_DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "0001_foundation")
    command.upgrade(config, "head")
    command.check(config)
    _attempts.clear()
    settings = Settings(
        _env_file=None, database_url=url, environment="test", allowed_hosts=["testserver"]
    )
    with TestClient(create_app(settings)) as client:
        yield client


def mutate(client, path, body=None, method="POST", **headers):
    csrf = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    return client.request(
        method,
        "/api/v1" + path,
        json=body,
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf, **headers},
    )


def account(client, email="owner@example.com"):
    assert (
        mutate(client, "/auth/register", {"email": email, "password": PASSWORD}).status_code == 201
    )
    assert mutate(client, "/auth/login", {"email": email, "password": PASSWORD}).status_code == 200


def test_full_flow_and_revocation(auth_client):
    c = auth_client
    account(c)
    cookie = c.cookies.get(COOKIE)
    assert (
        "HttpOnly"
        in mutate(c, "/auth/login", {"email": "owner@example.com", "password": PASSWORD}).headers[
            "set-cookie"
        ]
    )
    assert c.get("/api/v1/auth/me").json()["organization"] is None
    created = mutate(c, "/organizations", {"name": "  My   company "})
    assert created.status_code == 201
    assert created.json()["name"] == "My company"
    assert mutate(c, "/organizations", {"name": "Duplicate"}).status_code == 409
    assert mutate(c, "/organizations/current", {"name": "Renamed"}, "PATCH").status_code == 200
    assert c.get("/api/v1/auth/me").json()["organization"]["name"] == "Renamed"
    with c.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")
        assert PASSWORD not in user.password_hash
        assert db.get(LoginSession, digest(cookie)).revoked
    old = c.cookies.get(COOKIE)
    assert mutate(c, "/auth/logout").status_code == 200
    c.cookies.set(COOKIE, old)
    assert c.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("password", ["short", "x" * 129])
def test_password_bounds(auth_client, password):
    assert (
        mutate(
            auth_client, "/auth/register", {"email": "a@example.com", "password": password}
        ).status_code
        == 422
    )


def test_email_and_generic_login(auth_client):
    c = auth_client
    account(c, "Owner@Example.com")
    assert (
        mutate(
            c, "/auth/register", {"email": "owner@example.com", "password": PASSWORD}
        ).status_code
        == 409
    )
    assert mutate(c, "/auth/register", {"email": "bad", "password": PASSWORD}).status_code == 422
    failures = [
        mutate(c, "/auth/login", {"email": email, "password": "wrong passphrase here"}).json()
        for email in ["owner@example.com", "missing@example.com"]
    ]
    assert failures[0] == failures[1]


def test_csrf_and_origin(auth_client):
    c = auth_client
    account(c)
    for path, method, body in [
        ("/auth/login", "POST", {"email": "a@example.com", "password": PASSWORD}),
        ("/auth/register", "POST", {"email": "b@example.com", "password": PASSWORD}),
        ("/auth/logout", "POST", None),
        ("/organizations", "POST", {"name": "Company"}),
        ("/organizations/current", "PATCH", {"name": "Other"}),
    ]:
        assert (
            c.request(method, "/api/v1" + path, json=body, headers={"Origin": ORIGIN}).status_code
            == 403
        )
        assert (
            c.request(
                method,
                "/api/v1" + path,
                json=body,
                headers={"Origin": ORIGIN, "X-CSRF-Token": "wrong"},
            ).status_code
            == 403
        )
        assert mutate(c, path, body, method, Origin="https://evil.example").status_code == 403


def test_tenant_isolation_and_payloads(auth_client):
    c = auth_client
    account(c)
    first = mutate(c, "/organizations", {"name": "First"}).json()
    account(c, "second@example.com")
    assert c.get("/api/v1/organizations/current").status_code == 404
    second = mutate(c, "/organizations", {"name": "Second"}).json()
    assert second["id"] != first["id"]
    assert c.get("/api/v1/organizations/" + first["id"]).status_code == 404
    assert (
        mutate(
            c, "/organizations/current", {"name": "Stolen", "organization_id": first["id"]}, "PATCH"
        ).status_code
        == 422
    )
    assert mutate(c, "/organizations/current", {"name": " "}, "PATCH").status_code == 422
    mutate(c, "/auth/login", {"email": "owner@example.com", "password": PASSWORD})
    assert c.get("/api/v1/organizations/current").json()["name"] == "First"
    assert "password" not in c.get("/api/v1/auth/me").text
    assert "csrf" not in c.get("/api/v1/auth/me").text


def test_invalid_expired_and_unauthenticated(auth_client):
    c = auth_client
    for path in ["/auth/me", "/organizations/current"]:
        assert c.get("/api/v1" + path).status_code == 401
    c.cookies.set(COOKIE, "forged-session-token-more-than-20")
    assert c.get("/api/v1/auth/me").status_code == 401
    c.cookies.clear()
    account(c)
    with c.app.state.database.sessions() as db:
        session = db.get(LoginSession, digest(c.cookies.get(COOKIE)))
        session.expires_at = int(time.time()) - 1
        db.commit()
    assert c.get("/api/v1/auth/me").status_code == 401
    assert c.patch("/api/v1/organizations/current", json={"name": "No access"}).status_code in [
        401,
        403,
    ]


def test_rate_limit(auth_client):
    c = auth_client
    c.app.state.settings.auth_rate_limit = 2
    for _ in range(2):
        assert (
            mutate(
                c, "/auth/login", {"email": "absent@example.com", "password": PASSWORD}
            ).status_code
            == 401
        )
    assert (
        mutate(c, "/auth/login", {"email": "absent@example.com", "password": PASSWORD}).status_code
        == 429
    )


def test_production_fails_closed():
    with pytest.raises(ValueError):
        Settings(_env_file=None, environment="production")


def test_session_survives_new_application_instance(auth_client):
    c = auth_client
    account(c)
    mutate(c, "/organizations", {"name": "Persistent company"})
    cookie = c.cookies.get(COOKIE)
    with TestClient(create_app(c.app.state.settings)) as restarted:
        restarted.cookies.set(COOKIE, cookie)
        result = restarted.get("/api/v1/auth/me")
        assert result.status_code == 200
        assert result.json()["organization"]["name"] == "Persistent company"


def test_body_limit_and_private_mutations(auth_client):
    c = auth_client
    assert c.post("/api/v1/auth/register", content="x" * 17000).status_code == 413
    assert mutate(c, "/organizations", {"name": "Unauthenticated"}).status_code == 401
    assert (
        mutate(c, "/organizations/current", {"name": "Unauthenticated"}, "PATCH").status_code == 401
    )


def test_registration_rate_limit(auth_client):
    c = auth_client
    c.app.state.settings.auth_rate_limit = 1
    assert (
        mutate(
            c, "/auth/register", {"email": "first@example.com", "password": PASSWORD}
        ).status_code
        == 201
    )
    assert (
        mutate(c, "/auth/register", {"email": "next@example.com", "password": PASSWORD}).status_code
        == 429
    )


def test_secure_cookie_configuration(auth_client):
    c = auth_client
    settings = Settings(
        _env_file=None,
        environment="production",
        cookie_secure=True,
        trusted_origins=["https://testserver"],
        allowed_hosts=["testserver"],
        database_url=c.app.state.settings.database_url,
    )
    with TestClient(create_app(settings), base_url="https://testserver") as secure:
        response = secure.get("/api/v1/auth/csrf")
        cookie = response.headers["set-cookie"]
        assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
        assert "Path=/api" in cookie and "Max-Age=1800" in cookie
        assert response.headers["cache-control"] == "no-store"
