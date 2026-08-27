# -*- coding: utf-8 -*-
"""
Content audit — reports only, changes nothing.

Looks for the things that actually cost money on a site like this: prices that
contradict each other between pages, copy repeated verbatim across dozens of
city pages, thin pages, stale dates, and spelling that survived the migration.
"""
import os, re, json, collections, difflib
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
pages = json.load(open(os.path.join(ROOT, "_source", "content.json"), encoding="utf-8"))

import sys
sys.path.insert(0, HERE)
import content_fixes
pages = [content_fixes.apply(p) for p in pages]   # audit the corrected copy

findings = collections.OrderedDict()


def plain(fragment):
    s = BeautifulSoup(fragment or "", "html.parser")
    for t in s.find_all(["style", "script"]):
        t.decompose()
    return re.sub(r"\s+", " ", s.get_text(" ", strip=True))


def page_text(p):
    parts = []
    for b in p["blocks"]:
        t = b.get("type")
        if t == "faq":
            for i in b["items"]:
                parts += [i["q"], plain(i["a"])]
        elif t == "reviews":
            parts += [i["text"] for i in b["items"]]
        elif isinstance(b.get("html"), str):
            parts.append(plain(b["html"]))
    return " ".join(parts)


TEXT = {p["path"]: page_text(p) for p in pages}
WORDS = {k: len(v.split()) for k, v in TEXT.items()}


# ---------------------------------------------------------------- prices ----
PRICE = re.compile(r"(\d[\d,]{1,6})\s*(?:–|-|עד)\s*(\d[\d,]{1,6})\s*ש\"?ח|(\d[\d,]{1,6})\s*ש\"?ח")


def money(v):
    return int(v.replace(",", ""))


SERVICES = {
    "ביקור טכנאי": r"ביקור (?:של )?טכנאי",
    "מילוי גז": r"מילוי גז",
    "החלפת מדחס": r"החלפת מדחס",
    "ניקוי מזגן עילי": r"ניקוי מזגן עילי",
    "החלפת עינית": r"החלפת עינית",
    "החלפת מנוע": r"החלפת מנוע",
    "פירוק מזגן": r"פירוק מזגן",
    "החלפת קבל": r"החלפת קבל",
}

price_map = collections.defaultdict(list)
for p in pages:
    for label, rx in SERVICES.items():
        for m in re.finditer(rx + r"[^.!?\n]{0,80}", TEXT[p["path"]]):
            seg = m.group(0)
            pm = PRICE.search(seg)
            if not pm:
                continue
            lo, hi, single = pm.group(1), pm.group(2), pm.group(3)
            rng = (money(lo), money(hi)) if lo else (money(single), money(single))
            if rng[0] < 30 or rng[0] > 100000:
                continue
            price_map[label].append((p["path"], rng, seg[:90]))

rows = []
for label, entries in price_map.items():
    ranges = {e[1] for e in entries}
    if len(ranges) > 1:
        spread = (min(r[0] for r in ranges), max(r[1] for r in ranges))
        rows.append({"service": label, "distinct_quotes": len(ranges),
                     "span": "%d–%d" % spread, "pages": len(entries),
                     "examples": [{"path": e[0], "range": "%d–%d" % e[1], "text": e[2]}
                                  for e in sorted(entries, key=lambda x: x[1])[:4]]})
findings["price_contradictions"] = sorted(rows, key=lambda r: -r["distinct_quotes"])

# inverted or zero-width ranges anywhere in the copy
bad_ranges = []
for p in pages:
    for m in re.finditer(r"(\d[\d,]{1,6})\s*(?:–|-)\s*(\d[\d,]{1,6})\s*ש\"?ח", TEXT[p["path"]]):
        a, b = money(m.group(1)), money(m.group(2))
        if a > b:
            bad_ranges.append({"path": p["path"], "range": "%d–%d" % (a, b),
                               "text": TEXT[p["path"]][max(0, m.start()-60):m.end()+20]})
findings["inverted_ranges"] = bad_ranges

# VAT wording
vat = collections.Counter()
for p in pages:
    t = TEXT[p["path"]]
    if "מע\"מ" in t or "מעמ" in t:
        vat["mentions VAT"] += 1
        if "כולל מע" in t:
            vat["says including"] += 1
        if "ללא מע" in t or "לא כולל מע" in t:
            vat["says excluding"] += 1
    elif re.search(r"ש\"?ח", t):
        vat["prices with no VAT wording"] += 1
findings["vat_wording"] = dict(vat)


# ------------------------------------------------------ duplicate content ---
def shingles(text, n=8):
    w = text.split()
    return {" ".join(w[i:i + n]) for i in range(0, max(1, len(w) - n), 3)}


city = [p["path"] for p in pages if p["path"].startswith("/טכנאי-מזגנים-ב")]
sh = {c: shingles(TEXT[c]) for c in city}
pairs = []
for i, a in enumerate(city):
    for b in city[i + 1:]:
        if not sh[a] or not sh[b]:
            continue
        j = len(sh[a] & sh[b]) / len(sh[a] | sh[b])
        if j > 0.45:
            pairs.append({"a": a, "b": b, "overlap": round(j * 100)})
pairs.sort(key=lambda x: -x["overlap"])
findings["near_duplicate_city_pages"] = {
    "city_pages": len(city),
    "pairs_over_45pct": len(pairs),
    "worst": pairs[:12],
}

# blocks of copy repeated verbatim on many pages
para = collections.Counter()
for p in pages:
    for b in p["blocks"]:
        if b.get("type") == "paragraph":
            t = plain(b["html"])
            if len(t) > 140:
                para[t] += 1
findings["boilerplate_paragraphs"] = [
    {"pages": n, "text": t[:190]} for t, n in para.most_common(8) if n > 5]


# ------------------------------------------------------------- thin pages ---
findings["thin_pages"] = [
    {"path": k, "words": v} for k, v in sorted(WORDS.items(), key=lambda x: x[1])[:10]]
findings["word_count"] = {
    "median": sorted(WORDS.values())[len(WORDS) // 2],
    "min": min(WORDS.values()), "max": max(WORDS.values()),
}


# ---------------------------------------------------------- stale content ---
years = collections.Counter()
stale = []
for p in pages:
    for y in re.findall(r"\b(20\d\d)\b", TEXT[p["path"]] + " " + (p.get("meta_title") or "")):
        years[y] += 1
        if int(y) < 2026:
            stale.append({"path": p["path"], "year": y})
findings["years_mentioned"] = dict(sorted(years.items()))
findings["pages_naming_a_past_year"] = stale[:15]

# claims that should agree everywhere
claims = collections.Counter()
for p in pages:
    for m in re.findall(r"(\d{1,2})\s*שנ(?:ה|ים)\s*(?:של\s*)?(?:ניסיון|נסיון|בתחום|בענף)", TEXT[p["path"]]):
        claims["%s שנות ניסיון" % m] += 1
findings["experience_claims"] = dict(claims)


# --------------------------------------------------------------- spelling ---
freq = collections.Counter()
where = collections.defaultdict(set)
for p in pages:
    for w in re.findall(r"[֐-׿\"']{3,}", TEXT[p["path"]]):
        freq[w] += 1
        where[w].add(p["path"])
common = {w for w, c in freq.items() if c >= 15}


def ed1(a, b):
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


suspect = []
for w, c in freq.items():
    if c > 2 or len(w) < 4:
        continue
    for cw in common:
        if freq[cw] >= 40 and ed1(w, cw):
            suspect.append({"word": w, "uses": c, "looks_like": cw,
                            "where": sorted(where[w])[:2]})
            break
findings["spelling_suspects"] = sorted(suspect, key=lambda x: x["word"])[:40]

# double words and spacing that survived
patterns = {
    "מילה כפולה": r"\b([֐-׿]{2,})\s+\1\b",
    "רווח לפני סימן פיסוק": r"\s+[,.!?]",
    "שלוש נקודות/סימנים": r"[!?]{2,}",
}
misc = collections.Counter()
misc_ex = collections.defaultdict(list)
for p in pages:
    for label, rx in patterns.items():
        for m in re.finditer(rx, TEXT[p["path"]]):
            misc[label] += 1
            if len(misc_ex[label]) < 3:
                misc_ex[label].append({"path": p["path"], "text": m.group(0)[:60]})
findings["punctuation_and_repeats"] = {k: {"count": v, "examples": misc_ex[k]}
                                       for k, v in misc.items()}


# ------------------------------------------------------------- structure ----
titles = collections.Counter(p.get("meta_title") or "" for p in pages)
descs = collections.Counter(p.get("meta_description") or "" for p in pages)
findings["duplicate_titles"] = [{"title": t, "count": n} for t, n in titles.items() if n > 1]
findings["duplicate_descriptions"] = [{"count": n, "text": d[:120]} for d, n in descs.items() if n > 1]
findings["long_titles"] = [{"path": p["path"], "chars": len(p["meta_title"] or ""),
                            "title": p["meta_title"]}
                           for p in pages if len(p.get("meta_title") or "") > 62]
findings["long_descriptions"] = [{"path": p["path"], "chars": len(p["meta_description"] or "")}
                                 for p in pages if len(p.get("meta_description") or "") > 165]

h2_counts = []
for p in pages:
    h2 = [b for b in p["blocks"] if b["type"] == "heading" and b["level"] == 2]
    h2_counts.append((p["path"], len(h2)))
findings["heading_load"] = {
    "median_h2_per_page": sorted(c for _, c in h2_counts)[len(h2_counts) // 2],
    "most_h2": [{"path": a, "h2": b} for a, b in sorted(h2_counts, key=lambda x: -x[1])[:5]],
}

faq_pages = sum(1 for p in pages if any(b["type"] == "faq" for b in p["blocks"]))
findings["coverage"] = {
    "pages": len(pages),
    "with_faq": faq_pages,
    "without_faq": len(pages) - faq_pages,
    "with_tables": sum(1 for p in pages if any(b["type"] == "table" for b in p["blocks"])),
    "with_images": sum(1 for p in pages if any(b["type"] == "image" for b in p["blocks"])),
    "without_images": sum(1 for p in pages if not any(b["type"] == "image" for b in p["blocks"])),
}

json.dump(findings, open(os.path.join(ROOT, "content-audit.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

for key, val in findings.items():
    if isinstance(val, list):
        print("%-32s %d" % (key, len(val)))
    elif isinstance(val, dict):
        print("%-32s %s" % (key, json.dumps(val, ensure_ascii=False)[:110]))
print("\nwritten: content-audit.json")
