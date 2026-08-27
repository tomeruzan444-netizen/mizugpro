# -*- coding: utf-8 -*-
"""
Drop legacy-widget rules whose selectors match nothing in the built pages.
The capture step is deliberately generous (it keys off class names, and a few
of those are generic), so this pass keeps the shipped stylesheet honest.
Run after build.py, then re-minify and rebuild.
"""
import os, re, io, glob
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSS = os.path.join(ROOT, "assets", "css", "legacy-widgets.css")
DIST = os.path.join(ROOT, "dist")

RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")


def selectors_in_use():
    present = set()
    for f in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
        soup = BeautifulSoup(io.open(f, encoding="utf-8").read(), "html.parser")
        for embed in soup.select(".embed"):
            for el in embed.find_all(True):
                present.update(el.get("class") or [])
                if el.get("id"):
                    present.add("#" + el["id"])
                present.add(el.name)
    return present


def main():
    present = selectors_in_use()
    css = io.open(CSS, encoding="utf-8").read()

    out, kept, dropped = [], 0, 0
    pos = 0
    for m in RULE.finditer(css):
        out.append(css[pos:m.start()])
        pos = m.end()
        sel, body = m.group(1), m.group(2)
        stripped = sel.strip()
        if stripped.startswith("@") or "keyframes" in stripped:
            out.append(m.group(0))
            kept += 1
            continue
        classes = set(re.findall(r"\.([\w-]+)", stripped)) - {"embed"}
        ids = {"#" + x for x in re.findall(r"#([\w-]+)", stripped)}
        if (classes & present) or (ids & present) or not classes:
            out.append(m.group(0))
            kept += 1
        else:
            dropped += 1
    out.append(css[pos:])

    result = re.sub(r"\n{2,}", "\n", "".join(out)).strip() + "\n"
    io.open(CSS, "w", encoding="utf-8").write(result)
    print("legacy widget rules kept: %d | dropped: %d" % (kept, dropped))
    print("stylesheet %d -> %d bytes" % (len(css), len(result)))


if __name__ == "__main__":
    main()
