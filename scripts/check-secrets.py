"""High-confidence working-tree signature scan; not a full history/entropy audit."""

import json
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "openai_project_key": re.compile(r"\bsk-proj-[A-Za-z0-9_-]{40,}\b"),
}


def scan(text: str) -> list[dict[str, object]]:
    return [
        {"kind": name, "line": text.count("\n", 0, match.start()) + 1}
        for name, pattern in PATTERNS.items()
        for match in pattern.finditer(text)
    ]


if __name__ == "__main__":
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
        )
        .decode()
        .split("\0")
    )
    findings = []
    checked = 0
    for name in sorted(set(paths)):
        path = Path(name)
        if not path.is_file() or path.suffix.lower() in {
            ".png",
            ".jpg",
            ".pdf",
            ".ttf",
            ".woff",
            ".woff2",
        }:
            continue
        try:
            value = path.read_text()
        except (UnicodeError, OSError):
            continue
        checked += 1
        findings.extend({"file": name, **entry} for entry in scan(value))
    print(
        json.dumps(
            {
                "files_checked": checked,
                "findings": findings,
                "scope": (
                    "Working tracked/untracked text only; binary artifacts and Git history "
                    "are not scanned. Values are never printed."
                ),
            },
            indent=2,
        )
    )
    raise SystemExit(bool(findings))
