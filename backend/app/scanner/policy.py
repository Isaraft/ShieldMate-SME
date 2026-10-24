"""Fail-closed authorization, IP classification and shared monotonic time budget."""

import ipaddress
import time
from dataclasses import dataclass

from app.domain_validation import canonical_domain
from app.models import DomainAsset, ScanRun
from app.scanner.contracts import ScanFailure

SPECIAL_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in (
        "168.63.129.16/32",  # Azure host/platform virtual endpoint, despite public classification.
        "192.0.0.0/24",  # Protocol assignments, including globally flagged anycast exceptions.
        "192.88.99.0/24",  # Deprecated 6to4 relay space.
        "100:0:0:1::/64",  # IANA dummy prefix (2025), independent of stdlib version.
        "3fff::/20",  # Documentation (2024).
        "5f00::/16",  # SRv6 SIDs, not globally reachable website destinations.
        "2001::/23",  # IETF protocol assignments, not ordinary website address space.
    )
)


def eligible(asset: DomainAsset | None, moment: int, run: ScanRun | None = None) -> bool:
    if asset is None or not (
        0 < asset.authorization_attested_at <= moment
        and asset.authorization_policy_version == "starter-authorization-v1"
        and asset.verified_at is not None
        and asset.verified_at <= moment
        and (asset.verification_valid_until or 0) > moment
    ):
        return False
    try:
        if canonical_domain(asset.canonical_fqdn) != asset.canonical_fqdn:
            return False
    except ValueError:
        return False
    return run is None or (
        asset.organization_id == run.organization_id
        and asset.canonical_fqdn == run.hostname
        and asset.challenge_generation == run.proof_generation
        and asset.verified_at == run.proof_verified_at
    )


def public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if any(address in network for network in SPECIAL_NETWORKS):
        return False
    # Reject transition mechanisms/mapped addresses entirely; no alternate routing interpretation.
    if isinstance(address, ipaddress.IPv6Address) and (
        address.ipv4_mapped
        or address.sixtofour
        or address.teredo
        or address in ipaddress.ip_network("64:ff9b::/96")
        or address in ipaddress.ip_network("64:ff9b:1::/48")
    ):
        return False
    return (
        address.is_global
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
        and not address.is_loopback
        and not address.is_link_local
        and "%" not in value
    )


def destinations(values: list[str]) -> list[str]:
    if not values:
        raise ScanFailure("no_public_addresses")
    if len(values) > 32:
        raise ScanFailure("dns_limit")
    if any(not public_ip(value) for value in values):
        raise ScanFailure("unsafe_destination")
    return sorted(set(values))


@dataclass
class Budget:
    end: float
    io_timeout: float

    @classmethod
    def start(cls, seconds: float, io_timeout: float) -> "Budget":
        return cls(time.monotonic() + seconds, io_timeout)

    def remaining(self) -> float:
        left = self.end - time.monotonic()
        if left <= 0:
            raise ScanFailure("overall_timeout")
        return min(left, self.io_timeout)
