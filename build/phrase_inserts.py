# -*- coding: utf-8 -*-
"""
Work the missing service phrases into the city pages.

Six phrases - תיקון מזגנים, התקנת מזגן, התקנת מזגנים, טכנאי מיזוג אוויר,
תיקון מזגן, מתקין מזגנים - were absent from most city pages. The gap was
widest on "טכנאי מיזוג אוויר" (61 pages of 64) and "מתקין מזגנים" (50).

Two rules govern everything here:

**Nothing existing is touched.** Every entry inserts a new block. No paragraph
is rewritten, no sentence appended to someone else's, no heading changed. A
page can only gain text.

**No two pages get the same sentence.** Sixty-two near-identical insertions
would have recreated the templating this site is already being treated for -
next week's audit would flag it, and it would deserve to. Each page gets its
own angle, drawn from something true about that town: salt air in Or Akiva,
hillside height difference in Nesher, sixties housing stock in Holon, a town
built all at once in Harish. Placement moves too, so the addition does not sit
in the same slot on every page.

The copy lives in _source/phrase-inserts.json, next to the rest of the site's
content rather than inside a build script.

Anchors are semantic, not positional, because block indices shift as the other
passes run:

    before_faq          a new block immediately before the FAQ
    after_heading:TEXT  after the first heading whose text starts with TEXT
    faq                 an extra question appended to the FAQ
    end                 after the last content block
"""
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "_source", "phrase-inserts.json")

CHANGES = []

INSERTS = {}
if os.path.exists(DATA):
    INSERTS = json.load(io.open(DATA, encoding="utf-8"))


def _find_faq(blocks):
    for i, b in enumerate(blocks):
        if b.get("type") == "faq":
            return i
    return None


def _find_heading(blocks, prefix):
    for i, b in enumerate(blocks):
        if b.get("type") == "heading" and (b.get("text") or "").startswith(prefix):
            return i
    return None


def _last_content(blocks):
    for i in range(len(blocks) - 1, -1, -1):
        if blocks[i].get("type") in ("paragraph", "list", "table", "faq"):
            return i
    return len(blocks) - 1


def apply(page):
    """Insert this page's additions. Returns the page, changed in place."""
    spec = INSERTS.get(page["path"])
    if not spec:
        return page

    blocks = page["blocks"]
    for entry in spec:
        anchor = entry["at"]

        if anchor == "faq":
            i = _find_faq(blocks)
            if i is None:
                blocks.append({"type": "faq", "items": []})
                i = len(blocks) - 1
            blocks[i]["items"].append({"q": entry["q"],
                                       "a": "<p>%s</p>" % entry["a"]})
            CHANGES.append({"path": page["path"], "where": "faq",
                            "text": entry["q"]})
            continue

        block = {"type": "paragraph", "html": entry["html"]}

        if anchor == "before_faq":
            i = _find_faq(blocks)
            at = i if i is not None else _last_content(blocks) + 1
        elif anchor.startswith("after_heading:"):
            i = _find_heading(blocks, anchor.split(":", 1)[1])
            # past the heading *and* the block it introduces, so the insert
            # never wedges itself between a heading and its own paragraph
            at = (i + 2) if i is not None else _last_content(blocks) + 1
        else:
            at = _last_content(blocks) + 1

        blocks.insert(max(0, min(at, len(blocks))), block)
        CHANGES.append({"path": page["path"], "where": anchor,
                        "text": re.sub(r"<[^>]+>", "", entry["html"])[:70]})
    return page
