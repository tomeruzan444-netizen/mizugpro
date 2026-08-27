# -*- coding: utf-8 -*-
"""
Subset the self-hosted webfont down to the glyphs the built site actually uses,
then regenerate assistant.css. Run after build.py, then re-minify + rebuild.
"""
import os, re, glob, json
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
FONTS = os.path.join(ROOT, "assets", "fonts")

TAG = re.compile(r"<[^>]+>")
SCRIPTS = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def used_chars():
    chars = set(" 0123456789.,:;!?()[]{}%$-–—/\\'\"״׳@&+=#*|<>₪…‏‎ ")
    for path in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
        html = open(path, encoding="utf-8").read()
        html = SCRIPTS.sub(" ", html)
        text = TAG.sub(" ", html)
        chars.update(text)
    # drop control characters
    return {c for c in chars if c.isprintable() or c in ("‏", "‎", " ")}


def main():
    chars = used_chars()
    text = "".join(sorted(chars))
    print("distinct characters on the site:", len(chars))

    total_before = total_after = 0
    for path in sorted(glob.glob(os.path.join(FONTS, "*.woff2"))):
        if path.endswith(".sub.woff2"):
            continue
        before = os.path.getsize(path)
        font = TTFont(path)
        options = subset.Options()
        options.flavor = "woff2"
        options.layout_features = ["kern", "liga", "rlig", "ccmp", "mark", "mkmk", "locl"]
        options.desubroutinize = False
        options.hinting = False            # woff2 + modern rasterisers don't need it
        options.glyph_names = False
        options.legacy_kern = False
        options.name_IDs = ["*"]
        options.name_legacy = False
        options.name_languages = ["*"]
        options.drop_tables += ["DSIG", "LTSH", "hdmx", "VDMX", "PCLT"]
        options.notdef_outline = True
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(text=text)
        subsetter.subset(font)
        font.flavor = "woff2"
        font.save(path)
        after = os.path.getsize(path)
        total_before += before
        total_after += after
        print("%-34s %6d -> %6d" % (os.path.basename(path), before, after))
    print("FONT TOTAL %d -> %d bytes" % (total_before, total_after))
    json.dump({"chars": len(chars), "bytes_before": total_before,
               "bytes_after": total_after},
              open(os.path.join(FONTS, "subset-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
