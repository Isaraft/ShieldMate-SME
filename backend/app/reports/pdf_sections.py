"""Report narrative and evidence sections; no collection, risk calculation or persistence."""

from typing import Any

from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Spacer

from app.findings.schemas import FindingOut
from app.reports.pdf_layout import Layout, stamp
from app.reports.schemas import Snapshot

LIMITS = (
    "This is a limited external configuration assessment, not a penetration test, "
    "compliance audit or guarantee of safety. Missing, failed or stale checks do not "
    "prove security. Human task completion is not technical resolution."
)


def details(layout: Layout, finding: FindingOut, index: int, *, first: bool = False) -> list[Any]:
    f = finding
    opening = ([layout.h("Findings and evidence")] if first else []) + [
        layout.p(f"{index:02d} / {layout.tr(f.title)}", "finding"),
        layout.p(f"{layout.tr(f.severity)} · {layout.tr(f.status)} · {f.hostname}", "small"),
        layout.label("Why this matters"),
        layout.p(layout.tr(f.impact)),
    ]
    story = [
        KeepTogether(opening),
        layout.label("Recommended next step"),
        layout.p(layout.tr(f.recommendation)),
    ]
    story += [
        layout.label("Verification guidance"),
        layout.p(layout.tr("pdf.verify")),
        layout.label("Why this priority"),
        layout.p(layout.tr(f.rationale)),
        layout.p(layout.msg("pdf.risk_context", urgency=f.urgency, relevance=f.relevance), "small"),
        layout.p(
            layout.msg(
                "pdf.finding_meta",
                date=stamp(f.observed_at, layout.locale),
                confidence=layout.tr(f.confidence),
            ),
            "small",
        ),
        layout.p(f"{f.rule_id} · {f.policy_version} · /app/findings/{f.id}", "small"),
    ]
    if f.stale:
        story.append(layout.p(layout.tr("Historical evidence - stale"), "label"))
    if f.recheck_status == "not_rechecked":
        story.append(layout.p(layout.tr("Not rechecked"), "label"))
    story += [layout.label("Technical evidence")]
    if f.evidence:
        rows = [
            [
                f"{e.check_id}\n{stamp(e.observed_at, layout.locale)}\n{layout.tr(e.outcome)}",
                "\n".join(f"{key}: {value}" for key, value in e.values.items())
                or layout.tr("pdf.no_values"),
                e.observation_id,
            ]
            for e in f.evidence
        ]
        story.append(
            layout.table(
                ["pdf.check_time", "pdf.values", "Observation ID:"],
                rows,
                [51 * mm, 86 * mm, 37 * mm],
            )
        )
    else:
        story.append(layout.p(layout.tr("pdf.no_evidence")))
    story += [layout.label("Limits of this conclusion"), layout.p(layout.tr(f.limitation), "small")]
    return story


def compose(snapshot: Snapshot, layout: Layout) -> list[Any]:
    s = snapshot
    story = [
        layout.p(layout.tr("pdf.title"), "title"),
        layout.p(s.organization_name, "organization"),
        layout.p(layout.tr("Security Snapshot"), "small"),
        layout.p(
            layout.msg("pdf.identity", date=stamp(s.created_at, s.locale), report=s.id), "small"
        ),
        layout.p(f"{layout.tr('Policy')}: {s.policy_version} · {s.template_version}", "small"),
        layout.p(layout.tr("Limited external configuration assessment"), "label"),
        layout.p(layout.tr(LIMITS), "small"),
        layout.h("pdf.executive"),
    ]
    story += [
        layout.p(
            layout.msg(
                "pdf.summary",
                assessed=s.counts.get("assessed_domains", 0),
                enrolled=s.counts.get("enrolled_domains", 0),
                readiness=layout.tr(s.readiness),
            )
        )
    ]
    count_rows = [
        [layout.tr("Currently authorized domains"), s.counts.get("authorized_domains", 0)],
        [layout.tr("Unverified or expired domains"), s.counts.get("unverified_domains", 0)],
        [layout.tr("Domains with usable saved evidence"), s.counts.get("assessed_domains", 0)],
        [layout.tr("Domains without usable evidence"), s.counts.get("without_usable_evidence", 0)],
        [layout.tr("Domains with stale evidence"), s.counts.get("stale_domains", 0)],
        [
            layout.tr("Historical findings excluded from assessed scope"),
            s.counts.get("excluded_historical_findings", 0),
        ],
    ]
    story += [
        layout.table(["pdf.coverage", "pdf.count"], count_rows, [145 * mm, 29 * mm]),
        layout.p(
            " · ".join(
                f"{layout.tr(status)} / {layout.tr(severity)}: {count}"
                for key, count in sorted(s.finding_counts.items())
                for status, severity in [key.split(":", 1)]
            ),
            "small",
        ),
        layout.h("Top priorities"),
    ]
    if s.priorities:
        rows = [
            [str(i), f"{layout.tr(f.severity)}\n{f.hostname}", f"{layout.tr(f.title)}\n{f.rule_id}"]
            for i, f in enumerate(s.priorities, 1)
        ]
        story += [
            layout.table(
                ["pdf.rank", "pdf.asset_level", "pdf.priority_issue"],
                rows,
                [17 * mm, 57 * mm, 100 * mm],
            )
        ]
    else:
        story += [
            layout.p(
                layout.tr(
                    "No supported findings in the assessed scope. "
                    "This does not mean no security risks exist."
                )
            )
        ]
    story += [
        layout.h("pdf.method"),
        layout.p(layout.tr("pdf.method_text")),
        layout.p(layout.tr("pdf.exclusions"), "small"),
    ]
    if s.assets:
        story += [
            layout.table(
                ["Domain", "pdf.scope_status", "pdf.observation_window"],
                [
                    [
                        a.hostname,
                        f"{layout.tr(a.reason)}\n{layout.tr(a.scan_status or 'not_checked')}",
                        stamp(a.scan_finished_at, s.locale),
                    ]
                    for a in s.assets
                ],
                [53 * mm, 76 * mm, 45 * mm],
            )
        ]
    else:
        story += [layout.p(layout.tr("pdf.empty_scope"))]
    if s.findings:
        for index, finding in enumerate(s.findings, 1):
            story += details(layout, finding, index, first=index == 1)
    story += [
        layout.h("Remediation work"),
        layout.p(layout.tr("Human task status does not determine finding resolution.")),
    ]
    if s.tasks:
        story += [
            layout.table(
                ["Task status", "pdf.count"],
                [[layout.tr(status), count] for status, count in sorted(s.task_counts.items())],
                [145 * mm, 29 * mm],
            )
        ]
        for t in s.tasks:
            owner = layout.tr(t.owner_label) if s.kind == "demo" else t.owner_label
            task_story = [
                layout.p(layout.tr(t.title), "finding"),
                layout.p(
                    f"{t.hostname} · {layout.tr('Task status')}: {layout.tr(t.status)} · "
                    f"{layout.tr('Finding status')}: {layout.tr(t.finding_status)}",
                    "small",
                ),
                layout.p(
                    f"{layout.tr('Owner label')}: {owner or layout.tr('Owner label not set')}"
                ),
                layout.p(layout.tr(t.recommendation)),
                layout.p(
                    f"{layout.tr('Updated')}: {stamp(t.updated_at, s.locale)} · /app/tasks/{t.id}",
                    "small",
                ),
            ]
            if t.status == "done" and t.finding_status == "open":
                task_story.append(
                    layout.p(layout.tr("Task marked done - remediation not yet verified"), "label")
                )
            story.append(KeepTogether(task_story))
    else:
        story += [layout.p(layout.tr("No tasks in the assessed scope."))]
    story += [
        layout.h("pdf.definitions"),
        layout.p(layout.tr("pdf.definitions_text")),
        layout.p(layout.tr(LIMITS), "small"),
        Spacer(1, 3 * mm),
    ]
    if s.assets:
        for asset_index, asset in enumerate(s.assets):
            asset_intro = (
                [layout.h("pdf.appendix"), layout.p(layout.tr("pdf.evidence_note"), "small")]
                if asset_index == 0
                else []
            ) + [
                layout.p(asset.hostname, "finding"),
                layout.p(layout.tr(asset.reason)),
                layout.p(
                    f"{layout.tr('Ownership proof valid until')}: "
                    f"{stamp(asset.verification_valid_until, s.locale)}",
                    "small",
                ),
                layout.p(
                    f"{asset.scan_id or layout.tr('No saved scan')} · /app/assets#asset-{asset.id}",
                    "small",
                ),
                layout.p(
                    " · ".join(
                        f"{layout.tr(key)}: {count}"
                        for key, count in sorted(asset.observation_counts.items())
                    ),
                    "small",
                ),
            ]
            story += [KeepTogether(asset_intro)]
            if asset.stale:
                story += [layout.p(layout.tr("Historical evidence - stale"), "label")]
            if asset.observations:
                rows = [
                    [
                        f"{o.check_id}\n{stamp(o.observed_at, s.locale)}\n{layout.tr(o.outcome)}",
                        "\n".join(f"{key}: {value}" for key, value in o.values.items())
                        or layout.tr("pdf.no_values"),
                        o.id,
                    ]
                    for o in asset.observations
                ]
                story += [
                    layout.table(
                        ["pdf.check_time", "pdf.values", "Observation ID:"],
                        rows,
                        [51 * mm, 86 * mm, 37 * mm],
                        compact=True,
                    )
                ]
    return story
