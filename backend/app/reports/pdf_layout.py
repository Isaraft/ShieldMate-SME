"""Print primitives: escaped text, consistent measure, reusable tables and fixed rhythm."""

import unicodedata
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Table, TableStyle

from app.locales import message, translate
from app.reports.schemas import Locale

WIDTH = 174 * mm
INK = colors.HexColor("#321015")
BURGUNDY = colors.HexColor("#570711")
RED = colors.HexColor("#98121F")
PAPER = colors.HexColor("#F7F0EA")
STROKE = colors.HexColor("#D9C7C3")


def clean(value: object) -> str:
    return "".join(
        c for c in str(value) if unicodedata.category(c) not in {"Cc", "Cs", "Cf"} or c in "\n\t"
    )


def stamp(value: int | None, locale: str) -> str:
    if value is None:
        return translate("Not checked", locale)
    return datetime.fromtimestamp(value, UTC).strftime(
        "%Y-%m-%d %H:%M UTC" if locale == "en" else "%d.%m.%Y %H:%M UTC"
    )


class Layout:
    def __init__(self, locale: Locale):
        self.locale = locale
        body = ParagraphStyle(
            "body",
            fontName="ShieldSans",
            fontSize=10,
            leading=14.5,
            textColor=INK,
            spaceAfter=7,
            splitLongWords=True,
            allowWidows=0,
            allowOrphans=0,
        )
        self.styles = {
            "body": body,
            "small": ParagraphStyle("small", parent=body, fontSize=8, leading=11, spaceAfter=5),
            "label": ParagraphStyle(
                "label",
                parent=body,
                fontName="ShieldSansBold",
                fontSize=9,
                leading=12,
                spaceBefore=5,
                keepWithNext=True,
            ),
            "section": ParagraphStyle(
                "section",
                parent=body,
                fontName="ShieldSansBold",
                fontSize=16,
                leading=20,
                spaceBefore=16,
                spaceAfter=10,
                keepWithNext=True,
            ),
            "finding": ParagraphStyle(
                "finding",
                parent=body,
                fontName="ShieldSansBold",
                fontSize=12,
                leading=16,
                spaceBefore=12,
                spaceAfter=7,
                keepWithNext=True,
            ),
            "title": ParagraphStyle(
                "title",
                parent=body,
                fontName="ShieldSansBold",
                fontSize=25,
                leading=30,
                spaceAfter=12,
                keepWithNext=True,
            ),
            "organization": ParagraphStyle(
                "organization",
                parent=body,
                fontName="ShieldSansBold",
                fontSize=14,
                leading=18,
                spaceAfter=12,
                keepWithNext=True,
            ),
            "cell": ParagraphStyle("cell", parent=body, fontSize=9, leading=12, spaceAfter=0),
            "technical": ParagraphStyle(
                "technical", parent=body, fontSize=8.5, leading=11, spaceAfter=0
            ),
            "table_head": ParagraphStyle(
                "table_head",
                parent=body,
                fontName="ShieldSansBold",
                fontSize=8,
                leading=11,
                spaceAfter=0,
                textColor=colors.white,
            ),
        }

    def tr(self, text: str) -> str:
        return translate(text, self.locale)

    def msg(self, key: str, **values: object) -> str:
        return message(key, self.locale, **values)

    def p(self, text: object, style: str = "body") -> Any:
        return Paragraph(escape(clean(text)).replace("\n", "<br/>"), self.styles[style])

    def h(self, key: str) -> Any:
        return self.p(self.tr(key), "section")

    def label(self, key: str) -> Any:
        return self.p(self.tr(key), "label")

    def table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[object]],
        widths: Sequence[float],
        *,
        compact: bool = False,
    ) -> Any:
        data = [[self.p(self.tr(h), "table_head") for h in headers]]
        data += [
            [self.p(value, "technical" if compact else "cell") for value in row] for row in rows
        ]
        table = Table(
            data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1, splitInRow=1
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BURGUNDY),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5 if compact else 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5 if compact else 6),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER]),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.35, STROKE),
                ]
            )
        )
        table.spaceAfter = 10
        return table
