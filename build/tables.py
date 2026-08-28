# -*- coding: utf-8 -*-
"""
Normalise every table on the site into one predictable shape, so a single set
of CSS rules can render all 148 of them well on a phone without side-scrolling.

The source tables arrive in five shapes: real <thead>, a bold first row acting
as a header, no header at all, a one-cell title row above the real header, and
legacy widget tables carrying inline styles. This module turns each into:

    <table class="t-pair|t-multi" data-cols="N">
      <caption>…</caption>                     (only when a title row existed)
      <thead><tr><th>…</th></tr></thead>       (only when a header exists)
      <tbody><tr><td data-label="header">…     (label drives the mobile layout)

Content is untouched — only structure and markup.
"""
import re
from bs4 import BeautifulSoup

# a cell that is entirely bold/heading markup is acting as a header
_HEADERISH = ("b", "strong", "h2", "h3", "h4", "h5", "h6")


def _cells(row):
    return row.find_all(["td", "th"], recursive=False) or row.find_all(["td", "th"])


def _looks_like_header(row):
    cells = _cells(row)
    if not cells:
        return False
    if any(c.name == "th" for c in cells):
        return True
    for c in cells:
        if not c.get_text(strip=True):
            return False
        if not c.find(_HEADERISH):
            return False
    return True


def _text(cell):
    return re.sub(r"\s+", " ", cell.get_text(" ", strip=True))


def normalise(table, soup, strip_inline=False):
    """Rewrite one <table> in place. Returns the number of body rows."""
    rows = table.find_all("tr")
    if not rows:
        return 0

    widths = [len(_cells(r)) for r in rows]
    cols = max(widths) if widths else 0
    if cols == 0:
        return 0

    # a lone wide cell above everything else is a title, not data
    caption_text = None
    if len(rows) > 1 and widths[0] == 1 and cols > 1:
        caption_text = _text(rows[0])
        rows[0].decompose()
        rows = table.find_all("tr")
        widths = [len(_cells(r)) for r in rows]

    header_row = rows[0] if rows and _looks_like_header(rows[0]) else None
    labels = []
    if header_row is not None:
        for c in _cells(header_row):
            c.name = "th"
            c.attrs.pop("style", None)
            # a header cell wrapped in <h5><strong> is styling, not structure
            for inner in c.find_all(_HEADERISH):
                inner.unwrap()
            labels.append(_text(c))

    # rebuild the table skeleton
    for tag in table.find_all(["thead", "tbody", "tfoot"]):
        tag.unwrap()

    thead = None
    if header_row is not None:
        thead = soup.new_tag("thead")
        header_row.extract()
        thead.append(header_row)

    tbody = soup.new_tag("tbody")
    body_rows = 0
    for row in table.find_all("tr"):
        row.extract()
        cells = _cells(row)
        for i, c in enumerate(cells):
            if strip_inline:
                c.attrs.pop("style", None)
            if labels and i < len(labels) and labels[i]:
                c["data-label"] = labels[i]
        tbody.append(row)
        body_rows += 1

    table.clear()
    if caption_text:
        cap = soup.new_tag("caption")
        cap.string = caption_text
        table.append(cap)
    if thead is not None:
        table.append(thead)
    table.append(tbody)

    if strip_inline:
        table.attrs.pop("style", None)
    classes = [c for c in (table.get("class") or []) if c not in ("t-pair", "t-multi")]
    # two columns read as description + value; more than two need per-cell labels
    classes.append("t-pair" if cols <= 2 else "t-multi")
    table["class"] = classes
    table["data-cols"] = str(cols)
    return body_rows


def normalise_fragment(html, is_table_body=False, strip_inline=False):
    """
    Normalise every table in an HTML fragment.
    `is_table_body` handles our stored table blocks, which hold only the inner
    rows without the surrounding <table>.
    """
    wrapped = "<table>" + html + "</table>" if is_table_body else html
    soup = BeautifulSoup("<x-root>" + wrapped + "</x-root>", "html.parser")
    root = soup.find("x-root")
    tables = root.find_all("table")
    if not tables:
        return html, 0
    changed = 0
    for t in tables:
        changed += 1 if normalise(t, soup, strip_inline) else 0
    if is_table_body:
        table = root.find("table")
        return table.decode_contents(), changed
    return root.decode_contents(), changed


def apply(pages):
    """Normalise the tables in every page's blocks. Returns how many were touched."""
    touched = 0
    for p in pages:
        for b in p["blocks"]:
            if b.get("type") == "table" and isinstance(b.get("html"), str):
                b["html"], n = normalise_fragment(b["html"], is_table_body=True)
                touched += n
            elif b.get("type") == "custom_html" and isinstance(b.get("html"), str):
                # legacy widgets carry inline table styling that fights the design
                b["html"], n = normalise_fragment(b["html"], strip_inline=True)
                touched += n
    return touched
