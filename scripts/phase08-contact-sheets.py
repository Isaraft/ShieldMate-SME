"""Small review sheets of every rendered PDF page; originals remain available."""

from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1] / "docs/evidence/phase-08"
for pdf in sorted((root / "pdfs").glob("*.pdf")):
    pages = sorted((root / "pdf-pages").glob(pdf.stem + "-*.png"))
    assert pages, pdf.name
    for old in (root / "pdf-pages").glob(pdf.stem + "-sheet-*.jpg"):
        old.unlink()
    for start in range(0, len(pages), 12):
        subset = pages[start : start + 12]
        sheet = Image.new("RGB", (1000, ((len(subset) + 3) // 4) * 380), "#ded6d1")
        draw = ImageDraw.Draw(sheet)
        for i, path in enumerate(subset):
            image = Image.open(path).convert("RGB")
            image.thumbnail((242, 350))
            x, y = (i % 4) * 250, (i // 4) * 380
            sheet.paste(image, (x + 4, y + 20))
            draw.text((x + 4, y + 3), path.stem, fill="#321015")
        sheet.save(root / "pdf-pages" / (pdf.stem + f"-sheet-{start // 12 + 1}.jpg"))

# Supplemental all-width UI review strips, when the interaction screenshots exist.
for language in ["en", "ru", "kk"]:
    for name in ["landing", "app", "reports"]:
        files = [
            root / "screenshots" / f"all-widths-{name}-{language}-{width}.png"
            for width in [360, 390, 768, 1024, 1280, 1440, 1920]
        ]
        if not all(file.exists() for file in files):
            continue
        sheet = Image.new("RGB", (1470, 620), "#ded6d1")
        draw = ImageDraw.Draw(sheet)
        for index, file in enumerate(files):
            image = Image.open(file).convert("RGB")
            image.thumbnail((202, 580))
            x = index * 210
            sheet.paste(image, (x + 4, 26))
            draw.text((x + 4, 6), file.stem.split("-")[-1] + "px", fill="#321015")
        sheet.save(root / "screenshots" / f"review-{name}-{language}.jpg")
