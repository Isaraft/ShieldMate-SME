from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import inspect, text

from app.config import BACKEND_ROOT, Settings
from app.db import Database


@pytest.mark.parametrize(
    "values",
    [
        {"allowed_hosts": ["*"]},
        {"cors_origins": ["*"]},
        {"cors_origins": ["https://user:password@example.com"]},
        {"cors_origins": ["https://example.com/path"]},
        {"database_url": "postgresql://localhost/example"},
    ],
)
def test_reject_unsafe_configuration(values) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


def test_migration_upgrade_downgrade_and_sqlite_constraints(tmp_path: Path, monkeypatch) -> None:
    url = f"sqlite:///{tmp_path / 'database.sqlite'}"
    monkeypatch.setenv("SHIELDMATE_DATABASE_URL", url)
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    command.upgrade(config, "head")  # Safe to run again at each local startup.
    database = Database(url)
    try:
        assert inspect(database.engine).get_table_names() == [
            "alembic_version",
            "domain_events",
            "domains",
            "organizations",
            "sessions",
            "users",
        ]
        with database.sessions() as session:
            assert session.scalar(text("SELECT version_num FROM alembic_version")) == (
                "90bff5eabc24"
            )
            assert session.scalar(text("PRAGMA foreign_keys")) == 1
        command.check(config)
        command.downgrade(config, "base")
        with database.sessions() as session:
            assert session.scalar(text("SELECT count(*) FROM alembic_version")) == 0
        command.upgrade(config, "head")
    finally:
        database.close()
