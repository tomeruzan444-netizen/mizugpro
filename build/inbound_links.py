# -*- coding: utf-8 -*-
"""
Give every page written after the migration inbound links from within prose.

The build already hands each page six related links, but they all sit in the
same templated "אזורי שירות נוספים" grid with the page title as the anchor
text. That is a footer-shaped link, and it is worth far less than a link
inside a sentence that had a reason to be written.

So each new page also gets one to three links from the pages most relevant to
it - for a city page, the councils that actually border it. The reason is
stated out loud in the sentence ("גובלת ... ממזרח", "אותו צוות"), because a
link whose only justification is SEO reads like one.

Directions here are checked, not assumed - the Azor page was published on an
invented description of the town, and that is the mistake this file refuses to
repeat. Sources: he.wikipedia.org entries for אזור, רמת השרון and באר יעקב.
    אזור        borders Tel Aviv-Yafo (N), Bat Yam (W), Rishon LeZion (SE)
    רמת השרון   borders Herzliya (N), Hod Hasharon (E), Tel Aviv-Yafo (S)
    באר יעקב    borders Rishon LeZion (N,W), Nes Tziona (W); near Ramla, Lod

Nothing is deleted and no existing sentence is rewritten: the sentence is
appended to the end of a paragraph that was already about coverage or about
the crew, so it continues the thought instead of interrupting it. An anchor
that stops matching raises - a silently skipped insert is how a page ends up
with no inbound link and nobody notices.
"""
import re

CHANGES = []

# source page -> (anchor: start of the paragraph to append to, sentence)
LINKS = {
 # ---- אזור -------------------------------------------------------------
 "/טכנאי-מזגנים-בבת-ים/": [(
  "בקיצור אם אתם צריכים טכנאי מזגנים בבת ים",
  ' אזור שוכנת ממש ממזרח לבת ים, ואותו צוות מכסה את שתי הרשויות באותו יום - '
  'אם יש לכם נכס גם שם, <a href="/טכנאי-מזגנים-באזור/">טכנאי מזגנים באזור</a> '
  'יוצא מאותה משאית.')],

 "/טכנאי-מזגנים-בראשון-לציון/": [(
  "כשמדובר בשירות התקנה ותיקון מזגנים",
  ' אותו עיקרון עובד גם ביישובים שגובלים בראשון לציון מצפון: '
  '<a href="/טכנאי-מזגנים-באזור/">טכנאי מזגנים באזור</a> מגיע מאותו צוות ועם '
  'אותו מחירון, בלי תוספת על מרחק.')],

 "/טכנאי-מזגנים-בחולון/": [(
  "מתגאה בצוות טכנאים מנוסה",
  ' אותם טכנאים עובדים גם ביישובים הסמוכים, כמה דקות נסיעה מחולון - למשל '
  '<a href="/טכנאי-מזגנים-באזור/">טכנאי מזגנים באזור</a>, שם השיכונים משנות '
  'החמישים מצריכים עבודה על תושבת בקיר החיצוני ולא על מרפסת שירות.')],

 # ---- רמת השרון --------------------------------------------------------
 "/טכנאי-מזגנים-בהרצליה/": [(
  "בחירה בטכנאי מזגנים מקצועי כמו מיזוג פרו",
  ' רמת השרון גובלת בהרצליה מדרום ואותו צוות מכסה את שתיהן, כך שאם חיפשתם '
  '<a href="/טכנאי-מזגנים-ברמת-השרון/">טכנאי מזגנים ברמת השרון</a> מדובר '
  'באותו שירות ובאותו מחירון.')],

 "/טכנאי-מזגנים-בהוד-השרון/": [(
  "חברת מיזוג פרו מספקת מגוון רחב של שירותי מזגנים לתושבי הוד השרון",
  ' הסביבה הזאת קרובה מאוד: רמת השרון גובלת בהוד השרון ממערב, ו'
  '<a href="/טכנאי-מזגנים-ברמת-השרון/">טכנאי מזגנים ברמת השרון</a> יוצא '
  'לשתיהן מאותה נקודה.')],

 "/טכנאי-מזגנים-בתל-אביב/": [(
  "חשוב לציין שזיהוי ותיקון תקלות במזגן דורשים ידע ומומחיות",
  ' אותו טכנאי מוסמך מכסה גם את הרשויות שגובלות בתל אביב מצפון - '
  '<a href="/טכנאי-מזגנים-ברמת-השרון/">טכנאי מזגנים ברמת השרון</a> הוא אותו '
  'צוות ואותו מחירון.')],

 # ---- באר יעקב ---------------------------------------------------------
 "/טכנאי-מזגנים-בנס-ציונה/": [(
  "חשוב לבחור טכנאי בעל ניסיון והסמכה מתאימה",
  ' באר יעקב גובלת בנס ציונה ממזרח ואותו טכנאי מוסמך מכסה את שתיהן, כך '
  'ש<a href="/טכנאי-מזגנים-בבאר-יעקב/">טכנאי מזגנים בבאר יעקב</a> הוא אותו '
  'צוות בדיוק.')],

 "/טכנאי-מזגנים-ברמלה/": [(
  "מזגן תקול עלול לשבש את שגרת היום",
  ' אותה זמינות תקפה גם ליישובים הסמוכים לרמלה, וביניהם באר יעקב - '
  '<a href="/טכנאי-מזגנים-בבאר-יעקב/">טכנאי מזגנים בבאר יעקב</a> מגיע מאותה '
  'משאית ובאותו זמן תגובה.')],

 # ---- קריית עקרון -------------------------------------------------------
 # borders Rehovot to its north (verified); Mazkeret Batya is "near" it with no
 # direction given, so that sentence says near and nothing more
 "/טכנאי-מזגנים-ברחובות/": [(
  "מתגאה בצוות טכנאים מנוסה",
  ' קריית עקרון גובלת ברחובות מדרום, ואותם טכנאים מכסים את שתיהן באותו יום - '
  '<a href="/טכנאי-מזגנים-בקריית-עקרון/">טכנאי מזגנים בקריית עקרון</a> מגיע '
  'מאותו צוות ועם אותו מחירון.')],

 "/טכנאי-מזגנים-במזכרת-בתיה/": [(
  "צוות הטכנאים המיומן של מיזוג פרו מצויד",
  ' אותו צוות עובד גם בקריית עקרון הסמוכה, כך ש'
  '<a href="/טכנאי-מזגנים-בקריית-עקרון/">טכנאי מזגנים בקריית עקרון</a> מקבל '
  'את אותו מענה ואת אותם כלים.')],

 "/טכנאי-מזגנים-בלוד/": [(
  "אל תהססו לפנות אלינו",
  ' השירות לא נעצר בגבול העיר: באר יעקב נמצאת כמה דקות נסיעה מלוד, ו'
  '<a href="/טכנאי-מזגנים-בבאר-יעקב/">טכנאי מזגנים בבאר יעקב</a> מקבל את אותו '
  'מענה ואת אותו מחירון.')],
}

_TAGS = re.compile(r"<[^>]+>")


def apply(page):
    """Append each sentence to its anchor paragraph. Adds only, never edits."""
    spec = LINKS.get(page["path"])
    if not spec:
        return page

    for anchor, sentence in spec:
        for b in page["blocks"]:
            if b.get("type") != "paragraph":
                continue
            text = _TAGS.sub("", b.get("html") or "").strip()
            if text.startswith(anchor) or anchor in text:
                b["html"] = (b["html"] or "").rstrip() + sentence
                target = re.search(r'href="([^"]+)"', sentence).group(1)
                CHANGES.append({"from": page["path"], "to": target})
                break
        else:
            raise SystemExit(
                "inbound_links: anchor no longer matches on %s: %r"
                % (page["path"], anchor))
    return page
