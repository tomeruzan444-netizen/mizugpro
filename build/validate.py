# -*- coding: utf-8 -*-
"""Post-build QA: URL parity with the old site, metadata, links, schema."""
import os, re, json, glob, urllib.parse
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
SRC = os.path.join(ROOT, "_source")

old = json.load(open(os.path.join(SRC, "content.json"), encoding="utf-8"))
old_paths = {p["path"] for p in old}
old_meta = {p["path"]: p for p in old}

built = {}
for f in glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True):
    rel = os.path.relpath(f, DIST).replace("\\", "/")[: -len("index.html")]
    built["/" + rel if rel else "/"] = f

issues = {"missing_pages": [], "extra_pages": [], "no_h1": [], "multi_h1": [],
          "no_title": [], "no_desc": [], "no_canonical": [], "bad_schema": [],
          "broken_links": [], "title_changed": [], "desc_changed": [],
          "canonical_changed": [], "empty_main": [], "img_no_dims": []}

issues["missing_pages"] = sorted(old_paths - set(built))
issues["extra_pages"] = sorted(set(built) - old_paths)

for path, f in sorted(built.items()):
    html = open(f, encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")
    o = old_meta.get(path, {})

    h1s = soup.find_all("h1")
    if not h1s:
        issues["no_h1"].append(path)
    elif len(h1s) > 1:
        issues["multi_h1"].append(path)

    title = soup.title.get_text() if soup.title else None
    desc = soup.select_one('meta[name="description"]')
    canon = soup.select_one('link[rel="canonical"]')
    if not title:
        issues["no_title"].append(path)
    if not desc or not desc.get("content"):
        issues["no_desc"].append(path)
    if not canon and path != "/404.html":
        issues["no_canonical"].append(path)

    # metadata parity with the live site (fixes are expected, so only report)
    if o.get("meta_title") and title and title != o["meta_title"]:
        issues["title_changed"].append({"path": path, "old": o["meta_title"], "new": title})
    if o.get("meta_description") and desc and desc.get("content") != o["meta_description"]:
        issues["desc_changed"].append({"path": path})
    if o.get("canonical") and canon and canon.get("href") != o["canonical"]:
        issues["canonical_changed"].append({"path": path, "old": o["canonical"],
                                            "new": canon.get("href")})

    for s in soup.find_all("script", type="application/ld+json"):
        try:
            json.loads(s.string or "")
        except Exception as e:
            issues["bad_schema"].append({"path": path, "error": str(e)[:80]})

    main = soup.select_one("main#main")
    if main and len(main.get_text(strip=True)) < 400:
        issues["empty_main"].append(path)

    for a in soup.select("main a[href^='/'], footer a[href^='/'], header a[href^='/']"):
        href = urllib.parse.unquote(a["href"].split("#")[0])
        if href.startswith("/assets/"):
            continue
        if href not in built:
            issues["broken_links"].append({"on": path, "href": href,
                                           "text": a.get_text(" ", strip=True)[:40]})

    for im in soup.find_all("img"):
        if not im.get("width") or not im.get("height"):
            issues["img_no_dims"].append({"path": path, "src": im.get("src", "")[:60]})

json.dump(issues, open(os.path.join(ROOT, "validation-report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("built pages          :", len(built))
for k in ("missing_pages", "extra_pages", "no_h1", "multi_h1", "no_title", "no_desc",
          "no_canonical", "bad_schema", "broken_links", "empty_main", "img_no_dims",
          "title_changed", "desc_changed", "canonical_changed"):
    v = issues[k]
    print("%-22s %d" % (k, len(v)), ("" if len(v) > 6 or not v else v))
