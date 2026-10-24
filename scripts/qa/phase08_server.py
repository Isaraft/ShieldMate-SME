"""LOCAL QA only: explicit synthetic TXT provider; absent from application images."""

from app.config import Settings
from app.main import create_app

settings = Settings()
app = create_app(settings)


def fixture_txt(hostname: str, expected: str, timeout: float) -> str:
    if not hostname.startswith("_shieldmate-challenge.qa-") or not hostname.endswith(
        ".example.com"
    ):
        return "not_found"
    assert expected.startswith("shieldmate-verification=") and 0 < timeout <= 5
    return "match"


app.state.check_txt = fixture_txt
