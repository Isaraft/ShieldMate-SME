# ruff: noqa: F811
import hashlib
import io
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from pypdf import PdfReader
from sqlalchemy import func, select

from app.models import DomainAsset, ReportEvent, ScanRun, SecurityReport
from app.reports import pdf
from app.reports.demo import sample
from tests.test_auth import ORIGIN, account, auth_client, mutate  # noqa: F401
from tests.test_findings import process, saved, workspace  # noqa: F401


def prepared(workspace, issues=True, status="completed", at=None):
    c, _, asset = workspace
    moment = at or int(time.time()) - 10
    with c.app.state.database.sessions() as db:
        domain = db.get(DomainAsset, asset)
        if not domain.verified_at:
            domain.verified_at = moment - 100
        domain.verification_valid_until = int(time.time()) + 86400
        verified = domain.verified_at
        db.commit()
    run = saved(workspace, issues=issues, status=status, at=moment)
    with c.app.state.database.sessions() as db:
        db.get(ScanRun, run).proof_verified_at = verified
        db.commit()
    process(workspace, run)
    return run


def make(c, locale="en", key=None):
    return mutate(c, "/reports", {"locale": locale, "request_key": key or str(uuid4())})


def test_scoped_snapshot_current_evidence_and_pdf_immutability(workspace):
    c, _, asset = workspace
    prepared(workspace)
    current = c.get("/api/v1/reports/overview").json()
    assert current["can_generate"] and current["counts"]["assessed_domains"] == 1
    assert len(current["assets"][0]["observations"]) == 8 and len(current["findings"]) == 6
    assert [f["id"] for f in current["priorities"]] == [
        f["id"] for f in c.get("/api/v1/findings").json()["priorities"]
    ]
    finding = current["priorities"][0]
    task = mutate(c, f"/findings/{finding['id']}/task", {}).json()
    mutate(
        c,
        "/tasks/" + task["id"],
        {
            "version": 1,
            "status": "done",
            "owner_label": "ИТ-провайдер",
            "note": "PRIVATE-NOTE-NOT-FOR-PDF",
        },
        "PATCH",
    )
    key = str(uuid4())
    created = make(c, key=key)
    assert created.status_code == 200, created.text
    record = created.json()
    assert record["status"] == "ready"
    result = c.get(f"/api/v1/reports/{record['id']}/download")
    assert result.status_code == 200 and result.headers["content-type"] == "application/pdf"
    assert result.headers["content-disposition"].startswith('attachment; filename="shieldmate-')
    assert (
        result.headers["cache-control"] == "private, no-store"
        and result.headers["x-content-type-options"] == "nosniff"
    )
    assert hashlib.sha256(result.content).hexdigest() == record["sha256"]
    reader = PdfReader(io.BytesIO(result.content))
    text = "\n".join(p.extract_text() for p in reader.pages)
    assert len(reader.pages) >= 2 and "Security Snapshot" in text and asset in text
    assert "remediation not yet verified" in text and "PRIVATE-NOTE" not in text
    assert make(c, key=key).json()["id"] == record["id"]
    assert make(c, "ru", key).status_code == 409
    prepared(workspace, issues=False, at=int(time.time()) + 1)
    assert c.get("/api/v1/reports/overview").json()["priorities"] == []
    assert c.get(f"/api/v1/reports/{record['id']}/download").content == result.content
    newer = make(c).json()
    assert newer["status"] == "ready" and newer["sha256"] != record["sha256"]
    assert c.get("/api/v1/reports").json()["total"] == 2


@pytest.mark.parametrize(
    "scenario",
    ["empty", "unverified", "no_scan", "expired", "rotated", "unsupported", "failed", "pending"],
)
def test_no_evidence_readiness_cannot_fabricate_clean_report(workspace, scenario):
    c, _, asset = workspace
    if scenario in {"expired", "rotated", "unsupported", "failed", "pending"}:
        run = prepared(workspace)
    with c.app.state.database.sessions() as db:
        domain = db.get(DomainAsset, asset)
        if scenario == "empty":
            db.delete(domain)
        elif scenario == "no_scan":
            domain.verified_at = int(time.time()) - 100
            domain.verification_valid_until = int(time.time()) + 100
        elif scenario == "expired":
            domain.verification_valid_until = int(time.time()) - 1
        elif scenario == "rotated":
            domain.challenge_generation += 1
        elif scenario == "unsupported":
            db.get(ScanRun, run).engine_version = "unknown"
        elif scenario == "failed":
            db.get(ScanRun, run).error_code = "authorization_changed"
        elif scenario == "pending":
            db.get(ScanRun, run).status = "running"
        db.commit()
    overview = c.get("/api/v1/reports/overview").json()
    assert not overview["can_generate"] and overview["counts"]["assessed_domains"] == 0
    assert overview["findings"] == [] and overview["priorities"] == []
    assert make(c).status_code == 409


def test_mixed_partial_stale_and_pruned_source(workspace):
    c, _, asset = workspace
    run = prepared(workspace, status="partial", at=int(time.time()) - 8 * 86400)
    current = c.get("/api/v1/reports/overview").json()
    assert current["can_generate"] and current["readiness"] == "stale"
    other = mutate(
        c, "/domains", {"fqdn": "unverified.example.com", "authorization_acknowledged": True}
    ).json()
    current = c.get("/api/v1/reports/overview").json()
    assert current["counts"]["enrolled_domains"] == 2 and current["counts"]["assessed_domains"] == 1
    assert next(a for a in current["assets"] if a["id"] == other["id"])["observations"] == []
    with c.app.state.database.sessions() as db:
        db.delete(db.get(ScanRun, run))
        db.commit()
    current = c.get("/api/v1/reports/overview").json()
    assert current["findings"] == [] and current["counts"]["excluded_historical_findings"] == 6


def test_organization_idor_csrf_session_and_query_bounds(workspace):
    c, _, _ = workspace
    prepared(workspace)
    record = make(c).json()
    for headers in [{}, {"Origin": "https://evil.example", "X-CSRF-Token": "invalid"}]:
        assert (
            c.post(
                "/api/v1/reports", json={"request_key": str(uuid4())}, headers=headers
            ).status_code
            == 403
        )
    for query in ["limit=21", "offset=-1", "organization_id=forged"]:
        assert c.get("/api/v1/reports?" + query).status_code == 422
    for payload in [
        {"locale": "xx", "request_key": str(uuid4())},
        {"locale": "en", "request_key": "../file"},
        {"request_key": str(uuid4()), "organization_id": "forged"},
    ]:
        assert mutate(c, "/reports", payload).status_code == 422
    account(c, "second@example.com")
    mutate(c, "/organizations", {"name": "Other"})
    for suffix in ["", "/download"]:
        assert c.get("/api/v1/reports/" + record["id"] + suffix).status_code == 404
    assert c.get("/api/v1/reports").json()["total"] == 0
    c.cookies.clear()
    for path in [
        "/reports",
        "/reports/overview",
        "/reports/" + record["id"],
        "/reports/" + record["id"] + "/download",
    ]:
        assert c.get("/api/v1" + path).status_code == 401
    assert c.get("/api/v1/reports/..%2Ffile/download").status_code in {404, 422}


def test_renderer_failure_is_not_published_and_attempts_bounded(workspace, monkeypatch):
    c, _, _ = workspace
    prepared(workspace)
    monkeypatch.setattr(
        pdf, "render", lambda _: (_ for _ in ()).throw(OSError("secret-path-and-token"))
    )
    for _i in range(5):
        record = make(c).json()
        assert (
            record["status"] == "failed" and record["byte_count"] == 0 and record["sha256"] is None
        )
        assert c.get("/api/v1/reports/" + record["id"] + "/download").status_code == 409
    assert make(c).status_code == 429
    assert "secret-path" not in str(c.get("/api/v1/reports").json())


def test_concurrent_generation_duplicate_and_guard(workspace, monkeypatch):
    c, _, _ = workspace
    prepared(workspace)
    enter, release = threading.Event(), threading.Event()
    original = pdf.render

    def slow(snapshot):
        enter.set()
        assert release.wait(10)
        return original(snapshot)

    monkeypatch.setattr(pdf, "render", slow)
    csrf = c.get("/api/v1/auth/csrf").json()["csrf_token"]
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
    key = str(uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(c.post, "/api/v1/reports", json={"request_key": key}, headers=headers)
        assert enter.wait(5)
        duplicate = c.post("/api/v1/reports", json={"request_key": key}, headers=headers)
        assert duplicate.status_code == 200 and duplicate.json()["status"] == "generating"
        assert (
            c.post(
                "/api/v1/reports", json={"request_key": str(uuid4())}, headers=headers
            ).status_code
            == 409
        )
        release.set()
        assert pending.result().json()["status"] == "ready"
    assert c.get("/api/v1/reports").json()["total"] == 1


def test_stale_generation_and_corrupt_bytes_fail_closed(workspace):
    c, _, _ = workspace
    prepared(workspace)
    record = make(c).json()
    with c.app.state.database.sessions() as db:
        row = db.get(SecurityReport, record["id"])
        row.pdf = b"corrupt"
        db.commit()
    assert c.get("/api/v1/reports/" + record["id"] + "/download").status_code == 409
    with c.app.state.database.sessions() as db:
        row = db.get(SecurityReport, record["id"])
        row.status = "generating"
        row.created_at = int(time.time()) - 400
        db.commit()
    assert make(c).json()["status"] == "ready"
    assert c.get("/api/v1/reports/" + record["id"]).json()["status"] == "failed"


def test_history_limit_and_pdf_audit_are_bounded(workspace):
    c, _, _ = workspace
    prepared(workspace)
    first = make(c).json()
    with c.app.state.database.sessions() as db:
        original = db.get(SecurityReport, first["id"])
        for _i in range(19):
            db.add(
                SecurityReport(
                    id=str(uuid4()),
                    organization_id=original.organization_id,
                    created_by=original.created_by,
                    request_key=str(uuid4()),
                    locale="en",
                    created_at=1,
                    status="failed",
                    schema_version=original.schema_version,
                    snapshot=original.snapshot,
                )
            )
        db.commit()
    assert make(c).status_code == 429
    assert len(c.get("/api/v1/reports?offset=10&limit=10").json()["items"]) == 10
    for _ in range(105):
        assert c.get("/api/v1/reports/" + first["id"] + "/download").status_code == 200
    with c.app.state.database.sessions() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(ReportEvent)
                .where(ReportEvent.report_id == first["id"])
            )
            == 100
        )


def test_pdf_unicode_escaping_pages_and_demo_separation(auth_client, monkeypatch):
    c = auth_client
    for locale in ["en", "ru", "kk"]:
        snapshot = sample(locale)
        snapshot.organization_name = (
            'ТОО «ӘҒҚҢӨҰҮҺІ» <img src="https://evil.example"> \u202e' + "ДлинноеНазвание" * 25
        )
        snapshot.findings = snapshot.findings * 7
        data = pdf.render(snapshot)
        reader = PdfReader(io.BytesIO(data))
        texts = [p.extract_text() for p in reader.pages]
        assert 3 <= len(texts) <= 80
        assert "https://evil.example" in "\n".join(texts)
        assert all("DEMO" in text for text in texts)
        assert (
            {
                "en": "External Security Configuration Assessment",
                "ru": "Проверка внешних настроек безопасности",
                "kk": "Сыртқы қауіпсіздік баптауларын бағалау",
            }[locale]
        ) in " ".join(texts[0].split())
        assert "ӘҒҚҢӨҰҮҺІ" in texts[0] and "\u202e" not in "\n".join(texts)
        assert len(data) <= pdf.MAX_BYTES
    # Public routes cannot touch real sessions, tenant records or sockets.
    monkeypatch.setattr(
        c.app.state.database, "sessions", lambda: pytest.fail("Demo must not access tenant storage")
    )
    monkeypatch.setattr(
        socket, "socket", lambda *a, **kw: pytest.fail("Demo must not probe network")
    )
    assert c.get("/api/v1/demo").json()["kind"] == "demo"
    assert c.get("/api/v1/demo?organization_id=forged").status_code == 422
    assert c.get("/api/v1/demo/report?locale=ru").content.startswith(b"%PDF-")
    assert c.post("/api/v1/demo").status_code == 405


def test_migration_preserves_reports_tasks_and_baseline(workspace):
    c, _, _ = workspace
    prepared(workspace)
    record = make(c).json()
    config = Config("alembic.ini")
    command.check(config)
    with c.app.state.database.sessions() as db:
        before = db.get(SecurityReport, record["id"]).sha256
    command.upgrade(config, "head")
    assert c.get("/api/v1/auth/me").status_code == 200
    assert c.get("/api/v1/reports/" + record["id"]).json()["sha256"] == before
    command.downgrade(config, "e53b215e4b66")
    command.upgrade(config, "head")
    command.check(config)
    assert c.get("/api/v1/findings").json()["total"] == 6
    assert c.get("/api/v1/reports").json()["total"] == 0


def test_pdf_bounds_fonts_and_controlled_russian_templates(monkeypatch):
    from reportlab.pdfbase import pdfmetrics

    from app.locales import RU, translate

    pdf.render(sample("ru"))
    font = pdfmetrics.getFont("ShieldSans")
    for character in set("".join(RU.values()) + "ӘҒҚҢӨҰҮҺІәғқңөұүһі"):
        if not character.isspace():
            assert ord(character) in font.face.charToGlyph, repr(character)
    reason = (
        "High severity; urgency 3/3; observed relevance 2/2; conclusive evidence. "
        "Ties use newest issue observation, then stable fingerprint. These"
        " are ordering labels, not a risk score."
    )
    assert "срочность 3/3" in translate(reason, "ru")
    monkeypatch.setattr(pdf, "MAX_PAGES", 1)
    with pytest.raises(ValueError, match="page limit"):
        pdf.render(sample())
    monkeypatch.setattr(pdf, "MAX_PAGES", 80)
    monkeypatch.setattr(pdf, "MAX_BYTES", 100)
    with pytest.raises(ValueError, match="byte limit"):
        pdf.render(sample())


def test_demo_fixture_matches_offline_policy_and_ordering():
    from app.findings.contracts import SEVERITY_RANK
    from app.findings.engine import evaluate
    from app.models import CheckObservation

    fixture = sample()
    asset = fixture.assets[0]
    run = ScanRun(
        id=asset.scan_id,
        hostname=asset.hostname,
        status=asset.scan_status,
        engine_version="starter-checks-1",
        created_at=asset.scan_finished_at - 2,
        finished_at=asset.scan_finished_at,
    )
    assessment = evaluate(
        run,
        [
            CheckObservation(
                id=o.id,
                scan_id=run.id,
                check_id=o.check_id,
                outcome=o.outcome,
                observed_at=o.observed_at,
                evidence=o.values,
            )
            for o in asset.observations
        ],
    )
    actual = {r.rule_id: r for r in assessment.rules if r.decision == "issue"}
    assert set(actual) == {f.rule_id for f in fixture.findings}
    for f in fixture.findings:
        r = actual[f.rule_id]
        assert (f.severity, f.urgency, f.relevance, f.confidence, f.evidence) == (
            r.severity,
            r.urgency,
            r.relevance,
            r.confidence,
            r.evidence,
        )
    ordered = sorted(
        fixture.findings,
        key=lambda f: (
            -SEVERITY_RANK[f.severity],
            -f.urgency,
            -f.relevance,
            -(f.confidence == "conclusive"),
            -f.last_seen_at,
            f.fingerprint,
        ),
    )
    assert [f.id for f in ordered] == [f.id for f in fixture.priorities]
    assert not fixture.can_generate and not asset.currently_authorized
    assert all(t.finding_status == "open" for t in fixture.tasks)


def test_expiry_and_recovery_are_persisted(workspace):
    from app.auth import COOKIE, digest
    from app.models import LoginSession

    c, _, _ = workspace
    prepared(workspace)
    record = make(c).json()
    old_cookie = c.cookies.get(COOKIE)
    with c.app.state.database.sessions() as db:
        row = db.get(SecurityReport, record["id"])
        row.status = "generating"
        row.created_at = int(time.time()) - 400
        key = row.request_key
        db.commit()
    assert make(c, key=key).json()["status"] == "failed"
    assert c.get("/api/v1/reports/" + record["id"]).json()["status"] == "failed"
    with c.app.state.database.sessions() as db:
        session = db.get(LoginSession, digest(old_cookie))
        session.expires_at = int(time.time()) - 1
        db.commit()
    assert c.get("/api/v1/reports/" + record["id"] + "/download").status_code == 401


def test_logout_during_render_does_not_grant_late_download(workspace, monkeypatch):
    from app.auth import COOKIE

    c, _, _ = workspace
    prepared(workspace)
    enter, release = threading.Event(), threading.Event()
    original = pdf.render

    def slow(snapshot):
        enter.set()
        assert release.wait(10)
        return original(snapshot)

    monkeypatch.setattr(pdf, "render", slow)
    key = str(uuid4())
    token = c.get("/api/v1/auth/csrf").json()["csrf_token"]
    old_cookie = c.cookies.get(COOKIE)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(
            c.post,
            "/api/v1/reports",
            json={"request_key": key},
            headers={"Origin": ORIGIN, "X-CSRF-Token": token},
        )
        assert enter.wait(5)
        assert mutate(c, "/auth/logout").status_code == 200
        release.set()
        record = pending.result().json()
    assert record["status"] == "ready"
    c.cookies.set(COOKIE, old_cookie)
    assert c.get("/api/v1/reports/" + record["id"] + "/download").status_code == 401


def test_report_controlled_error_messages_have_russian_entries():
    import ast
    from pathlib import Path

    from app.locales import RU

    for source in (Path(__file__).parents[1] / "app/reports").glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            argument = 1 if node.func.id == "PublicError" else 0
            if node.func.id not in {"PublicError", "tr", "h"} or len(node.args) <= argument:
                continue
            value = node.args[argument]
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                assert " ".join(value.value.split()) in RU, (source.name, value.value)


def test_kazakh_api_locale_and_template_metadata_preserve_download(workspace):
    c, _, _ = workspace
    prepared(workspace)
    assert make(c, "kz").status_code == 422
    record = make(c, "kk").json()
    assert record["status"] == "ready" and record["locale"] == "kk"
    with c.app.state.database.sessions() as db:
        saved_report = db.get(SecurityReport, record["id"])
        assert saved_report.snapshot["template_version"] == "assessment-2"
        assert saved_report.snapshot["schema_version"] == "security-snapshot-1"
    body = c.get(f"/api/v1/reports/{record['id']}/download").content
    text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(body)).pages)
    assert "қауіпсіздік" in text and "assessment-2" in text
    assert hashlib.sha256(body).hexdigest() == record["sha256"]
