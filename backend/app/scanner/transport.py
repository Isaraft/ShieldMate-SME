"""Exact-host transport. Numeric socket.connect only; no URL clients or proxy support."""

import ipaddress
import socket
import ssl
from collections.abc import Callable

from app.domain_validation import canonical_domain
from app.scanner.contracts import ScanFailure
from app.scanner.dns_checks import DNS
from app.scanner.policy import Budget, destinations


def network_error(exc: Exception) -> str:
    if isinstance(exc, ssl.SSLCertVerificationError):
        if exc.verify_code == 10:
            return "tls_expired"
        if exc.verify_code == 62:
            return "tls_hostname_mismatch"
        return "tls_invalid_chain"
    if isinstance(exc, TimeoutError):
        return "network_timeout"
    if isinstance(exc, ConnectionRefusedError):
        return "connection_refused"
    if isinstance(exc, ssl.SSLError):
        return "tls_failure"
    return "network_failure"


class Transport:
    def __init__(self, dns: DNS):
        self.dns = dns

    def open(
        self, host: str, port: int, budget: Budget, guard: Callable[[], None]
    ) -> socket.socket:
        if port not in {80, 443}:
            raise ScanFailure("unsupported_port")
        try:
            if canonical_domain(host) != host:
                raise ValueError
        except ValueError:
            raise ScanFailure("invalid_target") from None
        guard()
        addresses = destinations(self.dns.resolve(host, budget))
        # Use one address only, with no fallback amplification. Never call getaddrinfo(host).
        pinned = addresses[0]
        guard()  # Recheck after DNS, immediately before opening the pinned connection.
        address = ipaddress.ip_address(pinned)
        channel = socket.socket(
            socket.AF_INET6 if address.version == 6 else socket.AF_INET, socket.SOCK_STREAM
        )
        try:
            channel.settimeout(budget.remaining())
            channel.connect((pinned, port))
            if ipaddress.ip_address(channel.getpeername()[0]) != address:
                raise ScanFailure("peer_mismatch")
            if port == 443:
                context = ssl.create_default_context()
                # Default trust store, CERT_REQUIRED and check_hostname remain enabled.
                channel = context.wrap_socket(
                    channel, server_hostname=host, do_handshake_on_connect=False
                )
                channel.settimeout(budget.remaining())
                channel.do_handshake()
            return channel
        except Exception as exc:
            channel.close()
            if isinstance(exc, ScanFailure):
                raise
            raise ScanFailure(network_error(exc)) from None
