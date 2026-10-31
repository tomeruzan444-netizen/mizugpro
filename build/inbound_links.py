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

 # ---- תקלות וקודי שגיאה --------------------------------------------------
 # the two fault pages where a reader is most likely to be holding a code
 "/קצר-במזגן/": [(
  "חשוב לציין שתיקון קצר במזגן דורש ידע וניסיון מקצועיים",
  ' אם המזגן גם מציג קוד על הצג, שווה לדעת מה הוא מדווח לפני שמחליפים רכיב: '
  '<a href="/תקלות-וקודי-שגיאה-במזגנים/">תקלות וקודי שגיאה במזגנים</a> מסביר '
  'איזו הגנה כל קוד מייצג ומה לרשום לפני שמתקשרים.'),
  ("קצר חשמלי במזגן הוא תקלה נפוצה",
   ' ולפני שבודקים רכיב כדאי לראות איך המזגן מדווח על עצמו: אם נורה מהבהבת '
   'במקום להידלק קבוע, <a href="/מזגן-מהבהב/">מזגן מהבהב</a> מראה מה לספור '
   'ומה זה אומר.')],

 # anchored on a source paragraph: gsc_answers adds its text later in the
 # pipeline, so an anchor taken from there is not here yet when this runs
 "/תיקון-מזגנים/": [(
  "היי, הגעתם למיזוג פרו. מומחים בכל מה שקשור לתיקון והתקנת מזגן",
  ' כשהמזגן מציג קוד ולא רק נכבה, אפשר לצמצם את האבחון עוד לפני הביקור - '
  '<a href="/תקלות-וקודי-שגיאה-במזגנים/">תקלות וקודי שגיאה במזגנים</a> מרכז '
  'את משפחות ההגנה ואת מה שכדאי לרשום מהצג.')],

 # ---- פרדסיה -------------------------------------------------------------
 # both relations are on the record: Kfar Yona borders it to the north and
 # east, and Pardesiya sits east of Netanya
 "/טכנאי-מזגנים-בכפר-יונה/": [(
  "במיזוג פרו אנו גאים בצוות טכנאי המזגנים המיומן והמנוסה שלנו",
  ' פרדסיה גובלת בכפר יונה מדרום וממערב, ואותו צוות מכסה את שתיהן באותו יום '
  '- <a href="/טכנאי-מזגנים-בפרדסיה/">טכנאי מזגנים בפרדסיה</a> מגיע מאותה '
  'משאית ועם אותו מחירון.')],

 "/טכנאי-מזגנים-בנתניה/": [(
  # anchored before "איזור", which content_fixes corrects to "אזור" earlier
  # in the pipeline - the longer anchor stopped matching and raised
  "בין אם אתם צריכים טכנאי מזגנים בנתניה או בכל",
  ' פרדסיה, למשל, שוכנת ממש ממזרח לנתניה, ו'
  '<a href="/טכנאי-מזגנים-בפרדסיה/">טכנאי מזגנים בפרדסיה</a> יוצא לשתיהן '
  'מאותה נקודה.')],

 # ---- כוכב יאיר צור יגאל ------------------------------------------------
 # Wikipedia gives its borders as Tzur Yitzhak, Eyal, Tira and the South
 # Sharon Regional Council - none of which has a page here. So these two
 # sentences say "in the eastern Sharon" and "a few minutes away", and claim
 # no border that is not on the record.
 "/טכנאי-מזגנים-בכפר-סבא/": [(
  "ניסיון ומומחיות: צוות טכנאי מיזוג פרו מורכב",
  ' אותו צוות עובד גם בשרון המזרחי, כמה דקות נסיעה מכאן - '
  '<a href="/טכנאי-מזגנים-בכוכב-יאיר-צור-יגאל/">טכנאי מזגנים בכוכב יאיר צור '
  'יגאל</a> מגיע מאותה משאית ועם אותו מחירון.')],

 "/טכנאי-מזגנים-בתל-מונד/": [(
  "מיזוג פרו מבינה שתקלות במזגן יכולות להתרחש בכל עת",
  ' אותה זמינות תקפה גם ליישובי השרון המזרחי, וביניהם כוכב יאיר צור יגאל - '
  '<a href="/טכנאי-מזגנים-בכוכב-יאיר-צור-יגאל/">טכנאי מזגנים בכוכב יאיר צור '
  'יגאל</a> מקבל את אותו מענה ואת אותו זמן תגובה.')],

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

 # ---- מזגן מהבהב --------------------------------------------------------
 # the two pages whose reader is most likely to be looking at a blinking
 # light rather than a code on a display
 "/תקלות-וקודי-שגיאה-במזגנים/": [(
  "לא כל תקלה מגיעה עם קוד",
  ' וביחידות בלי צג אין קוד בכלל - שם <a href="/מזגן-מהבהב/">מזגן מהבהב</a> '
  'מסביר מה לספור.'),
  ("E1 אצל יצרן אחד",
   ' זה נכון גם בתוך אותו מותג: <a href="/קודי-שגיאה-מזגן-אלקטרה/">קודי '
   'שגיאה מזגן אלקטרה</a> מסביר למה אין טבלה אחת לכל הדגמים.')],

 # ---- קודי שגיאה אלקטרה --------------------------------------------------
 "/המזגן-לא-מקרר/": [(
  "למרות שישנן פעולות תחזוקה בסיסיות שתוכלו לבצע בעצמכם",
  ' סימן נוסף שמחייב טכנאי הוא קוד שגיאה על הצג, ושם כדאי להתחיל מזיהוי '
  'הדגם: <a href="/קודי-שגיאה-מזגן-אלקטרה/">קודי שגיאה מזגן אלקטרה</a> מסביר '
  'מה לרשום לפני שמתקשרים.')],

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
