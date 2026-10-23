from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_errors_do_not_echo_input_or_exception(caplog) -> None:
    app: FastAPI = create_app(
        Settings(_env_file=None, database_url="sqlite:///:memory:", allowed_hosts=["testserver"])
    )

    @app.get("/test-error")
    def broken() -> None:
        raise RuntimeError("private-value-must-not-leak")

    @app.get("/test-validation")
    def validated(count: int) -> dict[str, int]:
        return {"count": count}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-error")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "internal_error"
        assert "private-value" not in response.text + caplog.text
        assert response.headers["x-content-type-options"] == "nosniff"
        invalid = client.get("/test-validation?count=private-value-must-not-leak")
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "invalid_request"
        assert "private-value" not in invalid.text
