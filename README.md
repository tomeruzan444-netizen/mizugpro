# מיזוג פרו — האתר החדש

מיגרציה מלאה של mizugpro.co.il מ‑WordPress/Elementor לאתר סטטי מהיר,
עם עיצוב חדש בצבעי הלוגו ושמירה מלאה על התוכן, הכתובות והמטא דאטא.

```
_source/    חילוץ מהאתר החי (HTML גולמי, content.json, site.json, סקריפטים)
assets/     css / js / fonts / img — המקור לעריכה
build/      תבניות Jinja + סקריפטי הבנייה והבדיקות
dist/       הפלט המוכן להעלאה
preview/    קובץ HTML יחיד עם כל האתר, לשיתוף כתצוגה מקדימה
```

## כתיבת תוכן חדש

[`CONTENT-GUIDE.md`](CONTENT-GUIDE.md) — הטון, המבנה, כללי הקישור הפנימי,
המחירים הקנוניים והעובדות שאסור לשנות. לקרוא לפני כתיבת כל עמוד חדש.

## בנייה

הסדר חשוב — כל שלב צורך את הפלט של קודמו:

```bash
cd build

python assets_pipeline.py     # פונט מקומי + WebP לכל התמונות + מיניפיקציה
python build.py               # מרנדר את 120 העמודים ל-dist/
python subset_fonts.py        # מצמצם את הפונט לתווים שבשימוש בפועל
python prune_css.py           # מוחק חוקי CSS של ווידג'טים שאין להם התאמה
python critical_css.py        # מחלץ את ה-CSS של המסך הראשון להטמעה
python -c "import assets_pipeline as a; a.minify()"
python build.py               # בנייה סופית עם הנכסים המצומצמים
```

`build/capture_widget_css.py` ו‑`_source/capture_runtime_images.py` פונים לאתר
החי ומושכים CSS ותמונות שמוזרקים בזמן ריצה. צריך להריץ אותם רק אם האתר הישן
עדיין באוויר ומשהו השתנה בו.

## בדיקות

```bash
python -m http.server 8811 --directory ../dist   # או serve_utf8

python validate.py            # כתובות, מטא, H1, סכמה, לינקים שבורים, מידות תמונה
python verify_rendering.py    # רינדור צד-שרת / ללא JS / צד-לקוח בכל עמוד
python crawl_check.py         # זחילה מעמוד הבית: יתומים, עומק, התאמה ל-sitemap
python ../_source/audit_images.py   # כל תמונה מהאתר הישן עברה?
```

הדוחות נכתבים לשורש הפרויקט: `validation-report.json`, `render-report.json`,
`crawl-report.json`, `image-audit.json`, `content-fixes.json`, `migration-report.json`.

## העלאה

מעלים את תוכן `dist/` לשורש הדומיין. הקבצים `.htaccess`, `_headers` ו‑
`nginx.conf.snippet` כבר בפנים — משאירים את זה שמתאים לשרת ומוחקים את השאר.
הם מגדירים דחיסה, קאשינג ל‑`/assets` לשנה, כותרות אבטחה ו‑UTF‑8.

**מה עוד צריך לחבר לפני עלייה לאוויר**

1. טופס הלידים ב‑`build/templates/partials/leadform.html` שולח POST ל‑`/thank-you/`.
   צריך לחבר אותו לשירות טפסים או ל‑endpoint בצד השרת.
2. מספר הטלפון של האתר הוא `033820923`. באתר הישן הופיע גם `033820823` בפוטר
   ובעמוד יצירת קשר — הוא תוקן בכל מקום.
3. אם נשארים ב‑WordPress: `dist/` הוא אתר סטטי מלא, אפשר להגיש אותו כמו שהוא
   או להמיר את התבניות לתבנית WP.
