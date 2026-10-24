"""Bounded offline A4 renderer. Saved artifacts are never re-rendered by downloads."""

import io
import threading
from pathlib import Path
from typing import Any

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

from app.reports.pdf_layout import BURGUNDY, RED, Layout, clean, stamp  # noqa: F401
from app.reports.pdf_sections import LIMITS, compose  # noqa: F401
from app.reports.schemas import Snapshot

MAX_BYTES, MAX_PAGES = 2 * 1024 * 1024, 80
_font_lock = threading.Lock()


def render(snapshot: Snapshot) -> bytes:
    with _font_lock:
        if "ShieldSans" not in pdfmetrics.getRegisteredFontNames():
            folder = Path(__file__).parent / "fonts"
            for name, filename in [
                ("ShieldSans", "IBMPlexSans-Regular.ttf"),
                ("ShieldSansBold", "IBMPlexSans-SemiBold.ttf"),
            ]:
                pdfmetrics.registerFont(TTFont(name, str(folder / filename)))
            pdfmetrics.registerFontFamily(
                "ShieldSans",
                normal="ShieldSans",
                bold="ShieldSansBold",
                italic="ShieldSans",
                boldItalic="ShieldSansBold",
            )
    layout = Layout(snapshot.locale)
    buffer = io.BytesIO()
    doc = BaseDocTemplate(
        buffer,
        pagesize=(210 * mm, 297 * mm),
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=27 * mm,
        bottomMargin=23 * mm,
        title=layout.tr("pdf.title"),
        author="ShieldMate SME",
        subject=layout.tr("Limited external configuration assessment"),
        pageCompression=1,
    )
    context = (
        "pdf.demo"
        if snapshot.kind == "demo"
        else "pdf.qa"
        if snapshot.organization_name.startswith("LOCAL QA")
        else "pdf.confidential"
    )

    def page(canvas: Any, document: Any) -> None:
        if document.page > MAX_PAGES:
            raise ValueError("Report page limit")
        canvas.saveState()
        canvas.setFillColor(BURGUNDY)
        canvas.setFont("ShieldSansBold", 10)
        canvas.drawString(18 * mm, 282 * mm, "SHIELDMATE SME")
        canvas.setFont("ShieldSansBold", 8)
        canvas.drawRightString(192 * mm, 282 * mm, layout.tr(context))
        canvas.setStrokeColor(RED)
        canvas.setLineWidth(1)
        canvas.line(18 * mm, 278 * mm, 192 * mm, 278 * mm)
        canvas.setFont("ShieldSans", 7.5)
        canvas.drawString(18 * mm, 13 * mm, f"{clean(snapshot.id)} · {snapshot.template_version}")
        canvas.drawRightString(192 * mm, 13 * mm, f"{layout.tr('Page')} {document.page}")
        canvas.restoreState()

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(PageTemplate(id="assessment", frames=[frame], onPage=page))
    doc.build(compose(snapshot, layout))
    data = buffer.getvalue()
    if len(data) > MAX_BYTES:
        raise ValueError("Report byte limit")
    return data
