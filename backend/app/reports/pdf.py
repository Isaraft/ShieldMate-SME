"""Offline selectable-text PDFs. No HTML/URL/image fetch or browser subprocess."""

import io
import threading
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from app.locales import translate
from app.reports.schemas import Snapshot

MAX_BYTES, MAX_PAGES = 2 * 1024 * 1024, 80
_font_lock = threading.Lock()
LIMITS = (
    "This is a limited external configuration assessment, not a penetration test, "
    "compliance audit or guarantee of safety. Missing, failed or stale checks do not "
    "prove security. Human task completion is not technical resolution."
)


def clean(value: object) -> str:
    text = str(value)
    return "".join(
        c for c in text if unicodedata.category(c) not in {"Cc", "Cs", "Cf"} or c in "\n\t"
    )


def stamp(value: int | None, locale: str) -> str:
    if value is None:
        return "—"
    return datetime.fromtimestamp(value, UTC).strftime(
        "%d.%m.%Y %H:%M UTC" if locale == "ru" else "%Y-%m-%d %H:%M UTC"
    )


def render(snapshot: Snapshot) -> bytes:
    with _font_lock:
        if "ShieldSans" not in pdfmetrics.getRegisteredFontNames():
            folder = Path(__file__).parent / "fonts"
            pdfmetrics.registerFont(
                TTFont("ShieldSans", str(folder / "LiberationSans-Regular.ttf"))
            )
            pdfmetrics.registerFont(
                TTFont("ShieldSansBold", str(folder / "LiberationSans-Bold.ttf"))
            )
            pdfmetrics.registerFontFamily(
                "ShieldSans",
                normal="ShieldSans",
                bold="ShieldSansBold",
                italic="ShieldSans",
                boldItalic="ShieldSansBold",
            )
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(210 * mm, 297 * mm),
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=28 * mm,
        bottomMargin=24 * mm,
        title=translate("Security Snapshot", snapshot.locale),
        author="ShieldMate SME",
        pageCompression=1,
    )
    base = ParagraphStyle(
        "body",
        fontName="ShieldSans",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#321015"),
        spaceAfter=7,
        splitLongWords=True,
        alignment=TA_LEFT,
    )
    heading = ParagraphStyle(
        "heading",
        parent=base,
        fontName="ShieldSansBold",
        fontSize=15,
        leading=20,
        spaceBefore=16,
        spaceAfter=9,
        keepWithNext=True,
    )
    small = ParagraphStyle("small", parent=base, fontSize=8, leading=11)
    title = ParagraphStyle("title", parent=heading, fontSize=25, leading=30)

    def tr(text: str) -> str:
        return translate(text, snapshot.locale)

    def p(value: object, style: Any = base, controlled: bool = False) -> Any:
        value = tr(str(value)) if controlled else str(value)
        return Paragraph(escape(clean(value)).replace("\n", "<br/>"), style)

    def h(text: str) -> Any:
        return p(text, heading, True)

    story = [
        p("Security Snapshot", title, True),
        p(snapshot.organization_name, heading),
        p(f"{tr('Generated at')}: {stamp(snapshot.created_at, snapshot.locale)}"),
        p(f"{tr('Report ID')}: {snapshot.id}", small),
        p(f"{tr('Policy')}: {snapshot.policy_version}", small),
        p("Limited external configuration assessment", base, True),
        p(LIMITS, base, True),
        h("Scope"),
    ]
    labels = {
        "enrolled_domains": "Enrolled domains",
        "authorized_domains": "Currently authorized domains",
        "unverified_domains": "Unverified or expired domains",
        "stale_domains": "Domains with stale evidence",
        "assessed_domains": "Domains with usable saved evidence",
        "without_usable_evidence": "Domains without usable evidence",
        "excluded_historical_findings": "Historical findings excluded from assessed scope",
    }
    table = Table(
        [[p(tr(label)), p(snapshot.counts.get(key, 0))] for key, label in labels.items()],
        colWidths=[135 * mm, 35 * mm],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9C7C3")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([table, p(tr(snapshot.readiness)), h("Finding and work summary")])
    for key, count in sorted(snapshot.finding_counts.items()):
        status, severity = key.split(":", 1)
        story.append(p(f"{tr(status)} · {tr(severity)}: {count}"))
    for status, count in sorted(snapshot.task_counts.items()):
        story.append(p(f"{tr('Task status')} · {tr(status)}: {count}"))
    story.append(h("Top priorities"))
    if not snapshot.priorities:
        story.append(
            p(
                "No supported findings in the assessed scope. "
                "This does not mean no security risks exist.",
                controlled=True,
            )
        )
    for index, f in enumerate(snapshot.priorities, 1):
        story.extend(
            [
                p(f"{index}. {tr(f.title)}", heading),
                p(f"{f.hostname} · {tr(f.severity)} · {tr(f.status)}"),
                p(tr("Why this matters") + ": " + tr(f.impact)),
                p(tr("Recommended next step") + ": " + tr(f.recommendation)),
                p(tr(f.rationale), small),
                p(
                    f"{tr('Observed at')}: {stamp(f.observed_at, snapshot.locale)} · {f.rule_id}",
                    small,
                ),
            ]
        )
    story.append(h("Findings and evidence"))
    for f in snapshot.findings:
        story.extend(
            [
                p(tr(f.title), heading),
                p(f"{f.hostname} · {tr(f.status)} · {tr(f.severity)}"),
                p(tr(f.impact)),
                p(tr(f.recommendation)),
                p(tr(f.limitation), small),
                p(f"{tr('Source')}: /app/findings/{f.id}", small),
                p(
                    f"{f.rule_id} · {f.policy_version} · {stamp(f.observed_at, snapshot.locale)}",
                    small,
                ),
            ]
        )
        if f.stale:
            story.append(p("Historical evidence - stale", controlled=True))
        if f.recheck_status == "not_rechecked":
            story.append(p("Not rechecked", controlled=True))
        for e in f.evidence:
            story.append(
                p(
                    f"{e.check_id} · {e.observation_id} · "
                    f"{stamp(e.observed_at, snapshot.locale)} · {tr(e.outcome)}",
                    small,
                )
            )
            story.append(p(" | ".join(f"{k}: {v}" for k, v in e.values.items()), small))
    story.append(h("Remediation work"))
    if not snapshot.tasks:
        story.append(p("No tasks in the assessed scope.", controlled=True))
    for t in snapshot.tasks:
        story.extend(
            [
                p(tr(t.title), heading),
                p(
                    f"{t.hostname} · {tr('Task status')}: {tr(t.status)} · "
                    f"{tr('Finding status')}: {tr(t.finding_status)}"
                ),
                p(
                    f"{tr('Owner label')}: "
                    + ((tr(t.owner_label) if snapshot.kind == "demo" else t.owner_label) or "—")
                ),
                p(tr(t.recommendation)),
                p(
                    f"{tr('Updated')}: {stamp(t.updated_at, snapshot.locale)} · /app/tasks/{t.id}",
                    small,
                ),
            ]
        )
        if t.status == "done" and t.finding_status == "open":
            story.append(p("Task marked done - remediation not yet verified", controlled=True))
    story.append(h("Domain and check details"))
    for a in snapshot.assets:
        story.extend(
            [
                p(a.hostname, heading),
                p(tr(a.reason)),
                p(
                    f"{tr('Ownership proof valid until')}: "
                    f"{stamp(a.verification_valid_until, snapshot.locale)}",
                    small,
                ),
                p(
                    " · ".join(
                        f"{tr(key)}: {value}" for key, value in sorted(a.observation_counts.items())
                    ),
                    small,
                ),
                p(
                    f"{tr(a.scan_status or 'not_checked')} · "
                    f"{stamp(a.scan_finished_at, snapshot.locale)}"
                ),
                p(f"{tr('Source')}: {a.scan_id or '—'}", small),
                p(f"/app/assets#asset-{a.id}", small),
            ]
        )
        if a.stale:
            story.append(p("Historical evidence - stale", controlled=True))
        for o in a.observations:
            story.extend(
                [
                    p(
                        f"{o.check_id} · {tr(o.outcome)} · {stamp(o.observed_at, snapshot.locale)}",
                        small,
                    ),
                    p(
                        f"{o.id} · "
                        + " | ".join(f"{key}: {value}" for key, value in o.values.items()),
                        small,
                    ),
                ]
            )
    story.extend([h("Scope and limitations"), p(LIMITS, controlled=True)])

    def page(canvas: Any, document: Any) -> None:
        if document.page > MAX_PAGES:
            raise ValueError("Report page limit")
        canvas.saveState()
        canvas.setFont("ShieldSansBold", 10)
        canvas.setFillColor(colors.HexColor("#570711"))
        canvas.drawString(19 * mm, 282 * mm, "SHIELDMATE SME")
        canvas.setStrokeColor(colors.HexColor("#CF2431"))
        canvas.line(19 * mm, 278 * mm, 191 * mm, 278 * mm)
        if snapshot.kind == "demo":
            canvas.setFont("ShieldSansBold", 8)
            canvas.drawString(19 * mm, 273 * mm, tr("SAMPLE DATA / DEMO - NOT A LIVE ASSESSMENT"))
        canvas.setFont("ShieldSans", 8)
        canvas.drawString(19 * mm, 14 * mm, tr("Limited external configuration assessment"))
        canvas.drawRightString(191 * mm, 14 * mm, f"{tr('Page')} {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=page, onLaterPages=page)
    data = buffer.getvalue()
    if len(data) > MAX_BYTES:
        raise ValueError("Report byte limit")
    return data
