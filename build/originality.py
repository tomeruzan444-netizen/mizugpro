# -*- coding: utf-8 -*-
"""
Two gates for content written from here on: originality, and a declared source.

The owner's standing rule is that every new page must be reliable, original and
authoritative, grounded in real sources, and new to both the reader and the
algorithm. Two parts of that can be measured.

ORIGINALITY is measured as the share of six-word runs a page has in common with
any other page on the site - the standard shingle overlap. Measured on the
page's own copy, after the furniture every page repeats is stripped, or all 127
pages would look identical.

Where the 20% ceiling comes from, measured on this site:

    pages written here      5.2% - 15.7%   (worst: two city pages sharing
                                            their VAT and warranty answers)
    migrated pages          median 27.8%
    worst migrated pair     62.6%   two city pages almost word for word
    /בלוג/ vs /category/בלוג/  66.3%

So 20% sits above anything written to the guide and well below the templating
the gate exists to prevent. It applies to new pages only: the migrated ones
would all fail, and the owner has asked to leave them alone for now.

A DECLARED SOURCE is the second gate. Every new page carries a `sources` list
in _source/new-pages.json, and a page about a place must cite at least one URL.
This exists because of a specific failure: /טכנאי-מזגנים-באזור/ shipped with an
invented description of the town's housing stock, reasoned backwards from the
work the page wanted to describe. A page that cannot name where its facts came
from does not go up.

What neither gate can check is whether a cited source actually says what the
page claims. That stays a human read against the checklist in
GOOGLE-CONTENT-POLICY.md.
"""
import re

MAX_OVERLAP = 0.20
SHINGLE = 6
PLACE_PAGE = re.compile(r"^/(?:טכנאי|ניקוי)-מזגנים-")

FINDINGS = {"unoriginal": [], "no_sources": []}


def shingles(text, n=SHINGLE):
    words = text.split()
    return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n))}


def overlap(a, b):
    """Share of six-word runs two pages have in common."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def check_originality(new_paths, texts):
    """texts: {path: own copy}. Reports new pages too close to any other page."""
    sh = {p: shingles(t) for p, t in texts.items()}
    for path in sorted(new_paths):
        if path not in sh:
            continue
        worst, against = 0.0, None
        for other in sh:
            if other == path:
                continue
            share = overlap(sh[path], sh[other])
            if share > worst:
                worst, against = share, other
        if worst > MAX_OVERLAP:
            FINDINGS["unoriginal"].append(
                "%s | חפיפה %.1f%% מול %s (הרף %.0f%%)"
                % (path, worst * 100, against, MAX_OVERLAP * 100))
    return FINDINGS["unoriginal"]


def check_sources(pages):
    """Every new page declares its sources; a page about a place cites a URL."""
    for p in pages:
        path = p["path"]
        sources = p.get("sources") or []
        if not sources:
            FINDINGS["no_sources"].append(
                "%s | אין שדה sources - עמוד חדש חייב להצהיר על מקורותיו" % path)
            continue
        if PLACE_PAGE.match(path) and not any(
                str(s).startswith("http") for s in sources):
            FINDINGS["no_sources"].append(
                "%s | עמוד על יישוב חייב לצטט לפחות כתובת אחת, ולא רק מקור פנימי"
                % path)
    return FINDINGS["no_sources"]
