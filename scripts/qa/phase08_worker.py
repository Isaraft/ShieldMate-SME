"""Actual queue/catalog/reconciliation around clearly synthetic DNS and socket responses."""

import signal
import time
from pathlib import Path
from threading import Event

from app.config import Settings
from app.db import Database
from app.findings.reconcile import reconcile_pending
from app.scanner.contracts import ScanFailure
from app.scanner.dns_checks import Records
from app.scanner.runner import Runner
from app.scanner.worker import work_once

from scripts.qa.phase04_worker import FixtureDNS, FixtureSocket

stop = Event()


class DNS(FixtureDNS):
    def resolve(self, host, budget):
        if host.startswith("qa-blocked"):
            raise ScanFailure("unsafe_destination")
        return super().resolve(host, budget)

    def query(self, host, kind, budget):
        clean = Path("/tmp/phase08-clean").exists()
        if host.startswith("_dmarc."):
            return Records(["v=DMARC1; p=reject" if clean else "v=DMARC1; p=invalid"])
        return (
            Records(["v=spf1 -all"] if clean else ["v=spf1 -all", "v=spf1 ~all"])
            if kind == "TXT"
            else Records(["10 fixture.invalid."])
        )


class Socket(FixtureSocket):
    def __init__(self, host, port, clean):
        super().__init__(host, port)
        if not clean:
            self.bytes = iter(bytes([v]) for v in b"HTTP/1.1 200 OK\r\n\r\n")
        self.clean = clean

    def getpeercert(self):
        result = super().getpeercert()
        result["notAfter"] = time.strftime(
            "%b %d %H:%M:%S %Y GMT", time.gmtime(time.time() + (90 if self.clean else 5) * 86400)
        )
        return result


class Transport:
    def open(self, host, port, budget, guard):
        guard()
        budget.remaining()
        if host.startswith("qa-interrupt"):
            # Long-lived controlled pause for a real container crash/lease recovery test.
            stop.wait(120)
            raise ScanFailure("network_timeout")
        if host.startswith("qa-edge") and port == 443:
            raise ScanFailure("network_timeout")
        stop.wait(0.15)
        return Socket(host, port, Path("/tmp/phase08-clean").exists())


if __name__ == "__main__":
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    database = Database(Settings().database_url)
    try:
        while not stop.is_set():
            reconcile_pending(database)
            if not work_once(database, Settings(), Runner(DNS(), Transport())):
                stop.wait(0.2)
    finally:
        database.close()
