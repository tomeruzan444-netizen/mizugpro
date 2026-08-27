# -*- coding: utf-8 -*-
"""Download every image the site references into ../assets/img."""
import json, os, re, urllib.parse
import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "img")
os.makedirs(OUT, exist_ok=True)

pages = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))

urls = set()
for p in pages:
    for b in p["blocks"]:
        if b.get("type") == "image" and b.get("src"):
            urls.add(b["src"])
        if isinstance(b.get("html"), str):
            urls.update(re.findall(r'src="([^"]+)"', b["html"]))
    if p.get("og_image"):
        urls.add(p["og_image"])

# header / footer assets picked up from the crawled homepage
home = os.path.join(HERE, "raw", "home-980480e7.html")
if os.path.exists(home):
    soup = BeautifulSoup(open(home, encoding="utf-8").read(), "html.parser")
    for scope in (".elementor-location-header", ".elementor-location-footer"):
        el = soup.select_one(scope)
        if el:
            for im in el.select("img[src]"):
                urls.add(im["src"])

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 MizugProMigration"})

mapping = {}
for u in sorted(urls):
    if not u.startswith("http"):
        continue
    name = urllib.parse.unquote(u.rsplit("/", 1)[-1].split("?")[0])
    name = re.sub(r"[^\w֐-׿.\-]+", "-", name)
    dest = os.path.join(OUT, name)
    if not os.path.exists(dest):
        try:
            r = s.get(u, timeout=60)
            if r.status_code == 200 and r.content:
                open(dest, "wb").write(r.content)
                print("saved", name, len(r.content))
            else:
                print("skip", r.status_code, u[:80])
                continue
        except Exception as e:
            print("ERR", u[:80], e)
            continue
    mapping[u] = "/assets/img/" + name

json.dump(mapping, open(os.path.join(HERE, "image-map.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("mapped", len(mapping), "images")
