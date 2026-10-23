"""Bounded UDP DNS; no recursive policy expansion, selector guesses or TCP fallback."""

import re
from dataclasses import dataclass

import dns.exception
import dns.message
import dns.query
import dns.rcode
import dns.rdatatype
import dns.resolver

from app.scanner.contracts import Observation, ScanFailure, observation
from app.scanner.policy import Budget, destinations


@dataclass
class Records:
    values: list[str]
    error: str | None = None


class DNS:
    def query(self, host: str, kind: str, budget: Budget) -> Records:
        try:
            resolver = dns.resolver.Resolver()
            if not resolver.nameservers:
                return Records([], "dns_unavailable")
            question = dns.message.make_query(host + ".", kind)
            response = dns.query.udp(
                question,
                str(resolver.nameservers[0]),
                timeout=budget.remaining(),
                raise_on_truncation=True,
            )
            if response.rcode() == dns.rcode.NXDOMAIN:
                return Records([])
            if response.rcode() != dns.rcode.NOERROR:
                return Records([], "dns_unavailable")
            if sum(len(rr) for rr in response.answer) > 32 or len(response.answer) > 32:
                return Records([], "dns_limit")
            values: list[str] = []
            total = 0
            expected = dns.rdatatype.from_text(kind)
            for rr in response.answer:
                # Resolver CNAME chains are deliberately inconclusive: never expand scope.
                if rr.rdtype == dns.rdatatype.CNAME:
                    return Records([], "dns_alias_unsupported")
                if rr.name != question.question[0].name or rr.rdtype != expected:
                    return Records([], "dns_ambiguous")
                for record in rr:
                    if kind == "TXT":
                        value = b"".join(record.strings).decode("ascii", errors="strict")
                    elif kind in {"A", "AAAA"}:
                        value = record.address
                    else:
                        value = record.to_text()
                    if any(ord(char) < 32 or ord(char) == 127 for char in value):
                        return Records([], "dns_malformed")
                    total += len(value)
                    if len(value) > 1024 or total > 4096:
                        return Records([], "dns_limit")
                    values.append(value)
            return Records(values)
        except (dns.exception.DNSException, OSError, ValueError, IndexError, UnicodeError):
            return Records([], "dns_unavailable")

    def resolve(self, host: str, budget: Budget) -> list[str]:
        a, aaaa = self.query(host, "A", budget), self.query(host, "AAAA", budget)
        if a.error or aaaa.error:
            raise ScanFailure(a.error or aaaa.error or "dns_unavailable")
        return destinations(a.values + aaaa.values)


def policy_observation(check: str, records: Records) -> Observation:
    explanation = "Record presence is a limited configuration observation, not proof of protection."
    if records.error:
        return observation(
            check,
            "inconclusive",
            "DNS retrieval was inconclusive",
            "DNS TXT",
            {"error_code": records.error},
            explanation,
        )
    if check == "DNS_SPF_PRESENT":
        matches = [v for v in records.values if re.match(r"^v=spf1(?:\s|$)", v)]
        count = len(matches)
        return observation(
            check,
            "informational" if count == 1 else "attention",
            "One SPF record observed"
            if count == 1
            else ("Multiple SPF records observed" if count else "No SPF record observed"),
            "DNS TXT",
            {"record_count": count},
            explanation + " SPF includes, mechanisms and authorization are not evaluated.",
        )
    matches = [v for v in records.values if v.lower().startswith("v=dmarc1")]
    policy = "missing"
    if len(matches) == 1:
        parts = [part.strip() for part in matches[0].split(";") if part.strip()]
        tags = [part.split("=", 1) for part in parts]
        if (
            all(len(tag) == 2 for tag in tags)
            and parts[0] == "v=DMARC1"
            and len({tag[0] for tag in tags}) == len(tags)
        ):
            policies = [tag[1] for tag in tags if tag[0] == "p"]
            if len(policies) == 1 and policies[0] in {"none", "quarantine", "reject"}:
                policy = policies[0]
            else:
                policy = "malformed"
        else:
            policy = "malformed"
    elif matches:
        policy = "ambiguous"
    return observation(
        check,
        "informational" if policy in {"none", "quarantine", "reject"} else "attention",
        "DMARC policy: " + policy,
        "DNS TXT _dmarc",
        {"policy": policy, "record_count": len(matches)},
        explanation
        + " Only version and p tags are checked; reporting and alignment are not assessed.",
    )
