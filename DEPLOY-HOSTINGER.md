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

`contact.php` שולח מייל ל‑`ben3n4456@gmail.com` **וגם** רושם כל ליד ל‑
`leads.csv` שנשמר מחוץ ל‑`public_html` — כדי שכשל במייל לא יאבד פנייה.
הטופס זהה בכל 120 העמודים ושולח לאותו handler, אז כתובת אחת מכסה את הכל.
להוספת נמענים: `$TO = ['a@x.com', 'b@y.com'];`

לפני עלייה:

1. צור תיבת דואר `no-reply@mizugpro.co.il` ב‑hPanel → **Emails**.
   בלעדיה השרת שולח מכתובת לא קיימת, ו‑SPF עלול להפיל את המייל לספאם.
2. לשינוי היעד — ערוך את `$TO` בראש `build/form/contact.php`, בנה, ודחוף.
   שים לב: השולח נשאר `no-reply@mizugpro.co.il` ולא כתובת ג'ימייל, אחרת
   גוגל תדחה את המייל כזיוף.
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

## פרסום אוטומטי

הצינור בנוי כך:

```
דחיפה ל-main  →  GitHub Actions בונה ובודק  →  ענף deploy מתעדכן  →  הוסטינגר מושכת
```

`.github/workflows/deploy.yml` רץ על כל דחיפה שנוגעת ב-`assets/`, `build/` או
`_source/`. הוא בונה את האתר מחדש, מריץ את `validate.py`, **ונכשל אם משהו
נשבר** — עמוד בלי H1, לינק פנימי שבור, סכמה לא תקינה. רק בנייה נקייה מגיעה
לענף `deploy`.

### איך יודעים שזה באמת עבד

כל בנייה כותבת `/version.json` עם ה-commit שממנו היא נוצרה. אפשר לשאול את
האתר החי מה הוא מריץ:

```bash
python build/check_live.py
```

הוא משווה את מה שחי מול ראש ענף `main` ומוודא שהעמודים באמת נענים:

```
✓ live build : daddcd9  (2026-08-28T07:02:15Z, github-actions)
  deploy branch head : daddcd9
  main branch head   : daddcd9
✓ the live site is running the latest commit
✓ home           200
✓ a Hebrew URL   200
```

אפשר גם פשוט לפתוח `https://mizugpro.co.il/version.json` בדפדפן ולהשוות את
`short` ל-commit האחרון בגיטהאב. אם הם זהים — הצינור עובד.

### מה צריך להגדיר פעם אחת

1. **חיבור הוסטינגר לריפו** — hPanel → **Advanced → GIT**:
   - Repository: `https://github.com/tomeruzan444-netizen/mizugpro`
   - Branch: `deploy`
   - Directory: `public_html`
   - אם ה-repo פרטי, הוסף את מפתח ה-SSH שהיא מציגה כ-Deploy key בגיטהאב.

2. **סגירת הלולאה** — אחרי היצירה הוסטינגר מציגה **Auto deployment URL**.
   העתק אותו והוסף אותו בגיטהאב תחת
   **Settings → Secrets and variables → Actions → New repository secret**:
   - Name: `HOSTINGER_DEPLOY_WEBHOOK`
   - Secret: הכתובת שהעתקת

   בלי הסוד הזה הכל עדיין עובד — פשוט תצטרך ללחוץ Deploy ידנית ב-hPanel.

3. **הפעלה ידנית** בכל רגע: GitHub → **Actions → build & deploy → Run workflow**.

## עדכון האתר ידנית

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

---

## ביקורת SEO

**מושהה כרגע (29.8.2026).** התזמון השבועי בוטל לבקשתך, ושום דבר לא רץ מעצמו.
הביקורת עצמה נשארה במקום ואפשר להריץ אותה מתי שרוצים:
GitHub → **Actions → SEO audit → Run workflow**. להחזרת התזמון — להסיר את
סימון ההערה משתי שורות ה-`schedule` בראש הקובץ.

`.github/workflows/seo-audit.yml`:
הוא זוחל על **האתר החי** — לא על הקוד — ומדווח על מה שגוגל והגולשים באמת
מקבלים.

מה הוא בודק: כותרות ותיאורי מטא כפולים/חסרים/ארוכים, H1, עמודים חסומים
לאינדוקס, canonical שגוי, עמודים יתומים וקישורים שבורים, סכמה לא תקינה,
עמודים כמעט זהים, מחירים שסותרים זה את זה בין עמודים, **עמוד עיר שמזכיר עיר
אחרת**, שגיאות כתיב, תוכן שהתיישן, ומשקל וזמן תגובה.

**איפה הדוח:**

1. **Issue בגיטהאב** — נפתח אוטומטית ומשויך אליך, וגיטהאב שולחת עליו מייל.
   זו דרך המסירה שעובדת בלי להגדיר כלום.
2. **בריפו** — `seo-reports/YYYY-MM-DD.md`, ו-`seo-reports/latest.md` תמיד
   האחרון. `seo-reports/metrics.json` שומר 52 שבועות אחורה, ולכן בכל דוח יש
   עמודת "שבוע שעבר" להשוואה.
3. **מייל ישיר (רשות)** — הוסף שני סודות תחת
   **Settings → Secrets and variables → Actions**:
   - `SEO_MAIL_TO` — לאן לשלוח, למשל `tomeruzan444@gmail.com`
   - `SEO_MAIL_USER` — חשבון הג'ימייל השולח
   - `SEO_MAIL_PASSWORD` — **App Password** מ-
     https://myaccount.google.com/apppasswords (סיסמת ג'ימייל רגילה תיכשל;
     צריך אימות דו-שלבי פעיל)

**הרצה ידנית בכל רגע:** GitHub → **Actions → SEO audit → Run workflow**.

**מקומית:**

```bash
cd build
python seo_audit.py              # כותב seo-reports/
```

הביקורת קוראת בלבד. היא לא משנה דבר באתר, ולכן דחיפה של דוח לא מפעילה בנייה
מחדש ולא נוגעת באוויר.
