"""All network responses are controlled fixtures; no external targets in this suite."""

import socket
import ssl
import time
from unittest.mock import Mock

import dns.exception
import dns.message
import dns.rcode
import dns.rrset
import pytest

from app.scanner.contracts import ScanFailure
from app.scanner.dns_checks import DNS, Records, policy_observation
from app.scanner.http_checks import (
    Headers,
    header_observations,
    redirect_scope,
    request_headers,
)
from app.scanner.policy import Budget, destinations, public_ip
from app.scanner.runner import Runner
from app.scanner.tls_checks import certificate_observation
from app.scanner.transport import Transport, network_error


def budget():
    return Budget.start(30, 1)


@pytest.mark.parametrize(
    "address",
    [
        "168.63.129.16",
        "192.0.0.9",
        "192.0.0.10",
        "192.88.99.1",
        "2001:1::1",
        "127.0.0.1",
        "10.0.0.1",
        "192.168.1.1",
        "172.16.0.1",
        "169.254.169.254",
        "0.0.0.0",
        "100.64.0.1",
        "192.0.0.1",
        "192.0.2.1",
        "198.51.100.1",
        "203.0.113.1",
        "224.0.0.1",
        "240.0.0.1",
        "255.255.255.255",
        "::1",
        "::",
        "fc00::1",
        "fdff::1",
        "fe80::1",
        "ff02::1",
        "2001:db8::1",
        "::ffff:10.0.0.1",
        "::ffff:8.8.8.8",
        "64:ff9b::a00:1",
        "64:ff9b:1::1",
        "2002:0808:0808::1",
        "2001::1",
        "8.8.8.8%eth0",
        "not an address",
    ],
)
def test_special_use_addresses_rejected(address):
    assert not public_ip(address)
    with pytest.raises(ScanFailure, match="unsafe_destination"):
        destinations(["8.8.8.8", address])


@pytest.mark.parametrize("addresses", [[], ["8.8.8.8", "::1"], ["8.8.8.8"] * 33])
def test_no_or_mixed_addresses_make_no_socket(monkeypatch, addresses):
    dns = Mock()
    dns.resolve.return_value = addresses
    constructor = Mock(side_effect=AssertionError("No socket allowed"))
    monkeypatch.setattr(socket, "socket", constructor)
    with pytest.raises(ScanFailure):
        Transport(dns).open("example.com", 443, budget(), lambda: None)
    constructor.assert_not_called()


def test_socket_pin_sni_host_and_no_second_name_resolution(monkeypatch):
    dns = Mock()
    dns.resolve.side_effect = [["8.8.8.8"], ["127.0.0.1"]]
    channel = Mock()
    channel.getpeername.return_value = ("8.8.8.8", 443)
    tls = Mock()
    context = Mock()
    context.wrap_socket.return_value = tls
    monkeypatch.setattr(socket, "socket", Mock(return_value=channel))
    monkeypatch.setattr(socket, "getaddrinfo", Mock(side_effect=AssertionError("Rebinding")))
    create = Mock(return_value=context)
    monkeypatch.setattr(ssl, "create_default_context", create)
    transport = Transport(dns)
    guard = Mock()
    assert transport.open("example.com", 443, budget(), guard) is tls
    channel.connect.assert_called_once_with(("8.8.8.8", 443))
    context.wrap_socket.assert_called_once_with(
        channel, server_hostname="example.com", do_handshake_on_connect=False
    )
    tls.do_handshake.assert_called_once()
    assert guard.call_count == 2
    with pytest.raises(ScanFailure, match="unsafe_destination"):
        transport.open("example.com", 443, budget(), guard)
    assert channel.connect.call_count == 1
    with pytest.raises(ScanFailure, match="unsupported_port"):
        transport.open("example.com", 8080, budget(), guard)


def test_real_default_tls_context_requires_trust_and_hostname():
    context = ssl.create_default_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname


@pytest.mark.parametrize(
    "failure,code",
    [
        (TimeoutError(), "network_timeout"),
        (ConnectionRefusedError(), "connection_refused"),
        (ssl.SSLError(), "tls_failure"),
        (OSError(), "network_failure"),
    ],
)
def test_network_failures_close_socket(monkeypatch, failure, code):
    channel = Mock()
    channel.connect.side_effect = failure
    monkeypatch.setattr(socket, "socket", Mock(return_value=channel))
    dns = Mock()
    dns.resolve.return_value = ["8.8.8.8"]
    with pytest.raises(ScanFailure, match=code):
        Transport(dns).open("example.com", 443, budget(), lambda: None)
    channel.close.assert_called_once()


@pytest.mark.parametrize(
    "code,expected", [(10, "tls_expired"), (62, "tls_hostname_mismatch"), (20, "tls_invalid_chain")]
)
def test_certificate_errors_never_become_trusted(code, expected):
    error = ssl.SSLCertVerificationError()
    error.verify_code = code
    assert network_error(error) == expected


def certificate_socket():
    channel = Mock()
    moment = int(time.time())
    channel.getpeercert.return_value = {
        "notBefore": time.strftime("%b %d %H:%M:%S %Y GMT", time.gmtime(moment - 100)),
        "notAfter": time.strftime("%b %d %H:%M:%S %Y GMT", time.gmtime(moment + 864000)),
        "subject": ((("commonName", "example.com\x00"),),),
        "issuer": ((("organizationName", "Test CA"),),),
    }
    channel.version.return_value = "TLSv1.3"
    return channel


def test_certificate_evidence_bounded_and_expiry_checked():
    channel = certificate_socket()
    row = certificate_observation(channel)
    assert row.outcome == "pass"
    assert row.evidence["subject"] == "example.com"
    assert row.evidence["remaining_days"] in {9, 10}
    channel.getpeercert.return_value["notAfter"] = "Jan 01 00:00:00 2000 GMT"
    with pytest.raises(ScanFailure, match="tls_validity_error"):
        certificate_observation(channel)


def wire(data):
    channel = Mock()
    iterator = iter(bytes([value]) for value in data)
    channel.recv.side_effect = lambda count: next(iterator, b"")
    return channel


def test_root_request_ignores_proxy_and_never_reads_body(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:8888")
    headers = (
        b"HTTP/1.1 200 OK\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: secret=hidden\r\n\r\n"
    )
    channel = wire(headers + b"SECRET BODY")
    response = request_headers(channel, "example.com", budget())
    assert channel.recv.call_count == len(headers)
    assert response.values == {"x-content-type-options": "nosniff"}
    request = channel.sendall.call_args.args[0]
    assert b"HEAD / HTTP/1.1\r\nHost: example.com\r\n" in request
    assert b"ShieldMate-SME-MVP/0.4" in request
    assert b"Cookie" not in request and b"Authorization" not in request
    assert request_headers(wire(headers), "example.com", budget(), "GET").method == "GET"


@pytest.mark.parametrize(
    "data,code",
    [
        (b"x" * 16385, "http_header_limit"),
        (b"HTTP/1.1 200 OK\r\nX:" + b"x" * 2100 + b"\r\n\r\n", "http_header_limit"),
        (b"HTTP/1.1 200 OK\r\nBad header\r\n\r\n", "http_invalid_headers"),
        (b"HTTP/1.1 200 OK\r\nLocation: /\r\nLocation: /x\r\n\r\n", "http_ambiguous_headers"),
        (b"HTTP/1.1 200 OK\r\n", "http_incomplete_headers"),
        (b"HTTP/1.1 100 Continue\r\n\r\n", "http_invalid_response"),
    ],
)
def test_header_limits_and_ambiguity(data, code):
    with pytest.raises(ScanFailure, match=code):
        request_headers(wire(data), "example.com", budget())


def test_read_timeout_and_overall_deadline():
    channel = Mock()
    channel.recv.side_effect = TimeoutError()
    with pytest.raises(ScanFailure, match="network_timeout"):
        request_headers(channel, "example.com", budget())
    with pytest.raises(ScanFailure, match="overall_timeout"):
        request_headers(wire(b""), "example.com", Budget(time.monotonic() - 1, 1))


@pytest.mark.parametrize(
    "location",
    [
        "http://127.0.0.1/",
        "http://169.254.169.254/",
        "https://other.com/",
        "file:///etc/passwd",
        "ftp://example.com/",
        "https://user:pass@example.com/",
        "https://example.com:8080/",
        "//other.com/",
        "https://example.com%2f.evil.com/",
        "https://example.com\\@evil.com/",
        "/",
        "https://example.com/",
    ],
)
def test_redirects_never_follow(location):
    scope = redirect_scope(location, "example.com")
    assert scope in {
        "outside_exact_host",
        "unsupported_destination",
        "unsupported_port",
        "same_host_not_followed",
        "same_host_https_not_followed",
    }
    transport = Mock()
    transport.open.return_value = wire(
        ("HTTP/1.1 302 Found\r\nLocation: " + location + "\r\n\r\n").encode()
    )
    dns = Mock()
    dns.resolve.return_value = ["8.8.8.8"]
    dns.query.return_value = Records([])
    # TLS diagnostic is mocked; destinations must remain the exact host and fixed ports.
    import app.scanner.runner as module

    original = module.certificate_observation
    module.certificate_observation = Mock(
        return_value=certificate_observation(certificate_socket())
    )
    try:
        rows = []
        Runner(dns, transport).run("example.com", budget(), lambda: None, rows.append)
        assert [call.args[:2] for call in transport.open.call_args_list] == [
            ("example.com", 443),
            ("example.com", 80),
        ]
        assert not any("pass@" in str(row.evidence) for row in rows)
    finally:
        module.certificate_observation = original


@pytest.mark.parametrize(
    "values,count",
    [
        ([], 0),
        (["v=spf1 -all"], 1),
        (["v=spf1 -all", "v=spf1 ~all"], 2),
        (["v=spf10", "unrelated=secret"], 0),
    ],
)
def test_spf(values, count):
    row = policy_observation("DNS_SPF_PRESENT", Records(values))
    assert row.evidence["record_count"] == count
    assert "secret" not in str(row.evidence)


@pytest.mark.parametrize(
    "values,policy",
    [
        ([], "missing"),
        (["v=DMARC1; p=none"], "none"),
        (["v=DMARC1;p=quarantine"], "quarantine"),
        (["v=DMARC1; p=reject; rua=secret"], "reject"),
        (["v=DMARC1"], "malformed"),
        (["v=DMARC1;p=invalid"], "malformed"),
        (["v=DMARC1;p=none;p=reject"], "malformed"),
        (["v=dmarc1;p=none"], "malformed"),
        (["v=DMARC1;p=none", "v=DMARC1;p=reject"], "ambiguous"),
    ],
)
def test_dmarc(values, policy):
    row = policy_observation("DNS_DMARC_PRESENT", Records(values))
    assert row.evidence["policy"] == policy
    assert "secret" not in str(row.evidence)
    assert (
        policy_observation("DNS_DMARC_PRESENT", Records([], "dns_unavailable")).outcome
        == "inconclusive"
    )


def test_headers_have_narrow_rules_and_no_raw_secret_policy():
    rows = header_observations(
        Headers(
            200,
            {
                "strict-transport-security": "max-age=100",
                "x-content-type-options": "nosniff",
                "content-security-policy": "frame-ancestors 'none'; nonce-secret",
                "referrer-policy": "same-origin",
                "permissions-policy": "camera=()",
            },
            "HEAD",
        )
    )
    assert {row.check_id: row.outcome for row in rows} == {
        "HTTPS_HSTS": "pass",
        "HTTPS_CSP": "informational",
        "HTTPS_NOSNIFF": "pass",
        "HTTPS_REFERRER": "informational",
        "HTTPS_PERMISSIONS": "informational",
        "HTTPS_FRAME": "informational",
    }
    assert "nonce-secret" not in str(rows)
    rows = header_observations(Headers(200, {"x-content-type-options": "wrong"}, "HEAD"))
    assert all(row.outcome == "attention" for row in rows)


@pytest.mark.parametrize(
    "kind,value",
    [
        ("A", "8.8.8.8"),
        ("AAAA", "2606:4700:4700::1111"),
        ("TXT", '"v=spf1 " "-all"'),
        ("MX", "10 mail.example.com."),
    ],
)
def test_dns_wire_exact_bounded(monkeypatch, kind, value):
    def udp(query, nameserver, **kwargs):
        assert kwargs["raise_on_truncation"] and 0 < kwargs["timeout"] <= 1
        response = dns.message.make_response(query)
        response.answer.append(dns.rrset.from_text("example.com.", 60, "IN", kind, value))
        return response

    monkeypatch.setattr(dns.query, "udp", udp)
    monkeypatch.setattr(dns.query, "tcp", Mock(side_effect=AssertionError("No TCP")))
    assert DNS().query("example.com", kind, budget()).values


@pytest.mark.parametrize(
    "mode,error",
    [
        ("nxdomain", None),
        ("servfail", "dns_unavailable"),
        ("timeout", "dns_unavailable"),
        ("alias", "dns_alias_unsupported"),
        ("wrongname", "dns_ambiguous"),
        ("oversized", "dns_limit"),
    ],
)
def test_dns_failures(monkeypatch, mode, error):
    def udp(query, *args, **kwargs):
        if mode == "timeout":
            raise dns.exception.Timeout()
        response = dns.message.make_response(query)
        if mode in {"nxdomain", "servfail"}:
            response.set_rcode(dns.rcode.NXDOMAIN if mode == "nxdomain" else dns.rcode.SERVFAIL)
        else:
            name, kind, value = "example.com.", "TXT", '"v=spf1 -all"'
            if mode == "alias":
                kind, value = "CNAME", "other.com."
            elif mode == "wrongname":
                name = "other.com."
            else:
                value = '"' + "x" * 250 + '" '
                value *= 5
            response.answer.append(dns.rrset.from_text(name, 60, "IN", kind, value))
        return response

    monkeypatch.setattr(dns.query, "udp", udp)
    assert DNS().query("example.com", "TXT", budget()).error == error


def test_head_get_fallback_and_partial_preservation(monkeypatch):
    dns = Mock()
    dns.resolve.return_value = ["8.8.8.8"]
    dns.query.return_value = Records([], "dns_unavailable")
    transport = Mock()
    head = wire(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
    get = wire(b"HTTP/1.1 200 OK\r\nX-Content-Type-Options: nosniff\r\n\r\nSECRET BODY")
    transport.open.side_effect = [head, get, ScanFailure("network_timeout")]
    monkeypatch.setattr(
        "app.scanner.runner.certificate_observation",
        Mock(return_value=certificate_observation(certificate_socket())),
    )
    rows = []
    Runner(dns, transport).run("example.com", budget(), lambda: None, rows.append)
    assert len(rows) == 13
    assert next(row for row in rows if row.check_id == "TLS_CERTIFICATE").outcome == "pass"
    assert next(row for row in rows if row.check_id == "HTTP_REDIRECT").outcome == "inconclusive"
    assert get.sendall.call_args.args[0].startswith(b"GET / ")
    assert head.close.called and get.close.called


def test_redirect_headers_do_not_claim_destination_policy_success():
    rows = header_observations(Headers(302, {"strict-transport-security": "max-age=100"}, "HEAD"))
    assert len(rows) == 6
    assert all(row.outcome == "inconclusive" for row in rows)
    assert all(row.evidence["error_code"] == "redirect_not_followed" for row in rows)


def test_direct_transport_rejects_arbitrary_host_even_if_dns_mocked(monkeypatch):
    constructor = Mock(side_effect=AssertionError("No socket"))
    monkeypatch.setattr(socket, "socket", constructor)
    for host in ["https://example.com", "example.com\r\nX: injected", "127.0.0.1", "localhost"]:
        with pytest.raises(ScanFailure, match="invalid_target"):
            Transport(Mock()).open(host, 443, budget(), lambda: None)
    constructor.assert_not_called()


def test_tls_verification_failure_closes_wrapped_socket(monkeypatch):
    channel, tls = Mock(), Mock()
    channel.getpeername.return_value = ("8.8.8.8", 443)
    error = ssl.SSLCertVerificationError()
    error.verify_code = 62
    tls.do_handshake.side_effect = error
    context = Mock()
    context.wrap_socket.return_value = tls
    monkeypatch.setattr(socket, "socket", Mock(return_value=channel))
    monkeypatch.setattr(ssl, "create_default_context", Mock(return_value=context))
    dns = Mock()
    dns.resolve.return_value = ["8.8.8.8"]
    with pytest.raises(ScanFailure, match="tls_hostname_mismatch"):
        Transport(dns).open("example.com", 443, budget(), lambda: None)
    tls.close.assert_called_once()
    tls.sendall.assert_not_called()


def test_overall_runner_deadline_prevents_any_later_probe():
    dns, transport = Mock(), Mock()
    clock = budget()

    def expire_during_resolution(host, current_budget):
        current_budget.end = time.monotonic() - 1
        return ["8.8.8.8"]

    dns.resolve.side_effect = expire_during_resolution
    rows = []
    with pytest.raises(ScanFailure, match="overall_timeout"):
        Runner(dns, transport).run("example.com", clock, lambda: None, rows.append)
    transport.open.assert_not_called()
    dns.query.assert_not_called()
    assert len(rows) == 13 and all(row.outcome == "inconclusive" for row in rows)
