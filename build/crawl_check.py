# -*- coding: utf-8 -*-
"""
Crawl the built site the way Googlebot would — start at /, follow only the
links in the served HTML — and report orphans, depth, and sitemap agreement.
"""
import json, os, re, sys, urllib.parse, collections
import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8814"

session = requests.Session()
seen, depth, queue = set(), {}, [("/", 0)]
external, mailto_tel = set(), set()
inbound = collections.Counter()

while queue:
    path, d = queue.pop(0)
    if path in seen:
        continue
    seen.add(path)
    depth[path] = d
    r = session.get(BASE + urllib.parse.quote(path), timeout=60)
    r.encoding = "utf-8"
    if r.status_code != 200:
        print("  !! %s -> %s" % (path, r.status_code))
        continue
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("tel:", "mailto:")):
            mailto_tel.add(href)
            continue
        if href.startswith("#"):
            continue
        if href.startswith("http"):
            netloc = urllib.parse.urlparse(href).netloc
            if netloc and netloc not in ("mizugpro.co.il", "www.mizugpro.co.il"):
                external.add(netloc)
                continue
        target = urllib.parse.unquote(urllib.parse.urlparse(href).path)
        if not target.startswith("/") or target.startswith("/assets/"):
            continue
        if not target.endswith("/") and "." not in target.rsplit("/", 1)[-1]:
            target += "/"
        inbound[target] += 1
        if target not in seen:
            queue.append((target, d + 1))

pages = json.load(open(os.path.join(ROOT, "_source", "content.json"), encoding="utf-8"))
all_paths = {p["path"] for p in pages}
orphans = sorted(all_paths - seen)

sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
sm = {urllib.parse.unquote(urllib.parse.urlparse(u).path)
      for u in re.findall(r"<loc>(.*?)</loc>", sitemap)}

by_depth = collections.Counter(depth.values())
weakest = sorted(((inbound[p], p) for p in all_paths), key=lambda x: x[0])[:5]

print("pages reachable from the homepage :", len(seen & all_paths), "/", len(all_paths))
print("orphans (no internal link)        :", len(orphans), orphans[:5])
print("click depth from home             :", dict(sorted(by_depth.items())))
print("max depth                         :", max(depth.values()))
print("sitemap URLs                      :", len(sm))
print("in sitemap but unreachable        :", sorted(sm - seen)[:5])
print("reachable but not in sitemap      :", sorted((seen & all_paths) - sm)[:5])
print("fewest inbound internal links     :", weakest)
print("external domains linked           :", sorted(external))
print("tel/mailto links                  :", sorted(mailto_tel))

json.dump({"reachable": sorted(seen), "orphans": orphans,
           "depth": depth, "inbound": dict(inbound)},
          open(os.path.join(ROOT, "crawl-report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
