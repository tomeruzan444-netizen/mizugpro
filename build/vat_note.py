# -*- coding: utf-8 -*-
"""
Every price on the site is quoted before VAT — say so, once, next to the first
price on each page. 71 pages used to show prices and never mention VAT at all.

Kept in its own module so the build and the content audit apply the same rule
and the audit reports on what actually ships.
"""
import re

VAT_NOTE = 'כל המחירים באתר אינם כוללים מע"מ.'

# A block prices something when it carries a currency token and a number.
# Matching them separately catches tables that put "(ש"ח)" in the header row
# and the figures in cells further down, which a proximity rule misses.
_CURRENCY = re.compile(r'ש"ח|₪|שקלים')
_NUMBER = re.compile(r"\d{2,}")


def _prices(text):
    return bool(_CURRENCY.search(text) and _NUMBER.search(text))

# This page prices electricity, not our work, and quotes the tariff with VAT
# included — the site-wide note would contradict it.
SKIP = {"/כמה-עולה-מזגן-לשעה/"}


def block_text(block):
    if block.get("type") == "faq":
        return " ".join(i["q"] + " " + i["a"] for i in block.get("items", []))
    return block.get("html") or ""


def add(body, path):
    """Return the body with the note placed after the first block showing a price."""
    if path in SKIP or any(b.get("type") == "note" for b in body):
        return body
    for i, block in enumerate(body):
        if block.get("type") in ("table", "paragraph", "list", "custom_html", "faq") \
                and _prices(block_text(block)):
            return body[:i + 1] + [{"type": "note", "html": VAT_NOTE}] + body[i + 1:]
    return body


def apply(pages):
    """Audit-side helper: annotate the content model the same way the build does."""
    for p in pages:
        p["blocks"] = add(p["blocks"], p["path"])
    return pages
