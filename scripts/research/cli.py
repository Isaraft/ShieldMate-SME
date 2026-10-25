"""File-only entrypoint; no network, server, telemetry or automatic evidence deletion."""

import argparse
import json
import os
import sys
from pathlib import Path

from research.alpha import alpha
from research.analysis import REPO, beta, scenario_check
from research.validation import InvalidEvidence, file_hash, require

KIT = REPO / "docs/testing"


def write_new(path: Path, value: str) -> None:
    # Exclusive creation also refuses symlinks/existing inputs; never clobber research evidence.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
        stream.write(value)


def initialize(root: Path) -> None:
    target = root.resolve()
    require(
        not target.is_relative_to(REPO) or target.is_relative_to(REPO / "research-private"),
        "Inside the repository, initialize studies only under ignored research-private/",
    )
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    for name in ["notes", "raw", "redacted"]:
        (root / name).mkdir(mode=0o700)
    for name in [
        "alpha-results-template.csv",
        "beta-results-template.csv",
        "evidence-manifest-template.csv",
        "study-declaration-template.json",
    ]:
        write_new(root / name.replace("-template", ""), (KIT / name).read_text(encoding="utf-8"))
    print("Created private empty records. NO REAL BETA RESULTS YET. Human sessions NOT CONDUCTED.")


def markdown(summary: dict[str, object]) -> str:
    # Only aggregate, validated fields; no participant answers, paths, names, media or quotes.
    lines = ["# ShieldMate evidence summary", "", str(summary["status"]), ""]
    if "primary" in summary:
        primary = summary["primary"]
        assert isinstance(primary, dict)
        lines += [
            "| Metric | Value |",
            "|---|---|",
            f"| Primary successes / denominator | {primary['successes']} / "
            f"{primary['denominator']} |",
            "| Percentage | "
            + str(primary["percent"] if primary["percent"] is not None else "NOT AVAILABLE")
            + " |",
            f"| Proposed criterion | {summary['criterion']} |",
            "| Withdrawn primary starts (excluded; sensitivity retained) | "
            + str(summary["withdrawn_started"])
            + " |",
            "",
            str(summary["denominator_policy"]),
            "",
            str(summary["limitations"]),
        ]
    else:
        lines += [
            f"Human alpha sessions: {summary['human_sessions']}",
            f"Automated engineering records: {summary['automated_records']}",
        ]
    return "\n".join(lines) + "\n"


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser(
        "init", help="Create a new private folder with blank templates; never overwrite"
    )
    init.add_argument("directory", type=Path)
    checksum = commands.add_parser(
        "hash", help="Hash an existing consented/redacted file locally; does not create proof"
    )
    checksum.add_argument("file", type=Path)
    scenario = commands.add_parser(
        "scenario", help="Check frozen demo/rubric; moderator-only, do not display to testers"
    )
    scenario.add_argument("--scenario", type=Path, default=KIT / "scenario.json")
    for name in ["alpha", "beta"]:
        sub = commands.add_parser(
            name, help="Validate existing records; never create participants or answers"
        )
        sub.add_argument("--csv", type=Path, required=True)
        sub.add_argument("--manifest", type=Path, required=True)
        sub.add_argument("--evidence-root", type=Path, required=True)
        sub.add_argument("--output", type=Path)
        sub.add_argument("--format", choices=["json", "markdown"], default="json")
        sub.add_argument(
            "--internal-test-data",
            action="store_true",
            help="Accept ONLY INTERNAL_TEST_DATA; output never counts as human research",
        )
        if name == "beta":
            sub.add_argument("--study", type=Path, required=True)
            sub.add_argument("--scenario", type=Path, default=KIT / "scenario.json")
    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize(args.directory)
            return 0
        if args.command == "hash":
            print(file_hash(args.file))
            return 0
        if args.command == "scenario":
            checked = scenario_check(args.scenario)
            print(
                json.dumps(
                    {
                        "status": "FROZEN SYNTHETIC SCENARIO MATCHES",
                        "scenario_id": checked["scenario_id"],
                        "snapshot_sha256": checked["snapshot_sha256"],
                        "scenario_sha256": checked["definition_sha256"],
                    },
                    indent=2,
                )
            )
            return 0
        if args.command == "beta":
            summary = beta(
                args.csv,
                args.manifest,
                args.evidence_root,
                args.study,
                args.scenario,
                args.internal_test_data,
            )
        else:
            summary = alpha(args.csv, args.manifest, args.evidence_root, args.internal_test_data)
        rendered = (
            markdown(summary)
            if args.format == "markdown"
            else json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
        )
        if args.output:
            write_new(args.output, rendered)
        else:
            print(rendered, end="")
        return 0
    except (InvalidEvidence, OSError):
        # Validation messages are controlled; never print OS paths or evidence contents.
        error = sys.exception()
        print(
            str(error)
            if isinstance(error, InvalidEvidence)
            else (
                "File operation failed; existing files were not overwritten. "
                "Check local permissions/paths."
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
