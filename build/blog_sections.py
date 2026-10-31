# -*- coding: utf-8 -*-
"""
The blog index: categories, and the articles inside them.

The blog came over from WordPress as four articles hardcoded into /בלוג/ and
/category/בלוג/ - each one a thumbnail, a linked heading and its entire opening
paragraph, stacked in a single column. Nothing grouped them, the two pages had
to be edited separately, and the only way to find a guide was to read the whole
page. Twenty-three guides now exist on the site; fourteen of them were not
listed on the blog at all.

This file is the index. A category declares its title, its icon and its
articles; the articles render as cards, and the whole thing is built into both
blog pages from one definition so they cannot drift apart. To add an article:
one entry, in one list.

    {"href": "/מזגן-מהבהב/",
     "title": "מזגן מהבהב - מה זה אומר ואיך מתקנים",
     "text": "ביחידה בלי צג, מספר ההבהובים הוא הקוד."}

Three things make it navigable rather than merely sorted. The chip row under
the intro jumps to a category and shows how many guides are in it, which is
what a phone reader gets instead of the sidebar. The category headings carry
explicit ids, so site.js lists them in the rail's table of contents and
highlights the one being read. And the excerpts are one line each, so a
category is scannable at a glance instead of being read.

What the flat run gave up: the four opening paragraphs, which are each the
article's own first paragraph and are still there on the article itself, and
four WordPress thumbnails - two of which were the same picture on different
articles, and one of which was the company logo. A listing illustrated with
the wrong images is not an illustrated listing.

The prices in the excerpts say nothing a page does not say itself, and no
excerpt claims a figure: a card is an invitation to the guide, not a summary
that can go stale separately from it.
"""
CHANGES = []

CATEGORIES = [
 {
  "key": "faults",
  "title": "תקלות ואבחון",
  "icon": "wrench",
  "intro": "המדריכים כאן מתחילים מהסימן שאתם רואים - קוד על הצג, נורה "
           "שמהבהבת, רעש או מים על הקיר - ולא מהרכיב שאולי אשם. זה הסדר שבו "
           "אפשר לאבחן בטלפון ולדעת מה טווח המחיר לפני שמזמינים טכנאי.",
  "articles": [
   {"href": "/תקלות-וקודי-שגיאה-במזגנים/",
    "title": "קודי שגיאה במזגן - איך קוראים אותם",
    "text": "קוד שגיאה אומר איזו הגנה נתקה, לא מה נשרף. חמש משפחות ההגנה "
            "וארבעה פרטים שכדאי לרשום לפני שמתקשרים."},
   {"href": "/מזגן-מהבהב/",
    "title": "מזגן מהבהב - מה זה אומר",
    "text": "ביחידה בלי צג מספר ההבהובים הוא הקוד. מה לספור, ואילו שלוש "
            "בדיקות אפשר לעשות לבד בחמש דקות."},
   {"href": "/קודי-שגיאה-מזגן-אלקטרה/",
    "title": "קודי שגיאה מזגן אלקטרה",
    "text": "באלקטרה אותו קוד אומר דברים שונים בדגמים שונים. איך מזהים את "
            "הדגם ומה לרשום לפני שמתקשרים."},
   {"href": "/קצר-במזגן/",
    "title": "קצר במזגן - למה הוא נעצר",
    "text": "מזגן שנעצר אחרי דקות ספורות מצביע על תקלה חשמלית; אחרי שעה - "
            "על משהו תרמי. העיתוי הוא הרמז."},
   {"href": "/המזגן-לא-מקרר/",
    "title": "המזגן לא מקרר",
    "text": "חמש סיבות, מגז חסר ועד מעבה מלוכלך, וארבע בדיקות שמצמצמות את "
            "הרשימה לפני שמזמינים ביקור."},
   {"href": "/מזגן-לא-מחמם/",
    "title": "המזגן לא מחמם",
    "text": "מזגן שמקרר אבל לא מחמם מצביע כמעט תמיד על השסתום המהפך. עשר "
            "סיבות ומחירי תיקון."},
   {"href": "/מזגן-מטפטף/",
    "title": "מזגן מטפטף - מאיפה המים",
    "text": "המקום שממנו יורדים המים קובע את האבחנה: ניקוז סתום, מאייד שקפא, "
            "או טפטוף תקין לגמרי בחוץ."},
   {"href": "/מזגן-רועש/",
    "title": "מזגן רועש - מה מרעיש",
    "text": "הרעש כמעט תמיד מגיע ממה שמחזיק את המזגן ולא מהמזגן: ברגים, "
            "בולמי רעד או תושבת שנוגעת בקיר."},
   {"href": "/ריח-רע-מהמזגן/",
    "title": "ריח רע מהמזגן",
    "text": "ריח טחב מגיע מהמאייד, ריח חמצמץ מקו ניקוז עומד, וריח שרוף מחייב "
            "כיבוי מיידי מהמפסק."},
  ],
 },
 {
  "key": "choose",
  "title": "בחירת מזגן וסוגים",
  "icon": "ac-unit",
  "intro": "לפני שקונים: איזה סוג מזגן מתאים לחלל, איזה גודל צריך בשביל חדר "
           "בגודל שלכם, ומה ההבדל שבאמת מרגישים אחר כך בחשבון החשמל.",
  "articles": [
   {"href": "/איזה-מזגן-הכי-טוב/",
    "title": "איזה מזגן הכי טוב?",
    "text": "הקריטריונים שבאמת מבדילים בין מזגנים, והשוואה בין המותגים "
            "הנפוצים בשוק הישראלי."},
   {"href": "/מזגן-אינוורטר-חסרונות-ויתרונות/",
    "title": "מזגן אינוורטר - יתרונות וחסרונות",
    "text": "איך אינוורטר עובד, מה הוא חוסך בפועל ומתי הוא לא הבחירה הנכונה. "
            "כולל טבלת השוואה."},
   {"href": "/מזגן-מולטי-איוורטר/",
    "title": "מזגן מולטי אינוורטר",
    "text": "מערכת אחת לכמה חדרים: איך זה עובד, למי זה מתאים, ומה המחיר כולל "
            "התקנה."},
   {"href": "/מזגן-לחדר-שינה/",
    "title": "מזגן לחדר שינה",
    "text": "מה חשוב דווקא בחדר שינה - רעש, עוצמה ומיקום ההתקנה - ואיזה גודל "
            "מתאים לחדר שלכם."},
   {"href": "/מזגן-חלון/",
    "title": "מזגן חלון - האם כדאי",
    "text": "מהו מזגן חלון, מתי הוא עדיין הפתרון הנכון, וטבלת מחירים של "
            "הדגמים המובילים."},
   {"href": "/מזגן-אלקטרה-1-כס/",
    "title": "מזגן אלקטרה 1 כ\"ס",
    "text": "הגודל שמתאים לחדרים בינוניים עד כ-15 מ\"ר: תהליך ההתקנה, "
            "יתרונות ומחירים."},
   {"href": "/מזגן-חצי-כוח-סוס/",
    "title": "מזגן חצי כוח סוס (0.5 כ\"ס)",
    "text": "לאילו חללים 0.5 כ\"ס באמת מספיק, ומתי עדיף לעלות גודל אחד "
            "למעלה."},
   {"href": "/מערכות-מיזוג-חכמות-בבנייה-ירוקה/",
    "title": "מערכות מיזוג חכמות בבנייה ירוקה",
    "text": "מה הופך מערכת מיזוג לחכמה, איך היא נכנסת לתכנון של בנייה ירוקה "
            "ומה זה אומר על הצריכה."},
  ],
 },
 {
  "key": "prices",
  "title": "מחירים ועלות הפעלה",
  "icon": "price",
  "intro": "כמה עולה העבודה, וכמה עולה להפעיל את המזגן אחר כך. כל המחירים "
           "באתר הם לפני מע\"מ, והמחיר הסופי נמסר לפני שמתחילים לעבוד.",
  "articles": [
   {"href": "/מחירון-מזגנים/",
    "title": "מחירון מזגנים",
    "text": "המחירון המלא: התקנה, תיקון, ניקוי והחלפת חלקים, עם טווח לכל "
            "סוג עבודה."},
   {"href": "/כמה-עולה-מזגן-לשעה/",
    "title": "כמה עולה מזגן לשעה",
    "text": "צריכת החשמל של מזגן ומה היא אומרת בשקלים - לשעה, לשבוע "
            "ולחודש."},
  ],
 },
 {
  "key": "care",
  "title": "התקנה, תחזוקה ואחריות",
  "icon": "shield",
  "intro": "מה קורה סביב ההתקנה ואחריה: מה האחריות מכסה, איך מתחזקים כדי "
           "שתקלה לא תחזור, ומה עושים כשצריך לפרק.",
  "articles": [
   {"href": "/אחריות-על-התקנת-מזגן/",
    "title": "אחריות על התקנת מזגן",
    "text": "מה אחריות התקנה כוללת, מה היא לא כוללת, וכמה זמן מקובל לתת "
            "עליה בשוק."},
   {"href": "/פירוק-מזגן/",
    "title": "פירוק מזגן",
    "text": "פירוק לפני צבע, שיפוץ או מעבר דירה: מה חשוב בתהליך כדי שהמזגן "
            "יעבוד גם אחרי ההרכבה."},
   {"href": "/ניקוי-מזגן-מעובש-מידע-ומחירים/",
    "title": "ניקוי מזגן מעובש",
    "text": "איך מזהים עובש, למה הוא חוזר אחרי ניקוי שטחי, ומה כולל ניקוי "
            "בקיטור."},
   {"href": "/ניקוי-מיני-מרכזי/",
    "title": "ניקוי מזגן מיני מרכזי",
    "text": "למה ניקוי מיני מרכזי שונה מניקוי עילי: מה נפתח, מה מנקים ומתי "
            "זה נדרש."},
  ],
 },
]

# the two blog pages the index is built into
BLOG_PAGES = ("/בלוג/", "/category/בלוג/")

# /category/בלוג/ carries the same index as /בלוג/, so it points its canonical
# there instead of competing with it. The value is the encoded form the rest of
# the extract uses.
CANONICAL = {"/category/בלוג/": "https://mizugpro.co.il/%d7%91%d7%9c%d7%95%d7%92/"}

INTRO = ("כל המדריכים של מיזוג פרו, לפי נושא. כל מדריך פותח בשאלה שבגללה "
         "חיפשתם אותו, ונותן טווח מחירים לפני שמזמינים טכנאי - בחרו קטגוריה "
         "או גללו למטה.")

# the articles the flat WordPress run listed: their blocks come out, and each
# one is a card in its category instead
LISTED = ("/מערכות-מיזוג-חכמות-בבנייה-ירוקה/", "/כמה-עולה-מזגן-לשעה/",
          "/אחריות-על-התקנת-מזגן/", "/איזה-מזגן-הכי-טוב/")


def _index_blocks():
    """The index: intro, a chip row per category, then the categories."""
    out = [
        {"type": "paragraph", "html": INTRO},
        {"type": "chipnav", "links": [
            {"href": "#" + c["key"], "icon": c["icon"],
             "text": "%s (%d)" % (c["title"], len(c["articles"]))}
            for c in CATEGORIES]},
    ]
    for c in CATEGORIES:
        out.append({"type": "heading", "level": 2, "id": c["key"],
                    "text": c["title"], "html": c["title"]})
        out.append({"type": "paragraph", "html": c["intro"]})
        out.append({"type": "cardgrid", "cols": 2, "items": [
            dict(a, cta="קראו את המדריך") for a in c["articles"]]})
    return out


def _strip_flat_run(page):
    """Remove the flat article run, and report where it started.

    Each entry is a linked heading, the paragraph after it and the thumbnail
    beside it, in either order - /בלוג/ puts the image first and
    /category/בלוג/ puts it second. Raises rather than guessing: a listing
    that quietly keeps both shapes is how a page ends up with the articles
    twice.
    """
    blocks = page["blocks"]
    heads = [i for i, b in enumerate(blocks)
             if b.get("type") == "heading"
             and any('href="%s"' % p in (b.get("html") or "") for p in LISTED)]
    if len(heads) != len(LISTED):
        raise SystemExit("blog_sections: expected %d listed articles on %s, "
                         "found %d" % (len(LISTED), page["path"], len(heads)))

    drop = set()
    for i in heads:
        drop.add(i)
        for j in (i - 1, i + 1, i + 2):
            if 0 <= j < len(blocks) and j not in heads:
                t = blocks[j].get("type")
                if t == "image" or (t == "paragraph" and j > i):
                    drop.add(j)
    at = min(drop)
    page["blocks"] = [b for i, b in enumerate(blocks) if i not in drop]
    return at - sum(1 for d in drop if d < at)


def apply(page):
    """Build the index into both blog pages, in place of the flat run."""
    if page["path"] not in BLOG_PAGES:
        return page
    if any(b.get("type") == "cardgrid" for b in page["blocks"]):
        return page

    at = _strip_flat_run(page)
    page["blocks"][at:at] = _index_blocks()
    if page["path"] in CANONICAL:
        page["canonical"] = CANONICAL[page["path"]]
    CHANGES.append({"path": page["path"], "categories": len(CATEGORIES),
                    "articles": sum(len(c["articles"]) for c in CATEGORIES)})
    return page
