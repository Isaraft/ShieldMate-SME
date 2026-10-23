from typing import Literal

import dns.exception
import dns.flags
import dns.message
import dns.query
import dns.rcode
import dns.rdatatype
import dns.resolver

Outcome = Literal["match", "not_found", "temporarily_unavailable"]


def check_txt(hostname: str, expected: str, timeout: float) -> Outcome:
    """One UDP request to the configured recursive resolver; no TCP fallback or aliases."""
    try:
        resolver = dns.resolver.Resolver()
        server = str(resolver.nameservers[0])
        query = dns.message.make_query(hostname + ".", dns.rdatatype.TXT)
        reply = dns.query.udp(query, server, timeout=timeout, raise_on_truncation=True)
        if reply.rcode() == dns.rcode.NXDOMAIN:
            return "not_found"
        if reply.rcode() != dns.rcode.NOERROR or len(reply.answer) > 64:
            return "temporarily_unavailable"
        for records in reply.answer:
            if records.name != query.question[0].name or records.rdtype != dns.rdatatype.TXT:
                continue
            if len(records) > 64:
                return "temporarily_unavailable"
            for record in records:
                strings = getattr(record, "strings", ())
                if sum(map(len, strings)) > 4096:
                    return "temporarily_unavailable"
                if b"".join(strings) == expected.encode("ascii"):
                    return "match"
        return "not_found"
    except (dns.exception.DNSException, OSError, ValueError, IndexError):
        return "temporarily_unavailable"
