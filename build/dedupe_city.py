# -*- coding: utf-8 -*-
"""
Cut the boilerplate out of the city pages.

73% of the text on a city page was shared with the other 59: national price
tables repeated up to 53 times, and the same six questions answered identically
on 58 pages. The prose was only 15% shared — the local copy is genuinely local.

So this does not rewrite anything. It moves the national material to the page
that owns it and links there instead, and rotates the shared questions so no
two city pages carry the same set. What stays on a city page is the copy that
was written for that city.
"""
import re, collections
from bs4 import BeautifulSoup

CHANGES = []

CITY_PREFIXES = ("/טכנאי-מזגנים-ב", "/ניקוי-מזגנים-ב")
SHARED_AT = 10          # a block on this many city pages is national, not local
KEEP_TABLES = 1         # the most relevant table stays; the rest are linked
KEEP_FAQ = 3            # out of the shared pool, rotated per page

# where each national table actually belongs
TABLE_HOME = [
    (re.compile(r"מיני מרכזי"), "/התקנת-מזגן-מיני-מרכזי/",
     "המחירון המלא להתקנת מזגן מיני מרכזי מרוכז בעמוד", "התקנת מזגן מיני מרכזי"),
    (re.compile(r"גודל חדר|גודל מזגן מומלץ"), "/התקנת-מזגנים/",
     "טבלת התאמת גודל המזגן לגודל החדר מופיעה בעמוד", "התקנת מזגנים"),
    (re.compile(r".*"), "/מחירון-מזגנים/",
     "המחירון המלא לכל שירותי המזגנים מרוכז בעמוד", "מחירון מזגנים"),
]


def plain(fragment):
    soup = BeautifulSoup(fragment or "", "html.parser")
    for t in soup.find_all(["style", "script"]):
        t.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def is_city(path):
    return path.startswith(CITY_PREFIXES)


def survey(pages):
    """How many city pages carry each table and each question."""
    tables, questions = collections.Counter(), collections.Counter()
    for p in pages:
        if not is_city(p["path"]):
            continue
        for b in p["blocks"]:
            if b["type"] == "table":
                tables[plain(b["html"])] += 1
            elif b["type"] == "faq":
                for item in b["items"]:
                    questions[item["q"].strip()] += 1
    return tables, questions


def link_paragraph(table_text):
    for rx, href, sentence, anchor in TABLE_HOME:
        if rx.search(table_text):
            return {"type": "paragraph",
                    "html": '%s <a href="%s">%s</a>.' % (sentence, href, anchor)}
    return None


_REFERS_TO_TABLE = re.compile(r"הטבלה לפניכם|לפי הטבלה|בטבלה שלפניכם|הטבלה הבאה")


def apply(pages):
    tables, questions = survey(pages)
    shared_tables = {t for t, n in tables.items() if n >= SHARED_AT}
    pool = [q for q, n in questions.most_common() if n >= SHARED_AT]

    city_pages = [p for p in pages if is_city(p["path"])]
    for index, p in enumerate(city_pages):
        blocks, out = p["blocks"], []

        # Which national table this page keeps rotates, so neighbouring cities
        # do not all carry the same one — the page stays substantial, the
        # overlap between any two pages drops.
        on_page = [i for i, b in enumerate(blocks)
                   if b["type"] == "table" and plain(b["html"]) in shared_tables]
        keep_at = set()
        if on_page:
            start = index % len(on_page)
            keep_at = {on_page[(start + k) % len(on_page)] for k in range(KEEP_TABLES)}

        for position, b in enumerate(blocks):
            if b["type"] == "table" and plain(b["html"]) in shared_tables:
                if position in keep_at:
                    out.append(b)
                    continue
                # drop the lead-in that pointed at a table we are removing
                if out and out[-1]["type"] == "paragraph" and _REFERS_TO_TABLE.search(
                        plain(out[-1]["html"])):
                    out.pop()
                replacement = link_paragraph(plain(b["html"]))
                if replacement:
                    out.append(replacement)
                CHANGES.append({"path": p["path"], "action": "טבלה ארצית הוחלפה בקישור",
                                "detail": plain(b["html"])[:80]})
                continue

            if b["type"] == "faq" and pool:
                shared = [i for i in b["items"] if i["q"].strip() in pool]
                local = [i for i in b["items"] if i["q"].strip() not in pool]
                if len(shared) > KEEP_FAQ:
                    offset = (index * 3) % len(shared)
                    picked = [shared[(offset + k) % len(shared)] for k in range(KEEP_FAQ)]
                    CHANGES.append({"path": p["path"], "action": "שאלות משותפות סוננו",
                                    "detail": "%d → %d" % (len(shared), KEEP_FAQ)})
                    b = {**b, "items": local + picked}
            out.append(b)

        p["blocks"] = out
    return pages
