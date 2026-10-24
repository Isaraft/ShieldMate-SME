"""Reconstruct print TTFs from the locked, licensed UI font subsets (maintainer tool only)."""

import hashlib
import json
import tempfile
from pathlib import Path

from fontTools.merge import Merger
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

root = Path(__file__).resolve().parents[1]
source = root / "frontend/node_modules/@fontsource/ibm-plex-sans"
output = root / "backend/app/reports/fonts"
manifest = {
    "source": "@fontsource/ibm-plex-sans",
    "version": json.loads((source / "package.json").read_text())["version"],
    "files": {},
}
with tempfile.TemporaryDirectory(prefix="shieldmate-fonts-") as temporary:
    for weight, name in [
        (400, "IBMPlexSans-Regular.ttf"),
        (600, "IBMPlexSans-SemiBold.ttf"),
    ]:
        paths = []
        original_times = None
        for subset in ["latin", "cyrillic", "cyrillic-ext"]:
            font = TTFont(
                source / f"files/ibm-plex-sans-{subset}-{weight}-normal.woff",
                recalcTimestamp=False,
            )
            if original_times is None:
                original_times = (font["head"].created, font["head"].modified)
            font.flavor = None
            target = Path(temporary) / f"{subset}.ttf"
            font.save(target)
            paths.append(str(target))
        merged = Merger().merge(paths)
        merged.recalcTimestamp = False
        merged["head"].created, merged["head"].modified = original_times
        # Plex supplies vertical arrows only. Rotate its own outline for the right
        # arrow used by product copy, rather than introducing a fallback family.
        glyphs = merged.getGlyphSet()
        arrow = glyphs[merged.getBestCmap()[0x2191]]
        pen = TTGlyphPen(glyphs)
        arrow.draw(TransformPen(pen, (0, -1, 1, 0, 40, 700)))
        name_arrow = "shieldmateRightArrow"
        merged.setGlyphOrder([*merged.getGlyphOrder(), name_arrow])
        merged["glyf"][name_arrow] = pen.glyph()
        merged["hmtx"][name_arrow] = (1000, 40)
        for cmap in merged["cmap"].tables:
            if cmap.isUnicode():
                cmap.cmap[0x2192] = name_arrow
        for record in merged["name"].names:
            if record.nameID in {1, 4, 6}:
                record.string = (
                    record.toUnicode()
                    .replace("IBM Plex Sans", "ShieldMate Plex Print")
                    .replace("IBMPlexSans", "ShieldMatePlexPrint")
                    .encode(record.getEncoding())
                )
        manifest["modification"] = (
            "Merged licensed subsets; right arrow rotated from Plex up arrow; derivative print family renamed ShieldMate Plex Print."
        )
        if "DSIG" in merged:
            del merged["DSIG"]
        merged.save(output / name)
        manifest["files"][name] = hashlib.sha256(
            (output / name).read_bytes()
        ).hexdigest()
(output / "LICENSE").write_text((source / "LICENSE").read_text().strip() + "\n")
(output / "sources.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
