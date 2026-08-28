# -*- coding: utf-8 -*-
"""
Editorial corrections applied on top of the migrated copy.

Every rule here fixes a spelling slip, a punctuation defect or a factual /
logical error that exists on the live site. Wording, keywords and structure are
otherwise left exactly as they are. Each applied change is logged so the whole
diff can be reviewed.
"""
import re
from bs4 import BeautifulSoup, NavigableString

CHANGES = []


def _log(path, kind, before, after):
    CHANGES.append({"path": path, "rule": kind, "before": before, "after": after})


# --------------------------------------------------------------- text rules --
# (label, pattern, replacement)
TEXT_RULES = [
    # spelling
    ("מידי → מדי", re.compile(r"(גדול|קטן|יקר|זול|רב|רבה|הרבה|חם|קר|ארוך|קצר|מהר|מוקדם|מאוחר)\s+מידי"), r"\1 מדי"),
    ("מזגנן → מזגן", re.compile(r"מזגנן"), "מזגן"),
    ("מזגון → מזגן", re.compile(r"שירותי מזגון"), "שירותי מיזוג"),
    ("במזן → במזגן", re.compile(r"\bבמזן\b"), "במזגן"),
    ("ואמיi → ואמין", re.compile(r"ואמיi"), "ואמין"),
    ("אמיניים → אמינים", re.compile(r"אמיניים"), "אמינים"),
    ("איוורטר → אינוורטר", re.compile(r"(?<!א)איוורטר"), "אינוורטר"),
    ("והתרנה → וההתקנה", re.compile(r"והתרנה"), "וההתקנה"),
    ("טבלאת → טבלת", re.compile(r"\bטבלאת\b"), "טבלת"),
    # a different company's name left over from the template this site was cloned from
    ("מותג זר בתוכן", re.compile(r"דודים וחוסכים"), "מיזוג פרו"),
    ("מותג זר בתוכן", re.compile(r"אלוף הגגות"), "מיזוג פרו"),
    ("VRF באותיות גדולות", re.compile(r"(?<![A-Za-z])vrf(?![A-Za-z])"), "VRF"),
    ("ללמילוי → למילוי", re.compile(r"ללמילוי"), "למילוי"),
    ("איזור → אזור", re.compile(r"(?<![א-ת])([בלמכשוה]?)איזור"), "\g<1>אזור"),
    # a word repeated back to back is always a slip, never emphasis here
    ("מילה כפולה", re.compile(r"(?<![א-ת])([א-ת]{2,})\s+\1(?![א-ת])"), "\g<1>"),
    # the live site printed two different phone numbers; this is the wrong one
    ("מספר טלפון שגוי", re.compile(r"0?33820823"), "033820923"),
    ("פרוייקט → פרויקט", re.compile(r"פרוייקט"), "פרויקט"),
    # stray maqaf glued to a one-letter prefix: ב־מיזוג → במיזוג
    ("מקף מיותר", re.compile(r"(?<=[\s(])([בלמכשוה])־(?=[א-ת])"), r"\1"),
    # grammar
    ("במידה ו → אם", re.compile(r"במידה ו(?=[א-ת])"), "אם "),
    # punctuation
    ('כפל ש"ח', re.compile(r'ש"ח\s+ש"ח'), 'ש"ח'),
    ("רווח לפני נקודה", re.compile(r"\s+\.(\s|$)"), r".\1"),
    ("רווח אחרי נקודה", re.compile(r"([א-ת])\.([א-ת])"), r"\1. \2"),
    ("רווח אחרי פסיק", re.compile(r"([א-ת]),([א-ת])"), r"\1, \2"),
    ("רווח כפול", re.compile(r"  +"), " "),
]


def fix_text(value, path, label=""):
    """Apply the text rules to a bare string."""
    if not value:
        return value
    original = value
    for name, rx, repl in TEXT_RULES:
        new = rx.sub(repl, value)
        if new != value:
            _log(path, name, value[:150], new[:150])
            value = new
    return value if value != original else original


def fix_html(fragment, path):
    """Apply the text rules to the text nodes of an HTML fragment only."""
    if not fragment or not isinstance(fragment, str):
        return fragment
    soup = BeautifulSoup("<x-root>" + fragment + "</x-root>", "html.parser")
    root = soup.find("x-root")
    touched = False
    for node in list(root.descendants):
        if isinstance(node, NavigableString) and node.parent.name not in ("script", "style"):
            new = str(node)
            for name, rx, repl in TEXT_RULES:
                candidate = rx.sub(repl, new)
                if candidate != new:
                    _log(path, name, new.strip()[:150], candidate.strip()[:150])
                    new = candidate
            if new != str(node):
                node.replace_with(NavigableString(new))
                touched = True
    return root.decode_contents() if touched else fragment


# ------------------------------------------------------------- page rules ----
# Copy-paste leftovers: the אלעד page carries headings written for גן יבנה.
HEADING_REWRITES = {
    "/טכנאי-מזגנים-באלעד/": [
        ("התקנת מזגן בגן יבנה", "התקנת מזגן באלעד"),
        ("מחירון התקנת מזגנים בגן יבנה", "מחירון התקנת מזגנים באלעד"),
    ],
    "/טכנאי-מזגנים-בסביון/": [
        ("בסביון- מידע", "בסביון – מידע"),
    ],
}


def fix_schema(node, path):
    """Run the text rules over schema strings, leaving URLs and ids alone."""
    URL_KEYS = {"@id", "url", "contentUrl", "item", "target", "sameAs", "@type", "@context"}
    if isinstance(node, dict):
        return {k: (v if k in URL_KEYS else fix_schema(v, path)) for k, v in node.items()}
    if isinstance(node, list):
        return [fix_schema(v, path) for v in node]
    if isinstance(node, str) and not node.startswith(("http://", "https://")):
        return fix_text(node, path)
    return node

# One figure per service, so the site stops quoting itself differently.
#
# מילוי גז appeared five ways: 350–550, 400–1000, 500–700, and 450–650 on the
# shared price table that runs on 46 pages. The table figure is the site's own
# dominant, scope-stated number ("כולל טיפול ואיתור דליפה פשוטה"), so the loose
# quotes are aligned to it. The dedicated page keeps its 400–1,500 span, which
# it explicitly describes as covering every system type — that is a wider
# scope, not a contradiction. Change GAS_FILL_RANGE to reprice in one place.
GAS_FILL_RANGE = "450 – 650"

PRICE_ALIGNMENTS = {
    "/תיקון-מזגנים/": [
        (r"(מילוי גז מזגנים חדש</p></td><td>)350 – 550", r"\g<1>" + GAS_FILL_RANGE),
    ],
    "/מזגן-אלקטרה-1-כס/": [
        (r"המחירים כוללים מע", "המחירים אינם כוללים מע"),
    ],
    "/מזגן-לא-מחמם/": [
        (r"(<td>מילוי גז</td><td>)500-700", r"\g<1>450-650"),
    ],
    "/מזגן-מטפטף/": [
        (r"(<strong>מילוי גז:</strong>\s*)400-1000", r"\g<1>450-650"),
    ],
    "/מזגן-לא-מחמם/": [
        (r"טווחים ממוצעים \(כולל מע\"מ\)", 'טווחים ממוצעים (ללא מע"מ)'),
    ],
    "/המזגן-לא-מקרר/": [
        (r"(<td>בדיקה ומילוי גז</td><td>)250-350", r"\g<1>450-650"),
    ],
}

# Years that dated the page rather than citing a source. Citations with a year
# (electricity tariff, published studies) are left alone — a dated source is
# correct practice; a price list that calls 2022 models "the new ones" is not.
DATE_FIXES = {
    "/מחירון-מזגנים/": [
        (r"מהדגמים החדשים\s*[–-]\s*2022", "מהדגמים החדשים"),
        (r"דגם\s*2022\s*אינוורטר", "דגם אינוורטר"),
    ],
    "/התקנת-מזגן-3-כוח-סוס/": [
        (r"מעודכנים לשנת\s*2024", "מעודכנים לשנת 2026"),
    ],
}


# Titles that were copied from another page and never rewritten.
META_OVERRIDES = {
    "/טכנאי-מזגנים-גבעתיים/": {
        "meta_title": "טכנאי מזגנים גבעתיים | תיקון והתקנת מזגנים בגבעתיים | מיזוג פרו",
    },
    "/thank-you/": {
        "meta_title": "תודה שפניתם למיזוג פרו | נחזור אליכם בהקדם",
        "meta_description": "קיבלנו את הפנייה שלכם. טכנאי מיזוג פרו יחזור אליכם בהקדם. "
                            "לפנייה דחופה אפשר להתקשר אלינו ישירות.",
        # a thank-you page should never compete in search
        "robots": "noindex, follow",
    },
}

# The thank-you page opened with the generic site pitch ("need a new air
# conditioner?") and buried the actual acknowledgement further down — the wrong
# way round for someone who has just submitted the form.
THANK_YOU = "/thank-you/"
THANK_YOU_H1 = "תודה שהשארתם פרטים, מיד נחזור אליכם"
THANK_YOU_LEAD = ('<strong>טכנאי מיזוג פרו יחזור אליכם בהקדם.</strong> '
                  'לפנייה דחופה אפשר להתקשר אלינו ישירות.')


def rewrite_thank_you(page):
    if page["path"] != THANK_YOU:
        return page
    blocks = page["blocks"]
    if blocks and blocks[0].get("type") == "heading" and blocks[0].get("level") == 1:
        _log(THANK_YOU, "כותרת עמוד תודה", blocks[0]["text"], THANK_YOU_H1)
        blocks[0]["text"] = THANK_YOU_H1
        blocks[0]["html"] = THANK_YOU_H1
        page["h1"] = THANK_YOU_H1
    if len(blocks) > 1 and blocks[1].get("type") == "paragraph":
        _log(THANK_YOU, "פתיח עמוד תודה", _plain(blocks[1]["html"])[:90], _plain(THANK_YOU_LEAD))
        blocks[1]["html"] = THANK_YOU_LEAD
    # the old acknowledgement further down now just repeats the headline
    kept = []
    for b in blocks:
        if b.get("type") == "paragraph" and "תודה שיצרתם קשר" in _plain(b.get("html")):
            _log(THANK_YOU, "פסקה כפולה הוסרה", _plain(b["html"])[:90], "(הוסרה)")
            continue
        kept.append(b)
    page["blocks"] = kept
    return page


# Missing meta descriptions on the two blog listings.
META_ADDITIONS = {
    "/בלוג/": "הבלוג של מיזוג פרו — מדריכים, טיפים ומחירים בכל מה שקשור למזגנים: "
              "התקנה, תיקון, תחזוקה ובחירת המזגן הנכון לבית ולעסק.",
    "/category/בלוג/": "כל המאמרים והמדריכים של מיזוג פרו בנושא מזגנים ומיזוג אוויר — "
                       "התקנה, תיקון, ניקוי, מחירים והמלצות מקצועיות.",
}


def fix_price_range(block, path):
    """A price scale must ascend: low ≤ average ≤ high."""
    pts = block.get("points") or []
    if len(pts) != 3:
        return block
    nums = []
    for pt in pts:
        digits = re.sub(r"[^\d]", "", pt.get("value") or "")
        nums.append(int(digits) if digits else 0)
    if nums == sorted(nums) or 0 in nums:
        return block
    order = sorted(range(3), key=lambda i: nums[i])
    values = [pts[i]["value"] for i in order]
    before = " | ".join(pt["value"] for pt in pts)
    for pt, v in zip(pts, values):
        pt["value"] = v
    _log(path, "טווח מחירים לא עולה", before, " | ".join(values))
    return block


# A paragraph never legitimately ends on a connector — when it does, the
# sentence was split across two <p> tags in the page builder.
_DANGLING = re.compile(
    r"(?:^|\s)(או|ו|של|את|עם|גם|אל|על|כי|אם|אך|אבל|מן|בין|לפי|אצל|כמו|עד|לכל|בכל)$")


def _plain(fragment):
    return BeautifulSoup(fragment or "", "html.parser").get_text(" ", strip=True)


def merge_split_paragraphs(page):
    blocks, out, i = page["blocks"], [], 0
    while i < len(blocks):
        b = blocks[i]
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        if (b.get("type") == "paragraph" and nxt and nxt.get("type") == "paragraph"
                and _DANGLING.search(_plain(b.get("html")))):
            merged = b["html"].rstrip() + " " + nxt["html"].lstrip()
            _log(page["path"], "משפט שנחתך בין פסקאות",
                 _plain(b["html"])[-70:], _plain(merged)[-70:])
            out.append({**b, "html": merged})
            i += 2
            continue
        out.append(b)
        i += 1
    page["blocks"] = out
    return page


_LEADING_BR = re.compile(r"^(?:\s*<br\s*/?>\s*)+", re.I)


def strip_leading_breaks(page):
    """<br> used as paragraph spacing — the stylesheet handles that now."""
    for b in page["blocks"]:
        if b.get("type") == "paragraph" and isinstance(b.get("html"), str):
            stripped = _LEADING_BR.sub("", b["html"])
            if stripped != b["html"]:
                b["html"] = stripped
    return page


_JUNK_SCRIPT = re.compile(r"lazyLoadOptions|LazyLoad|data-no-optimize", re.I)


def clean_embed(fragment, path):
    """
    The hand-built widgets were pasted into the page builder as whole HTML
    documents, and the cache plugin appended its lazy-loader to each one.
    Keep the widget markup (and its own data: scripts), drop the rest.
    """
    soup = BeautifulSoup(fragment, "html.parser")

    for tag in soup.find_all(["!doctype", "meta", "title", "link"]):
        tag.decompose()
    for name in ("html", "head", "body"):
        for tag in soup.find_all(name):
            tag.unwrap()

    removed = 0
    for sc in soup.find_all("script"):
        src = sc.get("src") or ""
        if src.startswith("data:"):      # the widget's own logic — keep it
            continue
        if not src or _JUNK_SCRIPT.search(sc.get_text() or "") or _JUNK_SCRIPT.search(str(sc.attrs)):
            removed += len(str(sc))
            sc.decompose()

    demoted = 0
    for h1 in soup.find_all("h1"):
        h1.name = "h2"
        demoted += 1

    # bare tables inside a widget get the site's table treatment, which also
    # gives them a horizontal scroll container on narrow screens
    for table in soup.find_all("table"):
        if table.find_parent(class_="tablewrap"):
            continue
        wrapper = soup.new_tag("div")
        wrapper["class"] = "tablewrap"
        table.wrap(wrapper)

    out = str(soup)
    out = re.sub(r"<!DOCTYPE[^>]*>", "", out, flags=re.I).strip()
    if removed or demoted:
        _log(path, "ניקוי ווידג'ט מוטמע",
             "%d תווי סקריפט מיותרים, %d כותרות H1" % (removed, demoted),
             "הוסרו / הוסבו ל-H2")
    return out


def apply(page):
    """Mutate one extracted page dict in place. Returns the page."""
    path = page["path"]
    rewrite_thank_you(page)
    merge_split_paragraphs(page)
    strip_leading_breaks(page)
    for b in page["blocks"]:
        if b.get("type") == "custom_html":
            b["html"] = clean_embed(b["html"], path)

    # meta text
    for key, value in META_OVERRIDES.get(path, {}).items():
        if page.get(key) != value:
            _log(path, "מטא שהועתק מעמוד אחר", str(page.get(key))[:120], value[:120])
            page[key] = value
            if key == "meta_title":
                page["og_title"] = value
            if key == "meta_description":
                page["og_description"] = value

    for key in ("meta_title", "meta_description", "og_title", "og_description"):
        if page.get(key):
            page[key] = fix_text(page[key], path)

    if page.get("schema"):
        page["schema"] = fix_schema(page["schema"], path)
    for target, text in META_ADDITIONS.items():
        if path == target and not page.get("meta_description"):
            page["meta_description"] = text
            page["og_description"] = page.get("og_description") or text
            _log(path, "תיאור מטא חסר", "(ריק)", text[:150])

    if page.get("h1"):
        page["h1"] = fix_text(page["h1"], path)

    seen_h1 = 0
    prev_level = 1
    for b in page["blocks"]:
        t = b.get("type")

        if t == "heading":
            # exactly one H1 per page
            if b["level"] == 1:
                seen_h1 += 1
                if seen_h1 > 1:
                    _log(path, "H1 כפול הוסב ל-H2", b["text"][:120], b["text"][:120])
                    b["level"] = 2
            # no skipped heading levels
            if b["level"] - prev_level > 1:
                _log(path, "דילוג רמת כותרת", "h%d → h%d" % (prev_level, b["level"]),
                     "h%d" % (prev_level + 1))
                b["level"] = prev_level + 1
            prev_level = b["level"]

        if t == "price_range":
            fix_price_range(b, path)

        # per-page price alignment and date refresh, on the rendered text
        for table, label in ((PRICE_ALIGNMENTS, "יישור מחיר סותר"),
                             (DATE_FIXES, "תאריך מתיישן")):
            for pattern, repl in table.get(path, []):
                for key in ("html",):
                    if isinstance(b.get(key), str):
                        new = re.sub(pattern, repl, b[key])
                        if new != b[key]:
                            _log(path, label, b[key][:150], new[:150])
                            b[key] = new
                if t == "faq":
                    for item in b["items"]:
                        item["a"] = re.sub(pattern, repl, item["a"])

        for key in ("html",):
            if isinstance(b.get(key), str):
                b[key] = fix_html(b[key], path)
        if t == "heading":
            b["text"] = fix_text(b["text"], path)
            # copy-paste leftovers naming the wrong city — run last, so the
            # spelling pass above has already normalised the wording
            for before, after in HEADING_REWRITES.get(path, []):
                if before in b["text"]:
                    b["text"] = b["text"].replace(before, after)
                    b["html"] = b["html"].replace(before, after)
                    _log(path, "כותרת מעיר אחרת", before, after)
        if t == "faq":
            for item in b["items"]:
                item["q"] = fix_text(item["q"], path)
                item["a"] = fix_html(item["a"], path)
        if t == "reviews":
            for item in b["items"]:
                item["text"] = fix_text(item["text"], path)
        if t in ("card", "button"):
            for key in ("title", "text"):
                if b.get(key):
                    b[key] = fix_text(b[key], path)
        if t == "linkgrid":
            for l in b["links"]:
                l["text"] = fix_text(l["text"], path)

    return page
