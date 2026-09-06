# -*- coding: utf-8 -*-
"""
Answer the Search Console questions the site was not answering.

Six months of queries, grouped into questions rather than counted as rows -
"כמה עולה מזגן לשעה" and "כמה כסף מזגן לשעה" are one question asked twice. Of
the 39 real questions, 35 were already answered somewhere on the right page.
These are the rest.

Each entry adds an h3 carrying the question in the words people search with,
and one paragraph that answers it. Nothing existing is touched, and no price
is invented: figures come from the canonical table in CONTENT-GUIDE.md or from
the page's own numbers.

Anchors work like phrase_inserts:
    before_faq          just above the FAQ
    after_heading:TEXT  after the first heading starting with TEXT
"""
import re

CHANGES = []

ANSWERS = {
 "/תיקון-מזגנים/": [
  {"at": "before_faq",
   "impressions": 650,
   "q": "כמה עולה להחליף יחידה פנימית של מזגן?",
   "a": "זו אחת השאלות שאנחנו הכי הרבה נשאלים, והתשובה הכנה היא שברוב המקרים "
        "לא כדאי להחליף רק את היחידה הפנימית. מאייד חדש צריך להתאים למעבה "
        "הקיים בהספק ובסוג הגז, ובמזגן בן עשר שנים ההתאמה הזאת כבר לא תמיד "
        "אפשרית - הדגם יצא מייצור והגז שבמערכת אינו הגז שבשימוש היום. כשההתאמה "
        "כן אפשרית, המחיר תלוי בדגם ואנחנו מוסרים אותו אחרי שראינו את היחידה. "
        "כשהיא לא, עדיף להשוות מול החלפת המערכת כולה, שבמזגן עילי 1 כוח סוס "
        "מתחילה ב-750 עד 1,200 ש\"ח להתקנה. בביקור האבחון נגיד לכם לאיזה משני "
        "המסלולים אתם שייכים, ולמה."},
  {"at": "before_faq",
   "impressions": 24,
   "q": "כמה עולה ביקור טכנאי מזגנים?",
   "a": "ביקור אבחון עולה 150 עד 350 ש\"ח לפני מע\"מ, והפער נובע ממרחק, משעה "
        "ומדחיפות. אם אתם מבצעים את התיקון באותו ביקור, עלות הביקור מתקזזת מול "
        "מחיר התיקון - כלומר בפועל אתם משלמים על העבודה ולא על ההגעה. אנחנו "
        "מוסרים את המחיר הסופי לפני שמתחילים, ואם בזמן האבחון מתברר שהתקלה "
        "אחרת ממה שדווח בטלפון, אומרים את זה בזמן אמת ולא בסוף."},
 ],

 "/פירוק-מזגן/": [
  {"at": "before_faq",
   "impressions": 54,
   "q": "כמה עולה להזיז מזגן ממקום למקום?",
   "a": "העברת מזגן היא שתי עבודות ולא אחת: פירוק במקום הישן והתקנה מחדש "
        "בחדש. פירוק בלבד עולה 250 עד 400 ש\"ח, והעברה מלאה שכוללת גם את "
        "ההתקנה מחדש נעה בין 600 ל-850 ש\"ח. מה שמזיז את המחיר בתוך הטווח הוא "
        "אורך הצנרת החדשה ומיקום המעבה - העברה בתוך אותה דירה זולה מהעברה "
        "לבית אחר. לפני שמזמינים, שווה לוודא שהמזגן בכלל שווה העברה: ביחידה "
        "בת עשר שנים ומעלה עלות ההעברה מתקרבת למחיר מזגן חדש, ואנחנו נגיד לכם "
        "את זה בכנות."},
 ],

 "/קצר-במזגן/": [
  {"at": "before_faq",
   "impressions": 38,
   "q": "אחרי כמה זמן המזגן מקצר?",
   "a": "העיתוי הוא הרמז הכי חשוב לאבחון, ולכן זו השאלה הראשונה שאנחנו שואלים "
        "בטלפון. מזגן שמקצר אחרי דקות ספורות מצביע כמעט תמיד על תקלה חשמלית - "
        "קבל שנחלש, מגען שרוף או כרטיס שמזהה עומס יתר ומנתק להגנה. מזגן "
        "שעובד שעה או שעתיים ואז נעצר מצביע על משהו תרמי: מעבה מלוכלך שלא "
        "מצליח לפלוט חום, מסנן סתום שגורם למאייד לקפוא, או לחץ גז נמוך "
        "שמפעיל את מגן הלחץ. ההבדל הזה משנה גם את המחיר, כי החלפת קבל היא "
        "450 עד 750 ש\"ח ואילו טיפול בגז או בזרימת אוויר הוא עבודה אחרת "
        "לגמרי. אל תפעילו שוב ושוב מזגן שמקצר - כל הפעלה כזאת שוחקת את "
        "המדחס."},
 ],

 "/כמה-עולה-מזגן-לשעה/": [
  {"at": "before_faq",
   "impressions": 70,
   "q": "כמה חשמל צורך מזגן 3 ו-3.5 כוח סוס?",
   "a": "הטבלאות שלמעלה מגיעות עד 2.5 כוח סוס, אבל בסלונים ובחללים גדולים "
        "מתקינים לרוב יחידות גדולות יותר. באותו חישוב ובאותו תעריף, מזגן 3 "
        "כוח סוס צורך כ-2.6 קילוואט-שעה ועולה כ-1.30 ש\"ח לשעה, ומזגן 3.5 "
        "כוח סוס צורך כ-3 קילוואט-שעה ועולה כ-1.50 ש\"ח לשעה. בשמונה שעות "
        "ביום זה כ-10.40 ש\"ח ליום ליחידת 3 כוח סוס וכ-12 ש\"ח ליחידת 3.5. "
        "המספרים האלה נכונים ליחידה אינוורטר תקינה עם מסננים נקיים - מעבה "
        "מלוכלך או מסנן סתום מעלים את הצריכה בעשרות אחוזים בלי שאף אחד מרגיש, "
        "וזאת הסיבה שניקוי שנתי מחזיר את עצמו."},
 ],
}


def _find_faq(blocks):
    for i, b in enumerate(blocks):
        if b.get("type") == "faq":
            return i
    return None


def _find_heading(blocks, prefix):
    for i, b in enumerate(blocks):
        if b.get("type") == "heading" and (b.get("text") or "").startswith(prefix):
            return i
    return None


def _last_content(blocks):
    for i in range(len(blocks) - 1, -1, -1):
        if blocks[i].get("type") in ("paragraph", "list", "table", "faq"):
            return i
    return len(blocks) - 1


def apply(body, path=""):
    """Insert this page's answers as an h3 and a paragraph. Adds only."""
    spec = ANSWERS.get(path)
    if not spec:
        return body

    for entry in spec:
        anchor = entry["at"]
        if anchor == "before_faq":
            i = _find_faq(body)
            at = i if i is not None else _last_content(body) + 1
        elif anchor.startswith("after_heading:"):
            i = _find_heading(body, anchor.split(":", 1)[1])
            at = (i + 2) if i is not None else _last_content(body) + 1
        else:
            at = _last_content(body) + 1

        at = max(0, min(at, len(body)))
        heading = {"type": "heading", "level": 3, "text": entry["q"],
                   "html": entry["q"]}
        para = {"type": "paragraph", "html": entry["a"]}
        body = body[:at] + [heading, para] + body[at:]
        CHANGES.append({"path": path, "question": entry["q"],
                        "impressions": entry["impressions"]})
    return body
