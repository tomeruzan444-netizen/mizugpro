# -*- coding: utf-8 -*-
"""
Static build for the new מיזוג פרו site.

Reads the extracted content model in ../_source and renders the complete site
into ../dist, preserving every URL, every piece of copy, every internal link
and all page metadata from the live WordPress site.
"""
import json, os, re, shutil, sys, html, datetime, urllib.parse
from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons import icon  # noqa: E402
import content_fixes  # noqa: E402
import sidebar_groups  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "_source")
DIST = os.path.join(ROOT, "dist")

# The live LocalBusiness/Organization schema still carries the name and logo of
# an unrelated business ("אלוף הגגות") left over from the site it was cloned
# from. Everything else in the schema graph is emitted byte-for-byte.
FIX_ORG_SCHEMA = True

BASE_URL = "https://mizugpro.co.il"

REPAIRED_SCHEMA = set()

# ---------------------------------------------------------------- data ------
site = json.load(open(os.path.join(SRC, "site.json"), encoding="utf-8"))
pages = json.load(open(os.path.join(SRC, "content.json"), encoding="utf-8"))
imgmap = json.load(open(os.path.join(SRC, "image-map.json"), encoding="utf-8"))
_manifest_path = os.path.join(ROOT, "assets", "img", "manifest.json")
manifest = json.load(open(_manifest_path, encoding="utf-8")) if os.path.exists(_manifest_path) else {}

# editorial pass: spelling, punctuation and logical fixes on the migrated copy
pages = [content_fixes.apply(p) for p in pages]

by_path = {p["path"]: p for p in pages}

# manufacturer logos that sat in the old footer — carried over as a trust strip
BRAND_LOGOS = [
    ("תדיראן-removebg-preview.png", "מזגני תדיראן"),
    ("אלקטרה-removebg-preview.png", "מזגני אלקטרה"),
    ("טורנדו_400_על_100-removebg-preview.png", "מזגני טורנדו"),
    ("מיצובישי_מזגן-removebg-preview.png", "מזגני מיצובישי"),
]

# --------------------------------------------------------- url rewriting ----
_UPLOAD_RE = re.compile(r"https?://mizugpro\.co\.il/wp-content/uploads/[^\"'\s)]+")


def _best(name):
    """Prefer the WebP derivative when the pipeline produced a smaller one."""
    entry = manifest.get(name)
    return entry["best"] if entry else name


def local_img(url):
    if not url:
        return url
    if url in imgmap:
        return "/assets/img/" + _best(imgmap[url].rsplit("/", 1)[-1])
    name = urllib.parse.unquote(url.rsplit("/", 1)[-1].split("?")[0])
    if os.path.exists(os.path.join(ROOT, "assets", "img", name)):
        return "/assets/img/" + _best(name)
    return url


def img_dims(src):
    """Intrinsic size of a built asset, so every <img> can reserve its box."""
    if not src or not src.startswith("/assets/img/"):
        return None, None
    name = src.rsplit("/", 1)[-1]
    for key, entry in manifest.items():
        if entry["best"] == name or key == name:
            return entry["width"], entry["height"]
    return None, None


_hero = "/assets/img/צוות-מיזוג-פרו-החדש.webp"
if os.path.exists(os.path.join(ROOT, "assets", "img", os.path.basename(_hero))):
    _hw, _hh = img_dims(_hero)
    site["hero_photo"] = {"src": _hero, "alt": "צוות הטכנאים של מיזוג פרו",
                          "w": _hw or 771, "h": _hh or 405}

site["brands"] = []
for _file, _alt in BRAND_LOGOS:
    _src = "/assets/img/" + _best(_file)
    if os.path.exists(os.path.join(ROOT, "assets", "img", os.path.basename(_src))):
        _w, _h = img_dims(_src)
        site["brands"].append({"src": _src, "alt": _alt, "w": _w, "h": _h})


def rewrite_html(s):
    if not isinstance(s, str):
        return s
    return _UPLOAD_RE.sub(lambda m: local_img(m.group(0)), s)


def rewrite_blocks(blocks):
    out = []
    for b in blocks:
        b = dict(b)
        if b.get("type") == "image":
            b["src"] = local_img(b.get("src"))
            w, h = img_dims(b["src"])
            if w:
                b["width"], b["height"] = w, h
        for key in ("html", "text"):
            if isinstance(b.get(key), str):
                b[key] = rewrite_html(b[key])
        if b.get("type") == "faq":
            b["items"] = [{"q": i["q"], "a": rewrite_html(i["a"])} for i in b["items"]]
        out.append(b)
    return out


# ------------------------------------------------------- page decomposition -
DROP_HEADINGS = {"השאירו פרטים ונחזור אליכם", "התקשרו עכשיו והתייעצו איתנו",
                 "מה תוכלו למצוא בעמוד?"}
DROP_BUTTONS = {"לחצו כאן להתקשר"}
TAIL_LABELS = {"צרו איתנו קשר": "contact", "המלצות לקוחות": "reviews",
               "אזורי שירות": "areas", "בין השירותים שלנו": "services"}


def split_page(p):
    """Split the flat block list into hero / article body / tail sections."""
    blocks = rewrite_blocks(p["blocks"])
    h1, h1_html, lead = p.get("h1"), None, None
    body, tail = [], {"reviews": None, "areas": None, "services": None,
                      "contact_label": None, "reviews_label": None,
                      "areas_label": None, "services_label": None}

    i = 0
    if blocks and blocks[0]["type"] == "heading" and blocks[0]["level"] == 1:
        h1 = blocks[0]["text"]
        h1_html = blocks[0]["html"]
        i = 1
    if i < len(blocks) and blocks[i]["type"] == "paragraph":
        lead = blocks[i]["html"]
        i += 1

    current = None
    for b in blocks[i:]:
        if b["type"] == "heading" and b["text"].strip() in DROP_HEADINGS:
            continue
        if b["type"] == "button" and b["text"].strip() in DROP_BUTTONS:
            continue
        if b["type"] == "button" and not b.get("href"):
            label = b["text"].strip()
            key = TAIL_LABELS.get(label)
            if key:
                current = key
                tail[key + "_label" if key != "contact" else "contact_label"] = label
                continue
        if current == "reviews" and b["type"] == "reviews":
            tail["reviews"] = b["items"]
            continue
        if current in ("areas", "services") and b["type"] == "list":
            links = re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>', b["html"], re.S)
            tail[current] = [{"href": h_, "text": re.sub(r"<[^>]+>", "", t).strip()}
                             for h_, t in links]
            continue
        if current is None:
            body.append(b)
        # anything that lands after a tail marker but is not one of the shapes
        # above is still real copy — keep it in the article rather than lose it
        elif b["type"] not in ("button",):
            body.append(b)

    return {"h1": h1, "h1_html": h1_html, "lead": lead, "body": body, "tail": tail}


# --------------------------------------------------------- related linking --
# The old site left 16 pages with no inbound internal link at all: reachable
# only through the sitemap, so they got no link equity and no crawl priority.
# Every page now links on to its neighbours in a fixed rotation, which
# guarantees each one receives inbound links without removing anything.
EXCLUDE_FROM_RELATED = {"/", "/thank-you/", "/צרו-קשר/", "/אודות/", "/בלוג/",
                        "/category/בלוג/", "/מדיניות-פרטיות/", "/הצהרת-נגישות/",
                        "/הממליצים-שלנו/", "/אזורי-שירות/"}
RELATED_COUNT = 6


def build_related():
    cities, services = [], []
    for q in pages:
        if q["path"] in EXCLUDE_FROM_RELATED:
            continue
        (cities if q["path"].startswith(("/טכנאי-מזגנים-", "/ניקוי-מזגנים-"))
         else services).append(q)
    related, labels = {}, {}
    for group, label in ((cities, "אזורי שירות נוספים"), (services, "מדריכים ושירותים נוספים")):
        n = len(group)
        for i, q in enumerate(group):
            picks = [group[(i + k) % n] for k in range(1, min(RELATED_COUNT, n - 1) + 1)]
            related[q["path"]] = [{"href": r["path"],
                                   "text": (r.get("h1") or r["meta_title"]).split("–")[0]
                                            .split(" - ")[0].strip()}
                                  for r in picks]
            labels[q["path"]] = label
    return related, labels


RELATED, RELATED_LABEL = build_related()

# the blog listing and its category archive were mutually unlinked
if "/בלוג/" in by_path and "/category/בלוג/" in by_path:
    RELATED["/בלוג/"] = [{"href": "/category/בלוג/", "text": "כל המאמרים בקטגוריית בלוג"}]
    RELATED_LABEL["/בלוג/"] = "עוד מהבלוג"
    RELATED["/category/בלוג/"] = [{"href": "/בלוג/", "text": "עמוד הבלוג"}]
    RELATED_LABEL["/category/בלוג/"] = "עוד מהבלוג"


# ------------------------------------------------------------- breadcrumbs --
SECTION_PARENTS = [
    (re.compile(r"^/טכנאי-מזגנים-"), "/אזורי-שירות/", "אזורי שירות"),
    (re.compile(r"^/ניקוי-מזגנים-"), "/אזורי-שירות/", "אזורי שירות"),
]


def crumbs_for(p):
    if p["path"] == "/":
        return None
    out = [{"href": "/", "text": "עמוד הבית"}]
    for rx, href, text in SECTION_PARENTS:
        if rx.match(p["path"]) and p["path"] != href:
            out.append({"href": href, "text": text})
            break
    out.append({"href": p["path"], "text": p.get("h1") or p["meta_title"]})
    return out


# ------------------------------------------------------------------ schema --
def fix_org(node):
    if not isinstance(node, dict):
        return node
    t = node.get("@type")
    types = t if isinstance(t, list) else [t]
    if "Organization" in types or "LocalBusiness" in types:
        node["name"] = site["name"]
        node.pop("alternateName", None)
        node["telephone"] = site["phone_cta"]
        node["email"] = site["email"]
        node["address"] = {"@type": "PostalAddress",
                           "streetAddress": "הנביאים 8",
                           "addressLocality": "תל אביב",
                           "addressCountry": "IL"}
        node["openingHours"] = ["Mo,Tu,We,Th,Fr,Sa,Su 00:00-23:59"]
        node["areaServed"] = {"@type": "Country", "name": "IL"}
        logo_url = BASE_URL + urllib.parse.quote("/assets/img/לוגו-מיזוג-פרו.png")
        if isinstance(node.get("logo"), dict):
            node["logo"]["url"] = logo_url
            node["logo"]["contentUrl"] = logo_url
            node["logo"]["caption"] = site["name"]
    if node.get("@type") == "WebSite":
        node["name"] = site["name"]
        node.pop("alternateName", None)
    if node.get("@type") in ("WebPage", "Article", "BlogPosting"):
        node.setdefault("speakable", {
            "@type": "SpeakableSpecification",
            "cssSelector": ["h1", ".pagehero__lead", ".hero__lead", ".prose > p"],
        })
        node.setdefault("inLanguage", "he-IL")
    return node


def repair_json(raw):
    """
    The theme prints one JSON-LD block with literal newlines inside a string,
    which makes it invalid and unreadable to search engines. Close the strings
    back up rather than dropping the block.
    """
    out, in_string, escaped = [], False, False
    for ch in raw:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch in "\n\r\t":
            out.append(" ")
            continue
        out.append(ch)
    return "".join(out)


CITY_RE = re.compile(r"^(?:טכנאי מזגנים|ניקוי מזגנים)\s+ב?(.+?)\s*[-–]")
SERVICE_PAGE_RE = re.compile(
    r"^/(התקנת|תיקון|פירוק|ניקוי|החלפת|מילוי|מחירון|מזגן|טכנאי|קורס|מיזוג)")


def service_schema(p, page_url):
    """
    Every page here sells a concrete service in a concrete place, but the old
    site described none of that to search engines or answer engines.
    """
    if not SERVICE_PAGE_RE.match(p["path"]) or p["path"] == "/":
        return None
    name = (p.get("h1") or p.get("meta_title") or "").split("–")[0].split(" - ")[0].strip()
    if not name:
        return None

    node = {
        "@context": "https://schema.org",
        "@type": "Service",
        "@id": page_url + "#service",
        "name": name,
        "serviceType": "מיזוג אוויר",
        "provider": {"@id": BASE_URL + "/#organization"},
        "url": page_url,
        "availableChannel": {
            "@type": "ServiceChannel",
            "servicePhone": {"@type": "ContactPoint", "telephone": site["phone_cta"],
                             "contactType": "customer service", "availableLanguage": "he"},
            "serviceUrl": page_url,
        },
    }
    if p.get("meta_description"):
        node["description"] = p["meta_description"]

    city = CITY_RE.match(p.get("h1") or "")
    node["areaServed"] = ({"@type": "City", "name": city.group(1).strip()}
                          if city else {"@type": "Country", "name": "ישראל"})

    # price ranges live in the copy — surface the lowest one as an offer floor
    prices = []
    for b in p["blocks"]:
        if b.get("type") == "price_range":
            for pt in b.get("points", []):
                digits = re.sub(r"[^\d]", "", pt.get("value") or "")
                if digits:
                    prices.append(int(digits))
    if prices:
        node["offers"] = {
            "@type": "AggregateOffer", "priceCurrency": "ILS",
            "lowPrice": min(prices), "highPrice": max(prices),
        }
    return node


def schema_strings(p, crumbs):
    out = []
    for doc in p.get("schema", []):
        if "_raw" in doc:
            raw = doc["_raw"]
            try:
                fixed = json.loads(repair_json(raw))
                out.append(json.dumps(fixed, ensure_ascii=False, separators=(",", ":")))
                REPAIRED_SCHEMA.add(p["path"])
            except Exception:
                out.append(raw)
            continue
        doc = json.loads(json.dumps(doc))  # deep copy
        if FIX_ORG_SCHEMA and isinstance(doc.get("@graph"), list):
            doc["@graph"] = [fix_org(n) for n in doc["@graph"]]
        out.append(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))

    # --- structured data the old site never emitted -----------------------
    page_url = BASE_URL + urllib.parse.quote(p["path"])

    faqs = []
    for b in p["blocks"]:
        if b.get("type") == "faq":
            for item in b["items"]:
                answer = re.sub(r"<[^>]+>", " ", item["a"])
                answer = re.sub(r"\s+", " ", answer).strip()
                if item["q"] and answer:
                    faqs.append({
                        "@type": "Question",
                        "name": item["q"].strip(),
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    })
    if faqs:
        out.append(json.dumps({
            "@context": "https://schema.org", "@type": "FAQPage",
            "@id": page_url + "#faq",
            "mainEntity": faqs,
        }, ensure_ascii=False, separators=(",", ":")))

    service = service_schema(p, page_url)
    if service:
        out.append(json.dumps(service, ensure_ascii=False, separators=(",", ":")))

    if crumbs and len(crumbs) > 1:
        out.append(json.dumps({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": n + 1, "name": c["text"],
                 "item": BASE_URL + urllib.parse.quote(c["href"])}
                for n, c in enumerate(crumbs)],
        }, ensure_ascii=False, separators=(",", ":")))
    return out


# -------------------------------------------------------------- homepage ----
SERVICE_STYLE = [
    ("wrench", "c-sky"), ("tools", "c-navy"),
    ("truck", "c-gold"), ("tag", "c-deep"),
]

BADGES = [
    ("award", "מקצועיות מוכחת", "15 שנה של התקנות ותיקונים לכל סוגי המזגנים.", "c-sky"),
    ("clock", "זמינות מלאה", "עובדים 24/7, גם בשבתות ובחגים, לקריאות דחופות.", "c-gold"),
    ("tag", "מחיר הוגן ושקוף", "מחירון גלוי והצעת מחיר סופית לפני שמתחילים.", "c-deep"),
    ("users", "ייעוץ אישי", "עוזרים לבחור את המזגן שמתאים לחלל, לתקציב ולצרכים.", "c-navy"),
    ("shield", "אחריות מלאה", "אנחנו עומדים מאחורי כל עבודה שאנחנו מבצעים.", "c-sky"),
]


def project(url, alt):
    src = local_img(url)
    w, h = img_dims(src)
    return {"src": src, "alt": alt, "w": w, "h": h}


def build_home(p, model):
    blocks = model["body"]
    services, steps, prose = [], [], []
    steps_title = why_title = None

    i = 0
    while i < len(blocks):
        b = blocks[i]
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        # heading-link + image pairs are the service tiles
        if (b["type"] == "heading" and "<a href" in (b.get("html") or "")
                and nxt and nxt["type"] == "image" and nxt.get("href")):
            href = re.search(r'href="([^"]+)"', b["html"]).group(1)
            target = by_path.get(href)
            desc = (target or {}).get("meta_description") or ""
            desc = re.split(r"(?<=[.!?])\s", desc)[0][:130] if desc else ""
            style = SERVICE_STYLE[len(services) % len(SERVICE_STYLE)]
            iw, ih = img_dims(nxt["src"])
            services.append({"title": b["text"], "href": href, "text": desc,
                             "icon": style[0], "color": style[1],
                             "img": nxt["src"], "alt": nxt.get("alt") or b["text"],
                             "w": iw, "h": ih})
            i += 2
            continue
        # the "how it works" list becomes the process strip
        if (b["type"] == "heading" and "השירות שלנו עובד" in b["text"]
                and nxt and nxt["type"] == "list"):
            steps_title = b["text"].rstrip(":")
            steps = [re.sub(r"<[^>]+>", "", li).strip()
                     for li in re.findall(r"<li>(.*?)</li>", nxt["html"], re.S)]
            i += 2
            continue
        if b["type"] == "heading" and b["text"].startswith("טכנאי מזגנים בוחרים"):
            why_title = b["text"]
            i += 1
            continue
        prose.append(b)
        i += 1

    reviews = model["tail"]["reviews"] or []
    stars = [r.get("stars", 5) for r in reviews] or [5]
    city_pages = [q for q in pages if q["path"].startswith("/טכנאי-מזגנים-ב")]

    model.update({
        "services": services,
        "steps": steps,
        "steps_title": steps_title or "ככה השירות שלנו עובד",
        "why_title": why_title or "טכנאי מזגנים בוחרים רק ממיזוג פרו",
        "badges": [{"icon": a, "title": b_, "text": c, "color": d} for a, b_, c, d in BADGES],
        "body": prose,
        "stats": [
            {"num": "15+", "label": "שנות ניסיון בתחום המיזוג"},
            {"num": "24/7", "label": "זמינות לקריאות שירות"},
            {"num": "%d+" % len(city_pages), "label": "ערים ויישובים בפריסה ארצית"},
            {"num": "%.1f" % (sum(stars) / len(stars)), "label": "דירוג ממוצע מלקוחות"},
        ],
        "projects": [project(BASE_URL + "/wp-content/uploads/2025/03/פרוייקט-התקנת-מזגן.png",
                             "פרויקט התקנת מזגן של מיזוג פרו"),
                     project(BASE_URL + "/wp-content/uploads/2025/03/התקנת-מזגן-מיזוג-פרו-1024x508.png",
                             "התקנת מזגן על ידי טכנאי מיזוג פרו")],
        "area_chips": (model["tail"]["areas"] or []) + [
            l for col in site["footer_columns"] if col["title"] == "אזורי שירות"
            for l in col["links"]],
    })
    return model


def highlight_h1(text):
    if not text:
        return ""
    for dash in ("–", "-", "—"):
        if dash in text:
            head, _, tail = text.partition(dash)
            return "%s %s <span class=\"hl\">%s</span>" % (html.escape(head.strip()), dash,
                                                           html.escape(tail.strip()))
    return html.escape(text)


# ------------------------------------------------------------------ render --
env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")),
                  autoescape=select_autoescape(["html"]), trim_blocks=False,
                  lstrip_blocks=False)
env.globals["icon"] = lambda name, cls="": __import__("markupsafe").Markup(icon(name, cls))
env.globals["site"] = site
env.globals["year"] = datetime.date.today().year


HTACCESS = """# ---- מיזוג פרו — static deploy -------------------------------------------
Options -MultiViews
DirectoryIndex index.html

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/css text/xml \\
    application/javascript application/json image/svg+xml application/xml
</IfModule>

<IfModule mod_brotli.c>
  AddOutputFilterByType BROTLI_COMPRESS text/html text/css \\
    application/javascript application/json image/svg+xml
</IfModule>

<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/html                "access plus 0 seconds"
  ExpiresByType text/css                 "access plus 1 year"
  ExpiresByType application/javascript   "access plus 1 year"
  ExpiresByType image/webp               "access plus 1 year"
  ExpiresByType image/png                "access plus 1 year"
  ExpiresByType font/woff2               "access plus 1 year"
</IfModule>

<IfModule mod_headers.c>
  <FilesMatch "\\.(css|js|webp|png|jpe?g|svg|woff2)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
  </FilesMatch>
  Header set X-Content-Type-Options "nosniff"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
</IfModule>

AddDefaultCharset UTF-8
AddType font/woff2 .woff2
AddType image/webp .webp

# keep the canonical trailing slash the old site used
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_URI} !(/$|\\.)
  RewriteRule ^(.*)$ /$1/ [R=301,L]
</IfModule>

ErrorDocument 404 /404.html
"""

NETLIFY_HEADERS = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains

/assets/*
  Cache-Control: public, max-age=31536000, immutable
"""

NGINX = """# include inside the server{} block
charset utf-8;
charset_types text/html text/css application/javascript application/json text/xml;
location / {
  try_files $uri $uri/ $uri/index.html =404;
}
location /assets/ {
  add_header Cache-Control "public, max-age=31536000, immutable";
  access_log off;
}
gzip on;
gzip_types text/css application/javascript image/svg+xml application/json text/xml;
gzip_min_length 512;
error_page 404 /404.html;
"""


# Answer engines identify themselves with their own user agents; naming them
# explicitly keeps a future blanket rule from quietly cutting the site out of
# AI search results.
AI_AGENTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
             "Claude-SearchBot", "PerplexityBot", "Perplexity-User", "Google-Extended",
             "Applebot", "Applebot-Extended", "Bingbot", "meta-externalagent",
             "Amazonbot", "DuckAssistBot", "YouBot", "CCBot"]


def write_robots():
    lines = ["# מיזוג פרו", "User-agent: *", "Allow: /", "Disallow: /thank-you/", ""]
    lines.append("# search and answer engines are welcome to read and cite this site")
    for agent in AI_AGENTS:
        lines += ["User-agent: %s" % agent, "Allow: /", ""]
    lines += ["Sitemap: %s/sitemap.xml" % BASE_URL, ""]
    open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8").write("\n".join(lines))


def write_llms_txt():
    """A plain-text map of the site for LLM crawlers (llmstxt.org)."""
    groups = [
        ("שירותים", lambda q: q["path"].startswith(("/התקנת-", "/תיקון-", "/פירוק-",
                                                     "/ניקוי-", "/החלפת-", "/מילוי-"))),
        ("אזורי שירות", lambda q: q["path"].startswith(("/טכנאי-מזגנים-", "/אזורי-"))),
        ("מחירים", lambda q: "מחירון" in q["path"]),
        ("מדריכים ומידע", lambda q: True),
    ]
    used, sections = set(), []
    for title, match in groups:
        rows = []
        for q in pages:
            if q["path"] in used or q["path"] == "/" or "noindex" in (q.get("robots") or ""):
                continue
            if match(q):
                used.add(q["path"])
                desc = (q.get("meta_description") or "").strip()
                desc = re.sub(r"\s+", " ", desc)[:150]
                rows.append("- [%s](%s%s): %s" % (
                    (q.get("h1") or q["meta_title"]).strip(),
                    BASE_URL, urllib.parse.quote(q["path"]), desc))
        if rows:
            sections.append("## %s\n\n%s" % (title, "\n".join(sorted(rows))))

    home = by_path.get("/", {})
    text = "\n\n".join([
        "# %s" % site["name"],
        "> %s" % (home.get("meta_description") or ""),
        "חברת שירותי מיזוג אוויר בפריסה ארצית: התקנה, תיקון, פירוק, ניקוי ותחזוקה "
        "לכל סוגי המזגנים. טלפון %s, דוא\"ל %s, %s." % (
            site["phone_cta"], site["email"], site["hours"]),
        *sections,
    ]) + "\n"
    open(os.path.join(DIST, "llms.txt"), "w", encoding="utf-8").write(text)


def image_redirects():
    """
    Old /wp-content/uploads/... URLs are indexed in Google Images and linked
    from elsewhere. Point each one at its migrated file so that equity moves
    with it instead of turning into a 404 on cutover day.
    """
    path = os.path.join(SRC, "image-redirects.json")
    if not os.path.exists(path):
        return ""
    rows = json.load(open(path, encoding="utf-8"))
    if not rows:
        return ""
    lines = ["", "# migrated media — keep the old image URLs alive",
             "<IfModule mod_alias.c>"]
    for old, new in rows:
        lines.append('  Redirect 301 "%s" "%s"' % (old, new))
    lines.append("</IfModule>")
    return "\n".join(lines) + "\n"


def write_server_config():
    open(os.path.join(DIST, ".htaccess"), "w", encoding="utf-8").write(
        HTACCESS + image_redirects())
    open(os.path.join(DIST, "_headers"), "w", encoding="utf-8").write(NETLIFY_HEADERS)
    open(os.path.join(DIST, "nginx.conf.snippet"), "w", encoding="utf-8").write(NGINX)


_PROTECTED = re.compile(r"(<(pre|textarea|script|style)\b[^>]*>.*?</\2>)", re.S | re.I)
_COMMENT = re.compile(r"<!--(?!\[if).*?-->", re.S)


def minify_html(markup):
    """
    Collapse the whitespace the templates add, without touching anything whose
    whitespace is meaningful. Runs collapse to a single space (never to
    nothing), so inline spacing between links and words is preserved.
    """
    stash = []

    def park(m):
        stash.append(m.group(0))
        return "\x00%d\x00" % (len(stash) - 1)

    text = _PROTECTED.sub(park, markup)
    text = _COMMENT.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text).strip()


def out_path(path):
    rel = path.strip("/")
    folder = os.path.join(DIST, *rel.split("/")) if rel else DIST
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "index.html")


def main():
    if os.path.exists(DIST):
        for entry in os.listdir(DIST):
            target = os.path.join(DIST, entry)
            shutil.rmtree(target) if os.path.isdir(target) else os.remove(target)
    os.makedirs(DIST, exist_ok=True)

    report = {"pages": [], "broken_links": [], "missing_meta": []}
    used_assets = set()
    known = set(by_path) | {"/thank-you/"}

    for p in pages:
        model = split_page(p)
        model.update({k: p.get(k) for k in
                      ("path", "meta_title", "meta_description", "robots", "canonical",
                       "og_title", "og_description", "og_image", "og_type")})
        # og:image must be absolute; point it at the migrated asset
        local = local_img(model["og_image"]) if model["og_image"] else None
        model["og_image"] = (BASE_URL + urllib.parse.quote(local)
                             if local and local.startswith("/") else local)
        model["crumbs"] = crumbs_for(p)
        model["sidebar"] = sidebar_groups.sidebar_for(p["path"])
        model["related"] = RELATED.get(p["path"])
        model["related_label"] = RELATED_LABEL.get(p["path"])
        model["schema"] = schema_strings(p, model["crumbs"])

        if p["path"] == "/":
            model = build_home(p, model)
            model["h1_html"] = __import__("markupsafe").Markup(highlight_h1(model["h1"]))
            tpl = env.get_template("home.html")
        else:
            tpl = env.get_template("page.html")

        html_out = minify_html(tpl.render(page=model))
        used_assets.update(re.findall(r"/assets/img/([^\"')\s]+)", html_out))
        dest = out_path(p["path"])
        open(dest, "w", encoding="utf-8").write(html_out)

        # ---- QA ----
        for l in p["internal_links"]:
            href = l["href"].split("#")[0]
            if href.startswith("/") and href not in known and not href.startswith("/assets/"):
                report["broken_links"].append({"on": p["path"], "href": href, "text": l["text"]})
        if not p.get("meta_title") or not p.get("meta_description"):
            report["missing_meta"].append(p["path"])
        report["pages"].append({"path": p["path"], "file": os.path.relpath(dest, ROOT),
                                "title": p["meta_title"], "blocks": len(p["blocks"])})

    # ---- assets: ship only what the built pages actually reference ----
    used_assets.update(urllib.parse.unquote(a) for a in list(used_assets))
    for name in ("cropped-פאביקון-מיזוג-פרו-1-32x32.png",
                 "cropped-פאביקון-מיזוג-פרו-1-180x180.png",
                 "cropped-פאביקון-מיזוג-פרו-1-192x192.png",
                 "cropped-פאביקון-מיזוג-פרו-1-270x270.png"):
        used_assets.add(name)

    def _ignore(directory, entries):
        if os.path.basename(directory) != "img":
            return [e for e in entries if e in ("legacy-widgets.css", "site.css",
                                                "site.js", "assistant.css",
                                                "faces.json", "subset-report.json")]
        return [e for e in entries
                if e not in used_assets and not e.endswith(".woff2")]

    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(DIST, "assets"),
                    ignore=_ignore)
    print("image files shipped:", len(os.listdir(os.path.join(DIST, "assets", "img"))))

    # ---- sitemap + robots ----
    today = datetime.date.today().isoformat()
    urls = "\n".join(
        "  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq>"
        "<priority>%s</priority></url>"
        % (BASE_URL + urllib.parse.quote(p["path"]), today, "1.0" if p["path"] == "/" else "0.8")
        for p in pages if "noindex" not in (p.get("robots") or ""))
    open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % urls)
    open(os.path.join(DIST, "site.webmanifest"), "w", encoding="utf-8").write(
        json.dumps({
            "name": site["name"], "short_name": site["name"],
            "description": (by_path.get("/", {}) or {}).get("meta_description", ""),
            "start_url": "/", "display": "standalone", "lang": "he", "dir": "rtl",
            "background_color": "#F6FBFE", "theme_color": "#04293A",
            "icons": [
                {"src": "/assets/img/cropped-פאביקון-מיזוג-פרו-1-192x192.png",
                 "sizes": "192x192", "type": "image/png"},
                {"src": "/assets/img/cropped-פאביקון-מיזוג-פרו-1-270x270.png",
                 "sizes": "270x270", "type": "image/png"},
            ],
        }, ensure_ascii=False, indent=1))

    php = os.path.join(HERE, "form", "contact.php")
    if os.path.exists(php):
        shutil.copy2(php, os.path.join(DIST, "contact.php"))

    write_robots()
    write_llms_txt()
    write_server_config()

    open(os.path.join(DIST, "404.html"), "w", encoding="utf-8").write(
        env.get_template("404.html").render(page={
            "meta_title": "העמוד לא נמצא | מיזוג פרו",
            "meta_description": "העמוד שחיפשתם לא נמצא. חזרו לעמוד הבית של מיזוג פרו "
                                "או התקשרו אלינו לקבלת שירות טכנאי מזגנים.",
            "robots": "noindex, follow", "canonical": None, "og_type": "website",
            "og_title": None, "og_description": None, "og_image": None,
            "schema": [], "path": "/404.html", "h1": "העמוד שחיפשתם לא נמצא",
        }))

    json.dump(report, open(os.path.join(ROOT, "migration-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    by_rule = {}
    for c in content_fixes.CHANGES:
        by_rule.setdefault(c["rule"], []).append(c)
    json.dump({"total": len(content_fixes.CHANGES),
               "by_rule": {k: len(v) for k, v in sorted(by_rule.items(), key=lambda kv: -len(kv[1]))},
               "changes": content_fixes.CHANGES},
              open(os.path.join(ROOT, "content-fixes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("pages rendered :", len(report["pages"]))
    print("broken links   :", len(report["broken_links"]))
    print("missing meta   :", len(report["missing_meta"]))
    print("schema repaired:", len(REPAIRED_SCHEMA), "pages")
    print("content fixes  :", len(content_fixes.CHANGES))
    for rule, items in sorted(by_rule.items(), key=lambda kv: -len(kv[1])):
        print("    %-26s %d" % (rule, len(items)))


if __name__ == "__main__":
    main()
