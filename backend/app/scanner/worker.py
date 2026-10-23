"""One durable worker slot across processes; fixed lease longer than the hard run deadline."""

import json
import logging
import signal
import time
from threading import Event

from sqlalchemy import select

from app.config import Settings
from app.db import Database
from app.domains import event, locked
from app.findings.reconcile import reconcile_pending
from app.models import CheckObservation, DomainAsset, Organization, ScanRun
from app.scanner.contracts import CHECKS, Observation, ScanFailure
from app.scanner.policy import Budget, eligible
from app.scanner.runner import Runner
from app.scanner.service import recover

logger = logging.getLogger("shieldmate.worker")


def work_once(database: Database, settings: Settings, runner: Runner | None = None) -> bool:
    moment = int(time.time())
    with database.sessions() as db:
        locked(db)
        recover(db, moment)
        if db.scalar(select(ScanRun.id).where(ScanRun.status == "running").limit(1)):
            db.commit()
            return False
        run = db.scalar(
            select(ScanRun)
            .where(ScanRun.status == "queued")
            .order_by(ScanRun.created_at, ScanRun.id)
            .limit(1)
        )
        if run is None:
            db.commit()
            return False
        run.status, run.started_at, run.lease_until = "running", moment, moment + 90
        run_id = run.id
        db.commit()
    logger.info("scan_started id=%s", run_id)

    def guard() -> None:
        with database.sessions() as db:
            current = db.get(ScanRun, run_id)
            if (
                current is None
                or current.status != "running"
                or (current.lease_until or 0) <= int(time.time())
                or db.scalar(
                    select(Organization.owner_id).where(Organization.id == current.organization_id)
                )
                != current.requested_by
                or not eligible(db.get(DomainAsset, current.asset_id), int(time.time()), current)
            ):
                raise ScanFailure("authorization_changed")

    def emit(row: Observation) -> None:
        if row.check_id not in CHECKS or len(json.dumps(row.evidence)) > 4096:
            raise ScanFailure("evidence_limit")
        with database.sessions() as db:
            locked(db)
            current = db.get(ScanRun, run_id)
            if current is None or current.status != "running":
                raise ScanFailure("worker_interrupted")
            if not db.scalar(
                select(CheckObservation.id).where(
                    CheckObservation.scan_id == run_id, CheckObservation.check_id == row.check_id
                )
            ):
                db.add(CheckObservation(scan_id=run_id, **row.model_dump()))
                current.completed_checks += 1
            db.commit()

    error: str | None = None
    try:
        guard()
        (runner or Runner()).run(
            run.hostname, Budget.start(settings.scan_timeout, settings.scan_io_timeout), guard, emit
        )
        guard()  # Recheck proof after the last request before publishing success.
    except ScanFailure as exc:
        error = exc.code
    except Exception as exc:
        error = "engine_failure"
        logger.error("scan_error id=%s exception_type=%s", run_id, type(exc).__name__)
    with database.sessions() as db:
        locked(db)
        current = db.get(ScanRun, run_id)
        if current and current.status == "running":
            # Serialize final authorization with proof rotation/deletion before publishing success.
            if (
                not eligible(db.get(DomainAsset, current.asset_id), int(time.time()), current)
                or db.scalar(
                    select(Organization.owner_id).where(Organization.id == current.organization_id)
                )
                != current.requested_by
            ):
                error = "authorization_changed"
            rows = list(
                db.scalars(select(CheckObservation).where(CheckObservation.scan_id == run_id))
            )
            useful = sum(row.outcome in {"pass", "attention", "informational"} for row in rows)
            current.status = (
                "failed"
                if not useful or error == "authorization_changed"
                else "partial"
                if error or useful < len(CHECKS)
                else "completed"
            )
            current.error_code = error or ("checks_incomplete" if useful < len(CHECKS) else None)
            current.finished_at = int(time.time())
            event(db, current.organization_id, current.asset_id, "scan_" + current.status)
            db.commit()
            logger.info("scan_finished id=%s status=%s", run_id, current.status)
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    settings = Settings()
    database = Database(settings.database_url)
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    try:
        while not stop.is_set():
            reconcile_pending(database)
            if not work_once(database, settings):
                stop.wait(1)
    finally:
        database.close()


if __name__ == "__main__":
    main()
