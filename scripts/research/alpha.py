"""Internal human checks and automated engineering checks stay explicitly separate."""

from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from research.schema import ALPHA_COLUMNS, INTERNAL, LANGUAGES
from research.validation import enum, manifest, moment, pattern, private_sources, require, rows


def alpha(
    csv_path: Path, manifest_path: Path, root: Path, internal: bool = False
) -> dict[str, object]:
    records = rows(csv_path, ALPHA_COLUMNS)
    if any(r["evidence_class"] == "HUMAN_ALPHA" for r in records):
        private_sources([csv_path, manifest_path, root], Path(__file__).resolve().parents[2])
    keys: set[tuple[str, str]] = set()
    owners: dict[str, dict[str, str]] = {}
    for number, row in enumerate(records, 2):
        kind = enum(
            row,
            "evidence_class",
            {INTERNAL} if internal else {"HUMAN_ALPHA", "AUTOMATED_ENGINEERING"},
            number,
        )
        pattern(
            row["tester_code"],
            r"A[0-9]{2,4}" if kind == "HUMAN_ALPHA" else r"AUTOMATION",
            "tester_code",
            number,
        )
        pattern(row["session_id"], r"[A-Z0-9-]{3,30}", "session_id", number)
        require(
            moment(row["local_datetime"], number=number)
            <= datetime.now(UTC) + timedelta(minutes=5),
            f"Row {number}: future session time",
        )
        enum(row, "language", LANGUAGES, number)
        pattern(row["build_id"], r"[a-f0-9]{7,40}", "build_id", number)
        require(
            row["scenario_id"] == "shieldmate-alpha-1", f"Row {number}: alpha scenario mismatch"
        )
        enum(row, "environment", {"localhost_rc", "isolated_qa", "public_demo"}, number)
        enum(row, "data_context", {"real_authorized", "synthetic", "not_applicable"}, number)
        require(
            row["environment"] == "localhost_rc" or row["data_context"] == "synthetic",
            f"Row {number}: QA/demo must remain synthetic",
        )
        enum(row, "check_id", {f"AL{i:02d}" for i in range(1, 9)}, number)
        enum(row, "result", {"PASS", "FAIL", "NOT_TESTED"}, number)
        enum(row, "severity", {"", "low", "medium", "high", "critical"}, number)
        require(
            row["consent"] == ("yes" if kind == "HUMAN_ALPHA" else "not_applicable"),
            f"Row {number}: invalid consent",
        )
        for field in ["screenshot_consent", "audio_consent", "quote_consent"]:
            enum(row, field, {"yes", "no"} if kind == "HUMAN_ALPHA" else {"no"}, number)
        key = (row["session_id"], row["check_id"])
        require(key not in keys, f"Row {number}: duplicate alpha check")
        keys.add(key)
        require(
            row["result"] != "FAIL" or bool(row["severity"] and row["issue_ref"]),
            f"Row {number}: failure needs severity and issue reference",
        )
        if row["result"] != "NOT_TESTED":
            pattern(row["evidence_id"], r"E[0-9]{3,6}", "evidence_id", number)
        previous = owners.setdefault(row["session_id"], row)
        require(
            all(
                previous[f] == row[f]
                for f in [
                    "evidence_class",
                    "tester_code",
                    "build_id",
                    "consent",
                    "screenshot_consent",
                    "audio_consent",
                    "quote_consent",
                ]
            ),
            f"Row {number}: inconsistent alpha session identity/consent",
        )

    def authorize(item: dict[str, str]) -> None:
        owner = owners.get(item["session_id"])
        require(owner is not None, "Manifest links unknown alpha session")
        assert owner is not None
        require(
            item["participant_id"] == owner["tester_code"]
            and item["evidence_class"] == owner["evidence_class"],
            "Alpha evidence owner/provenance mismatch",
        )
        if owner["evidence_class"] == "HUMAN_ALPHA":
            mapping = {
                "screenshot": "screenshot_consent",
                "audio": "audio_consent",
                "quote": "quote_consent",
            }
            require(
                item["kind"] in {"notes", "survey", *mapping},
                "Human alpha cannot use engineering evidence",
            )
            if item["kind"] in mapping:
                require(
                    owner[mapping[item["kind"]]] == "yes",
                    "Alpha media/quote lacks separate consent",
                )
        else:
            require(
                item["kind"] == "engineering_log",
                "Engineering proof must remain labeled engineering",
            )

    evidence = manifest(manifest_path, root, authorize)
    for row in records:
        if row["evidence_id"]:
            require(
                row["evidence_id"] in evidence
                and evidence[row["evidence_id"]]["session_id"] == row["session_id"],
                "Alpha check lacks its session evidence",
            )
    human = {r["session_id"] for r in records if r["evidence_class"] == "HUMAN_ALPHA"}
    return {
        "status": "INTERNAL TEST DATA — NOT HUMAN RESEARCH"
        if internal
        else "HUMAN ALPHA RECORDS REQUIRE TEAM REVIEW"
        if human
        else "NO HUMAN ALPHA SESSIONS CONDUCTED",
        "human_sessions": len(human),
        "distinct_human_testers": len(
            {r["tester_code"] for r in records if r["evidence_class"] == "HUMAN_ALPHA"}
        ),
        "automated_records": sum(r["evidence_class"] == "AUTOMATED_ENGINEERING" for r in records),
        "check_counts": dict(Counter(r["result"] for r in records)),
        "verified_evidence_files": len(evidence),
    }
