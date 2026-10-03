# -*- coding: utf-8 -*-
"""
Make dateModified tell the truth.

Every migrated page carries a WordPress dateModified that stopped moving at
the migration. Pages rewritten here in the last month still reported
themselves as a year old, and dateModified is one of the signals search
engines and assistants use to judge how current a page is.

The fix is a small ledger, _source/content-dates.json, keyed by path:

    {"/תיקון-מזגנים/": {"hash": "9f2c...", "modified": "2026-09-18"}}

On every build the page's own content is fingerprinted. If the fingerprint
matches the ledger, the stored date is reused; if it changed, the date becomes
the build date and the ledger is updated. A page that has never changed since
the migration keeps its WordPress value - stamping it with today would be a
worse lie than a stale date.

The fingerprint covers the article blocks only, which is what a reader sees.
It deliberately excludes the business schema and the related-links grid: both
change on every page whenever a city page is added, and neither is a content
change. Without that distinction a single new city page would date-stamp all
123 pages as rewritten.

The ledger is seeded from git history, so the dates start out true rather than
starting from the day this file was written.
"""
import datetime
import hashlib
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(os.path.dirname(HERE), "_source", "content-dates.json")
TODAY = datetime.date.today().isoformat()

_ledger = {}
if os.path.exists(LEDGER):
    _ledger = json.load(io.open(LEDGER, encoding="utf-8"))

CHANGED = []      # pages whose copy changed in this build
STAMPED = {}      # path -> the date actually used


def fingerprint(blocks):
    """A stable hash of what the article says, ignoring how it is wrapped."""
    parts = []
    for b in blocks or []:
        t = b.get("type")
        if t == "faq":
            for item in b.get("items", []):
                parts.append("faq|%s|%s" % (item.get("q", ""), item.get("a", "")))
        else:
            parts.append("%s|%s|%s" % (t, b.get("text") or "", b.get("html") or ""))
    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()


def modified_for(path, blocks, inherited):
    """The dateModified to publish for this page.

    Idempotent: called once per schema node that carries a date, and both
    calls on one page get the same answer.
    """
    if path in STAMPED:
        return STAMPED[path]

    fp = fingerprint(blocks)
    entry = _ledger.get(path)

    if entry is None:
        # never changed since the migration, or brand new - either way the
        # inherited value is the honest one until the copy moves
        _ledger[path] = {"hash": fp, "modified": None}
        date = inherited
    elif not entry.get("hash"):
        # seeded from git history, first build since: record the fingerprint
        entry["hash"] = fp
        date = _as_iso(entry.get("modified")) or inherited
    elif entry["hash"] == fp:
        date = _as_iso(entry.get("modified")) or inherited
    else:
        entry["hash"] = fp
        entry["modified"] = TODAY
        CHANGED.append(path)
        date = _as_iso(TODAY)

    STAMPED[path] = date
    return date


def _as_iso(day):
    """A date in the ledger becomes the timestamp format the graph already uses."""
    return (day + "T00:00:00+00:00") if day else None


def save():
    json.dump(_ledger, io.open(LEDGER, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
