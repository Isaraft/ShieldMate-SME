from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None,
        environment="test",
        database_url="sqlite:///:memory:",
        allowed_hosts=["testserver"],
        cors_origins=[],
    )
    with TestClient(create_app(settings), raise_server_exceptions=False) as test_client:
        yield test_client
