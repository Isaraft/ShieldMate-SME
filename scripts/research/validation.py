"""Strict, bounded local readers. Errors identify fields, never participant answers."""

import csv
import hashlib
import io
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

from research.schema import MANIFEST_COLUMNS


class InvalidEvidence(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidEvidence(message)


def rows(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        require(path.stat().st_size <= 2_000_000, "CSV exceeds 2 MB")
        text = path.read_text(encoding="utf-8-sig")
        require("\x00" not in text, "CSV contains a null character")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        require(
            reader.fieldnames == list(columns), "CSV header mismatch; use the original template"
        )
        result = []
        for number, raw in enumerate(reader, 2):
            require(
                None not in raw and None not in raw.values(), f"Row {number}: column count mismatch"
            )
            row = cast(dict[str, str], raw)
            require(number <= 5001, "CSV exceeds 5000 records")
            require(
                None not in row and None not in row.values(), f"Row {number}: column count mismatch"
            )
            require(
                all(len(v) <= 500 for v in row.values()),
                f"Row {number}: field exceeds 500 characters",
            )
            require(
                all(v == v.strip() for v in row.values()), f"Row {number}: surrounding whitespace"
            )
            result.append(row)
        return result
    except (OSError, UnicodeError, csv.Error):
        raise InvalidEvidence("CSV unreadable or malformed; no values were printed") from None


def enum(row: dict[str, str], field: str, allowed: set[str], number: int) -> str:
    value = row[field]
    require(value in allowed, f"Row {number}: invalid {field}")
    return value


def pattern(value: str, expression: str, field: str, number: int) -> None:
    require(re.fullmatch(expression, value) is not None, f"Row {number}: invalid {field}")


def moment(value: str, field: str = "local_datetime", number: int = 0) -> datetime:
    try:
        require("T" in value, f"Row {number}: {field} requires ISO date/time and UTC offset")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None, f"Row {number}: {field} requires UTC offset")
        return parsed
    except ValueError:
        raise InvalidEvidence(
            f"Row {number}: invalid {field}; use ISO date/time with offset"
        ) from None


def seconds(value: str, number: int) -> Decimal:
    try:
        result = Decimal(value)
        require(
            result.is_finite() and 0 <= result <= 86400, f"Row {number}: invalid elapsed_seconds"
        )
        return result
    except InvalidOperation:
        raise InvalidEvidence(f"Row {number}: invalid elapsed_seconds") from None


def rating(value: str, field: str, number: int) -> int | None:
    if value == "":
        return None
    pattern(value, r"[1-5]", field, number)
    return int(value)


def json_object(path: Path) -> dict[str, Any]:
    try:
        require(path.stat().st_size <= 100_000, "Configuration exceeds 100 KB")
        value = json.loads(path.read_text(encoding="utf-8"))
        require(isinstance(value, dict), "Configuration must be a JSON object")
        return cast(dict[str, Any], value)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise InvalidEvidence("Configuration unreadable or malformed") from None


def file_hash(path: Path) -> str:
    require(
        path.is_file() and path.stat().st_size <= 128 * 1024 * 1024,
        "Evidence file missing or exceeds 128 MB",
    )
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def manifest(
    path: Path, root: Path, authorize: Callable[[dict[str, str]], None] | None = None
) -> dict[str, dict[str, str]]:
    records = rows(path, MANIFEST_COLUMNS)
    require(root.is_dir(), "Evidence root must be an existing private local directory")
    root = root.resolve()
    result: dict[str, dict[str, str]] = {}
    files: set[str] = set()
    for number, row in enumerate(records, 2):
        identifier = row["evidence_id"]
        pattern(identifier, r"E[0-9]{3,6}", "evidence_id", number)
        require(identifier not in result, f"Row {number}: duplicate evidence_id")
        enum(
            row,
            "evidence_class",
            {"HUMAN_BETA", "HUMAN_ALPHA", "AUTOMATED_ENGINEERING", "INTERNAL_TEST_DATA"},
            number,
        )
        enum(
            row,
            "kind",
            {"notes", "screenshot", "survey", "audio", "quote", "engineering_log"},
            number,
        )
        enum(row, "redaction_status", {"private_raw", "redacted"}, number)
        require(
            moment(row["captured_at"], "captured_at", number)
            <= datetime.now(UTC) + timedelta(minutes=5),
            f"Row {number}: future evidence capture time",
        )
        if row["evidence_class"].startswith("HUMAN_"):
            require(
                root.stat().st_mode & 0o077 == 0,
                "Human evidence root must have private 0700 permissions",
            )
        relative = Path(row["relative_path"])
        require(
            bool(row["relative_path"])
            and not relative.is_absolute()
            and ".." not in relative.parts,
            f"Row {number}: unsafe relative_path",
        )
        require(
            "\\" not in row["relative_path"] and ":" not in row["relative_path"],
            f"Row {number}: invalid relative_path",
        )
        if authorize is not None:
            authorize(row)
        target = root / relative
        require(
            target.resolve().is_relative_to(root), f"Row {number}: evidence escapes private root"
        )
        require(
            not any(
                p.is_symlink() for p in [target, *list(target.parents)[: len(relative.parts) - 1]]
            ),
            f"Row {number}: evidence symlink prohibited",
        )
        canonical = str(target.resolve())
        require(canonical not in files, f"Row {number}: duplicate evidence path")
        pattern(row["sha256"], r"[0-9a-f]{64}", "sha256", number)
        require(file_hash(target) == row["sha256"], f"Row {number}: evidence checksum mismatch")
        files.add(canonical)
        result[identifier] = row
    return result


def private_sources(paths: list[Path], repository: Path) -> None:
    """Human inputs inside this checkout belong only in the ignored evidence boundary."""
    repository = repository.resolve()
    for path in paths:
        target = path.resolve()
        require(
            not target.is_relative_to(repository)
            or target.is_relative_to(repository / "research-private"),
            "Human inputs inside the repository must use ignored research-private/",
        )
