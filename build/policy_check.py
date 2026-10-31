# -*- coding: utf-8 -*-
"""
The parts of GOOGLE-CONTENT-POLICY.md a machine can check.

CONTENT-GUIDE.md says how to write a page; the policy says what may be written
at all. Four of its prohibitions are mechanical, so they run on every build
instead of relying on anyone remembering them:

    overreaching claims   a first-person superlative about price or results
    dangerous DIY         telling a reader to handle refrigerant or wiring
    medical claims        an air conditioner curing or treating something
    keyword stuffing      a service phrase at a density no prose reaches

Everything else in the policy - genuine uniqueness, E-E-A-T, fact-checking -
cannot be reduced to a regex and stays a human read against the checklist at
the end of the policy document.

The first version of this file produced 40 findings of which 39 were noise,
so the rules below are written around the three ways it was wrong:

  A superlative is not a claim. "הזול ביותר לא תמיד הטוב ביותר" and "זה המצב
  הזול ביותר שבו אפשר להתקין" are honest advice. Only a superlative the
  business applies to itself is a violation, so a first-person marker has to
  be within a few words of it, and a negation anywhere near it clears it.

  "מרפאות" is a clinic, not a cure. Medical patterns need the Hebrew letter
  boundary, or every page that serves commercial clients gets flagged.

  Stuffing is density, not a count. A 2,500-word page using "התקנת מזגן"
  23 times sits at 1.8% - ordinary prose. The threshold is therefore a share
  of the page's words, with a floor so short pages are not judged on noise,
  and link lists are excluded because a directory of city links is a
  directory, not stuffing.
"""
import re

FINDINGS = []

HEB = "א-ת"
PFX = "בלמהושכ"

# "we are the cheapest" is banned; "the cheapest is not always best" is good
# advice. The difference is a first-person marker and the absence of a negation.
_FIRST_PERSON = r"(?:אנחנו|אנו|אצלנו|שלנו|מיזוג פרו|נספק|נוכל לספק|מציעים)"
_NEGATION = r"(?:לא|אין|אל|אך|אבל|למרות|לא בהכרח|לא תמיד)"
_SUPERLATIVE = r"(?:הזול(?:ים|ה)?|הטוב(?:ים|ה)?|המקצועי(?:ים)?) ביותר"

# "על הצד הטוב ביותר" and "בצורה הטובה ביותר" are idioms for "as well as
# possible", not claims to be the best in the market. They are empty marketing
# language - which CONTENT-GUIDE.md already bans - but not a policy violation,
# and conflating the two buried the one real finding under five false ones.
_IDIOM = re.compile(r"על הצד הטוב ביותר|בצורה הטובה ביותר|"
                    r"בדרך הטובה ביותר|התמורה הטובה ביותר")

CLAIMS = [
    ("טענת עליונות על עצמנו",
     re.compile(r"%s[^.!?]{0,60}%s" % (_FIRST_PERSON, _SUPERLATIVE)),
     "אסור טענת 'הזולים/הטובים ביותר' על עצמנו ללא בסיס"),
    ("טענת עליונות בשוק",
     re.compile(r"%s (?:בשוק|בארץ|בישראל|באזור)" % _SUPERLATIVE),
     "אסור להצהיר על עליונות בשוק ללא בסיס"),
    ("אחריות ללא תנאים",
     re.compile(r"(?:מובטח|אחריות)[^.!?]{0,20}לכל החיים|אחריות נצחית"),
     "אסור 'מובטח לכל החיים' ללא תנאי אחריות ברור"),
    ("הבטחת תוצאה",
     re.compile(r"100%% הצלחה|הצלחה מובטחת|פתרון מובטח|"
                r"%s[^.!?]{0,40}מתקנים כל תקלה" % _FIRST_PERSON),
     "אסור להבטיח תוצאה שאינה ניתנת לערוב"),
]

# An imperative aimed at the reader. A negation in front of it is the opposite
# of a violation - the site is supposed to say "do not try this yourself".
_IMPERATIVE = r"(?<!אל )(?<!לא )(?<!אין )(?<!אסור )(?<![א-ת])"

DANGEROUS = [
    ("הנחיית DIY לגז קירור",
     re.compile(_IMPERATIVE + r"(?:תמלאו|מלאו)\s+(?:את\s+)?(?:ה)?גז|"
                r"למלא גז בעצמ|מילוי גז עצמי|תוסיפו גז"),
     "אסור להנחות טיפול בגז קירור"),
    ("הנחיית DIY לחשמל",
     re.compile(_IMPERATIVE + r"(?:תחברו|תחליפו)\s+(?:את\s+)?"
                r"(?:החוטים|הכבל|הקבל|המגען)|"
                r"(?:תפתחו|לפתוח)\s+את\s+לוח החשמל"),
     "אסור להנחות עבודות חשמל"),
    ("הנחיית DIY לפתיחת היחידה",
     re.compile(_IMPERATIVE + r"(?:תפרקו|תפתחו)\s+את\s+"
                r"(?:המזגן|היחידה החיצונית|המעבה|המדחס)"),
     "אסור להנחות פירוק עצמי של היחידה"),
]

MEDICAL = [
    ("טענה רפואית",
     re.compile(r"(?<![%s])מרפא(?:ת|ים)?(?![%s])|מטפל ב(?:אסתמה|אלרגיה)|"
                r"מונע מחלות|מחסל חיידקים ב-?100|פותר בעיות נשימה" % (HEB, HEB)),
     "אסור טענות רפואיות"),
]

# Share of the page's own words a service phrase may occupy before it stops
# reading as prose. Measured as words-in-phrase x occurrences / total words.
STUFF_SHARE = 0.045
STUFF_FLOOR = 8          # below this many occurrences, do not judge
PHRASES = ["טכנאי מזגנים", "תיקון מזגנים", "תיקון מזגן", "התקנת מזגנים",
           "התקנת מזגן", "מתקין מזגנים", "מיזוג אוויר"]


def _count(phrase, text):
    return len(re.findall(
        r"(?<![%s])[%s]?%s(?![%s])" % (HEB, PFX, re.escape(phrase), HEB), text))


def check(path, own_text, title="", description="", prose_text=None):
    """Run the mechanical policy rules over one page.

    `own_text` is the page's own copy with the repeating furniture stripped.
    `prose_text` is the same minus link lists and table cells, and is what
    density is measured on - pass it when the caller can separate them.
    """
    haystack = " ".join([title, description, own_text])

    for group in (CLAIMS, DANGEROUS, MEDICAL):
        for label, pattern, rule in group:
            for m in pattern.finditer(haystack):
                window = haystack[max(0, m.start() - 70):m.end() + 70]
                if label.startswith("טענת"):
                    if re.search(_NEGATION, window[:90]):
                        continue   # "the cheapest is not always the best"
                    if _IDIOM.search(haystack[max(0, m.end() - 30):m.end() + 5]):
                        continue   # an idiom, not a claim
                FINDINGS.append({
                    "path": path, "kind": label, "rule": rule,
                    "text": re.sub(r"\s+", " ", window),
                })

    prose = prose_text if prose_text is not None else own_text
    words = len(prose.split())
    if words >= 200:
        for phrase in PHRASES:
            n = _count(phrase, prose)
            share = n * len(phrase.split()) / words
            if n >= STUFF_FLOOR and share > STUFF_SHARE:
                FINDINGS.append({
                    "path": path, "kind": "דחיסת מילת מפתח",
                    "rule": "'%s' תופס %.1f%% מהמילים (%d מופעים ב-%d מילים, "
                            "הרף %.1f%%)" % (phrase, share * 100, n, words,
                                             STUFF_SHARE * 100),
                    "text": "",
                })
    return FINDINGS
