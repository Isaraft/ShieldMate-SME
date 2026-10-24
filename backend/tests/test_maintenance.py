"""Backups include committed WAL and preserve application records without overwrites."""

import os
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from app.maintenance import snapshot
from tests.test_auth import account, auth_client, mutate  # noqa: F401


def test_online_wal_restore_and_exclusive_publication(auth_client, tmp_path):  # noqa: F811
    c = auth_client
    account(c)
    mutate(c, "/organizations", {"name": "Backup company ӘҒҚҢӨҰҮҺІ"})
    source = Path(c.app.state.database.engine.url.database)
    with sqlite3.connect(source) as live:
        assert live.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        live.execute("UPDATE organizations SET name='WAL company ӘҒҚҢӨҰҮҺІ'")
        live.commit()
        backup = tmp_path / "consistent.sqlite"
        result = snapshot(source, backup)
        assert result["rows"]["users"] == 1 and result["rows"]["organizations"] == 1
        assert os.stat(backup).st_mode & 0o777 == 0o600
        restore = tmp_path / "restored.sqlite"
        assert snapshot(backup, restore)["rows"] == result["rows"]
        with sqlite3.connect(restore) as restored:
            assert (
                restored.execute("SELECT name FROM organizations").fetchone()[0]
                == "WAL company ӘҒҚҢӨҰҮҺІ"
            )
        with pytest.raises(FileExistsError):
            snapshot(source, backup)
        with pytest.raises(FileExistsError):
            snapshot(backup, source)
        sidecar = tmp_path / "refuse.sqlite-wal"
        sidecar.touch()
        with pytest.raises(FileExistsError):
            snapshot(backup, tmp_path / "refuse.sqlite")


def test_backup_failure_leaves_no_published_or_temporary_file(auth_client, tmp_path):  # noqa: F811
    source = Path(auth_client.app.state.database.engine.url.database)
    destination = tmp_path / "failed.sqlite"
    with patch("app.maintenance.verify", side_effect=sqlite3.OperationalError("disk full")):
        with pytest.raises(sqlite3.OperationalError):
            snapshot(source, destination)
    assert not destination.exists()
    assert list(tmp_path.glob(".shieldmate-backup-*")) == []
