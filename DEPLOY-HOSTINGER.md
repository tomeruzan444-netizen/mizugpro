# מעבר לאוויר בהוסטינגר

האתר החדש הוא HTML סטטי + קובץ PHP אחד לטופס. אין וורדפרס, אין מסד נתונים.
הכתובות זהות לאתר הישן, כך שאין צורך בהפניות 301 לעמודים — רק לתמונות,
וזה כבר בתוך `.htaccess`.

**שני ענפים ב‑GitHub:**

| ענף | מה בו | למה |
|---|---|---|
| `main` | הפרויקט המלא — קוד, נכסים, סקריפטים, דוחות | פיתוח |
| `deploy` | **תוכן `dist/` בשורש** | זה מה שהוסטינגר מושכת |

הוסטינגר משכפלת את שורש הענף אל התיקייה שתבחר. לכן יש `deploy` — אחרת
היו נוחתות ב‑`public_html` גם `build/` ו‑`_source/`, והאתר לא היה בשורש.

---

## 1. גיבוי (לפני הכל)

יש לך גיבויים, אבל קח אחד טרי ממש לפני המעבר — hPanel → **Files → Backups**:
גיבוי קבצים **וגם** גיבוי מסד נתונים. **הורד אותם למחשב.** גיבוי שיושב רק
אצל הספק הוא לא גיבוי.

אל תמחק את מסד הנתונים של וורדפרס גם אחרי המעבר. הוא לא מפריע לכלום.

## 2. חזרה כללית על סאב‑דומיין (מומלץ)

לפני שנוגעים בדומיין החי:

1. hPanel → **Domains → Subdomains** → צור `new.mizugpro.co.il`
2. hPanel → **Advanced → GIT** → **Create repository**
   - Repository: `https://github.com/tomeruzan444-netizen/mizugpro`
   - Branch: `deploy`
   - Directory: התיקייה של הסאב‑דומיין
   - אם ה‑repo פרטי — הוסף את מפתח ה‑SSH שהוסטינגר מציגה כ‑Deploy key בגיטהאב
     (Settings → Deploy keys → Add)
3. **חסום אינדוקס לסאב‑דומיין** — צור שם `.htaccess` נפרד עם:
   ```apache
   Header always set X-Robots-Tag "noindex, nofollow"
   ```
   בלי זה גוגל יאנדקס גרסה כפולה של כל 120 העמודים.
4. בדוק: כמה עמודים בעברית, שליחת ליד מהטופס, תפריט הנגישות, הודעת העוגיות.

## 3. המעבר עצמו

1. **הזז את וורדפרס הצידה, אל תמחק.** ב‑File Manager צור תיקייה
   `wp-old/` מחוץ ל‑`public_html` והעבר אליה את כל תוכן `public_html`.
   ודא שהקובץ `.htaccess` הישן של וורדפרס יצא משם — הוא יתנגש עם החדש.
2. hPanel → **Advanced → GIT** → הצבע על `public_html`, ענף `deploy`, ובצע Deploy.
3. ודא שנוצרו בשורש: `index.html`, `.htaccess`, `contact.php`, `assets/`,
   ותיקיות העמודים בעברית.
4. **נקה קאש**: הוסטינגר רצה על LiteSpeed. hPanel → **Advanced → Cache Manager
   → Purge**. אם יש Cloudflare — גם שם Purge Everything.

## 4. הטופס

`contact.php` שולח מייל ל‑`support@mizugpro.co.il` **וגם** רושם כל ליד ל‑
`leads.csv` שנשמר מחוץ ל‑`public_html` — כדי שכשל במייל לא יאבד פנייה.

לפני עלייה:

1. צור תיבת דואר `no-reply@mizugpro.co.il` ב‑hPanel → **Emails**.
   בלעדיה השרת שולח מכתובת לא קיימת, ו‑SPF עלול להפיל את המייל לספאם.
2. לשינוי היעד — ערוך את `$TO` בראש `build/form/contact.php`, בנה, ודחוף.
3. **שלח ליד בדיקה** ואמת שהוא הגיע.

## 5. אחרי המעבר

- **Search Console**: תג האימות נמצא בכל עמוד, האימות אמור לשרוד. הגש מחדש
  את `sitemap.xml` והרץ URL Inspection על 3–4 עמודים.
- עקוב אחרי 404 בשבועיים הראשונים.
- שמור את `wp-old/` ואת גיבוי מסד הנתונים לפחות 30 יום.

## 6. חזרה אחורה

אם משהו נשבר: מחק את תוכן `public_html`, החזר לשם את `wp-old/`, נקה קאש.
מסד הנתונים לא נגענו בו, אז וורדפרס חוזר לעבוד כמו שהיה.

---

## עדכון האתר אחרי שהוא באוויר

```bash
cd build
python build.py                      # בונה מחדש את dist/
cd ..
git add -A && git commit -m "..."
git push                             # main
git branch -D deploy 2>/dev/null
git subtree split --prefix=dist -b deploy
git push -f origin deploy            # מרענן את ענף הפריסה
```

בהוסטינגר: **Advanced → GIT → Deploy**. אפשר גם להדביק את כתובת ה‑Webhook
שהיא נותנת אל GitHub (Settings → Webhooks) וכל דחיפה ל‑`deploy` תעדכן לבד.
