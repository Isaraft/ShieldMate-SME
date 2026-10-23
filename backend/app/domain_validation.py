import ipaddress
import re

import idna
import tldextract

# Packaged PSL snapshot only: never fetch lists or write a runtime cache.
_suffixes = tldextract.TLDExtract(
    suffix_list_urls=(), cache_dir=None, include_psl_private_domains=True
)
RESERVED = {
    "localhost",
    "local",
    "internal",
    "test",
    "invalid",
    "example",
    "onion",
    "arpa",
    "home",
    "lan",
}


def canonical_domain(value: str) -> str:
    if (
        not value
        or len(value) > 254
        or any(ord(c) > 127 or c.isspace() or ord(c) < 33 for c in value)
    ):
        raise ValueError("Use an ASCII domain or valid Punycode, without whitespace")
    domain = value.lower().removesuffix(".")
    if len(domain) > 253 or not re.fullmatch(r"[a-z0-9.-]+", domain):
        raise ValueError("Enter a domain only, without a URL, path, wildcard or port")
    if len("_shieldmate-challenge." + domain) > 253:
        raise ValueError("Domain is too long for the ownership TXT hostname")
    labels = domain.split(".")
    if any(not label for label in labels):
        raise ValueError("Empty DNS labels are not allowed")
    if len(labels) < 2 or labels[-1] in RESERVED or labels[-1].isdigit():
        raise ValueError("Use a public registrable domain or its subdomain")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise ValueError("IP addresses are not domains")
    try:
        ascii_domain = idna.encode(domain, strict=True, std3_rules=True).decode("ascii")
        idna.decode(ascii_domain, strict=True, std3_rules=True)
    except idna.IDNAError:
        raise ValueError("Malformed DNS name or Punycode") from None
    suffix = _suffixes(ascii_domain)
    if not suffix.domain or not suffix.suffix:
        raise ValueError("A registrable public domain is required")
    return ascii_domain
