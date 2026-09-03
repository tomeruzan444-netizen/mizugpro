# -*- coding: utf-8 -*-
"""
Weekly SEO audit of the live site.

Crawls https://mizugpro.co.il exactly as a search engine would and writes a
Hebrew report to seo-reports/. It reads nothing from this repo on purpose:
what matters is what visitors and Google actually receive, which is not always
what the last build produced.

    python seo_audit.py                       # live site
    python seo_audit.py https://new.mizugpro.co.il

Findings are graded by what they cost:
    critical  traffic or leads are being lost right now
    warn      a real weakness, worth fixing this month
    idea      a way to grow
"""
import collections
import datetime
import json
import os
import re
import sys
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

SITE = (sys.argv[1] if len(sys.argv) > 1 else "https://mizugpro.co.il").rstrip("/")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seo-reports")

DELAY = float(os.environ.get("AUDIT_DELAY", "0.4"))
TIMEOUT = 30

# Things that look like defects but are deliberate. Without this list the
# report cries wolf every week and stops being read.
KNOWN_GOOD = {
    "noindex_ok": {"/thank-you/"},
    "orphan_ok": {"/thank-you/"},
    # this page quotes the electricity tariff, which really does include VAT
    "vat_including_ok": {"/כמה-עולה-מזגן-לשעה/"},
}

TITLE_MAX = 60
DESC_MAX = 155
DESC_MIN = 70
THIN_WORDS = 250

session = requests.Session()
session.headers.update({
    "User-Agent": "mizugpro-seo-audit/1.0 (+https://mizugpro.co.il)",
    "Accept-Language": "he-IL,he;q=0.9",
})


def get(url):
    """Fetch a URL, forcing UTF-8.

    requests guesses ISO-8859-1 when a server omits the charset, which turns
    every Hebrew page into mojibake and makes every text check below silently
    wrong. This is the single most important line in the file.
    """
    t0 = time.time()
    r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    r.encoding = "utf-8"
    r.elapsed_s = time.time() - t0
    return r


def norm(href, base):
    """Absolute, on-site, fragment-free path — or None if it leaves the site."""
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    u = urllib.parse.urljoin(base, href)
    parts = urllib.parse.urlsplit(u)
    if parts.netloc and parts.netloc != urllib.parse.urlsplit(SITE).netloc:
        return None
    path = urllib.parse.unquote(parts.path)
    if not path.startswith("/"):
        return None
    return path


def blocks_of(soup):
    """Split <main> into top-level blocks, each as a list of lines.

    Lines rather than one flat string: a doubled-word check on flattened text
    reports "מזגן מזגן" every time two link labels happen to sit side by side,
    which is a layout accident and not a typo.
    """
    main = soup.find("main") or soup.body or soup
    clone = BeautifulSoup(str(main), "html.parser")
    for t in clone.find_all(["script", "style", "aside", "nav", "header", "footer", "form"]):
        t.decompose()
    root = clone.find("main") or clone

    out = []
    children = [c for c in root.find_all(recursive=False)] or [root]
    for el in children:
        lines = [re.sub(r"\s+", " ", s).strip() for s in el.get_text("\n").split("\n")]
        lines = [l for l in lines if l]
        if lines:
            out.append(lines)
    return out


def strip_boilerplate(pages):
    """Drop blocks that repeat across the site before judging any page's copy.

    Reviews, service areas, "קראו גם" and the contact block appear on every
    page. Counted as content they inflate every page's word count and make
    unrelated pages look like near-duplicates of each other. Rather than name
    them by class — which the next redesign would break — find them by the fact
    that they are identical almost everywhere.
    """
    html_pages = [r for r in pages.values() if r.get("blocks")]
    if not html_pages:
        return
    seen = collections.Counter()
    for r in html_pages:
        for b in r["blocks"]:
            seen[hash(" ".join(b))] += 1
    cutoff = max(3, int(len(html_pages) * 0.4))

    for r in html_pages:
        kept = [b for b in r["blocks"] if seen[hash(" ".join(b))] < cutoff]
        r["lines"] = [l for b in kept for l in b]
        r["text"] = " ".join(r["lines"])
        r["words"] = len(r["text"].split())
        del r["blocks"]


# ----------------------------------------------------------------- crawl ----
def sitemap_urls():
    r = get(SITE + "/sitemap.xml")
    if r.status_code != 200:
        return []
    soup = BeautifulSoup(r.text, "xml")
    urls = [loc.get_text(strip=True) for loc in soup.find_all("loc")]
    # a sitemap index points at more sitemaps
    if urls and all(u.endswith(".xml") for u in urls):
        nested = []
        for u in urls:
            rr = get(u)
            if rr.status_code == 200:
                nested += [l.get_text(strip=True)
                           for l in BeautifulSoup(rr.text, "xml").find_all("loc")]
            time.sleep(DELAY)
        urls = nested
    return urls


def crawl():
    urls = sitemap_urls()
    pages = {}
    for i, url in enumerate(urls, 1):
        path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
        try:
            r = get(url)
        except Exception as e:
            pages[path] = {"path": path, "error": str(e)[:120], "status": 0}
            continue
        rec = {
            "path": path,
            "status": r.status_code,
            "bytes": len(r.content),
            "seconds": round(r.elapsed_s, 2),
            "redirected_to": (urllib.parse.unquote(urllib.parse.urlsplit(r.url).path)
                              if r.url.rstrip("/") != url.rstrip("/") else None),
        }
        if r.status_code == 200 and "html" in r.headers.get("Content-Type", ""):
            soup = BeautifulSoup(r.text, "html.parser")
            rec.update(parse(soup, url))
        pages[path] = rec
        if i % 20 == 0:
            print("  crawled %d/%d" % (i, len(urls)), file=sys.stderr)
        time.sleep(DELAY)
    strip_boilerplate(pages)
    return pages


def parse(soup, url):
    title = soup.title.get_text(strip=True) if soup.title else ""
    desc = soup.find("meta", attrs={"name": "description"})
    robots = soup.find("meta", attrs={"name": "robots"})
    canon = soup.find("link", rel=lambda v: v and "canonical" in v)
    h1s = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]

    schema, schema_bad, types = [], [], []
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = tag.string or tag.get_text() or ""
        try:
            data = json.loads(raw)
        except Exception as e:
            schema_bad.append(str(e)[:80])
            continue
        schema.append(data)
        for node in (data if isinstance(data, list) else [data]):
            if isinstance(node, dict):
                t = node.get("@type")
                types += t if isinstance(t, list) else [t] if t else []

    imgs = soup.find_all("img")
    # alt="" is a decision, not an omission: it marks an image as decorative so
    # a screen reader skips it, which is right for the agency mark sitting next
    # to its own name in the footer. Only a missing alt attribute is a fault.
    no_alt = [i.get("src", "")[:90] for i in imgs
              if i.get("alt") is None and i.get("role") != "presentation"]

    links = set()
    for a in soup.find_all("a", href=True):
        p = norm(a["href"], url)
        if p:
            links.add(p)

    return {
        "title": title,
        "description": desc.get("content", "").strip() if desc else "",
        "robots": robots.get("content", "").strip() if robots else "",
        "canonical": urllib.parse.unquote(canon.get("href", "")) if canon else "",
        "h1": h1s,
        "schema_types": sorted(set(types)),
        "schema_errors": schema_bad,
        "images": len(imgs),
        "images_no_alt": no_alt,
        "links": sorted(links),
        "blocks": blocks_of(soup),
    }


# -------------------------------------------------------------- analysis ----
def shingles(text, n=8, step=3):
    w = text.split()
    return {" ".join(w[i:i + n]) for i in range(0, max(1, len(w) - n), step)}


# "בין 250 ל- 400 ש\"ח" is a range, but the hyphen belongs to the word ל־
# and not to the range, so the plain form read it as a single price of
# 400 and reported a contradiction against pages that agreed with it.
PRICE = re.compile(
    r"בין\s*(?P<lo2>\d[\d,]{1,6})\s*ל[-־]?\s*(?P<hi2>\d[\d,]{1,6})\s*ש\"?ח"
    r"|(\d[\d,]{1,6})\s*(?:–|-|עד)\s*(\d[\d,]{1,6})\s*ש\"?ח"
    r"|(\d[\d,]{1,6})\s*ש\"?ח")
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

# spelling and wording that has bitten this site before
TYPOS = [
    (r"סתימה סתימה", "כפילות: «סתימה סתימה»"),
    (r"\bמזגן מזגן\b", "כפילות: «מזגן מזגן»"),
    (r"\bאת את\b", "כפילות: «את את»"),
    (r"\bשל של\b", "כפילות: «של של»"),
    (r"\bב ב\b", "כפילות: «ב ב»"),
    (r"אלוף הגגות|דודים וחוסכים|roofscha", "שם מותג זר שנשאר מהאתר המקורי"),
    (r"lorem ipsum", "טקסט ממלא שנשאר בעמוד"),
    (r"\[…\]|\.\.\.$", "משפט שנקטע"),
]


def analyse(pages, live_version):
    live = {p: r for p, r in pages.items() if r.get("status") == 200 and "title" in r}
    crit, warn, idea = [], [], []

    def add(bucket, kind, detail, urls, fix):
        bucket.append({"kind": kind, "detail": detail,
                       "urls": urls[:12], "more": max(0, len(urls) - 12), "fix": fix})

    # --- pages that do not answer -------------------------------------------
    dead = [p for p, r in pages.items() if r.get("status") not in (200,)]
    if dead:
        add(crit, "עמודים שלא נענים",
            "עמודים שמופיעים ב-sitemap אך מחזירים סטטוס שאינו 200. גוגל מוריד אותם מהאינדקס.",
            ["%s — %s" % (p, pages[p].get("status") or pages[p].get("error")) for p in dead],
            "או להחזיר את העמוד, או להסיר אותו מה-sitemap ולהפנות 301 לעמוד הקרוב ביותר.")

    redirected = [p for p, r in pages.items() if r.get("redirected_to")]
    if redirected:
        add(warn, "כתובות ב-sitemap שמפנות הלאה",
            "ה-sitemap צריך להצביע על היעד הסופי; הפניה מבזבזת תקציב סריקה.",
            ["%s → %s" % (p, pages[p]["redirected_to"]) for p in redirected],
            "עדכן את ה-sitemap לכתובת הסופית.")

    # --- titles --------------------------------------------------------------
    by_title = collections.defaultdict(list)
    for p, r in live.items():
        by_title[r["title"]].append(p)
    dup_titles = {t: ps for t, ps in by_title.items() if t and len(ps) > 1}
    if dup_titles:
        add(crit, "כותרות כפולות",
            "כשכמה עמודים חולקים אותה כותרת, גוגל בוחר אחד מהם ומדכא את השאר.",
            ["«%s» — %s" % (t, ", ".join(ps)) for t, ps in dup_titles.items()],
            "כתוב לכל עמוד כותרת ייחודית סביב הביטוי שהוא מכוון אליו.")

    no_title = [p for p, r in live.items() if not r["title"]]
    if no_title:
        add(crit, "עמודים בלי כותרת", "אין <title> — גוגל ימציא אחת.", no_title,
            "הוסף כותרת ייחודית.")

    long_titles = [(p, r["title"]) for p, r in live.items()
                   if len(r["title"]) > TITLE_MAX]
    if long_titles:
        add(warn, "כותרות ארוכות מדי",
            "מעל ~%d תווים גוגל חותך את הכותרת בתוצאות." % TITLE_MAX,
            ["%s (%d תווים) — %s" % (p, len(t), t) for p, t in long_titles],
            "קצר לכדי %d תווים והשאר את הביטוי המרכזי בהתחלה." % TITLE_MAX)

    # --- descriptions --------------------------------------------------------
    by_desc = collections.defaultdict(list)
    for p, r in live.items():
        if r["description"]:
            by_desc[r["description"]].append(p)
    dup_desc = {d: ps for d, ps in by_desc.items() if len(ps) > 1}
    if dup_desc:
        add(warn, "תיאורי מטא כפולים",
            "תיאור זהה בכמה עמודים מחליש את הקליקביליות של כולם.",
            ["%d עמודים: %s" % (len(ps), ", ".join(ps[:4])) for ps in dup_desc.values()],
            "כתוב תיאור ייחודי לכל עמוד.")

    no_desc = [p for p, r in live.items() if not r["description"]]
    if no_desc:
        add(warn, "עמודים בלי תיאור מטא",
            "בלי תיאור, גוגל מרכיב קטע מהטקסט — לרוב פחות משכנע.", no_desc,
            "הוסף תיאור של 120–155 תווים שכולל את הביטוי וקריאה לפעולה.")

    long_desc = [(p, len(r["description"])) for p, r in live.items()
                 if len(r["description"]) > DESC_MAX]
    if long_desc:
        add(warn, "תיאורי מטא ארוכים מדי",
            "מעל ~%d תווים התיאור נחתך." % DESC_MAX,
            ["%s (%d תווים)" % (p, n) for p, n in long_desc],
            "קצר ל-%d תווים." % DESC_MAX)

    # --- H1 ------------------------------------------------------------------
    no_h1 = [p for p, r in live.items() if not r["h1"]]
    if no_h1:
        add(crit, "עמודים בלי H1", "אין כותרת ראשית בגוף העמוד.", no_h1,
            "הוסף H1 יחיד שמכיל את הביטוי המרכזי.")

    many_h1 = [(p, len(r["h1"])) for p, r in live.items() if len(r["h1"]) > 1]
    if many_h1:
        add(warn, "יותר מ-H1 אחד",
            "כמה H1 מפזרים את האות על מה העמוד.",
            ["%s (%d)" % (p, n) for p, n in many_h1],
            "השאר H1 אחד; הפוך את השאר ל-H2.")

    # --- indexability --------------------------------------------------------
    noindexed = [p for p, r in live.items()
                 if "noindex" in r["robots"].lower()
                 and p not in KNOWN_GOOD["noindex_ok"]]
    if noindexed:
        add(crit, "עמודים חסומים לאינדוקס",
            "meta robots=noindex — העמוד לא יופיע בגוגל כלל.", noindexed,
            "אם העמוד אמור לדרג, הסר את ה-noindex.")

    bad_canon = [(p, r["canonical"]) for p, r in live.items()
                 if r["canonical"] and urllib.parse.unquote(
                     urllib.parse.urlsplit(r["canonical"]).path).rstrip("/") != p.rstrip("/")]
    if bad_canon:
        add(crit, "canonical שמצביע על עמוד אחר",
            "העמוד מוותר על עצמו לטובת כתובת אחרת ולא ידורג.",
            ["%s → %s" % (p, c) for p, c in bad_canon],
            "ודא שכל עמוד מצביע על עצמו, אלא אם הכפילות מכוונת.")

    no_canon = [p for p, r in live.items() if not r["canonical"]]
    if no_canon:
        add(warn, "עמודים בלי canonical", "חושף לכפילויות מפרמטרים בכתובת.",
            no_canon, "הוסף <link rel=canonical> שמצביע על העמוד עצמו.")

    # --- internal linking ----------------------------------------------------
    inbound = collections.Counter()
    for p, r in live.items():
        for target in r["links"]:
            if target.rstrip("/") != p.rstrip("/"):
                inbound[target.rstrip("/")] += 1
    orphans = [p for p in live
               if inbound[p.rstrip("/")] == 0 and p not in KNOWN_GOOD["orphan_ok"]]
    if orphans:
        add(crit, "עמודים יתומים",
            "אף עמוד באתר לא מקשר אליהם. גוגל מגיע אליהם רק דרך ה-sitemap ומדרג אותם נמוך.",
            orphans,
            "הוסף לכל אחד לפחות שני קישורים פנימיים מעמודים רלוונטיים.")

    known = {p.rstrip("/") for p in pages}
    broken = collections.defaultdict(list)
    for p, r in live.items():
        for target in r["links"]:
            if target.rstrip("/") not in known and not re.search(r"\.\w{2,4}$", target):
                broken[target].append(p)
    if broken:
        checked = {}
        for target in list(broken)[:40]:
            try:
                checked[target] = get(SITE + urllib.parse.quote(target)).status_code
            except Exception:
                checked[target] = 0
            time.sleep(DELAY)
        dead_links = {t: srcs for t, srcs in broken.items() if checked.get(t, 200) >= 400}
        if dead_links:
            add(crit, "קישורים פנימיים שבורים",
                "קישורים בגוף האתר שמובילים לעמוד שלא קיים.",
                ["%s (מ-%s)" % (t, ", ".join(s[:3])) for t, s in dead_links.items()],
                "תקן את הכתובת או הסר את הקישור.")

    weak = sorted([(inbound[p.rstrip("/")], p) for p in live
                   if 0 < inbound[p.rstrip("/")] <= 2
                   and p not in KNOWN_GOOD["orphan_ok"]])
    if weak:
        add(idea, "עמודים עם קישוריות פנימית דלה",
            "קישור פנימי אחד או שניים בלבד — מעט מאוד סמכות מגיעה אליהם.",
            ["%s (%d קישורים נכנסים)" % (p, n) for n, p in weak],
            "שלב אותם בטקסט של עמודים קרובים בנושא.")

    # --- structured data -----------------------------------------------------
    schema_broken = [(p, r["schema_errors"]) for p, r in live.items() if r["schema_errors"]]
    if schema_broken:
        add(crit, "סכמה (JSON-LD) לא תקינה",
            "בלוק שלא נפרס — גוגל מתעלם ממנו ותוצאות עשירות נעלמות.",
            ["%s — %s" % (p, "; ".join(e)) for p, e in schema_broken],
            "תקן את ה-JSON ובדוק ב-Rich Results Test.")

    no_schema = [p for p, r in live.items() if not r["schema_types"]]
    if no_schema:
        add(warn, "עמודים בלי סכמה", "אין נתונים מובנים כלל.", no_schema,
            "הוסף לפחות WebPage + BreadcrumbList.")

    # --- content -------------------------------------------------------------
    thin = sorted([(r["words"], p) for p, r in live.items() if r["words"] < THIN_WORDS])
    if thin:
        add(warn, "עמודים דלים בתוכן",
            "פחות מ-%d מילים. קשה לדרג על ביטוי תחרותי." % THIN_WORDS,
            ["%s (%d מילים)" % (p, n) for n, p in thin],
            "הרחב עם שאלות נפוצות, מחירים ודוגמאות מהשטח.")

    sh = {p: shingles(r["text"]) for p, r in live.items() if r["words"] > 120}
    dup_pairs = []
    keys = sorted(sh)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if not sh[a] or not sh[b]:
                continue
            j = len(sh[a] & sh[b]) / len(sh[a] | sh[b])
            if j > 0.45:
                dup_pairs.append((round(j * 100), a, b))
    dup_pairs.sort(reverse=True)
    if dup_pairs:
        add(crit, "עמודים כמעט זהים",
            "טקסט חופף בין עמודים — גוגל בוחר אחד ומדכא את השני.",
            ["%s ↔ %s (%d%% חפיפה)" % (a, b, o) for o, a, b in dup_pairs],
            "כתוב לכל עמוד פסקאות ייחודיות: שכונות, זמני הגעה, מקרים מהשטח.")

    # --- images --------------------------------------------------------------
    alt_missing = [(p, len(r["images_no_alt"])) for p, r in live.items()
                   if r["images_no_alt"]]
    if alt_missing:
        total = sum(n for _, n in alt_missing)
        add(warn, "תמונות בלי טקסט חלופי",
            "%d תמונות ב-%d עמודים. פוגע בנגישות ובחיפוש תמונות." % (total, len(alt_missing)),
            ["%s (%d תמונות)" % (p, n) for p, n in sorted(alt_missing, key=lambda x: -x[1])],
            "הוסף alt שמתאר את התמונה בעברית.")

    # --- prices --------------------------------------------------------------
    price_map = collections.defaultdict(list)
    for p, r in live.items():
        for label, rx in SERVICES.items():
            for m in re.finditer(rx + r"[^.!?\n]{0,80}", r["text"]):
                pm = PRICE.search(m.group(0))
                if not pm:
                    continue
                # groups: 1-2 the Hebrew "בין X ל Y" form, 3-4 the plain
                # X - Y form, 5 a lone figure. Take whichever matched.
                g = pm.groups()
                lo = g[0] or g[2]
                hi = g[1] or g[3]
                one = g[4]
                cut = lambda v: int(v.replace(",", ""))
                rng = (cut(lo), cut(hi)) if lo else (cut(one), cut(one))
                if 30 <= rng[0] <= 100000:
                    price_map[label].append((p, rng))
    # A price table on a single page legitimately lists several figures for
    # different unit sizes, so only disagreement *between* pages is a defect.
    contradictions = []
    for label, entries in price_map.items():
        per_page = collections.defaultdict(set)
        for p, rng in entries:
            per_page[p].add(rng)
        headline = {p: min(rs) for p, rs in per_page.items()}
        distinct = collections.defaultdict(list)
        for p, rng in headline.items():
            distinct[rng].append(p)
        if len(distinct) > 1:
            shown = sorted(distinct.items())
            contradictions.append("%s — %s" % (label, " · ".join(
                "‎%d–%d ב-%d עמודים (%s)" % (r[0], r[1], len(ps), ps[0])
                for r, ps in shown)))
    if contradictions:
        add(crit, "מחירים סותרים בין עמודים",
            "אותו שירות מתומחר אחרת בעמודים שונים. פוגע באמון ובלידים.",
            contradictions,
            "החלט על טווח אחד לכל שירות והחל אותו בכל העמודים.")

    # --- spelling and staleness ---------------------------------------------
    typo_hits = []
    for p, r in live.items():
        for rx, label in TYPOS:
            for line in r["lines"]:
                m = re.search(rx, line, re.I)
                if m:
                    ctx = line[max(0, m.start() - 50):m.end() + 50]
                    typo_hits.append("%s — %s: …%s…" % (p, label, ctx))
                    break
    if typo_hits:
        add(warn, "שגיאות כתיב וניסוח", "דפוסים שאותרו בטקסט החי.", typo_hits,
            "תקן ב-build/content_fixes.py כדי שהתיקון יישמר בבנייה הבאה.")

    # --- a city page that names the wrong city -------------------------------
    # The usual cause is a page built by copying its neighbour, and it is
    # expensive: the title is what a searcher reads before deciding to click.
    CITY_PATH = re.compile(r"^/טכנאי-מזגנים-ב?(.+?)/$")
    cities = {}
    for p in live:
        m = CITY_PATH.match(p)
        if m:
            cities[p] = m.group(1).replace("-", " ")
    # a region is a legitimate thing for a city page to mention — "גרים באזור
    # המרכז וצריכים טכנאי בהרצליה?" is correct copy, not a mix-up
    REGIONS = {"מרכז", "צפון", "דרום", "שרון", "שפלה", "ירושלים והסביבה"}
    others = {c for c in cities.values() if len(c) >= 3 and c not in REGIONS}

    def names(city, value):
        """Does `value` name this city?

        \\b is useless here: Hebrew glues its prepositions onto the noun, so in
        "התקנה באלעד" there is no word boundary before אלעד. Allow one attached
        prefix letter instead, and require a non-Hebrew character on each side.
        """
        HEB = r"֐-׿"
        return re.search(r"(?<![%s])[בלמהושכ]?%s(?![%s])"
                         % (HEB, re.escape(city), HEB), value)

    wrong_city = []
    for p, own in cities.items():
        r = live[p]
        for field, label in (("title", "כותרת"), ("description", "תיאור מטא")):
            value = r[field]
            if not value:
                continue
            named = {c for c in others if c != own and names(c, value)}
            # "רמת גן" contains "גן"; only a city the page is not about counts
            named = {c for c in named if c not in own and own not in c}
            if named:
                wrong_city.append("%s — ה%s מזכירה «%s» במקום «%s»: %s"
                                  % (p, label, ", ".join(sorted(named)), own, value))
    # "בבקדימה צורן" — the preposition typed onto a name that already carries it
    doubled = []
    for p, own in cities.items():
        for field, label in (("title", "כותרת"), ("description", "תיאור מטא"),
                             ("h1", "H1")):
            value = live[p][field]
            value = " ".join(value) if isinstance(value, list) else value
            m = re.search(r"[בלמהושכ]{2}%s" % re.escape(own), value or "")
            if m:
                doubled.append("%s — ב%s: «%s»" % (p, label, m.group(0)))
    if doubled:
        add(warn, "כפל אות יחס לפני שם העיר",
            "אות היחס הוקלדה פעמיים. נראה כמו שגיאת הקלדה בתוצאות החיפוש.",
            doubled, "הסר את האות הכפולה.")

    if wrong_city:
        add(crit, "עמוד עיר שמזכיר עיר אחרת",
            "העמוד מכוון לעיר אחת אך הטקסט שגוגל מציג מדבר על עיר אחרת. "
            "הגולש רואה עיר לא רלוונטית ולא מקליק.",
            wrong_city,
            "החלף לשם העיר הנכון בכותרת, בתיאור וב-H1.")

    year = datetime.date.today().year
    stale = []
    for p, r in live.items():
        for m in re.finditer(r"\b(20[12]\d)\b", r["text"]):
            y = int(m.group(1))
            if y < year - 1:
                ctx = r["text"][max(0, m.start() - 60):m.end() + 40]
                if re.search(r"נכון ל|מחירון|עדכני|השנה|לשנת", ctx):
                    stale.append("%s — %d: …%s…" % (p, y, ctx))
                    break
    if stale:
        add(warn, "תוכן שהתיישן",
            "שנה שעברה מוצגת כעדכנית. פוגע באמון ובאיתות הרעננות לגוגל.", stale,
            "החלף בניסוח שלא מתיישן, או עדכן לשנה הנוכחית בכל בנייה.")

    # --- weight and speed ----------------------------------------------------
    heavy = sorted([(r["bytes"], p) for p, r in live.items()
                    if r["bytes"] > 300_000], reverse=True)
    if heavy:
        add(warn, "עמודים כבדים",
            "מעל 300KB של HTML. פוגע ב-LCP ובמובייל.",
            ["%s (%d KB)" % (p, n // 1024) for n, p in heavy],
            "בדוק תמונות משובצות וטבלאות ארוכות.")

    slow = sorted([(r["seconds"], p) for p, r in live.items()
                   if r["seconds"] > 1.5], reverse=True)
    if slow:
        add(warn, "עמודים איטיים",
            "זמן תגובה מעל 1.5 שניות במדידה הזו.",
            ["%s (%.2f שניות)" % (p, s) for s, p in slow],
            "בדוק קאש ב-LiteSpeed; ייתכן שהמדידה תפסה קאש קר.")

    # --- deploy freshness ----------------------------------------------------
    if live_version:
        built = live_version.get("built_at", "")
        try:
            when = datetime.datetime.strptime(built, "%Y-%m-%dT%H:%M:%SZ")
            age = (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - when).days
            if age > 7:
                add(warn, "האתר החי לא נבנה מחדש",
                    "הבנייה החיה היא מ-%s (%d ימים). תיקונים שנעשו מאז לא הגיעו לאוויר."
                    % (built, age), ["/version.json — commit %s" % live_version.get("short")],
                    "הרץ Deploy ב-hPanel, או בדוק שה-webhook של הוסטינגר מחובר.")
        except ValueError:
            pass
    else:
        add(warn, "אין version.json באתר החי",
            "אי אפשר לדעת איזו גרסה באוויר.", ["/version.json"],
            "ודא שהבנייה כותבת את הקובץ ושהוא נפרס.")

    # --- opportunities -------------------------------------------------------
    # a FAQ belongs on a page someone is shopping on, not on the about page
    NOT_COMMERCIAL = re.compile(
        r"^/(אודות|הצהרת-נגישות|מדיניות|תנאי|צור-קשר|הממליצים|בלוג|category|thank-you)")
    without_faq = [p for p, r in live.items()
                   if "FAQPage" not in r["schema_types"]
                   and r["words"] > 400
                   and not NOT_COMMERCIAL.match(p)]
    if without_faq:
        add(idea, "עמודים ארוכים בלי מקטע שאלות נפוצות",
            "FAQ מוסיף תוצאות עשירות ותופס שאילתות של שאלה ישירה.", without_faq,
            "הוסף 4–6 שאלות אמיתיות שלקוחות שואלים, עם סכמת FAQPage.")

    return {"critical": crit, "warn": warn, "idea": idea,
            "inbound": inbound, "live": live}


# ----------------------------------------------------------------- report ---
def render(pages, res, live_version, previous):
    live = res["live"]
    today = datetime.date.today().isoformat()
    n = len(live)

    metrics = {
        "date": today,
        "pages_crawled": len(pages),
        "pages_ok": n,
        "avg_words": round(sum(r["words"] for r in live.values()) / max(1, n)),
        "orphans": sum(1 for p in live if res["inbound"][p.rstrip("/")] == 0
                       and p not in KNOWN_GOOD["orphan_ok"]),
        "duplicate_titles": n - len({r["title"] for r in live.values()}),
        "missing_desc": sum(1 for r in live.values() if not r["description"]),
        "images_no_alt": sum(len(r["images_no_alt"]) for r in live.values()),
        "schema_errors": sum(len(r["schema_errors"]) for r in live.values()),
        "critical": len(res["critical"]),
        "warn": len(res["warn"]),
        "idea": len(res["idea"]),
        "live_commit": (live_version or {}).get("short", "?"),
    }

    L = []
    L.append("# ביקורת SEO שבועית — מיזוג פרו")
    L.append("")
    L.append("**תאריך:** %s  •  **נסרקו:** %d עמודים  •  **גרסה חיה:** `%s`"
             % (today, len(pages), metrics["live_commit"]))
    L.append("")

    # headline
    L.append("## מה חשוב לעשות השבוע")
    L.append("")
    top = (res["critical"] + res["warn"])[:5]
    if not top:
        L.append("לא נמצאו תקלות. האתר נקי בבדיקות של השבוע.")
    else:
        for f in top:
            L.append("- **%s** — %d מופעים. %s" % (f["kind"], len(f["urls"]) + f["more"], f["fix"]))
    L.append("")

    for bucket, icon, title in (("critical", "🔴", "שובר — עולה תנועה או לידים עכשיו"),
                                ("warn", "🟡", "שווה תיקון"),
                                ("idea", "🟢", "הזדמנויות")):
        items = res[bucket]
        if not items:
            continue
        L.append("## %s %s" % (icon, title))
        L.append("")
        for f in items:
            L.append("### %s" % f["kind"])
            L.append("")
            L.append(f["detail"])
            L.append("")
            for u in f["urls"]:
                L.append("- `%s`" % u)
            if f["more"]:
                L.append("- …ועוד %d" % f["more"])
            L.append("")
            L.append("**התיקון:** %s" % f["fix"])
            L.append("")

    # numbers, with last week beside them
    L.append("## המספרים")
    L.append("")
    L.append("| מדד | השבוע | שבוע שעבר |")
    L.append("|---|---|---|")
    labels = [("pages_ok", "עמודים תקינים"), ("avg_words", "ממוצע מילים לעמוד"),
              ("orphans", "עמודים יתומים"), ("duplicate_titles", "כותרות כפולות"),
              ("missing_desc", "בלי תיאור מטא"), ("images_no_alt", "תמונות בלי alt"),
              ("schema_errors", "שגיאות סכמה"), ("critical", "ממצאים שוברים"),
              ("warn", "ממצאים לתיקון")]
    for key, label in labels:
        now = metrics[key]
        was = previous.get(key) if previous else None
        if was is None:
            cell = "—"
        elif was == now:
            cell = str(was)
        else:
            cell = "%s (%s%d)" % (was, "+" if now > was else "", now - was)
        L.append("| %s | %s | %s |" % (label, now, cell))
    L.append("")
    L.append("---")
    L.append("")
    L.append("נוצר אוטומטית על ידי `build/seo_audit.py`. הביקורת קוראת רק — "
             "היא לא משנה דבר באתר.")
    return "\n".join(L), metrics


def main():
    os.makedirs(OUT, exist_ok=True)
    print("auditing", SITE, file=sys.stderr)

    try:
        r = get(SITE + "/version.json")
        live_version = r.json() if r.status_code == 200 else None
    except Exception:
        live_version = None

    pages = crawl()
    if not pages:
        print("no pages crawled — is the sitemap reachable?", file=sys.stderr)
        return 1

    prev_path = os.path.join(OUT, "metrics.json")
    previous = None
    if os.path.exists(prev_path):
        try:
            history = json.load(open(prev_path, encoding="utf-8"))
            previous = history[-1] if history else None
        except Exception:
            history = []
    else:
        history = []

    res = analyse(pages, live_version)
    report, metrics = render(pages, res, live_version, previous)

    name = "%s.md" % metrics["date"]
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(report)
    with open(os.path.join(OUT, "latest.md"), "w", encoding="utf-8") as fh:
        fh.write(report)

    history.append(metrics)
    with open(prev_path, "w", encoding="utf-8") as fh:
        json.dump(history[-52:], fh, ensure_ascii=False, indent=1)

    print("wrote seo-reports/%s — %d critical, %d warn, %d ideas"
          % (name, metrics["critical"], metrics["warn"], metrics["idea"]),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
