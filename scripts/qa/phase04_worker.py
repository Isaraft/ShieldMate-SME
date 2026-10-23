"""Controlled DNS/socket fixtures around the actual durable worker and check catalog."""
import time

from app.db import Database
from app.scanner.contracts import ScanFailure
from app.scanner.dns_checks import DNS, Records
from app.scanner.runner import Runner
from app.scanner.worker import work_once
from scripts.qa.phase04_server import settings


class FixtureDNS(DNS):
    def resolve(self, host, budget):
        budget.remaining()
        if host == "qablocked.example.com":
            raise ScanFailure("unsafe_destination")
        return ["8.8.8.8"]  # Evidence fixture only; this IP is never connected to.

    def query(self, host, kind, budget):
        budget.remaining()
        if host.startswith("_dmarc."):
            return Records(["v=DMARC1; p=none"])
        return Records(["v=spf1 -all"] if kind == "TXT" else [])


class FixtureSocket:
    def __init__(self, host, port):
        self.port = port
        data = ("HTTP/1.1 200 OK\r\nStrict-Transport-Security: max-age=31536000\r\n"
                "Content-Security-Policy: default-src 'self'; frame-ancestors 'none'\r\n"
                "X-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\n"
                "Permissions-Policy: camera=()\r\n\r\n" if port == 443 else
                f"HTTP/1.1 301 Moved\r\nLocation: https://{host}/\r\n\r\n")
        self.bytes = iter(bytes([value]) for value in data.encode())
        self.host = host

    def settimeout(self, value):
        pass

    def sendall(self, data):
        assert data.startswith(b"HEAD / HTTP/1.1\r\n")

    def recv(self, count):
        return next(self.bytes, b"")

    def close(self):
        pass

    def version(self):
        return "TLSv1.3"

    def getpeercert(self):
        moment = int(time.time())
        return {"notBefore": time.strftime("%b %d %H:%M:%S %Y GMT", time.gmtime(moment - 3600)),
                "notAfter": time.strftime("%b %d %H:%M:%S %Y GMT", time.gmtime(moment + 864000)),
                "subject": ((("commonName", self.host),),),
                "issuer": ((("organizationName", "LOCAL QA fixture issuer"),),)}


class FixtureTransport:
    def open(self, host, port, budget, guard):
        guard()
        budget.remaining()
        time.sleep(0.5)  # QA only: make actual running state observable in the browser.
        if host == "qapartial.example.com" and port == 443:
            raise ScanFailure("tls_expired")
        return FixtureSocket(host, port)


if __name__ == "__main__":
    database = Database(settings.database_url)
    try:
        while True:
            if not work_once(database, settings, Runner(FixtureDNS(), FixtureTransport())):
                time.sleep(0.2)
    finally:
        database.close()
