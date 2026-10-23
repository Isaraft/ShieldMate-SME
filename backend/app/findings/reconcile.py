"""Atomic, repeatable offline reconciliation. Source snapshots survive scan retention."""

import hashlib
import time

from sqlalchemy import Integer, delete, exists, literal_column, select

from app.db import Database
from app.domains import locked
from app.findings.contracts import POLICY, SEVERITY_RANK
from app.findings.engine import evaluate
from app.models import (
    CheckObservation,
    DomainAsset,
    Finding,
    FindingEvaluation,
    FindingEvent,
    ScanRun,
)

TERMINAL = ("completed", "partial", "failed", "interrupted")


def reconcile(database: Database, scan_id: str, organization_id: str) -> bool:
    with database.sessions() as db:
        locked(db)
        run = db.scalar(
            select(ScanRun).where(ScanRun.id == scan_id, ScanRun.organization_id == organization_id)
        )
        if run is None or run.status not in TERMINAL:
            return False
        asset = db.scalar(
            select(DomainAsset).where(
                DomainAsset.id == run.asset_id, DomainAsset.organization_id == organization_id
            )
        )
        if asset is None:
            return False
        if db.scalar(
            select(FindingEvaluation.id).where(
                FindingEvaluation.scan_id == scan_id, FindingEvaluation.policy_version == POLICY
            )
        ):
            return False
        # SQLite insertion order breaks same-second ties; random UUID order is not chronology.
        source_order = db.scalar(
            select(literal_column("scan_runs.rowid", Integer))
            .select_from(ScanRun)
            .where(ScanRun.id == run.id)
        )
        previous = db.execute(
            select(ScanRun.created_at, literal_column("scan_runs.rowid", Integer))
            .join(FindingEvaluation, FindingEvaluation.scan_id == ScanRun.id)
            .where(
                FindingEvaluation.asset_id == asset.id,
                FindingEvaluation.organization_id == organization_id,
                FindingEvaluation.policy_version == POLICY,
            )
            .order_by(ScanRun.created_at.desc(), literal_column("scan_runs.rowid", Integer).desc())
            .limit(1)
        ).first()
        order = (run.created_at, run.id)
        apply = previous is None or (run.created_at, source_order) > tuple(previous)
        observations = list(
            db.scalars(
                select(CheckObservation).where(CheckObservation.scan_id == scan_id).limit(14)
            )
        )
        assessment = evaluate(run, observations)
        moment = int(time.time())
        db.add(
            FindingEvaluation(
                scan_id=scan_id,
                organization_id=organization_id,
                asset_id=asset.id,
                policy_version=POLICY,
                evaluated_at=moment,
                scan_created_at=run.created_at,
                applied=apply,
                assessment=assessment.model_dump(),
            )
        )
        if apply:
            for result in assessment.rules:
                fingerprint = hashlib.sha256(f"{asset.id}:{result.rule_id}".encode()).hexdigest()
                finding = db.scalar(
                    select(Finding).where(
                        Finding.organization_id == organization_id,
                        Finding.fingerprint == fingerprint,
                    )
                )
                if finding is None and result.decision != "issue":
                    continue
                kind = "confirmed"
                if finding is None:
                    finding = Finding(
                        organization_id=organization_id,
                        asset_id=asset.id,
                        fingerprint=fingerprint,
                        rule_id=result.rule_id,
                        policy_version=POLICY,
                        first_seen_at=max(e.observed_at for e in result.evidence),
                        status="open",
                    )
                    db.add(finding)
                    kind = "detected"
                elif result.decision == "issue" and finding.status == "resolved":
                    kind = "reopened"
                elif result.decision == "clear":
                    kind = "resolved" if finding.status == "open" else "clear_confirmed"
                elif result.decision not in {"issue", "clear"}:
                    kind = "not_rechecked"
                finding.last_evaluation_at = moment
                finding.last_scan_created_at, finding.last_scan_id = order
                finding.recheck_status = "not_rechecked" if kind == "not_rechecked" else "confirmed"
                if result.decision in {"issue", "clear"}:
                    observed = max(e.observed_at for e in result.evidence)
                    finding.observed_at, finding.source_scan_id = observed, run.id
                    finding.evidence = [e.model_dump() for e in result.evidence]
                    if result.decision == "issue":
                        finding.last_seen_at, finding.resolved_at, finding.status = (
                            observed,
                            None,
                            "open",
                        )
                        for key in (
                            "title",
                            "category",
                            "severity",
                            "urgency",
                            "relevance",
                            "confidence",
                            "impact",
                            "recommendation",
                            "rationale",
                            "limitation",
                        ):
                            setattr(finding, key, getattr(result, key))
                        finding.severity_rank = SEVERITY_RANK[result.severity]
                        finding.policy_version = POLICY
                    else:
                        if finding.status == "open":
                            finding.resolved_at = observed
                        finding.status = "resolved"
                db.flush()
                db.add(
                    FindingEvent(
                        finding_id=finding.id,
                        source_scan_id=run.id,
                        policy_version=POLICY,
                        occurred_at=max(
                            (e.observed_at for e in result.evidence),
                            default=run.finished_at or moment,
                        ),
                        kind=kind,
                        snapshot=result.model_dump(),
                    )
                )
                db.flush()
                # Keep first detection + latest49 events. Explicitly disclose compacted history.
                events = list(
                    db.scalars(
                        select(FindingEvent)
                        .where(FindingEvent.finding_id == finding.id)
                        .order_by(
                            FindingEvent.occurred_at,
                            literal_column("finding_events.rowid", Integer),
                        )
                    )
                )
                if len(events) > 50:
                    keep = {events[0].id}
                    for important in ("resolved", "reopened"):
                        if latest := next(
                            (e for e in reversed(events) if e.kind == important), None
                        ):
                            keep.add(latest.id)
                    for item in reversed(events):
                        if len(keep) < 50:
                            keep.add(item.id)
                    db.execute(
                        delete(FindingEvent).where(
                            FindingEvent.id.in_([e.id for e in events if e.id not in keep])
                        )
                    )
                    finding.history_truncated = True
        db.commit()
        return True


def reconcile_pending(
    database: Database, organization_id: str | None = None, limit: int = 5
) -> int:
    if not 1 <= limit <= 100:
        raise ValueError("Evaluation batch limit must be between 1 and 100")
    with database.sessions() as db:
        query = (
            select(ScanRun.id, ScanRun.organization_id)
            .join(
                DomainAsset,
                (DomainAsset.id == ScanRun.asset_id)
                & (DomainAsset.organization_id == ScanRun.organization_id),
            )
            .where(
                ScanRun.status.in_(TERMINAL),
                ~exists(
                    select(FindingEvaluation.id).where(
                        FindingEvaluation.scan_id == ScanRun.id,
                        FindingEvaluation.policy_version == POLICY,
                    )
                ),
            )
        )
        if organization_id is not None:
            query = query.where(ScanRun.organization_id == organization_id)
        jobs = list(
            db.execute(
                query.order_by(
                    ScanRun.created_at, literal_column("scan_runs.rowid", Integer)
                ).limit(min(limit, 100))
            )
        )
    return sum(reconcile(database, run_id, org_id) for run_id, org_id in jobs)
