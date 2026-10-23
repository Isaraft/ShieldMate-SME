"""Isolated browser harness ONLY. Not copied into application images."""
import os

from app.config import Settings
from app.main import create_app

settings = Settings(environment="test", database_url=os.environ.get("SHIELDMATE_DATABASE_URL", "sqlite:////tmp/shieldmate-phase04-browser.db"),
                    trusted_origins=[os.environ.get("SHIELDMATE_QA_ORIGIN", "http://127.0.0.1:15173")],
                    scan_domain_hourly=10, scan_org_hourly=30, scan_user_hourly=30,
                    domain_rate_limit=100)
app = create_app(settings)


def fixture(hostname, expected, timeout):
    assert hostname.startswith("_shieldmate-challenge.")
    assert expected.startswith("shieldmate-verification=")
    if hostname == "_shieldmate-challenge.qatemporary.example.com":
        return "temporarily_unavailable"
    return "not_found" if hostname == "_shieldmate-challenge.qapending.example.com" else "match"


app.state.check_txt = fixture
