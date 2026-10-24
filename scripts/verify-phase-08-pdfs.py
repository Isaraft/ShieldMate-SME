"""Validate/rasterize all Phase 08 saved PDFs with Poppler; no network access."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from itertools import pairwise
from pathlib import Path

root = Path(__file__).resolve().parents[1]
folder = root / "docs/evidence/phase-08"
rendered = folder / "pdf-pages"
rendered.mkdir(exist_ok=True)
results = []
ns = {"x": "http://www.w3.org/1999/xhtml"}
for file in sorted((folder / "pdfs").glob("*.pdf")):
    for stale in rendered.glob(file.stem + "-*.png"):
        stale.unlink()
    prefix = rendered / file.stem
    subprocess.run(
        ["pdftoppm", "-scale-to", "1400", "-png", str(file), str(prefix)],
        check=True,
        capture_output=True,
    )
    xml = subprocess.check_output(["pdftotext", "-bbox-layout", str(file), "-"], text=True)
    document = ET.fromstring(xml)
    pages = document.findall(".//x:page", ns)
    words = document.findall(".//x:word", ns)
    for word in words:
        x0, y0, x1, y1 = (float(word.attrib[k]) for k in ["xMin", "yMin", "xMax", "yMax"])
        assert 50 <= x0 <= x1 <= 545, (
            file.name,
            word.text,
            "horizontal bounds",
            word.attrib,
        )
        assert 28 <= y0 <= y1 <= 811, (
            file.name,
            word.text,
            "vertical bounds",
            word.attrib,
        )
        assert "\ufffd" not in (word.text or "")
    marker = "DEMO" if file.stem.startswith("demo") else "LOCAL QA"
    for page in pages:
        text = " ".join(w.text or "" for w in page.findall(".//x:word", ns))
        assert marker in text, (file.name, "context marker")
        assert "assessment-2" in text
    text = subprocess.check_output(["pdftotext", str(file), "-"], text=True)
    assert len(text) > 1000
    assert "PRIVATE-NOTE" not in text
    fonts = subprocess.check_output(["pdffonts", str(file)], text=True)
    assert "ShieldMatePlexPrint" in fonts
    assert all("yes" in row for row in fonts.splitlines()[2:] if "ShieldMatePlexPrint" in row)
    # Inspect each physical line, including content split over table cells.
    for line in document.findall(".//x:line", ns):
        line_words = line.findall("x:word", ns)
        for left, right in pairwise(line_words):
            assert float(left.attrib["xMax"]) <= float(right.attrib["xMin"]) + 0.5, (
                file.name,
                "overlapping words",
                left.text,
                right.text,
            )
    if file.stem.startswith("edge"):
        assert "ӘҒҚҢӨҰҮҺІ" in text
    results.append(
        {
            "file": str(file.relative_to(root)),
            "pages": len(pages),
            "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            "words": len(words),
            "bounds": "PASS",
            "context_each_page": marker,
            "text_extractable": True,
        }
    )
for record in json.loads((folder / "checks/final-report-records.json").read_text()):
    expected = folder / "pdfs" / (record["kind"] + "-" + record["locale"] + ".pdf")
    assert hashlib.sha256(expected.read_bytes()).hexdigest() == record["sha256"]
assert len(results) == 12, f"Expected 12 PDFs, got {len(results)}"
(folder / "checks/pdf-validation.json").write_text(
    json.dumps({"reports": results, "total_pages": sum(r["pages"] for r in results)}, indent=2)
    + "\n"
)
print(json.dumps(results, indent=2))
