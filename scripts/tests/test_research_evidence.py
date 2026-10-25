"""INTERNAL TEST DATA ONLY. Temporary test IDs/times are not people or study evidence."""

import csv
import hashlib
import json
import os
import subprocess
import sys

import pytest
from research.alpha import alpha
from research.analysis import MEASURES, REPO, beta, fraction, scenario_check
from research.schema import ALPHA_COLUMNS, BETA_COLUMNS, INTERNAL, MANIFEST_COLUMNS, SCENARIO
from research.validation import InvalidEvidence, manifest, rows

KIT = REPO / "docs/testing"
CLI = REPO / "scripts/research_evidence.py"


def write_csv(path, columns, records):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, columns)
        writer.writeheader()
        writer.writerows(records)


@pytest.fixture
def kit(tmp_path):
    config = json.loads((KIT / "study-declaration-template.json").read_text())
    config.update(
        hypothesis_state="ADOPTED",
        adopted_at="2026-10-23T09:00:00+05:00",
        retention_owner_code="M01",
        retention_until="2099-01-01",
        withdrawn_started_removed=0,
    )
    declaration = tmp_path / "study.json"
    declaration.write_text(json.dumps(config))
    records, evidence = [], []
    for index in range(1, 6):
        code, identifier = f"B{index:02d}", f"E{index:03d}"
        note = tmp_path / f"{code}.txt"
        note.write_text(
            "INTERNAL TEST DATA — no participant, no observed duration or human research"
        )
        records.append(dict(zip(BETA_COLUMNS, [""] * len(BETA_COLUMNS), strict=True)))
        records[-1].update(
            evidence_class=INTERNAL,
            participant_id=code,
            session_id=code + "-01",
            local_datetime="2026-10-24T09:00:00+05:00",
            language=["en", "ru", "kk", "ru", "kk"][index - 1],
            moderator_code="M01",
            role_segment="it_generalist",
            target_eligible="yes",
            relationship="other",
            eligibility_reason="sme_decision_responsibility",
            familiarity="some",
            consent="yes",
            screenshot_consent="no",
            audio_consent="no",
            quote_consent="no",
            scenario_id=SCENARIO,
            scenario_sha256=hashlib.sha256((KIT / "scenario.json").read_bytes()).hexdigest(),
            build_id="e9c7db4",
            session_status="completed",
            primary_started="yes",
            timing_method="manual_stopwatch",
            protocol_variant="standard",
            elapsed_seconds="90",
            paused="no",
            hint_given="no",
            top_issue_correct="yes",
            next_action_correct="yes",
            evidence_navigation_unaided="yes",
            done_vs_resolved_correct="yes",
            clarity_rating="4",
            usefulness_rating="5",
            error_count="0",
            notes_evidence_id=identifier,
        )
        evidence.append(
            dict(
                evidence_id=identifier,
                evidence_class=INTERNAL,
                participant_id=code,
                session_id=code + "-01",
                kind="notes",
                captured_at="2026-10-24T09:05:00+05:00",
                relative_path=note.name,
                sha256=hashlib.sha256(note.read_bytes()).hexdigest(),
                redaction_status="private_raw",
            )
        )
    csv_path, manifest_path = tmp_path / "beta.csv", tmp_path / "manifest.csv"

    def analyze():
        write_csv(csv_path, BETA_COLUMNS, records)
        write_csv(manifest_path, MANIFEST_COLUMNS, evidence)
        return beta(
            csv_path, manifest_path, tmp_path, declaration, KIT / "scenario.json", internal=True
        )

    return records, evidence, declaration, analyze, tmp_path


@pytest.mark.parametrize(("successes", "expected"), [(4, True), (3, False)])
def test_four_of_five_and_three_of_five_internal_only(kit, successes, expected):
    records, _, _, analyze, _ = kit
    for record in records[successes:]:
        record["next_action_correct"] = "no"
    result = analyze()
    assert result["primary"]["successes"] == successes
    assert result["primary"]["threshold_reached"] is expected
    assert result["criterion"] == "INTERNAL_TEST_ONLY"
    assert "NOT HUMAN RESEARCH" in result["status"]


def test_empty_templates_have_no_percentage_or_claim(tmp_path):
    result = beta(
        KIT / "beta-results-template.csv",
        KIT / "evidence-manifest-template.csv",
        tmp_path,
        KIT / "study-declaration-template.json",
        KIT / "scenario.json",
    )
    assert result["status"] == "NO REAL BETA RESULTS YET"
    assert result["primary"]["percent"] is None
    assert result["primary"]["threshold_reached"] is None
    assert result["criterion"] == "PENDING_MANUAL_EVIDENCE"


def test_frozen_scenario_matches_actual_deterministic_top_one():
    scenario = scenario_check(KIT / "scenario.json")
    assert scenario["top_rule_id"] == "TLS_CERTIFICATE_ACTION"


@pytest.mark.parametrize(
    "field,value",
    [
        ("participant_id", "PRIVATE-NAME"),
        ("language", "uk"),
        ("local_datetime", "2026-10-24"),
        ("local_datetime", "2099-01-01T12:00:00+05:00"),
        ("elapsed_seconds", "NaN"),
        ("elapsed_seconds", "-1"),
        ("elapsed_seconds", "Infinity"),
        ("clarity_rating", "6"),
        ("usefulness_rating", "0"),
        ("error_count", "-1"),
        ("scenario_sha256", "0" * 64),
        ("consent", "no"),
        ("relationship", "team"),
    ],
)
def test_malformed_and_contradictory_records_rejected(kit, field, value):
    records, _, _, analyze, _ = kit
    records[0][field] = value
    with pytest.raises(InvalidEvidence) as caught:
        analyze()
    assert "PRIVATE-NAME" not in str(caught.value)


def test_duplicate_participant_even_different_session_rejected(kit):
    records, _, _, analyze, _ = kit
    records[1]["participant_id"] = records[0]["participant_id"]
    records[1]["session_id"] = records[0]["participant_id"] + "-02"
    with pytest.raises(InvalidEvidence, match="duplicate"):
        analyze()


def test_hints_pause_and_late_answers_are_failures(kit):
    records, _, _, analyze, _ = kit
    records[0]["hint_given"] = "yes"
    records[1]["paused"] = "yes"
    records[2]["elapsed_seconds"] = "120.01"
    records[3]["elapsed_seconds"] = "120"
    result = analyze()
    assert result["primary"]["successes"] == 2
    assert result["hinted_primary_failures"] == 1
    assert result["paused_primary_failures"] == 1


def test_aborted_missing_time_stays_in_denominator(kit):
    records, _, _, analyze, _ = kit
    records[0].update(
        session_status="aborted",
        timing_method="not_recorded",
        elapsed_seconds="",
        top_issue_correct="",
        next_action_correct="",
    )
    result = analyze()
    assert result["primary"] == {
        "successes": 4,
        "denominator": 5,
        "percent": "80.00",
        "threshold_reached": True,
    }
    assert result["missing_time_primary_failures"] == 1


def test_withdrawal_explicit_and_conservative_denominator_retained(kit):
    records, evidence, declaration, analyze, _ = kit
    records[0].update(
        session_status="withdrawn",
        consent="withdrawn",
        timing_method="not_recorded",
        notes_evidence_id="",
    )
    for field in MEASURES:
        records[0][field] = ""
    evidence.pop(0)
    config = json.loads(declaration.read_text())
    config["withdrawn_started_removed"] = 1
    declaration.write_text(json.dumps(config))
    result = analyze()
    assert result["primary"]["denominator"] == 4
    assert result["conservative_with_withdrawn"]["denominator"] == 6
    assert result["withdrawn_started"] == 2


def test_withdrawal_cannot_keep_answers_or_media(kit):
    records, _, _, analyze, _ = kit
    records[0].update(session_status="withdrawn", consent="withdrawn")
    with pytest.raises(InvalidEvidence, match="responses"):
        analyze()


def test_mixed_languages_and_optional_ratings_not_imputed(kit):
    records, _, _, analyze, _ = kit
    records[0]["clarity_rating"] = ""
    records[0]["protocol_variant"] = "accessible"
    result = analyze()
    assert result["language_counts"] == {"en": 1, "ru": 2, "kk": 2}
    assert result["protocol_variant_counts"] == {"accessible": 1, "standard": 4}
    assert result["rating_distributions"]["clarity_rating"] == {"4": 4}


def test_posthoc_adoption_and_expired_retention_rejected(kit):
    _, _, declaration, analyze, _ = kit
    config = json.loads(declaration.read_text())
    config["adopted_at"] = "2026-10-24T10:00:00+05:00"
    declaration.write_text(json.dumps(config))
    with pytest.raises(InvalidEvidence, match="after trials"):
        analyze()
    config.update(adopted_at="2026-10-23T09:00:00+05:00", retention_until="2020-01-01")
    declaration.write_text(json.dumps(config))
    with pytest.raises(InvalidEvidence, match="Retention deadline"):
        analyze()


def test_missing_checksum_or_wrong_owner_evidence_rejected(kit):
    _, evidence, _, analyze, _ = kit
    evidence[0]["sha256"] = "0" * 64
    with pytest.raises(InvalidEvidence, match="checksum"):
        analyze()
    evidence[0]["participant_id"] = "B999"
    with pytest.raises(InvalidEvidence, match="unknown"):
        analyze()


@pytest.mark.parametrize("kind", ["screenshot", "audio", "quote"])
def test_separate_media_permissions_checked_before_file_read(kit, kind):
    _, evidence, _, analyze, _ = kit
    evidence[0].update(kind=kind, relative_path="nonexistent-private-file")
    with pytest.raises(InvalidEvidence, match="separate consent"):
        analyze()


@pytest.mark.parametrize(
    "relative", ["../outside", "/etc/passwd", "https://example.com/x", "..\\secret"]
)
def test_manifest_rejects_traversal_and_urls(kit, relative):
    _, evidence, _, analyze, _ = kit
    evidence[0]["relative_path"] = relative
    with pytest.raises(InvalidEvidence, match="relative_path"):
        analyze()


def test_manifest_rejects_symlinks(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("INTERNAL TEST DATA")
    root = tmp_path / "root"
    root.mkdir()
    (root / "link").symlink_to(outside)
    row = {key: "" for key in MANIFEST_COLUMNS}
    row.update(
        evidence_id="E001",
        evidence_class=INTERNAL,
        kind="notes",
        captured_at="2026-10-24T09:00:00+05:00",
        relative_path="link",
        sha256=hashlib.sha256(outside.read_bytes()).hexdigest(),
        redaction_status="private_raw",
    )
    path = tmp_path / "manifest.csv"
    write_csv(path, MANIFEST_COLUMNS, [row])
    with pytest.raises(InvalidEvidence):
        manifest(path, root)


def test_synthetic_records_rejected_by_real_mode(kit):
    _, _, declaration, analyze, root = kit
    analyze()
    with pytest.raises(InvalidEvidence, match="evidence_class"):
        beta(root / "beta.csv", root / "manifest.csv", root, declaration, KIT / "scenario.json")


def test_malformed_csv_and_unknown_sensitive_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("name,password\nPRIVATE,SECRET\n")
    with pytest.raises(InvalidEvidence) as caught:
        rows(path, BETA_COLUMNS)
    assert "SECRET" not in str(caught.value)
    write_csv(path, BETA_COLUMNS, [])
    with path.open("a") as f:
        f.write("bad,shape\n")
    with pytest.raises(InvalidEvidence, match="column count"):
        rows(path, BETA_COLUMNS)


def test_cli_private_init_empty_analysis_and_no_overwrite(tmp_path):
    private = tmp_path / "private"

    def run(args):
        return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True)

    assert run(["init", str(private)]).returncode == 0
    assert os.stat(private).st_mode & 0o777 == 0o700
    assert os.stat(private / "beta-results.csv").st_mode & 0o777 == 0o600
    arguments = [
        "beta",
        "--csv",
        str(private / "beta-results.csv"),
        "--manifest",
        str(private / "evidence-manifest.csv"),
        "--evidence-root",
        str(private),
        "--study",
        str(private / "study-declaration.json"),
    ]
    result = run(arguments)
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "NO REAL BETA RESULTS YET"
    output = private / "summary.md"
    assert run([*arguments, "--format", "markdown", "--output", str(output)]).returncode == 0
    before = output.read_bytes()
    assert run([*arguments, "--output", str(output)]).returncode == 2
    assert output.read_bytes() == before
    assert run(["init", str(private)]).returncode == 2


def test_alpha_automation_never_counts_as_human(tmp_path):
    note = tmp_path / "log.txt"
    note.write_text("INTERNAL TEST DATA — simulated engineering log")
    record = dict.fromkeys(ALPHA_COLUMNS, "")
    record.update(
        evidence_class="AUTOMATED_ENGINEERING",
        tester_code="AUTOMATION",
        session_id="AUTO-01",
        local_datetime="2026-10-24T09:00:00+05:00",
        language="en",
        build_id="e9c7db4",
        scenario_id="shieldmate-alpha-1",
        environment="isolated_qa",
        data_context="synthetic",
        check_id="AL01",
        consent="not_applicable",
        screenshot_consent="no",
        audio_consent="no",
        quote_consent="no",
        result="PASS",
        evidence_id="E001",
    )
    item = dict(
        evidence_id="E001",
        evidence_class="AUTOMATED_ENGINEERING",
        participant_id="AUTOMATION",
        session_id="AUTO-01",
        kind="engineering_log",
        captured_at=record["local_datetime"],
        relative_path=note.name,
        sha256=hashlib.sha256(note.read_bytes()).hexdigest(),
        redaction_status="private_raw",
    )
    csv_path, index = tmp_path / "alpha.csv", tmp_path / "manifest.csv"
    write_csv(csv_path, ALPHA_COLUMNS, [record])
    write_csv(index, MANIFEST_COLUMNS, [item])
    result = alpha(csv_path, index, tmp_path)
    assert result["human_sessions"] == 0 and result["automated_records"] == 1
    assert result["status"] == "NO HUMAN ALPHA SESSIONS CONDUCTED"
    write_csv(csv_path, ALPHA_COLUMNS, [record, record])
    with pytest.raises(InvalidEvidence, match="duplicate"):
        alpha(csv_path, index, tmp_path)


def test_zero_denominator_is_not_zero_percent():
    assert fraction(0, 0)["percent"] is None
    with pytest.raises(InvalidEvidence):
        fraction(2, 1)


def test_rubric_change_cannot_mix_with_existing_declaration(kit):
    _, _, declaration, analyze, root = kit
    analyze()
    definition = json.loads((KIT / "scenario.json").read_text())
    definition["grading"]["sensible_next_action"] += " INTERNAL TEST DATA altered rubric"
    other = root / "changed-scenario.json"
    other.write_text(json.dumps(definition))
    with pytest.raises(InvalidEvidence, match="Study/scenario mismatch"):
        beta(root / "beta.csv", root / "manifest.csv", root, declaration, other, True)


def test_translation_drift_detected_without_changing_repository(kit, monkeypatch):
    import shutil

    import research.analysis as policy

    _, _, _, _, root = kit
    fixture = root / "backend/app/reports"
    fixture.mkdir(parents=True)
    shutil.copy2(REPO / "backend/app/reports/demo_snapshot.json", fixture / "demo_snapshot.json")
    material = root / "docs/testing/materials"
    material.mkdir(parents=True)
    for lang in ["en", "ru", "kk"]:
        shutil.copy2(KIT / f"materials/participant-{lang}.md", material)
    with (material / "participant-kk.md").open("a") as stream:
        stream.write("INTERNAL TEST DATA — changed wording")
    monkeypatch.setattr(policy, "REPO", root)
    with pytest.raises(InvalidEvidence, match="wording changed"):
        policy.scenario_check(KIT / "scenario.json")


def test_default_cli_cannot_initialize_records_in_tracked_area(tmp_path, monkeypatch):
    import research.cli as cli

    monkeypatch.setattr(cli, "REPO", tmp_path)
    target = tmp_path / "docs" / "human-data"
    with pytest.raises(InvalidEvidence, match="research-private"):
        cli.initialize(target)
    assert not target.exists()


def test_no_network_needed_for_analysis(kit, monkeypatch):
    import socket

    def denied(*args, **kwargs):
        raise AssertionError("No network permitted for INTERNAL TEST DATA analysis")

    monkeypatch.setattr(socket, "socket", denied)
    assert kit[3]()["primary"]["denominator"] == 5


def test_completed_missing_time_and_missing_evidence_fail(kit):
    records, evidence, _, analyze, _ = kit
    records[0]["elapsed_seconds"] = ""
    with pytest.raises(InvalidEvidence, match="observed time"):
        analyze()
    records[0]["elapsed_seconds"] = "90"
    evidence.pop(0)
    with pytest.raises(InvalidEvidence, match="dated notes"):
        analyze()


def test_decline_is_explicitly_not_a_started_trial(kit):
    records, evidence, _, analyze, _ = kit
    records[0].update(
        consent="no",
        session_status="declined",
        primary_started="no",
        timing_method="not_recorded",
        notes_evidence_id="",
    )
    for field in MEASURES:
        records[0][field] = ""
    evidence.pop(0)
    result = analyze()
    assert result["primary"]["denominator"] == 4
    assert result["dispositions"]["declined"] == 1


def test_duplicate_manifest_and_future_capture_rejected(kit):
    _, evidence, _, analyze, _ = kit
    evidence.append(evidence[0].copy())
    with pytest.raises(InvalidEvidence, match="duplicate evidence_id"):
        analyze()
    evidence.pop()
    evidence[0]["captured_at"] = "2099-01-01T12:00:00+05:00"
    with pytest.raises(InvalidEvidence, match="future evidence"):
        analyze()


def test_mixed_application_builds_are_not_silently_pooled(kit):
    records, _, _, analyze, _ = kit
    records[0]["build_id"] = "deadbeef"
    with pytest.raises(InvalidEvidence, match="Mixed application builds"):
        analyze()


def test_human_source_paths_cannot_live_in_tracked_repository_area(tmp_path):
    from research.validation import private_sources

    repository = tmp_path / "repo"
    with pytest.raises(InvalidEvidence, match="research-private"):
        private_sources([repository / "docs" / "records.csv"], repository)
    private_sources([repository / "research-private" / "records.csv"], repository)
    private_sources([tmp_path / "outside-private" / "records.csv"], repository)


def test_future_adoption_not_a_recorded_decision(kit):
    _, _, declaration, analyze, _ = kit
    config = json.loads(declaration.read_text())
    config["adopted_at"] = "2099-01-01T10:00:00+05:00"
    declaration.write_text(json.dumps(config))
    with pytest.raises(InvalidEvidence, match="future"):
        analyze()


def test_completed_primary_can_skip_optional_secondary_without_imputation(kit):
    records, _, _, analyze, _ = kit
    records[0].update(
        evidence_navigation_unaided="",
        done_vs_resolved_correct="",
        clarity_rating="",
        usefulness_rating="",
    )
    result = analyze()
    assert result["primary"]["successes"] == 5
    assert result["secondary"]["evidence_navigation_unaided"] == {"recorded": 4, "yes": 4}
    assert result["rating_distributions"]["clarity_rating"] == {"4": 4}
