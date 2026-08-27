# -*- coding: utf-8 -*-
"""
Some images (hero backgrounds, favicons, footer brand logos) are only visible
once the page runs: they come from CSS the cache plugin injects at runtime, or
from lazy-loading attributes. Open every live URL in a browser, collect every
image reference, and download whatever the static crawl missed.
"""
import os, re, json, urllib.parse
import requests
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMGDIR = os.path.join(ROOT, "assets", "img")
os.makedirs(IMGDIR, exist_ok=True)

pages = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
paths = [p["path"] for p in pages]

JS = """
() => {
  const urls = new Set();
  const add = (u) => { if (u && u.includes('/wp-content/uploads/')) urls.add(u); };
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    for (const prop of ['backgroundImage', 'borderImageSource', 'maskImage']) {
      const v = cs[prop];
      if (v && v !== 'none') (v.match(/url\\(["']?([^"')]+)["']?\\)/g) || []).forEach(m => {
        add(m.replace(/^url\\(["']?/, '').replace(/["']?\\)$/, ''));
      });
    }
  });
  document.querySelectorAll('img, source').forEach(el => {
    ['src', 'data-src', 'data-lazy-src'].forEach(a => add(el.getAttribute(a)));
    ['srcset', 'data-srcset'].forEach(a => {
      (el.getAttribute(a) || '').split(',').forEach(part => add(part.trim().split(' ')[0]));
    });
  });
  document.querySelectorAll('link[href]').forEach(l => add(l.getAttribute('href')));
  document.querySelectorAll('meta[content]').forEach(m => add(m.getAttribute('content')));
  return [...urls];
}
"""


def basename(url):
    return urllib.parse.unquote(url.rsplit("/", 1)[-1].split("?")[0])


def main():
    found = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for i, path in enumerate(paths, 1):
            url = "https://mizugpro.co.il" + urllib.parse.quote(path)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(1200)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(900)
                for u in page.evaluate(JS):
                    if u.startswith("//"):
                        u = "https:" + u
                    elif u.startswith("/"):
                        u = "https://mizugpro.co.il" + u
                    found.setdefault(basename(u), u)
            except Exception as e:
                print("skip", path, str(e)[:60])
            if i % 20 == 0:
                print("  ...%d/%d pages, %d distinct images" % (i, len(paths), len(found)), flush=True)
        browser.close()

    have = {f for f in os.listdir(IMGDIR)}
    have_stems = {os.path.splitext(f)[0] for f in have}

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 MizugProMigration"})
    downloaded = []
    for name, url in sorted(found.items()):
        safe = re.sub(r"[^\w֐-׿.\-]+", "-", name)
        if os.path.splitext(safe)[0] in have_stems:
            continue
        try:
            r = session.get(url, timeout=90)
            if r.status_code == 200 and r.content:
                open(os.path.join(IMGDIR, safe), "wb").write(r.content)
                downloaded.append((safe, len(r.content)))
                print("downloaded", safe, len(r.content))
        except Exception as e:
            print("ERR", url[:70], e)

    json.dump({"found": found, "downloaded": [d[0] for d in downloaded]},
              open(os.path.join(HERE, "runtime-images.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("distinct images seen at runtime:", len(found))
    print("newly downloaded              :", len(downloaded))


if __name__ == "__main__":
    main()
