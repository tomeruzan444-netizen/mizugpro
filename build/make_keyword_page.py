# -*- coding: utf-8 -*-
"""Render the keyword map as a standalone reference page."""
import io, os, json, html, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = json.load(open(os.path.join(ROOT, "_source", "keyword-map.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "preview", "keyword-map.html")

rows, order = DATA["rows"], DATA["order"]
by_group = {g: [r for r in rows if r["group"] == g] for g in order}
total_words = sum(r["words"] for r in rows)
peak = max(r["words"] for r in rows)

BASE = "https://mizugpro.co.il"

NOTES = {
    "אזורי שירות": "65 עמודים — יותר ממחצית האתר. כל עמוד מכוון לעיר אחת, "
                   "והביטוי זהה במבנה: טכנאי מזגנים + שם היישוב.",
    "גדלים ומחירים": "הביטויים כאן הם כוונת קנייה מובהקת — מישהו שכבר יודע איזה גודל הוא צריך.",
    "תיקון ותקלות": "ביטויים של תקלה, לא של שירות. מי שמחפש אותם נמצא כרגע עם מזגן מקולקל.",
    "עמודי חברה ומשפט": "לא מיועדים לדירוג. עמוד התודה מסומן noindex.",
}


def bar(words):
    return round(100 * words / peak)


def section(group):
    items = by_group[group]
    words = sum(r["words"] for r in items)
    note = NOTES.get(group)
    out = ['<section class="grp">',
           '<header class="grp__head">',
           '<h2>%s</h2>' % html.escape(group),
           '<p class="grp__meta"><span>%d עמודים</span><span>%s מילים</span></p>' % (
               len(items), format(words, ",")),
           '</header>']
    if note:
        out.append('<p class="grp__note">%s</p>' % html.escape(note))
    out.append('<ol class="rows">')
    for r in items:
        flag = '<span class="flag">noindex</span>' if r["noindex"] else ""
        out.append(
            '<li class="row">'
            '<span class="row__phrase">%s%s</span>'
            '<a class="row__url" href="%s" target="_blank" rel="noopener">%s</a>'
            '<span class="row__n"><i style="--w:%d%%"></i><b>%s</b></span>'
            '</li>' % (
                html.escape(r["phrase"]), flag,
                BASE + urllib.parse.quote(r["path"]),
                html.escape(r["path"]),
                bar(r["words"]), format(r["words"], ",")))
    out += ['</ol>', '</section>']
    return "\n".join(out)


CSS = """
:root{
  --navy:#04293A; --sky:#00ADEE; --gold:#F5BC0C;
  --ink:#052335; --body:#3A5A6B; --muted:#6D8899;
  --line:#D8E6EF; --line-soft:#EBF3F8; --card:#FFFFFF; --ground:#F6FBFE;
  --bar:#BFE7FA;
  --font:"Assistant","Segoe UI","Arial Hebrew",Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ink:#EAF4FA; --body:#A9C4D2; --muted:#7C9AAA;
    --line:#123A50; --line-soft:#0C2C3E; --card:#082C3E; --ground:#04202E;
    --bar:#0E5F84;
  }
}
:root[data-theme="dark"]{
  --ink:#EAF4FA; --body:#A9C4D2; --muted:#7C9AAA;
  --line:#123A50; --line-soft:#0C2C3E; --card:#082C3E; --ground:#04202E; --bar:#0E5F84;
}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--body);font-family:var(--font);
  font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased}
.wrap{width:min(100% - 2.5rem,1080px);margin-inline:auto;padding:clamp(1.5rem,4vw,3.5rem) 0}
h1,h2{color:var(--ink);margin:0;line-height:1.25;letter-spacing:-.01em}
a{color:inherit}

.top{border-bottom:3px solid var(--navy);padding-bottom:1.6rem;margin-bottom:2rem}
.eyebrow{display:inline-flex;align-items:center;gap:.5em;font-size:.78rem;font-weight:800;
  letter-spacing:.08em;text-transform:uppercase;color:var(--sky);margin-bottom:.6rem}
.eyebrow::before{content:"";width:20px;height:3px;border-radius:2px;background:var(--gold)}
h1{font-size:clamp(1.7rem,1.2rem+2vw,2.5rem);font-weight:800;text-wrap:balance}
.lede{margin:.7rem 0 0;max-width:62ch;font-size:1.05rem}

.totals{display:flex;flex-wrap:wrap;gap:2.4rem;margin-top:1.6rem}
.tot b{display:block;font-size:1.7rem;font-weight:800;color:var(--ink);
  font-variant-numeric:tabular-nums;line-height:1.1}
.tot span{font-size:.86rem;color:var(--muted);font-weight:700}

.grp{margin-top:2.6rem}
.grp__head{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem 1rem;
  padding-bottom:.6rem;border-bottom:1px solid var(--line)}
.grp__head h2{font-size:1.22rem;font-weight:800}
.grp__meta{margin:0;display:flex;gap:1rem;font-size:.84rem;color:var(--muted);font-weight:700;
  font-variant-numeric:tabular-nums;margin-inline-start:auto}
.grp__note{margin:.7rem 0 0;font-size:.92rem;color:var(--muted);max-width:70ch}

.rows{list-style:none;margin:.5rem 0 0;padding:0}
.row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.05fr) 116px;
  gap:.5rem 1.2rem;align-items:center;padding:.62rem .75rem;border-radius:9px}
.row:nth-child(odd){background:var(--card)}
.row__phrase{font-weight:700;color:var(--ink);font-size:1rem}
.flag{margin-inline-start:.5em;font-size:.68rem;font-weight:800;letter-spacing:.04em;
  color:var(--muted);border:1px solid var(--line);border-radius:99px;padding:.05em .5em}
.row__url{font-family:var(--mono);font-size:.78rem;color:var(--muted);direction:ltr;
  text-align:start;text-decoration:none;overflow-wrap:anywhere;unicode-bidi:plaintext}
.row__url:hover{color:var(--sky);text-decoration:underline}
.row__n{display:flex;align-items:center;gap:.55rem;justify-content:flex-end}
.row__n i{display:block;height:6px;border-radius:99px;background:var(--bar);
  width:var(--w);min-width:3px;flex:none}
.row__n b{font-variant-numeric:tabular-nums;font-size:.84rem;font-weight:700;
  color:var(--muted);min-width:3.2em;text-align:start}

@media (max-width:720px){
  /* the bar is a % of its track, so the track stays a fixed width */
  .row{grid-template-columns:minmax(0,1fr) 96px;gap:.15rem .8rem}
  .row__url{grid-column:1/-1;font-size:.72rem}
  .row__n{justify-content:flex-start}
  .row__n b{min-width:2.8em}
}
"""

page = """<title>מפת הביטויים של מיזוג פרו</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&display=swap">
<style>%s</style>
<script>document.documentElement.setAttribute("dir","rtl");document.documentElement.setAttribute("lang","he");</script>
<div dir="rtl" lang="he">
<div class="wrap">
  <header class="top">
    <span class="eyebrow">mizugpro.co.il</span>
    <h1>מפת הביטויים של מיזוג פרו</h1>
    <p class="lede">כל %d העמודים באתר, לפי הביטוי שכל עמוד בנוי סביבו. הביטוי נלקח
    מכותרת ה־H1 של העמוד עד למפריד הראשון — זה מה שהעמוד באמת מכוון אליו.
    הפס לצד כל שורה מציג את נפח התוכן ביחס לעמוד העשיר באתר.</p>
    <div class="totals">
      <div class="tot"><b>%d</b><span>עמודים</span></div>
      <div class="tot"><b>%s</b><span>מילים באתר</span></div>
      <div class="tot"><b>%d</b><span>קבוצות נושא</span></div>
      <div class="tot"><b>%d</b><span>עמודי אזור שירות</span></div>
    </div>
  </header>
  %s
</div>
</div>
""" % (CSS, len(rows), len(rows), format(total_words, ","), len(order),
       len(by_group["אזורי שירות"]),
       "\n".join(section(g) for g in order))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write(page)
print("written:", OUT, os.path.getsize(OUT), "bytes |", len(rows), "rows")
