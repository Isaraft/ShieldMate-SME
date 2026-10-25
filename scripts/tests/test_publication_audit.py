"""Internal marker tests: no genuine credential or participant data."""

import json
import subprocess
from pathlib import Path

import pytest
from publication.audit import audit, detect


@pytest.mark.parametrize(
    "data,category",
    [
        (b"SQLite format 3\0internal test only", "sqlite_database"),
        (b"-----BEGIN PRIVATE KEY-----", "private_key"),
        (b"https://fixture:fixture@example.invalid", "credential_url"),
        (b"/home/fixture/checkout", "home_or_temp_path"),
    ],
)
def test_detectors_return_locations_without_input(data: bytes, category: str) -> None:
    result = detect(data)
    assert any(item["category"] == category for item in result)
    assert data.decode(errors="replace") not in json.dumps(result)


def test_reachable_deleted_blob_and_aliases_are_scanned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    def git(*args: str) -> None:
        subprocess.run(["git", *args], check=True, capture_output=True)

    git("init", "--initial-branch=main")
    git("config", "user.name", "Internal Fixture")
    git("config", "user.email", "fixture@example.invalid")
    marker = b"-----BEGIN PRIVATE KEY-----\nINTERNAL MARKER ONLY\n"
    (tmp_path / "old.txt").write_bytes(marker)
    (tmp_path / "alias.txt").write_bytes(marker)
    git("add", ".")
    git("commit", "-m", "Internal marker")
    (tmp_path / "old.txt").unlink()
    (tmp_path / "alias.txt").unlink()
    (tmp_path / "safe.txt").write_text("Internal fixture\n")
    git("add", "-A")
    git("commit", "-m", "Remove internal marker")
    result = audit()
    assert result["commits"] == 2
    history = result["history_candidates"]
    assert isinstance(history, list)
    assert len(history) == 1
    assert history[0]["paths"] == ["alias.txt", "old.txt"]
    assert result["current_candidates"] == []
    assert marker.decode() not in json.dumps(result)
