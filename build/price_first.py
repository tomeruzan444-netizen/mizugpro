# -*- coding: utf-8 -*-
"""
Put the price table near the top, after the second paragraph.

Someone who lands on a service page from a search for "כמה עולה" wants the
number, and on most of these pages it was three to thirteen paragraphs down.
Fourteen pages of ninety-nine already had it after the second paragraph; the
rest made the reader scroll for the one thing they came for.

The table does not travel alone. On 79 of the 99 pages a heading sits directly
above it - "מחירון תיקון ושירותי מזגנים בהרצליה" and the like - and moving the
table out from under its own heading would leave the heading introducing
whatever happened to follow. The heading moves with it.

Nothing is deleted and nothing is rewritten: the blocks are the same blocks in
a different order. A table already at or above the target position is left
alone, so this only ever moves a table earlier, never later.
"""
import re

CHANGES = []

_CURRENCY = re.compile(r'ש"ח|₪|שקלים')
_NUMBER = re.compile(r"\d{2,}")


def _is_price_table(block):
    """A block that shows prices in a table.

    Not every price table is a table block: some pages carry theirs inside a
    custom_html block, which is why /ניקוי-מיני-מרכזי/ kept its prices
    eighteen paragraphs down while every other page moved.
    """
    html = block.get("html") or ""
    if block.get("type") == "table":
        pass
    elif block.get("type") == "custom_html" and "<table" in html:
        pass
    else:
        return False
    return bool(_CURRENCY.search(html) and _NUMBER.search(html))


def _first_price_table(body):
    for i, b in enumerate(body):
        if _is_price_table(b):
            return i
    return None


def _target(body):
    """Index just after the second paragraph, or after the last one if fewer."""
    seen = 0
    for i, b in enumerate(body):
        if b.get("type") == "paragraph":
            seen += 1
            if seen == 2:
                return i + 1
    # fewer than two paragraphs: sit after whatever prose exists
    for i in range(len(body) - 1, -1, -1):
        if body[i].get("type") == "paragraph":
            return i + 1
    return 0


def apply(body, path=""):
    table_at = _first_price_table(body)
    if table_at is None:
        return body

    start = table_at
    if start and body[start - 1].get("type") == "heading":
        start -= 1

    dest = _target(body)
    # already at the top of the page, or the move would push it later
    if dest >= start:
        return body

    chunk = body[start:table_at + 1]
    rest = body[:start] + body[table_at + 1:]
    out = rest[:dest] + chunk + rest[dest:]

    CHANGES.append({"path": path, "from": start, "to": dest,
                    "moved": len(chunk)})
    return out
