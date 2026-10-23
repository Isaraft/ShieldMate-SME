from unittest.mock import Mock

import dns.exception
import dns.message
import dns.rcode
import dns.rrset
import pytest
from test_auth import account, auth_client, mutate  # noqa: F401

from app import domain_dns, domains
from app.domain_validation import canonical_domain
from app.models import DomainAsset


def enroll(c, fqdn="example.com", **extra):
    return mutate(c, "/domains", {"fqdn": fqdn, "authorization_acknowledged": True, **extra})


@pytest.fixture
def owner(auth_client):  # noqa: F811
    c = auth_client
    account(c)
    mutate(c, "/organizations", {"name": "QA domains"})
    c.app.state.check_txt = Mock(return_value="not_found")
    return c


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com",
        "127.0.0.1",
        "::1",
        "2130706433",
        "127.1",
        "localhost",
        "a.local",
        "a.internal",
        "test",
        "a.test",
        "com",
        "co.uk",
        "github.io",
        "*.example.com",
        "a@example.com",
        "example.com/path",
        "example.com:443",
        "example.com?x",
        "example.com#x",
        " example.com",
        "example.com\n",
        "a_b.com",
        "example\\com",
        "xn--.com",
        "éxample.com",
        "a" * 64 + ".com",
        "a." * 128 + "com",
        "a..com",
        "example.com..",
        "a.onion",
        "a.invalid",
        "a.home",
        "0x7f000001",
        "",
    ],
)
def test_invalid_names_never_query(owner, value):
    assert enroll(owner, value).status_code == 422
    owner.app.state.check_txt.assert_not_called()


def test_normalization_consent_uniqueness_and_quota(owner):
    c = owner
    first = enroll(c, "Example.COM.").json()
    assert first["canonical_fqdn"] == "example.com" and first["status"] == "pending"
    assert first["authorization_attested_at"] and first["authorization_policy_version"]
    assert first["record_hostname"] == "_shieldmate-challenge.example.com"
    assert len(first["record_value"].split("=")[1]) >= 43
    assert c.get("/api/v1/domains/" + first["id"]).json()["record_value"] == first["record_value"]
    assert enroll(c, "example.com").status_code == 409
    assert enroll(c, "shop.example.com").status_code == 201
    assert enroll(c, "different.com", verified=True).status_code == 422
    assert (
        mutate(
            c, "/domains", {"fqdn": "different.com", "authorization_acknowledged": False}
        ).status_code
        == 422
    )
    assert mutate(c, "/domains", {"fqdn": "different.com"}).status_code == 422
    c.app.state.settings.domain_quota = 2
    assert enroll(c, "another.com").status_code == 409
    c.app.state.check_txt.assert_not_called()


def test_exact_success_expiry_and_rotation(owner, monkeypatch):
    c = owner
    row = enroll(c).json()
    path = "/domains/" + row["id"]
    c.app.state.check_txt = Mock(return_value="match")
    result = mutate(c, path + "/verification/check").json()
    assert result["code"] == "verified" and result["domain"]["verified_at"]
    c.app.state.check_txt.assert_called_once_with(row["record_hostname"], row["record_value"], 3.0)
    monkeypatch.setattr(domains, "now", lambda: row["challenge_expires_at"] + 1)
    assert c.get("/api/v1" + path).json()["status"] == "verified"
    assert mutate(c, path + "/verification/check").json()["code"] == "challenge_expired"
    monkeypatch.setattr(domains, "now", lambda: result["domain"]["verification_valid_until"] + 1)
    assert c.get("/api/v1" + path).json()["status"] == "stale"
    fresh = mutate(c, path + "/verification/request").json()
    assert fresh["status"] == "pending" and fresh["challenge_generation"] == 2
    assert fresh["record_value"] != row["record_value"] and fresh["verified_at"] is None
    c.app.state.check_txt = Mock(return_value="not_found")
    assert mutate(c, path + "/verification/check").json()["domain"]["status"] == "pending"


@pytest.mark.parametrize("outcome", ["not_found", "temporarily_unavailable"])
def test_dns_failure_not_verified(owner, outcome):
    row = enroll(owner).json()
    owner.app.state.check_txt = Mock(return_value=outcome)
    response = mutate(owner, "/domains/" + row["id"] + "/verification/check")
    assert response.status_code == 200 and response.json()["code"] == outcome
    assert response.json()["domain"]["verified_at"] is None


@pytest.mark.parametrize("race", ["rotate", "delete", "expire"])
def test_delayed_lookup_cannot_override_new_state(owner, monkeypatch, race):
    c = owner
    row = enroll(c).json()
    path = "/domains/" + row["id"]

    def resolve(*_):
        with c.app.state.database.sessions() as db:
            asset = db.get(DomainAsset, row["id"])
            if race == "delete":
                db.delete(asset)
            elif race == "rotate":
                asset.challenge_generation += 1
                asset.challenge_token = "replacement"
            else:
                asset.challenge_expires_at = 0
            db.commit()
        return "match"

    c.app.state.check_txt = resolve
    assert mutate(c, path + "/verification/check").status_code == 409
    if race == "delete":
        assert c.get("/api/v1" + path).status_code == 404
    else:
        assert c.get("/api/v1" + path).json()["verified_at"] is None


def test_cross_tenant_csrf_and_deletion(owner):
    c = owner
    first = enroll(c).json()
    path = "/domains/" + first["id"]
    for suffix, method in [
        ("", "DELETE"),
        ("/verification/check", "POST"),
        ("/verification/request", "POST"),
    ]:
        assert (
            c.request(
                method, "/api/v1" + path + suffix, headers={"Origin": "http://127.0.0.1:5173"}
            ).status_code
            == 403
        )
        assert (
            mutate(c, path + suffix, method=method, Origin="https://evil.example").status_code
            == 403
        )
    account(c, "second@example.com")
    mutate(c, "/organizations", {"name": "Second"})
    assert enroll(c).status_code == 201
    assert c.get("/api/v1" + path).status_code == 404
    for suffix, method in [
        ("", "DELETE"),
        ("/verification/check", "POST"),
        ("/verification/request", "POST"),
    ]:
        assert mutate(c, path + suffix, method=method).status_code == 404
    assert enroll(c, "different.com", organization_id=first["id"]).status_code == 422
    c.app.state.check_txt.assert_not_called()
    own = c.get("/api/v1/domains").json()[0]
    assert mutate(c, "/domains/" + own["id"], method="DELETE").status_code == 200
    assert c.get("/api/v1/domains").json() == []
    mutate(c, "/auth/logout")
    assert c.get("/api/v1/domains").status_code == 401


def test_persisted_rate_limit(owner):
    c = owner
    row = enroll(c).json()
    c.app.state.settings.domain_rate_limit = 1
    for suffix in ["/verification/check", "/verification/request"]:
        assert mutate(c, "/domains/" + row["id"] + suffix).status_code == 429
    assert enroll(c, "another.com").status_code == 429


@pytest.mark.parametrize(
    "records,expected",
    [
        (['"wrong"'], "not_found"),
        (['"prefix shieldmate-verification=token suffix"'], "not_found"),
        (['"shieldmate-verification=token"'], "match"),
        (['"wrong"', '"shieldmate-verifi" "cation=token"'], "match"),
    ],
)
def test_udp_exact_answers_and_chunks(monkeypatch, records, expected):
    host = "_shieldmate-challenge.example.com"

    def udp(query, server, **kwargs):
        assert query.question[0].name.to_text() == host + "."
        assert query.question[0].rdtype == 16
        assert kwargs == {"timeout": 3, "raise_on_truncation": True}
        response = dns.message.make_response(query)
        response.answer.append(dns.rrset.from_text(host + ".", 60, "IN", "TXT", *records))
        return response

    monkeypatch.setattr(domain_dns.dns.query, "udp", udp)
    assert domain_dns.check_txt(host, "shieldmate-verification=token", 3) == expected


@pytest.mark.parametrize("code", [dns.rcode.NXDOMAIN, dns.rcode.SERVFAIL])
def test_dns_rcodes(monkeypatch, code):
    def udp(query, *args, **kwargs):
        response = dns.message.make_response(query)
        response.set_rcode(code)
        return response

    monkeypatch.setattr(domain_dns.dns.query, "udp", udp)
    assert domain_dns.check_txt("_shieldmate-challenge.example.com", "x", 3) == (
        "not_found" if code == dns.rcode.NXDOMAIN else "temporarily_unavailable"
    )


def test_dns_timeout(monkeypatch):
    monkeypatch.setattr(domain_dns.dns.query, "udp", Mock(side_effect=dns.exception.Timeout))
    assert (
        domain_dns.check_txt("_shieldmate-challenge.example.com", "x", 3)
        == "temporarily_unavailable"
    )


def test_punycode():
    assert canonical_domain("xn--e1afmkfd.com") == "xn--e1afmkfd.com"


def test_ip_limit(owner):
    c = owner
    c.app.state.settings.domain_ip_rate_limit = 1
    assert enroll(c).status_code == 201
    assert enroll(c, "another.com").status_code == 429


def test_wrong_owner_name_and_no_answer(monkeypatch):
    def udp(query, *args, **kwargs):
        reply = dns.message.make_response(query)
        reply.answer.append(
            dns.rrset.from_text(
                "_wrong.example.com.", 60, "IN", "TXT", '"shieldmate-verification=token"'
            )
        )
        return reply

    monkeypatch.setattr(domain_dns.dns.query, "udp", udp)
    assert (
        domain_dns.check_txt(
            "_shieldmate-challenge.example.com", "shieldmate-verification=token", 3
        )
        == "not_found"
    )
    monkeypatch.setattr(
        domain_dns.dns.query, "udp", lambda query, *args, **kwargs: dns.message.make_response(query)
    )
    assert (
        domain_dns.check_txt(
            "_shieldmate-challenge.example.com", "shieldmate-verification=token", 3
        )
        == "not_found"
    )


def test_upgrade_preserves_phase02_identity_and_session(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    url = f"sqlite:///{tmp_path / 'upgrade.db'}"
    monkeypatch.setenv("SHIELDMATE_DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "6b5520d9fa5d")
    with TestClient(
        create_app(
            Settings(
                _env_file=None, database_url=url, environment="test", allowed_hosts=["testserver"]
            )
        )
    ) as client:
        account(client)
        mutate(client, "/organizations", {"name": "Existing Phase 02 company"})
        before = client.get("/api/v1/auth/me").json()
        command.upgrade(config, "head")
        command.check(config)
        assert client.get("/api/v1/auth/me").json() == before
        assert enroll(client).status_code == 201
        with TestClient(create_app(client.app.state.settings)) as restarted:
            restarted.cookies.update(client.cookies)
            assert restarted.get("/api/v1/domains").json() == client.get("/api/v1/domains").json()


def test_verified_state_persists_and_scanner_is_absent(owner):
    from fastapi.testclient import TestClient

    from app.main import create_app

    c = owner
    row = enroll(c).json()
    c.app.state.check_txt = Mock(return_value="match")
    assert mutate(c, "/domains/" + row["id"] + "/verification/check").json()["code"] == "verified"
    with TestClient(create_app(c.app.state.settings)) as restarted:
        restarted.cookies.update(c.cookies)
        assert restarted.get("/api/v1/domains/" + row["id"]).json()["status"] == "verified"
    assert mutate(c, "/domains/" + row["id"] + "/scans").status_code == 404


def test_no_tcp_fallback(monkeypatch):
    monkeypatch.setattr(
        domain_dns.dns.query, "tcp", Mock(side_effect=AssertionError("TCP prohibited"))
    )
    monkeypatch.setattr(domain_dns.dns.query, "udp", Mock(side_effect=dns.exception.DNSException))
    assert (
        domain_dns.check_txt("_shieldmate-challenge.example.com", "x", 3)
        == "temporarily_unavailable"
    )
