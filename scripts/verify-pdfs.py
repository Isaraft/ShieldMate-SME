"""Offline Phase 07 evidence validation; run with backend/.venv/bin/python from repo root."""

import hashlib
import json
import subprocess
from pathlib import Path

from pypdf import PdfReader

folder = Path(__file__).resolve().parents[1] / "docs/evidence/phase-07"
results = []
for source in sorted(folder.glob("*.pdf")):
    data = source.read_bytes()
    assert data.startswith(b"%PDF-") and len(data) <= 2 * 1024 * 1024
    reader = PdfReader(source)
    assert 1 <= len(reader.pages) <= 80
    texts = [page.extract_text() for page in reader.pages]
    russian = source.stem.endswith("ru")
    marker = "ДЕМО" if russian else "DEMO"
    demo = source.stem.startswith("DEMO")
    if demo:
        assert all(marker in text for text in texts)
        assert "merchant.example" in "\n".join(texts)
    else:
        assert "LOCAL QA" in texts[0]
    assert ("Снимок состояния безопасности" if russian else "Security Snapshot") in texts[0]
    assert "PRIVATE-NOTE-MUST-NOT-ENTER-PDF" not in "\n".join(texts)
    assert all("SHIELDMATE SME" in text for text in texts)
    target = folder / "pdf-pages" / source.stem
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftoppm", "-scale-to", "1200", "-png", str(source), str(target)],
        check=True,
    )
    subprocess.run(
        ["pdftotext", "-layout", str(source), str(target.with_suffix(".txt"))],
        check=True,
    )
    images = sorted(target.parent.glob(source.stem + "-*.png"))
    assert len(images) == len(texts)
    results.append(
        {
            "file": source.name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "pages": len(texts),
            "locale": "ru" if russian else "en",
            "kind": "demo" if demo else "local_qa",
            "selectable_text": True,
            "demo_every_page": demo,
            "rendered_pages": [str(p.relative_to(folder)) for p in images],
        }
    )
assert len(results) == 4, (
    "Run the completed browser workflow first (two LOCAL QA and two DEMO PDFs)."
)
(folder / "pdf-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(results, ensure_ascii=False, indent=2))
