"""Predeclared usability calculations, never a claim of authenticated human participation."""

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any
from zoneinfo import ZoneInfo

from research.schema import (
    BETA_COLUMNS,
    INTERNAL,
    LANGUAGES,
    LIMIT,
    MIN_SAMPLE,
    ROLES,
    SCENARIO,
)
from research.validation import (
    enum,
    file_hash,
    json_object,
    manifest,
    moment,
    pattern,
    private_sources,
    rating,
    require,
    rows,
    seconds,
)

REPO = Path(__file__).resolve().parents[2]
MEASURES = (
    "elapsed_seconds",
    "hint_given",
    "top_issue_correct",
    "next_action_correct",
    "evidence_navigation_unaided",
    "done_vs_resolved_correct",
    "clarity_rating",
    "usefulness_rating",
    "error_count",
)


def scenario_check(path: Path) -> dict[str, Any]:
    scenario = json_object(path)
    source = REPO / "backend/app/reports/demo_snapshot.json"
    require(scenario.get("scenario_id") == SCENARIO, "Unsupported scenario version")
    require(
        scenario.get("snapshot_sha256") == file_hash(source),
        "Demo changed: freeze a new study version before collecting results",
    )
    snapshot = json_object(source)
    top = snapshot["priorities"][0]
    require(
        top["id"] == scenario.get("top_finding_id")
        and top["rule_id"] == scenario.get("top_rule_id"),
        "Scenario Top 1 mismatch",
    )
    require(
        top["recommendation"] == scenario.get("source_recommendation"), "Scenario action mismatch"
    )
    require(
        scenario.get("primary_time_limit_seconds") == LIMIT
        and scenario.get("threshold_percent") == 80
        and scenario.get("proposed_minimum_distinct_beta") == MIN_SAMPLE,
        "Unsupported study criterion; review a new protocol version",
    )
    for language in ["en", "ru", "kk"]:
        require(
            scenario.get("participant_materials_sha256", {}).get(language)
            == file_hash(REPO / "docs/testing/materials" / ("participant-" + language + ".md")),
            "Participant wording changed; freeze a new study version",
        )
    require(
        scenario.get("protocol_sha256") == file_hash(REPO / "docs/testing/beta-protocol.md"),
        "Beta protocol changed; freeze a new study version",
    )
    for relative in [
        "frontend/src/pages/Demo.tsx",
        *[f"backend/app/locales/{lang}.json" for lang in ["en", "ru", "kk"]],
    ]:
        require(
            scenario.get("application_files_sha256", {}).get(relative)
            == file_hash(REPO / relative),
            "Demo UI/catalog changed; freeze a new study version",
        )
    scenario["definition_sha256"] = file_hash(path)
    return scenario


def fraction(successes: int, denominator: int) -> dict[str, object]:
    require(0 <= successes <= denominator, "Invalid counts")
    return {
        "successes": successes,
        "denominator": denominator,
        "percent": str((Decimal(successes) * 100 / denominator).quantize(Decimal("0.01")))
        if denominator
        else None,
        "threshold_reached": successes * 5 >= denominator * 4 if denominator else None,
    }


def beta(
    csv_path: Path,
    manifest_path: Path,
    root: Path,
    study_path: Path,
    scenario_path: Path,
    internal: bool = False,
) -> dict[str, object]:
    scenario = scenario_check(scenario_path)
    study = json_object(study_path)
    require(study.get("schema_version") == "shieldmate-study-1", "Unsupported study declaration")
    require(
        study.get("scenario_id") == SCENARIO
        and study.get("scenario_sha256") == scenario["definition_sha256"],
        "Study/scenario mismatch",
    )
    require(study.get("hypothesis_state") in {"PROPOSED", "ADOPTED"}, "Invalid hypothesis state")
    records = rows(csv_path, BETA_COLUMNS)
    if not internal and any(r["evidence_class"] == "HUMAN_BETA" for r in records):
        private_sources([csv_path, manifest_path, root, study_path], REPO)
    participants: dict[str, dict[str, str]] = {}
    sessions: set[str] = set()
    starts: list[datetime] = []
    for number, row in enumerate(records, 2):
        enum(row, "evidence_class", {INTERNAL} if internal else {"HUMAN_BETA"}, number)
        pattern(row["participant_id"], r"B[0-9]{2,4}", "participant_id", number)
        pattern(row["session_id"], row["participant_id"] + r"-[0-9]{2}", "session_id", number)
        require(
            row["participant_id"] not in participants and row["session_id"] not in sessions,
            f"Row {number}: duplicate participant/session; follow-ups belong in a separate file",
        )
        participants[row["participant_id"]] = row
        sessions.add(row["session_id"])
        pattern(row["moderator_code"], r"M[0-9]{2,4}", "moderator_code", number)
        dt = moment(row["local_datetime"], number=number)
        require(
            dt <= datetime.now(UTC) + timedelta(minutes=5), f"Row {number}: future session time"
        )
        enum(row, "language", LANGUAGES, number)
        enum(row, "role_segment", ROLES, number)
        enum(row, "relationship", {"team", "close", "other"}, number)
        enum(row, "familiarity", {"none", "some", "regular"}, number)
        enum(row, "target_eligible", {"yes", "no"}, number)
        enum(
            row,
            "eligibility_reason",
            {"sme_decision_responsibility", "not_target", "team_member", "declined_screening"},
            number,
        )
        eligible = row["target_eligible"] == "yes"
        require(
            not eligible
            or (
                row["role_segment"] != "other"
                and row["relationship"] != "team"
                and row["eligibility_reason"] == "sme_decision_responsibility"
            ),
            f"Row {number}: eligibility contradicts target role/relationship",
        )
        require(
            eligible or row["eligibility_reason"] != "sme_decision_responsibility",
            f"Row {number}: eligibility reason mismatch",
        )
        for field in [
            "screenshot_consent",
            "audio_consent",
            "quote_consent",
            "primary_started",
            "paused",
        ]:
            enum(row, field, {"yes", "no"}, number)
        consent = enum(row, "consent", {"yes", "no", "withdrawn"}, number)
        status = enum(
            row,
            "session_status",
            {"completed", "incomplete", "aborted", "withdrawn", "declined", "not_started"},
            number,
        )
        require(
            (status == "withdrawn") == (consent == "withdrawn"),
            f"Row {number}: withdrawn consent/status mismatch",
        )
        require(
            (status == "declined") == (consent == "no"),
            f"Row {number}: declined consent/status mismatch",
        )
        enum(row, "timing_method", {"monotonic", "manual_stopwatch", "not_recorded"}, number)
        enum(row, "protocol_variant", {"standard", "accessible"}, number)
        require(
            row["scenario_id"] == SCENARIO
            and row["scenario_sha256"] == scenario["definition_sha256"],
            f"Row {number}: scenario version/hash mismatch",
        )
        pattern(row["build_id"], r"[a-f0-9]{7,40}", "build_id", number)
        if row["primary_started"] == "yes":
            require(
                status not in {"declined", "not_started"},
                f"Row {number}: primary start contradicts disposition",
            )
            if eligible:
                starts.append(dt)
        else:
            require(
                status in {"withdrawn", "declined", "not_started"},
                f"Row {number}: missing primary start",
            )
        if consent != "yes" or status == "not_started":
            require(
                all(row[f] == "" for f in MEASURES) and row["notes_evidence_id"] == "",
                f"Row {number}: no responses/media references may remain "
                "after decline/withdrawal or before starting",
            )
            require(
                all(
                    row[f] == "no" for f in ["screenshot_consent", "audio_consent", "quote_consent"]
                ),
                f"Row {number}: media consent must be no for unused/withdrawn records",
            )
            continue
        require(
            eligible,
            f"Row {number}: ineligible people must not begin the beta task; "
            "use alpha or screening records",
        )
        for field in ["hint_given", "top_issue_correct", "next_action_correct"]:
            enum(row, field, {"yes", "no", ""} if status != "completed" else {"yes", "no"}, number)
        for field in ["evidence_navigation_unaided", "done_vs_resolved_correct"]:
            enum(row, field, {"yes", "no", ""}, number)
        if row["elapsed_seconds"]:
            seconds(row["elapsed_seconds"], number)
            require(
                row["timing_method"] != "not_recorded", f"Row {number}: time has no timing method"
            )
        if status == "completed":
            require(
                bool(row["elapsed_seconds"]) and row["timing_method"] != "not_recorded",
                f"Row {number}: completed trial needs observed time",
            )
        rating(row["clarity_rating"], "clarity_rating", number)
        rating(row["usefulness_rating"], "usefulness_rating", number)
        if row["error_count"]:
            pattern(row["error_count"], r"0|[1-9][0-9]{0,3}", "error_count", number)
        pattern(row["notes_evidence_id"], r"E[0-9]{3,6}", "notes_evidence_id", number)
    require(
        len(
            {
                r["build_id"]
                for r in records
                if r["consent"] == "yes" and r["primary_started"] == "yes"
            }
        )
        <= 1,
        "Mixed application builds must be analyzed separately",
    )
    if records:
        pattern(
            str(study.get("retention_owner_code", "")), r"M[0-9]{2,4}", "retention_owner_code", 0
        )
        pattern(
            str(study.get("retention_until", "")),
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
            "retention_until",
            0,
        )
        try:
            retention = date.fromisoformat(str(study.get("retention_until", "")))
        except ValueError:
            require(False, "Set a consented retention date before processing records")
        require(
            retention >= datetime.now(ZoneInfo("Asia/Almaty")).date(),
            "Retention deadline passed; stop processing and follow withdrawal/deletion procedure",
        )
    removed = study.get("withdrawn_started_removed")
    require(
        not records
        or (isinstance(removed, int) and not isinstance(removed, bool) and 0 <= removed <= 5000),
        "Declare anonymized removed-withdrawal count before analysis",
    )
    adopted = None
    if study["hypothesis_state"] == "ADOPTED":
        adopted = moment(str(study.get("adopted_at", "")), "adopted_at")
        require(
            adopted <= datetime.now(UTC) + timedelta(minutes=5),
            "Adoption timestamp cannot be in the future",
        )
        require(
            not starts or adopted <= min(starts),
            "Hypothesis adopted after trials began; do not claim prospective confirmation",
        )
    else:
        require(
            not study.get("adopted_at"), "Proposed study must not contain an adoption timestamp"
        )

    def authorize(item: dict[str, str]) -> None:
        owner = participants.get(item["participant_id"])
        require(
            owner is not None and item["session_id"] == owner["session_id"],
            "Manifest links an unknown participant/session",
        )
        assert owner is not None
        require(item["evidence_class"] == owner["evidence_class"], "Manifest provenance mismatch")
        require(
            owner["consent"] == "yes" and owner["primary_started"] == "yes",
            "Evidence is not consented for processing",
        )
        mapping = {
            "screenshot": "screenshot_consent",
            "audio": "audio_consent",
            "quote": "quote_consent",
        }
        require(
            item["kind"] in {"notes", "survey", *mapping},
            "Beta manifest cannot contain engineering evidence",
        )
        if item["kind"] in mapping:
            require(owner[mapping[item["kind"]]] == "yes", "Media/quote lacks separate consent")

    evidence = manifest(manifest_path, root, authorize)
    for row in records:
        if row["notes_evidence_id"]:
            item = evidence.get(row["notes_evidence_id"])
            require(
                item is not None
                and item["kind"] == "notes"
                and item["participant_id"] == row["participant_id"],
                "Session requires its own dated notes evidence",
            )
    analyzed = [
        r
        for r in records
        if r["target_eligible"] == "yes" and r["consent"] == "yes" and r["primary_started"] == "yes"
    ]
    success = [
        r
        for r in analyzed
        if r["session_status"] == "completed"
        and r["paused"] == "no"
        and r["hint_given"] == "no"
        and r["top_issue_correct"] == r["next_action_correct"] == "yes"
        and seconds(r["elapsed_seconds"], 0) <= LIMIT
    ]
    withdrawn = sum(
        r["target_eligible"] == "yes"
        and r["primary_started"] == "yes"
        and r["consent"] == "withdrawn"
        for r in records
    )
    withdrawn += removed if isinstance(removed, int) else 0
    observed_times = [seconds(r["elapsed_seconds"], 0) for r in analyzed if r["elapsed_seconds"]]
    observed_errors = [int(r["error_count"]) for r in analyzed if r["error_count"]]
    n = len(analyzed)
    status = (
        "INTERNAL TEST DATA — NOT HUMAN RESEARCH"
        if internal
        else "NO REAL BETA RESULTS YET"
        if not n
        else "DECLARED HUMAN RECORDS — AUTHENTICITY/GRADING REQUIRE TEAM REVIEW"
    )
    criterion = "PENDING_MANUAL_EVIDENCE"
    if internal:
        criterion = "INTERNAL_TEST_ONLY"
    elif n and adopted:
        criterion = (
            "INSUFFICIENT_PLANNED_SAMPLE"
            if n < MIN_SAMPLE
            else "MET"
            if len(success) * 5 >= n * 4
            else "NOT_MET"
        )
    elif n:
        criterion = "EXPLORATORY_ONLY_HYPOTHESIS_NOT_ADOPTED"
    return {
        "status": status,
        "scenario_id": SCENARIO,
        "scenario_sha256": scenario["definition_sha256"],
        "hypothesis_state": study["hypothesis_state"],
        "criterion": criterion,
        "planned_sample_minimum": MIN_SAMPLE,
        "minimum_is_course_requirement": False,
        "primary": fraction(len(success), n),
        "denominator_policy": (
            "All eligible consented primary starts, including incomplete/aborted. "
            "Withdrawn excluded explicitly; sensitivity includes their counts only."
        ),
        "conservative_with_withdrawn": fraction(len(success), n + withdrawn),
        "dispositions": dict(Counter(r["session_status"] for r in records)),
        "withdrawn_started": withdrawn,
        "hinted_primary_failures": sum(r["hint_given"] == "yes" for r in analyzed),
        "paused_primary_failures": sum(r["paused"] == "yes" for r in analyzed),
        "protocol_variant_counts": dict(Counter(r["protocol_variant"] for r in analyzed)),
        "relationship_counts": dict(Counter(r["relationship"] for r in analyzed)),
        "missing_time_primary_failures": sum(not r["elapsed_seconds"] for r in analyzed),
        "language_counts": dict(Counter(r["language"] for r in analyzed)),
        "time_summary_seconds": {
            "observed_n": len(observed_times),
            "median": str(median(observed_times)) if observed_times else None,
            "min": str(min(observed_times)) if observed_times else None,
            "max": str(max(observed_times)) if observed_times else None,
        },
        "observed_error_counts": {
            "trials_with_recorded_count": len(observed_errors),
            "total": sum(observed_errors) if observed_errors else None,
        },
        "secondary": {
            field: {
                "recorded": sum(r[field] != "" for r in analyzed),
                "yes": sum(r[field] == "yes" for r in analyzed),
            }
            for field in ["evidence_navigation_unaided", "done_vs_resolved_correct"]
        },
        "rating_distributions": {
            field: dict(Counter(r[field] for r in analyzed if r[field]))
            for field in ["clarity_rating", "usefulness_rating"]
        },
        "verified_evidence_files": len(evidence),
        "limitations": (
            "Small nonrandom sample; declared records and checksums do not authenticate people "
            "or prove security, risk reduction, ROI, NPS, or willingness to pay. "
            "No qualitative responses exported."
        ),
    }
