"""Three-locale catalog and print-template regression checks."""

import io
import re

import pytest
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics

from app.locales import CATALOGS, message, translate
from app.reports import pdf
from app.reports.demo import sample
from app.reports.schemas import Snapshot


def test_catalog_parity_and_named_interpolation():
    en = CATALOGS["en"]
    for locale in ("ru", "kk"):
        catalog = CATALOGS[locale]
        assert catalog.keys() == en.keys()
        for key, value in catalog.items():
            assert value.strip(), key
            assert set(re.findall(r"\{(\w+)\}", value)) == set(re.findall(r"\{(\w+)\}", en[key])), (
                key
            )
    assert translate("customer.example.com", "kk") == "customer.example.com"
    assert "{" not in message("pdf.summary", "kk", assessed=2, enrolled=3, readiness="ready")


@pytest.mark.parametrize("locale", ["en", "ru", "kk"])
def test_template_grid_unicode_and_qa_context(locale):
    snapshot = sample(locale).model_copy(
        update={"kind": "real", "organization_name": "LOCAL QA — ӘҒҚҢӨҰҮҺІ әғқңөұүһі <script>&"}
    )
    data = pdf.render(snapshot)
    reader = PdfReader(io.BytesIO(data))
    assert snapshot.template_version == "assessment-2"
    for page in reader.pages:
        assert "LOCAL QA" in page.extract_text()
        assert page.mediabox.width == pytest.approx(595.2756, abs=0.01)
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "ӘҒҚҢӨҰҮҺІ әғқңөұүһі <script>&" in text
    assert "/JavaScript" not in str(reader.trailer)
    for name in ("ShieldSans", "ShieldSansBold"):
        font = pdfmetrics.getFont(name)
        for c in "ӘҒҚҢӨҰҮҺІәғқңөұүһі→":
            assert ord(c) in font.face.charToGlyph


def test_legacy_snapshot_schema_is_readable_without_rewriting():
    original = sample("en").model_dump()
    original.pop("template_version")
    restored = Snapshot.model_validate(original)
    assert restored.schema_version == "security-snapshot-1"
