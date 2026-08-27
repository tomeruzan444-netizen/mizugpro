# -*- coding: utf-8 -*-
"""Scan the extracted copy for spelling slips and logical inconsistencies."""
import json, os, re, collections
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
pages = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))

# common Hebrew misspellings / slips seen on service sites
TYPOS = [
    (r"יקר\s+מידי", "יקר מדי"),
    (r"גדול\s+מידי", "גדול מדי"),
    (r"קטן\s+מידי", "קטן מדי"),
    (r"הרבה\s+מידי", "הרבה מדי"),
    (r"\bפרוייקט", "פרויקט"),
    (r"\bתיקונים\s+תיקונים\b", "תיקונים"),
    (r"\bאיכפת", "אכפת"),
    (r"\bלמרות ש", "למרות ש"),
    (r"\bבמידה ו", "אם"),
    (r"\bמזגן\s+מזגן\b", "מזגן"),
    (r"\bשל\s+של\b", "של"),
    (r"\bאת\s+את\b", "את"),
    (r"\bעם\s+עם\b", "עם"),
    (r"\bכל\s+כל\b(?!\s+כך)", "כל"),
    (r"\bהוא\s+הוא\b", "הוא"),
    (r"\bזה\s+זה\b", "זה"),
    (r"\bאנו\s+אנו\b", "אנו"),
    (r"\bאנחנו\s+אנחנו\b", "אנחנו"),
    (r"\bטכנאי\s+טכנאי\b", "טכנאי"),
    (r"\bניתן\s+ניתן\b", "ניתן"),
    (r"\s+,", ","),
    (r"\s+\.", "."),
    (r"\bמעכשיו לעכשיו\b", "מעכשיו לעכשיו"),
    (r"\bבמיוחד\s+במיוחד\b", "במיוחד"),
    (r"\bמנת\s+ל", "מנת ל"),
]


def text_of(b):
    if b["type"] == "faq":
        return " ".join(i["q"] + " " + BeautifulSoup(i["a"], "html.parser").get_text(" ", strip=True)
                        for i in b["items"])
    if b["type"] == "reviews":
        return " ".join(i["text"] for i in b["items"])
    if b["type"] == "custom_html":
        s = BeautifulSoup(b["html"], "html.parser")
        for t in s.find_all(["style", "script"]):
            t.decompose()
        return s.get_text(" ", strip=True)
    if isinstance(b.get("html"), str):
        return BeautifulSoup(b["html"], "html.parser").get_text(" ", strip=True)
    return ""


print("=" * 70)
print("1. TYPO CANDIDATES")
hits = collections.Counter()
where = collections.defaultdict(set)
for p in pages:
    for b in p["blocks"]:
        t = text_of(b)
        for rx, fix in TYPOS:
            for m in re.finditer(rx, t):
                hits[(m.group(0), fix)] += 1
                where[(m.group(0), fix)].add(p["path"])
for (found, fix), n in hits.most_common(40):
    if found.strip() == fix.strip():
        continue
    print("  %-28r -> %-22r  x%-3d  %s" % (found, fix, n, list(where[(found, fix)])[:2]))

print()
print("=" * 70)
print("2. PRICE-RANGE WIDGETS (low / avg / high must ascend)")
for p in pages:
    for b in p["blocks"]:
        if b["type"] == "price_range":
            vals = [pt["value"] for pt in b["points"]]
            nums = [int(re.sub(r"[^\d]", "", v) or 0) for v in vals]
            flag = "  <-- NOT ASCENDING" if nums != sorted(nums) else ""
            print("  %-42s %s%s" % (p["path"][:42], " | ".join(vals), flag))

print()
print("=" * 70)
print("3. PHONE NUMBERS IN COPY")
phones = collections.Counter()
for p in pages:
    for b in p["blocks"]:
        for m in re.findall(r"0\d[\d\-]{7,10}", text_of(b)):
            phones[m] += 1
for k, v in phones.most_common(10):
    print("  ", k, v)

print()
print("=" * 70)
print("4. HEADING LEVEL JUMPS (h2 -> h4 etc.)")
bad = 0
for p in pages:
    prev = 1
    for b in p["blocks"]:
        if b["type"] == "heading":
            if b["level"] - prev > 1:
                bad += 1
                if bad < 12:
                    print("  %-40s h%d -> h%d  %s" % (p["path"][:40], prev, b["level"], b["text"][:40]))
            prev = b["level"]
print("  total jumps:", bad)

print()
print("=" * 70)
print("5. DUPLICATE H1 / MISSING H1")
for p in pages:
    h1s = [b for b in p["blocks"] if b["type"] == "heading" and b["level"] == 1]
    if len(h1s) != 1:
        print("  %-46s h1 count=%d" % (p["path"][:46], len(h1s)))

print()
print("=" * 70)
print("6. TITLE / DESCRIPTION LENGTH (SEO)")
for p in pages:
    t = p.get("meta_title") or ""
    d = p.get("meta_description") or ""
    notes = []
    if not d:
        notes.append("no description")
    elif len(d) > 165:
        notes.append("description %d chars" % len(d))
    if len(t) > 62:
        notes.append("title %d chars" % len(t))
    if notes:
        print("  %-44s %s" % (p["path"][:44], "; ".join(notes)))
