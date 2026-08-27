# -*- coding: utf-8 -*-
"""
Prove every page renders three ways:

  1. server-side  — the raw HTML response already carries the full page
                    (this is what Googlebot's first pass and every AI crawler see)
  2. no-JavaScript — the page is complete and usable with scripting off
  3. client-side  — with JS on, the enhancements attach and nothing is lost

Run against the local static server that serves ../dist.
"""
import json, os, re, sys, urllib.parse
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8811"

pages = json.load(open(os.path.join(ROOT, "_source", "content.json"), encoding="utf-8"))


def text_len(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup.find_all(["script", "style", "noscript"]):
        t.decompose()
    main = soup.select_one("main#main") or soup
    return len(re.sub(r"\s+", " ", main.get_text(" ", strip=True)))


def main():
    session = requests.Session()
    issues = []
    server = {}

    # ---- 1. server-side -----------------------------------------------------
    for p in pages:
        url = BASE + urllib.parse.quote(p["path"])
        r = session.get(url, timeout=60)
        r.encoding = "utf-8"   # the dev server omits charset; the file is UTF-8
        soup = BeautifulSoup(r.text, "html.parser")
        rec = {
            "status": r.status_code,
            "bytes": len(r.content),
            "text": text_len(r.text),  # counted with the same rules as the DOM
            "h1": len(soup.find_all("h1")),
            "h2": len(soup.select("main h2")),
            "links": len(soup.select("main a[href]")),
            "schema": len(soup.find_all("script", type="application/ld+json")),
            "title": bool(soup.title and soup.title.get_text().strip()),
        }
        server[p["path"]] = rec
        problems = []
        if rec["status"] != 200:
            problems.append("status %s" % rec["status"])
        if rec["text"] < 800:
            problems.append("thin server HTML (%d chars)" % rec["text"])
        if rec["h1"] != 1:
            problems.append("h1=%d" % rec["h1"])
        if not rec["title"]:
            problems.append("no title")
        if rec["schema"] < 1:
            problems.append("no structured data")
        if problems:
            issues.append({"stage": "server", "path": p["path"], "problems": problems})

    # ---- 2 + 3. browser, scripting off then on ------------------------------
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for js_enabled in (False, True):
            ctx = browser.new_context(viewport={"width": 1366, "height": 900},
                                      java_script_enabled=js_enabled)
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)[:100]))
            for p in pages:
                del errors[:]
                url = BASE + urllib.parse.quote(p["path"])
                page.goto(url, wait_until="load", timeout=60000)
                page.wait_for_timeout(150 if not js_enabled else 260)
                got = page.evaluate("""() => {
                  const main = document.querySelector('main#main');
                  return {
                    text: main ? main.textContent.replace(/\\s+/g,' ').trim().length : 0,
                    h1: document.querySelectorAll('h1').length,
                    links: document.querySelectorAll('main a[href]').length,
                    tocItems: document.querySelectorAll('.toc ol li').length,
                    faq: document.querySelectorAll('.faq details').length,
                    navLinks: document.querySelectorAll('.nav__list a').length,
                    formFields: document.querySelectorAll('form[data-lead] input, form[data-lead] textarea').length,
                    hiddenBody: getComputedStyle(document.body).display === 'none',
                  };
                }""")
                stage = "client" if js_enabled else "no-js"
                problems = []
                base_text = server[p["path"]]["text"]
                if got["hiddenBody"]:
                    problems.append("body hidden")
                if got["text"] < base_text * 0.75:
                    problems.append("rendered text %d vs server %d" % (got["text"], base_text))
                if got["h1"] != 1:
                    problems.append("h1=%d" % got["h1"])
                if got["navLinks"] < 5:
                    problems.append("nav links %d" % got["navLinks"])
                if got["formFields"] < 3:
                    problems.append("lead form fields %d" % got["formFields"])
                if js_enabled and got["faq"] and got["tocItems"] == 0 and server[p["path"]]["h2"] > 2:
                    problems.append("toc not built")
                if errors:
                    problems.append("js errors %s" % errors[:1])
                if problems:
                    issues.append({"stage": stage, "path": p["path"], "problems": problems})
            ctx.close()
        browser.close()

    json.dump({"pages": len(pages), "issues": issues},
              open(os.path.join(ROOT, "render-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    total_bytes = sum(v["bytes"] for v in server.values())
    print("pages checked            :", len(pages))
    print("avg server HTML          : %.1f KB" % (total_bytes / len(pages) / 1024))
    print("avg server-rendered text : %d chars" % (sum(v["text"] for v in server.values()) / len(pages)))
    print("avg links per page       : %d" % (sum(v["links"] for v in server.values()) / len(pages)))
    print("avg schema blocks        : %.1f" % (sum(v["schema"] for v in server.values()) / len(pages)))
    print("issues                   :", len(issues))
    for i in issues[:20]:
        print("   [%s] %s -> %s" % (i["stage"], i["path"][:40], i["problems"]))


if __name__ == "__main__":
    main()
