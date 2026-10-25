"""Read-only reachable-history audit. Output locations/categories, never matched values.

This targeted detector is not a substitute for an independent secret scanner or
human review. Binary documents/images require separate provenance/content review.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "cloud_access_key": rb"\bAKIA[A-Z0-9]{16}\b",
    "github_token": rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b",
    "slack_token": rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b",
    "openai_key": rb"\bsk-proj-[A-Za-z0-9_-]{40,}\b",
    "credential_url": rb"https?://[^\s/:@]+:[^\s/@]+@",
    "credential_literal": (
        rb"(?i)(?:password|secret|api[_-]?key|csrf[_-]?token|session[_-]?token)"
        rb"[\"']?\s*[:=]\s*[\"'][^\r\n\"']{8,}[\"']"
    ),
    "argon2_hash": rb"\$argon2(?:id|i|d)\$v=\d+\$[^\s\"']{20,}",
    "jwt": rb"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}",
    "cookie_or_auth_header": (
        rb"(?i)(?:set-cookie|authorization|cookie)[\"']?\s*[:=]\s*[\"']?"
        rb"(?:bearer\s+\S{20,}|shieldmate(?:_rc)?_session=[A-Za-z0-9_-]{20,})"
    ),
    "home_or_temp_path": rb"/(?:home|Users)/[A-Za-z0-9_.-]+/|/tmp/[A-Za-z0-9_.-]+",
    "email_candidate": rb"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "dns_challenge_candidate": rb"shieldmate-verification=[A-Za-z0-9_-]{16,}",
}
COMPILED = {key: re.compile(value) for key, value in PATTERNS.items()}
RISK_PATH = re.compile(
    r"(?:^|/)(?:\.env(?:\..*)?|research-private|storage|backups?|auth-state|storage-state)"
    r"(?:/|$)|\.(?:db|sqlite\d*|pem|key)(?:[-.]|$)"
)


def detect(data: bytes) -> list[dict[str, object]]:
    """Return no input fragments; locations only, including SQLite magic."""
    found: list[dict[str, object]] = []
    if data.startswith(b"SQLite format 3\0"):
        found.append({"category": "sqlite_database", "line": None})
    if b"\0" in data[:8192]:
        return found
    for category, pattern in COMPILED.items():
        lines = sorted(
            {data.count(b"\n", 0, match.start()) + 1 for match in pattern.finditer(data)}
        )
        if lines:
            found.append({"category": category, "lines": lines})
    return found


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args])


def audit() -> dict[str, object]:
    commits = git("rev-list", "--all").decode().splitlines()
    objects = git("rev-list", "--objects", "--all").decode().splitlines()
    ids = [line.split(" ", 1)[0] for line in objects]
    metadata = subprocess.check_output(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        input=("\n".join(ids) + "\n").encode(),
    )
    blobs = {
        line.split()[0]: int(line.split()[2])
        for line in metadata.decode().splitlines()
        if line.split()[1] == "blob"
    }
    # Every alias in every commit, not only rev-list's first path for an object.
    aliases: dict[str, set[str]] = collections.defaultdict(set)
    first: dict[str, str] = {}
    path_candidates: set[str] = set()
    modes: set[str] = set()
    for commit in reversed(commits):
        for record in git("ls-tree", "-rz", commit).split(b"\0"):
            if not record:
                continue
            header, name = record.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            path = name.decode("utf-8", "replace")
            modes.add(mode)
            if kind == "blob":
                aliases[oid].add(path)
                first.setdefault(oid, commit)
            if RISK_PATH.search(path):
                path_candidates.add(path)
    results = []
    binaries: collections.Counter[str] = collections.Counter()
    total = 0
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    assert proc.stdin and proc.stdout
    for oid, size in sorted(blobs.items()):
        proc.stdin.write((oid + "\n").encode())
        proc.stdin.flush()
        blob_header = proc.stdout.readline().split()
        if len(blob_header) != 3 or blob_header[1] != b"blob" or int(blob_header[2]) != size:
            raise RuntimeError("Unexpected Git object response")
        data = proc.stdout.read(size)
        if len(data) != size or proc.stdout.read(1) != b"\n":
            raise RuntimeError("Incomplete Git object")
        total += size
        found = detect(data)
        if found:
            results.append(
                {
                    "object": oid,
                    "first_commit": first.get(oid),
                    "paths": sorted(aliases[oid]),
                    "findings": found,
                }
            )
        if data.startswith(b"%PDF"):
            binaries["pdf"] += 1
        elif data.startswith(b"\x89PNG"):
            binaries["png"] += 1
        elif data.startswith(b"\xff\xd8"):
            binaries["jpeg"] += 1
        elif b"\0" in data[:8192]:
            binaries["other_binary"] += 1
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("Git object reader failed")
    authors = set(git("log", "--all", "--format=%an|%ae|%cn|%ce").splitlines())
    # Tree files include uncommitted changes: scan bytes, never follow symlinks.
    current = []
    for record in git("ls-files", "-z").split(b"\0"):
        if not record:
            continue
        p = Path(record.decode())
        if p.is_symlink():
            current.append({"path": str(p), "findings": [{"category": "symlink_review"}]})
        elif p.is_file() and (found := detect(p.read_bytes())):
            current.append({"path": str(p), "findings": found})
    return {
        "scope": "all reachable refs/commits/unique blobs and current tracked bytes; read-only",
        "head": git("rev-parse", "HEAD").decode().strip(),
        "refs": git("for-each-ref", "--format=%(refname)").decode().splitlines(),
        "commits": len(commits),
        "objects": len(ids),
        "unique_blobs": len(blobs),
        "blob_bytes": total,
        "binary_objects": dict(binaries),
        "file_modes": sorted(modes),
        "path_candidates": sorted(path_candidates),
        "author_identity_count": len(authors),
        "history_candidates": results,
        "current_candidates": current,
        "limitations": [
            "Not gitleaks; targeted patterns, no entropy/credential validity verification",
            "No unreachable/reflog-only objects or ignored local runtime data",
            "Binary image/PDF text needs separate content and provenance review",
            "Matches are candidates, not proof of a real credential",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("commits", "objects", "unique_blobs", "blob_bytes", "binary_objects")
            }
        )
    )


if __name__ == "__main__":
    main()
