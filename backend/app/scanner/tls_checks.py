import ssl
import time
from typing import Any

from app.scanner.contracts import Observation, ScanFailure, clean, observation


def certificate_observation(channel: ssl.SSLSocket) -> Observation:
    certificate: dict[str, Any] = channel.getpeercert() or {}
    try:
        start = int(ssl.cert_time_to_seconds(certificate["notBefore"]))
        end = int(ssl.cert_time_to_seconds(certificate["notAfter"]))
        moment = int(time.time())
        if not start <= moment < end:
            raise ScanFailure("tls_validity_error")

        def summary(key: str) -> str:
            # Restrict to organization/common name; no complete DN or email identity collection.
            return clean(
                ", ".join(
                    str(v)
                    for group in certificate.get(key, ())
                    for k, v in group
                    if k in {"organizationName", "commonName"}
                ),
                160,
            )

        return observation(
            "TLS_CERTIFICATE",
            "pass",
            "Trusted hostname handshake succeeded",
            "TLS 443",
            {
                "not_before": start,
                "not_after": end,
                "remaining_days": (end - moment) // 86400,
                "issuer": summary("issuer"),
                "subject": summary("subject"),
                "protocol": clean(channel.version() or "unknown", 24),
            },
            "Default trust-chain and hostname verification succeeded for one pinned "
            "address. Other addresses, supported ciphers and protocols are not assessed.",
        )
    except (KeyError, ValueError, TypeError):
        raise ScanFailure("tls_certificate_unavailable") from None
