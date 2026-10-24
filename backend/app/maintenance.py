"""Operator-only consistent SQLite snapshots. Never overwrites a database or backup."""

import argparse
import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import make_url

from app.config import BACKEND_ROOT, Settings


def verify(connection: sqlite3.Connection) -> dict[str, object]:
    if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("Database integrity check failed")
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("Database foreign-key check failed")
    revision = connection.execute("SELECT version_num FROM alembic_version").fetchall()
    head = ScriptDirectory.from_config(Config(str(BACKEND_ROOT / "alembic.ini"))).get_current_head()
    if revision != [(head,)]:
        raise ValueError("Backup must match this build migration head")
    if connection.execute(
        "SELECT count(*) FROM security_reports WHERE status='ready' "
        "AND (pdf IS NULL OR length(pdf)>2097152 OR byte_count!=length(pdf))"
    ).fetchone()[0]:
        raise ValueError("Stored report size mismatch")
    for data, checksum in connection.execute(
        "SELECT pdf, sha256 FROM security_reports WHERE status='ready'"
    ):
        if hashlib.sha256(data).hexdigest() != checksum:
            raise ValueError("Stored report checksum mismatch")
    # Table names come only from the local schema, never caller SQL.
    tables = [
        r[0]
        for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    counts = {
        name: connection.execute(
            'SELECT count(*) FROM "' + name.replace('"', '""') + '"'
        ).fetchone()[0]
        for name in tables
    }
    return {"revision": head, "rows": counts, "integrity": "ok", "report_hashes": "ok"}


def snapshot(source: Path, destination: Path, timeout: float = 120) -> dict[str, object]:
    """Online backup API includes committed WAL pages; publish exclusively after verification."""
    source = source.resolve(strict=True)
    if not source.is_file() or not 1 <= timeout <= 600:
        raise ValueError("Invalid source or timeout")
    parent = destination.parent.resolve(strict=True)
    destination = parent / destination.name
    if any(
        os.path.lexists(str(destination) + suffix) for suffix in ["", "-wal", "-shm", "-journal"]
    ):
        raise FileExistsError("Destination or SQLite sidecar already exists")
    temporary = parent / (".shieldmate-backup-" + secrets.token_hex(16))
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(descriptor)
    end = time.monotonic() + timeout

    def progress(*_: int) -> None:
        if time.monotonic() >= end:
            raise TimeoutError("Backup deadline exceeded")

    try:
        with closing(
            sqlite3.connect("file:" + quote(str(source)) + "?mode=ro", uri=True, timeout=5)
        ) as origin:
            with closing(sqlite3.connect(temporary, timeout=5)) as target:
                target.set_progress_handler(lambda: int(time.monotonic() >= end), 10000)
                origin.backup(target, pages=128, progress=progress, sleep=0.05)
                result = verify(target)
        with temporary.open("rb") as file:
            os.fsync(file.fileno())
        os.link(temporary, destination)  # Atomic no-clobber publication, same filesystem.
        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        with destination.open("rb") as file:
            checksum = hashlib.file_digest(file, "sha256").hexdigest()
        return {
            **result,
            "file": str(destination),
            "sha256": checksum,
        }
    finally:
        temporary.unlink(missing_ok=True)
        for suffix in ["-journal", "-wal", "-shm"]:
            Path(str(temporary) + suffix).unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("destination", type=Path)
    restore = commands.add_parser("restore")
    restore.add_argument("source", type=Path)
    restore.add_argument("destination", type=Path, help="New, unused database path only")
    args = parser.parse_args()
    try:
        source = (
            args.source
            if args.command == "restore"
            else Path(make_url(Settings().database_url).database or "")
        )
        print(json.dumps(snapshot(source, args.destination), indent=2))
    except (OSError, ValueError, sqlite3.Error, TimeoutError) as exc:
        parser.exit(
            1,
            f"Operation failed ({type(exc).__name__}); no existing destination was overwritten.\n",
        )


if __name__ == "__main__":
    main()
