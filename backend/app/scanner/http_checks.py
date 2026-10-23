"""Bounded root headers only. No redirects, cookies, response bodies or raw policy storage."""

import re
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.scanner.contracts import Observation, Outcome, ScanFailure, observation
from app.scanner.policy import Budget
from app.scanner.transport import network_error

HEADER_CHECKS = {
    "HTTPS_HSTS": "strict-transport-security",
    "HTTPS_CSP": "content-security-policy",
    "HTTPS_NOSNIFF": "x-content-type-options",
    "HTTPS_REFERRER": "referrer-policy",
    "HTTPS_PERMISSIONS": "permissions-policy",
    "HTTPS_FRAME": "x-frame-options",
}
ALLOWED = set(HEADER_CHECKS.values()) | {"location"}


@dataclass
class Headers:
    status: int
    values: dict[str, str]
    method: str


def request_headers(
    channel: socket.socket, host: str, budget: Budget, method: str = "HEAD"
) -> Headers:
    if method not in {"HEAD", "GET"}:
        raise ScanFailure("unsupported_method")
    try:
        channel.settimeout(budget.remaining())
        channel.sendall(
            (
                f"{method} / HTTP/1.1\r\nHost: {host}\r\n"
                "User-Agent: ShieldMate-SME-MVP/0.4\r\nAccept: */*\r\n"
                "Connection: close\r\n\r\n"
            ).encode("ascii")
        )
        raw = bytearray()
        # Read exactly headers: zero application body bytes, even for GET fallback.
        while not raw.endswith(b"\r\n\r\n"):
            if len(raw) >= 16384:
                raise ScanFailure("http_header_limit")
            channel.settimeout(budget.remaining())
            byte = channel.recv(1)
            if not byte:
                raise ScanFailure("http_incomplete_headers")
            raw.extend(byte)
        lines = raw.decode("ascii", errors="strict").split("\r\n")
        if len(lines) > 104 or any(len(line) > 2048 for line in lines):
            raise ScanFailure("http_header_limit")
        match = re.fullmatch(r"HTTP/1\.[01] ([2-5][0-9]{2})(?: [\x20-\x7e]*)?", lines[0])
        if not match:
            raise ScanFailure("http_invalid_response")
        values: dict[str, str] = {}
        for line in lines[1:-2]:
            name, separator, value = line.partition(":")
            if (
                not separator
                or not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name)
                or any(ord(c) < 32 and c != "\t" for c in value)
            ):
                raise ScanFailure("http_invalid_headers")
            key = name.lower()
            if key in ALLOWED:
                if key in values:
                    raise ScanFailure("http_ambiguous_headers")
                values[key] = value.strip()
        return Headers(int(match[1]), values, method)
    except (OSError, UnicodeError) as exc:
        raise ScanFailure(network_error(exc)) from None


def redirect_scope(location: str, host: str) -> str:
    """Classify without storing URLs, credentials, paths or query parameters."""
    try:
        if (
            not location
            or any(ord(c) < 33 or ord(c) > 126 for c in location)
            or "\\" in location
            or "%" in location
        ):
            return "unsupported_destination"
        parsed = urlsplit(location)
        if parsed.username or parsed.password or parsed.scheme not in {"", "http", "https"}:
            return "unsupported_destination"
        if parsed.port and parsed.port not in {80, 443}:
            return "unsupported_port"
        if parsed.hostname and parsed.hostname.lower() != host:
            return "outside_exact_host"
        if parsed.scheme == "https" and parsed.hostname == host and parsed.port in {None, 443}:
            return "same_host_https_not_followed"
        return "same_host_not_followed"
    except ValueError:
        return "unsupported_destination"


def response_observation(check: str, response: Headers, host: str) -> Observation:
    evidence: dict[str, str | int | list[str]] = {
        "status": response.status,
        "method": response.method,
        "path": "/",
    }
    if 300 <= response.status < 400:
        evidence["redirect"] = redirect_scope(response.values.get("location", ""), host)
    return observation(
        check,
        "informational",
        "Root response recorded",
        "HTTPS /" if check == "HTTPS_RESPONSE" else "HTTP /",
        evidence,
        "No redirect was followed. A status code does not establish website security.",
    )


def header_observations(response: Headers) -> list[Observation]:
    results = []
    for check, header in HEADER_CHECKS.items():
        if 300 <= response.status < 400:
            results.append(
                observation(
                    check,
                    "inconclusive",
                    "Redirect destination was not checked",
                    "HTTPS headers",
                    {"error_code": "redirect_not_followed", "status": response.status},
                    "No redirect is followed. Header policy at a redirect destination "
                    "is outside this observation.",
                )
            )
            continue
        value = response.values.get(header, "")
        present = bool(value)
        outcome: Outcome = "attention"
        detail = "missing"
        if present:
            detail = "present; policy needs review"
            if check == "HTTPS_NOSNIFF":
                detail = "nosniff" if value.lower() == "nosniff" else "unexpected value"
                outcome = "pass" if detail == "nosniff" else "attention"
            elif check == "HTTPS_HSTS":
                match = re.search(r"(?:^|;)\s*max-age=([0-9]+)(?:;|$)", value, re.I)
                detail = "positive max-age" if match and int(match[1]) > 0 else "needs review"
                outcome = "pass" if detail == "positive max-age" else "attention"
            elif check == "HTTPS_FRAME":
                frame = bool(
                    re.search(
                        r"(?:^|;)\s*frame-ancestors\s+[^;]+",
                        response.values.get("content-security-policy", ""),
                        re.I,
                    )
                )
                if value.upper() in {"DENY", "SAMEORIGIN"}:
                    outcome, detail = "pass", value.upper()
                elif frame:
                    outcome, detail = "informational", "CSP frame-ancestors present; review policy"
            else:
                outcome = "informational"
        elif check == "HTTPS_FRAME" and re.search(
            r"(?:^|;)\s*frame-ancestors\s+[^;]+",
            response.values.get("content-security-policy", ""),
            re.I,
        ):
            outcome, detail = "informational", "CSP frame-ancestors present; review policy"
        results.append(
            observation(
                check,
                outcome,
                header + ": " + detail,
                "HTTPS headers",
                {"header": header, "observation": detail},
                "Only the root response is observed. Presence is not proof of a safe "
                "policy; missing headers are not confirmed vulnerabilities. "
                "Raw policy values are omitted to avoid retaining embedded secrets.",
            )
        )
    return results
