# -*- coding: utf-8 -*-
"""
The hand-built widgets on the live site (price gauge, AC calculator, brand
comparison tables, diagrams…) are styled by CSS that LiteSpeed injects at
runtime, so it is not in the crawled HTML. Open those pages in a real browser,
pull the matching rules out of document.styleSheets, scope them under .embed
and save them as a stylesheet the build can ship.
"""
import os, re, json, urllib.parse
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "css", "legacy-widgets.css")

BASE = "https://mizugpro.co.il"

# one live page per widget family
PAGES = [
    "/איזה-מזגן-הכי-טוב/",
    "/החלפת-מדחס-במזגן/",
    "/התקנת-מזגן-1-25-כוח-סוס/",
    "/התקנת-מזגן-2-כוח-סוס/",
    "/אודות/",
    "/אחריות-על-התקנת-מזגן/",
    "/התקנת-מזגן-1-כוח-סוס/",
    "/התקנת-מזגן-מיני-מרכזי/",
    "/מזגן-אינוורטר-חסרונות-ויתרונות/",
    "/מזגן-חצי-כוח-סוס/",
    "/מזגן-מטפטף/",
    "/ניקוי-מיני-מרכזי/",
    "/ריח-רע-מהמזגן/",
    "/אזורי-שירות/",
    "/מחירון-מזגנים/",
    "/התקנת-מזגנים/",
]

# class names that belong to the hand-built widgets, never to Elementor
WIDGET_CLASSES = [
    "important-note", "note-title", "note-content", "note-icon",
    "price-range-widget", "price-container", "arc-container", "price-arc",
    "price-markers", "price-marker", "marker-dot", "marker-line", "price-labels",
    "price-label", "price-title", "price-value", "price-avg", "price-low",
    "price-high", "update-info",
    "brand-comparison", "brand-name", "brand-group", "feature-list", "header-row",
    "highlight-text", "credit-line", "best-value", "best-value-icon",
    "mizug-testimonials", "mizug-carousel", "mizug-slide", "mizug-rating",
    "mizug-text", "mizug-author", "mizug-location", "mizug-nav", "mizug-btn",
    "mizug-prev", "mizug-next",
    "pie-chart", "pie-center", "legend", "legend-item", "color-box",
    "tadiran", "electra", "tornado",
    "mini-insert-chart", "chart-header", "cons", "cons-title", "highlight",
    "installation-time",
    "advantages", "disadvantages",
    "progress-widget", "progress-bar", "progress-fill", "progress-stages",
    "progress-text", "stage",
    "price-table", "ac-table", "ac-diagram", "ac-title", "cause", "causes",
    "connector", "copyright",
    "service-areas-container", "service-areas-grid", "service-area-box",
    "advantages-mini", "advantage-mini", "adv-icon", "brand-mini", "brand-stars",
    "brand-title",
    "mp-txt", "mp-a", "mp-btn", "mp-c", "mp-l", "mp-n", "mp-s",
    "calculator", "options", "option", "buttons", "result",
]
# plus every class name that actually appears in the migrated embeds
_derived = os.path.join(ROOT, "_source", "embed-classes.json")
if os.path.exists(_derived):
    WIDGET_CLASSES += [c for c in json.load(open(_derived, encoding="utf-8")) if len(c) > 1]
WIDGET_CLASSES = sorted(set(WIDGET_CLASSES), key=len, reverse=True)
CLASS_RE = re.compile(r"\.(" + "|".join(re.escape(c) for c in WIDGET_CLASSES) + r")(?![\w-])")

# selectors that would leak out of the widget if we shipped them as-is
GLOBAL_SEL = re.compile(r"^(html|body|\*|:root)\b")


def scope(selector):
    parts = []
    for sel in selector.split(","):
        sel = sel.strip()
        if not sel:
            continue
        if GLOBAL_SEL.match(sel):
            sel = re.sub(r"^(html|body|\*|:root)", ".embed", sel).strip() or ".embed"
            parts.append(sel)
        else:
            parts.append(".embed " + sel)
    return ", ".join(parts)


JS = """
() => {
  const out = [];
  const walk = (rules, media) => {
    for (const r of rules) {
      if (r.type === CSSRule.MEDIA_RULE) { walk(r.cssRules, r.conditionText); continue; }
      if (r.type === CSSRule.KEYFRAMES_RULE) { out.push({kind:'keyframes', text:r.cssText}); continue; }
      if (r.type === CSSRule.STYLE_RULE) {
        out.push({kind:'style', sel:r.selectorText, body:r.style.cssText, media:media||null});
      }
    }
  };
  for (const sheet of document.styleSheets) {
    let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
    if (rules) walk(rules, null);
  }
  return out;
}
"""


def main():
    seen_style, seen_keyframes = {}, {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        for path in PAGES:
            url = BASE + urllib.parse.quote(path)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=180000)
                page.wait_for_timeout(2500)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                page.wait_for_timeout(1500)
                rules = page.evaluate(JS)
            except Exception as e:
                print("skip", path, e)
                continue
            hits = 0
            for r in rules:
                if r["kind"] == "keyframes":
                    name = r["text"].split("{")[0].strip()
                    seen_keyframes[name] = r["text"]
                    continue
                if not CLASS_RE.search(r["sel"] or ""):
                    continue
                key = (r["sel"], r["media"])
                if key not in seen_style:
                    seen_style[key] = r["body"]
                    hits += 1
            print("%-42s rules=%-5d new=%d" % (path[:42], len(rules), hits))
        browser.close()

    by_media = {}
    for (sel, media), body in seen_style.items():
        by_media.setdefault(media, []).append((sel, body))

    lines = ["/* Legacy hand-built widgets, captured from the live site and",
             "   scoped under .embed so they cannot leak into the new design. */"]
    for sel, body in by_media.pop(None, []):
        lines.append("%s{%s}" % (scope(sel), body))
    for media, items in by_media.items():
        lines.append("@media %s{" % media)
        for sel, body in items:
            lines.append("  %s{%s}" % (scope(sel), body))
        lines.append("}")
    # keyframes are global by nature
    used = " ".join(b for b in seen_style.values())
    for name, text in seen_keyframes.items():
        anim = name.split()[-1]
        if anim and anim in used:
            lines.append(text)

    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    print("rules kept:", len(seen_style), "| keyframes:", len(seen_keyframes))
    print("written:", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
