"""Sequential bounded catalog. Successful evidence is committed as it is collected."""

import socket
import ssl
from collections.abc import Callable

from app.scanner.contracts import CHECKS, Observation, ScanFailure, observation
from app.scanner.dns_checks import DNS, policy_observation
from app.scanner.http_checks import (
    HEADER_CHECKS,
    header_observations,
    request_headers,
    response_observation,
)
from app.scanner.policy import Budget
from app.scanner.tls_checks import certificate_observation
from app.scanner.transport import Transport


def error_observation(check: str, code: str) -> Observation:
    return observation(
        check,
        "inconclusive",
        "Check could not be completed",
        "check engine",
        {"error_code": code},
        "No security conclusion is available. Successful observations from other "
        "checks remain recorded. Recheck eligibility and retry when appropriate.",
    )


class Runner:
    def __init__(self, dns: DNS | None = None, transport: Transport | None = None):
        self.dns = dns or DNS()
        self.transport = transport or Transport(self.dns)

    def run(
        self,
        host: str,
        budget: Budget,
        guard: Callable[[], None],
        emit: Callable[[Observation], None],
    ) -> None:
        done: set[str] = set()

        def save(row: Observation) -> None:
            budget.remaining()
            emit(row)
            done.add(row.check_id)

        try:
            guard()
            try:
                addresses = self.dns.resolve(host, budget)
            except ScanFailure as exc:
                save(error_observation("DNS_ADDRESS", exc.code))
                # Unsafe/uncertain resolution prevents all active probes.
                raise
            save(
                observation(
                    "DNS_ADDRESS",
                    "informational",
                    "Public address records observed",
                    "DNS A/AAAA",
                    {"addresses": addresses},
                    "Every returned address passed the public-only policy. One address "
                    "per connection is probed; DNS may change after this observation.",
                )
            )
            for kind, label, check in (
                ("MX", host, "DNS_MX_PRESENT"),
                ("TXT", host, "DNS_SPF_PRESENT"),
                ("TXT", "_dmarc." + host, "DNS_DMARC_PRESENT"),
            ):
                guard()
                records = self.dns.query(label, kind, budget)
                if kind == "MX":
                    row = (
                        error_observation(check, records.error)
                        if records.error
                        else observation(
                            check,
                            "informational",
                            "MX records observed" if records.values else "No MX records observed",
                            "DNS MX",
                            {"record_count": len(records.values)},
                            "Mail exchange presence is context only. Absence can be normal; "
                            "mail hosts are never connected to.",
                        )
                    )
                else:
                    row = policy_observation(check, records)
                save(row)
            for port in (443, 80):
                channel: socket.socket | None = None
                try:
                    channel = self.transport.open(host, port, budget, guard)
                    if port == 443:
                        save(certificate_observation(channel))  # type: ignore[arg-type]
                    guard()
                    response = request_headers(channel, host, budget)
                    if response.status in {405, 501}:
                        channel.close()
                        channel = self.transport.open(host, port, budget, guard)
                        response = request_headers(channel, host, budget, "GET")
                    save(
                        response_observation(
                            "HTTPS_RESPONSE" if port == 443 else "HTTP_REDIRECT", response, host
                        )
                    )
                    if port == 443:
                        for row in header_observations(response):
                            save(row)
                except (ScanFailure, OSError, ssl.SSLError) as exc:
                    code = exc.code if isinstance(exc, ScanFailure) else "network_failure"
                    if code in {
                        "authorization_changed",
                        "unsafe_destination",
                        "no_public_addresses",
                        "dns_unavailable",
                        "dns_alias_unsupported",
                        "dns_ambiguous",
                        "dns_limit",
                        "dns_malformed",
                    }:
                        raise ScanFailure(code) from None
                    checks = (
                        ["TLS_CERTIFICATE", "HTTPS_RESPONSE", *HEADER_CHECKS]
                        if port == 443
                        else ["HTTP_REDIRECT"]
                    )
                    for check in checks:
                        if check not in done:
                            save(error_observation(check, code))
                finally:
                    if channel:
                        channel.close()
        except ScanFailure as exc:
            # Record explicit unobserved states for the remaining catalog.
            for check in CHECKS:
                if check not in done:
                    emit(error_observation(check, exc.code))
            raise
