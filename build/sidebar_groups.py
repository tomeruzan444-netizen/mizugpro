# -*- coding: utf-8 -*-
"""
Topical sidebar clusters.

Every page carries a sidebar of the pages closest to it in subject, so a reader
who lands on one fault page finds the neighbouring faults, and a reader on a
city page finds the services they actually came to buy. Seven clusters cover
the whole site; each page is assigned to exactly one.

The link lists are ordered by how useful they are to someone reading that
cluster, not alphabetically — the first two entries are the ones most people
want next.
"""

GROUPS = {
    "install": {
        "title": "התקנת מזגנים",
        "icon": "ac-unit",
        "links": [
            ("/התקנת-מזגנים/", "התקנת מזגן — כל הסוגים"),
            ("/מחירון-מזגנים/", "מחירון התקנה ותיקון"),
            ("/התקנת-מזגן-עילי/", "התקנת מזגן עילי"),
            ("/התקנת-מזגן-מיני-מרכזי/", "התקנת מזגן מיני מרכזי"),
            ("/התקנת-מזגן-נסתר/", "התקנת מזגן נסתר"),
            ("/מזגן-רצפתי/", "התקנת מזגן רצפתי"),
            ("/התקנת-מזגן-vrf/", "התקנת מזגן VRF"),
            ("/התקנת-מזגן-בממד/", "התקנת מזגן בממ\"ד"),
            ("/אחריות-על-התקנת-מזגן/", "אחריות על ההתקנה"),
        ],
    },
    "repair": {
        "title": "תיקון מזגנים ותקלות",
        "icon": "wrench",
        "links": [
            ("/תיקון-מזגנים/", "תיקון מזגנים — תהליך ומחירים"),
            ("/המזגן-לא-מקרר/", "המזגן לא מקרר"),
            ("/מזגן-לא-מחמם/", "המזגן לא מחמם"),
            ("/מזגן-מטפטף/", "מזגן מטפטף"),
            ("/מזגן-רועש/", "מזגן מרעיש"),
            ("/ריח-רע-מהמזגן/", "ריח רע מהמזגן"),
            ("/קצר-במזגן/", "קצר במזגן"),
            ("/תיקון-מזגן-מיני-מרכזי/", "תיקון מזגן מיני מרכזי"),
        ],
    },
    "parts": {
        "title": "החלפת חלקים ומילוי גז",
        "icon": "gauge",
        "links": [
            ("/החלפת-מדחס-במזגן/", "החלפת מדחס"),
            ("/מילוי-גז-למזגן/", "מילוי גז למזגן"),
            ("/החלפת-מנוע-למזגן/", "החלפת מנוע"),
            ("/החלפת-מאיץ-במזגן/", "החלפת מאיץ (מפוח)"),
            ("/החלפת-עינית-למזגן/", "החלפת עינית"),
            ("/צינור-ניקוז-למזגן/", "החלפת צינור ניקוז"),
            ("/פירוק-מזגן/", "פירוק והרכבת מזגן"),
            ("/תיקון-מזגנים/", "תיקון מזגנים"),
        ],
    },
    "clean": {
        "title": "ניקוי ותחזוקת מזגנים",
        "icon": "filter",
        "links": [
            ("/ניקוי-מזגן-2/", "ניקוי מזגן — מחירים"),
            ("/ניקוי-מיני-מרכזי/", "ניקוי מזגן מיני מרכזי"),
            ("/ניקוי-מזגן-מעובש-מידע-ומחירים/", "ניקוי מזגן מעובש"),
            ("/ניקוי-מזגנים-בצפון/", "ניקוי מזגנים בצפון"),
            ("/ריח-רע-מהמזגן/", "ריח רע מהמזגן"),
            ("/מזגן-מטפטף/", "מזגן מטפטף"),
            ("/מילוי-גז-למזגן/", "מילוי גז למזגן"),
            ("/מחירון-מזגנים/", "מחירון מזגנים"),
        ],
    },
    "sizes": {
        "title": "גדלי מזגן ומחירים",
        "icon": "price",
        "links": [
            ("/מחירון-מזגנים/", "מחירון מזגנים מלא"),
            ("/מזגן-חצי-כוח-סוס/", "מזגן 0.5 כ\"ס"),
            ("/התקנת-מזגן-1-כוח-סוס/", "מזגן 1 כ\"ס"),
            ("/התקנת-מזגן-1-25-כוח-סוס/", "מזגן 1.25 כ\"ס"),
            ("/מזגן-1-5-כוח-סוס/", "מזגן 1.5 כ\"ס"),
            ("/התקנת-מזגן-2-כוח-סוס/", "מזגן 2 כ\"ס"),
            ("/מזגן-2-5-כוח-סוס/", "מזגן 2.5 כ\"ס"),
            ("/התקנת-מזגן-3-כוח-סוס/", "מזגן 3 כ\"ס"),
            ("/מזגן-3-5-כוח-סוס/", "מזגן 3.5 כ\"ס"),
            ("/התקנת-מזגן-5-כוח-סוס/", "מזגן 5 כ\"ס"),
            ("/כמה-עולה-מזגן-לשעה/", "כמה עולה מזגן לשעה"),
        ],
    },
    "guides": {
        "title": "מדריכים ובחירת מזגן",
        "icon": "info",
        "links": [
            ("/איזה-מזגן-הכי-טוב/", "איזה מזגן הכי טוב?"),
            ("/מזגן-אינוורטר-חסרונות-ויתרונות/", "מזגן אינוורטר — יתרונות וחסרונות"),
            ("/מזגן-לחדר-שינה/", "מזגן לחדר שינה"),
            ("/מזגן-מולטי-איוורטר/", "מזגן מולטי אינוורטר"),
            ("/מזגן-חלון/", "מזגן חלון"),
            ("/מזגן-אלקטרה-1-כס/", "מזגן אלקטרה 1 כ\"ס"),
            ("/מערכות-מיזוג-חכמות-בבנייה-ירוקה/", "מערכות מיזוג חכמות"),
            ("/כמה-עולה-מזגן-לשעה/", "כמה עולה מזגן לשעה"),
            ("/מחירון-מזגנים/", "מחירון מזגנים"),
        ],
    },
    "services": {
        "title": "השירותים המבוקשים שלנו",
        "icon": "list",
        "links": [
            ("/תיקון-מזגנים/", "תיקון מזגנים"),
            ("/התקנת-מזגנים/", "התקנת מזגנים"),
            ("/ניקוי-מזגן-2/", "ניקוי מזגנים"),
            ("/מחירון-מזגנים/", "מחירון מזגנים"),
            ("/מילוי-גז-למזגן/", "מילוי גז למזגן"),
            ("/פירוק-מזגן/", "פירוק מזגן"),
            ("/החלפת-מדחס-במזגן/", "החלפת מדחס"),
            ("/אזורי-שירות/", "כל אזורי השירות"),
        ],
    },
}

# Explicit assignment wins; anything unlisted falls through to the rules below.
PAGE_GROUP = {
    # installation
    "/התקנת-מזגנים/": "install", "/התקנת-מזגן-עילי/": "install",
    "/התקנת-מזגן-מיני-מרכזי/": "install", "/התקנת-מזגן-נסתר/": "install",
    "/מזגן-רצפתי/": "install", "/התקנת-מזגן-vrf/": "install",
    "/התקנת-מזגן-בממד/": "install", "/אחריות-על-התקנת-מזגן/": "install",
    "/מיזוג-תעשייתי/": "install",
    # repair
    "/תיקון-מזגנים/": "repair", "/המזגן-לא-מקרר/": "repair",
    "/מזגן-לא-מחמם/": "repair", "/מזגן-מטפטף/": "repair",
    "/מזגן-רועש/": "repair", "/ריח-רע-מהמזגן/": "repair",
    "/קצר-במזגן/": "repair", "/תיקון-מזגן-מיני-מרכזי/": "repair",
    # parts
    "/החלפת-מדחס-במזגן/": "parts", "/החלפת-מנוע-למזגן/": "parts",
    "/החלפת-מאיץ-במזגן/": "parts", "/החלפת-עינית-למזגן/": "parts",
    "/צינור-ניקוז-למזגן/": "parts", "/מילוי-גז-למזגן/": "parts",
    "/פירוק-מזגן/": "parts",
    # cleaning
    "/ניקוי-מזגן-2/": "clean", "/ניקוי-מיני-מרכזי/": "clean",
    "/ניקוי-מזגן-מעובש-מידע-ומחירים/": "clean", "/ניקוי-מזגנים-בצפון/": "clean",
    # sizes and prices
    "/מחירון-מזגנים/": "sizes", "/מזגן-חצי-כוח-סוס/": "sizes",
    "/התקנת-מזגן-1-כוח-סוס/": "sizes", "/התקנת-מזגן-1-25-כוח-סוס/": "sizes",
    "/מזגן-1-5-כוח-סוס/": "sizes", "/התקנת-מזגן-2-כוח-סוס/": "sizes",
    "/מזגן-2-5-כוח-סוס/": "sizes", "/התקנת-מזגן-3-כוח-סוס/": "sizes",
    "/מזגן-3-5-כוח-סוס/": "sizes", "/התקנת-מזגן-5-כוח-סוס/": "sizes",
    "/כמה-עולה-מזגן-לשעה/": "sizes",
    # buying guides
    "/איזה-מזגן-הכי-טוב/": "guides", "/מזגן-אינוורטר-חסרונות-ויתרונות/": "guides",
    "/מזגן-לחדר-שינה/": "guides", "/מזגן-מולטי-איוורטר/": "guides",
    "/מזגן-חלון/": "guides", "/מזגן-אלקטרה-1-כס/": "guides",
    "/מערכות-מיזוג-חכמות-בבנייה-ירוקה/": "guides", "/קורס-טכנאי-מזגנים/": "guides",
    "/בלוג/": "guides", "/category/בלוג/": "guides",
}

MAX_LINKS = 8

# Region hubs the site already has. A city page leads with its own region, so
# the sidebar says something true about where the reader is — cities whose
# region is genuinely ambiguous (Jerusalem, Ariel) simply get no region line.
REGION_PAGES = {
    "north": ("/טכנאי-מזגנים-צפון/", "טכנאי מזגנים בצפון"),
    "center": ("/טכנאי-מזגנים-במרכז/", "טכנאי מזגנים במרכז"),
    "south": ("/טכנאי-מזגנים-בדרום/", "טכנאי מזגנים בדרום"),
}

CITY_REGION = {
    # north
    "חיפה": "north", "נשר": "north", "קריות": "north", "עתלית": "north",
    "טבריה": "north", "בית-שאן": "north", "עפולה": "north", "כרמיאל": "north",
    "יקנעם": "north", "זכרון-יעקב": "north", "בנימינה": "north",
    "קיסריה": "north", "אור-עקיבא": "north", "חדרה": "north",
    "פרדס-חנה": "north", "חריש": "north",
    # south
    "באר-שבע": "south", "אשקלון": "south", "אשדוד": "south",
    "קריית-גת": "south", "אופקים": "south",
    # center
    "תל-אביב": "center", "רמת-גן": "center", "גבעתיים": "center",
    "בני-ברק": "center", "חולון": "center", "בת-ים": "center",
    "ראשון-לציון": "center", "רחובות": "center", "נס-ציונה": "center",
    "יבנה": "center", "גן-יבנה": "center", "גדרה": "center",
    "מזכרת-בתיה": "center", "רמלה": "center", "לוד": "center",
    "מודיעין": "center", "פתח-תקווה": "center", "ראש-העין": "center",
    "אלעד": "center", "שוהם": "center", "יהוד": "center",
    "אור-יהודה": "center", "קריית-אונו": "center", "גני-תקווה": "center",
    "סביון": "center", "גבעת-שמואל": "center", "בית-דגן": "center",
    "הרצליה": "center", "רעננה": "center", "כפר-סבא": "center",
    "הוד-השרון": "center", "נתניה": "center", "אבן-יהודה": "center",
    "תל-מונד": "center", "כפר-יונה": "center", "קדימה-צורן": "center",
}


def region_link_for(path):
    """The region hub a city page belongs to, when it is unambiguous."""
    if not path.startswith("/טכנאי-מזגנים-ב"):
        return None
    slug = path.strip("/")[len("טכנאי-מזגנים-ב"):].rstrip("-0123456789")
    region = CITY_REGION.get(slug)
    if not region:
        return None
    href, text = REGION_PAGES[region]
    if href == path:
        return None
    return {"href": href, "text": text}


def group_for(path):
    """Which cluster this page belongs to."""
    if path in PAGE_GROUP:
        return PAGE_GROUP[path]
    # a city page visitor came to buy a service, so show services, not more cities —
    # neighbouring cities are already linked from the "קראו גם" block below the article
    return "services"


def sidebar_for(path):
    """The rendered link list for a page: its cluster, minus the page itself."""
    key = group_for(path)
    group = GROUPS[key]
    links = [{"href": href, "text": text}
             for href, text in group["links"] if href != path]

    region = region_link_for(path)
    if region:
        links = [region] + [l for l in links if l["href"] != region["href"]]

    return {"key": key, "title": group["title"], "icon": group["icon"],
            "links": links[:MAX_LINKS]}
