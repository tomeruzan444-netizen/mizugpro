# -*- coding: utf-8 -*-
"""
Sections in the blog, and the articles inside them.

The blog listing came over from WordPress as a flat run of four articles
hardcoded into /בלוג/ and /category/בלוג/. There was no way to group them, and
no single place to add one.

This file is that place. To add an article to a section, add one entry to its
`articles` list and publish the article page itself - nothing else. The section
is rendered into both blog pages and into its own hub page's listing, so the
three never drift apart.

    {"href": "/קוד-שגיאה-e1-במזגן/",
     "title": "קוד שגיאה E1 במזגן - מה הוא אומר",
     "excerpt": "המשפט הראשון של המאמר, שתי שורות."}

Order inside a section is the order of the list: newest first is the usual
choice, but it is a decision and not a default.

Nothing existing is touched. The section is appended after the articles that
are already on the page.
"""
CHANGES = []

SECTIONS = [
 {
  "key": "faults",
  # the hub page that carries the section's own copy
  "hub": "/תקלות-וקודי-שגיאה-במזגנים/",
  "title": "תקלות וקודי שגיאה במזגנים",
  "intro": "מה עושים כשהמזגן מציג קוד, נעצר מעצמו או עובד חצי. כל מדריך כאן "
           "מתחיל מהסימן שאתם רואים ולא מהרכיב, כי זה הסדר שבו אפשר לאבחן "
           "בטלפון ולדעת מה המחיר לפני שמזמינים טכנאי.",
  "articles": [
   {"href": "/מזגן-מהבהב/",
    "title": "מזגן מהבהב - מה זה אומר ואיך מתקנים",
    "excerpt": "ביחידות בלי צג, נורה שמהבהבת היא הקוד: מספר ההבהובים מדווח "
               "איזו הגנה נתקה. מה לספור, אילו שלוש בדיקות לעשות לבד ומה לא "
               "לעשות בשום מקרה."},
   {"href": "/קודי-שגיאה-מזגן-אלקטרה/",
    "title": "קודי שגיאה מזגן אלקטרה - איך קוראים אותם נכון",
    "excerpt": "אלקטרה משווקת קווי דגמים שונים, וטבלת הקודים משתנה ביניהם - "
               "אותו E5 אינו אותו E5. איך מזהים את הדגם ומה לרשום לפני "
               "שמתקשרים."},
   {"href": "/תקלות-וקודי-שגיאה-במזגנים/",
    "title": "קודי שגיאה במזגן - איך קוראים אותם ומה לעשות",
    "excerpt": "קוד שגיאה אומר איזו הגנה נתקה, לא מה נשרף, והוא שונה בין "
               "יצרן ליצרן. מה שכן זהה בכולם הוא שלושת הפרטים שכדאי לרשום "
               "לפני שמתקשרים."},
   {"href": "/קצר-במזגן/",
    "title": "קצר במזגן - למה הוא נעצר אחרי דקות",
    "excerpt": "מזגן שמקצר אחרי דקות ספורות מצביע על תקלה חשמלית; אחרי שעה "
               "או שעתיים - על משהו תרמי. העיתוי הוא הרמז הכי חשוב לאבחון."},
   {"href": "/המזגן-לא-מקרר/",
    "title": "המזגן לא מקרר - חמש סיבות ואיך לזהות כל אחת",
    "excerpt": "מחסור בגז, מסננים סתומים, מעבה מלוכלך, תקלה במדחס או במערכת "
               "החשמל. ארבע בדיקות של חמש דקות מצמצמות את הרשימה."},
   {"href": "/מזגן-לא-מחמם/",
    "title": "המזגן לא מחמם - עשר סיבות ומחירי תיקון",
    "excerpt": "מזגן שמקרר אבל לא מחמם מצביע כמעט תמיד על השסתום המהפך. "
               "מזגן שמחמם חלש הוא סיפור אחר לגמרי."},
   {"href": "/מזגן-מטפטף/",
    "title": "מזגן מטפטף - מאיפה המים ומה זה אומר",
    "excerpt": "המקום שממנו יורדים המים קובע את האבחנה: מהיחידה הפנימית זה "
               "ניקוז, מהתריס זה מאייד שקפא, ובחוץ זה בדרך כלל תקין."},
   {"href": "/מזגן-רועש/",
    "title": "מזגן רועש - מה מרעיש ומה עושים",
    "excerpt": "הרעש כמעט תמיד מגיע ממה שמחזיק את המזגן ולא מהמזגן: ברגים, "
               "בולמי רעד או תושבת שנוגעת בקיר."},
   {"href": "/ריח-רע-מהמזגן/",
    "title": "ריח רע מהמזגן - שלושה מקורות, שלושה פתרונות",
    "excerpt": "ריח טחב מגיע מהמאייד, ריח חמצמץ מקו ניקוז עומד, וריח שרוף "
               "מחייב כיבוי מיידי."},
  ],
 },
]

# the blog pages the sections are appended to
BLOG_PAGES = ("/בלוג/", "/category/בלוג/")


def _blocks(section):
    """A section rendered as content blocks, in the shape the blog already uses:
    a linked heading per article with a short excerpt under it."""
    out = [
        {"type": "heading", "level": 2, "text": section["title"],
         "html": section["title"]},
        {"type": "paragraph", "html": section["intro"]},
    ]
    for a in section["articles"]:
        title = '<a href="%s">%s</a>' % (a["href"], a["title"])
        out.append({"type": "heading", "level": 3, "text": a["title"],
                    "html": title})
        out.append({"type": "paragraph", "html": a["excerpt"]})
    return out


def apply(page):
    """Append every section to the blog listing pages. Adds only."""
    if page["path"] not in BLOG_PAGES:
        return page
    for section in SECTIONS:
        titles = {b.get("text") for b in page["blocks"]
                  if b.get("type") == "heading"}
        if section["title"] in titles:
            continue
        page["blocks"].extend(_blocks(section))
        CHANGES.append({"path": page["path"], "section": section["title"],
                        "articles": len(section["articles"])})
    return page
