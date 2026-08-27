# -*- coding: utf-8 -*-
import os, re, json, time, hashlib, urllib.parse
import requests

BASE = "https://mizugpro.co.il"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
os.makedirs(RAW, exist_ok=True)

urls = []
for f in ("sm-page.xml", "sm-post.xml", "sm-category.xml"):
    p = os.path.join(HERE, f)
    if not os.path.exists(p):
        continue
    xml = open(p, encoding="utf-8").read()
    urls += re.findall(r"<loc>(.*?)</loc>", xml)

# de-dup, keep order
seen = set(); ordered = []
for u in urls:
    if u not in seen:
        seen.add(u); ordered.append(u)

def fname(u):
    path = urllib.parse.urlparse(u).path
    slug = urllib.parse.unquote(path).strip("/") or "home"
    slug = re.sub(r"[^\w\u0590-\u05FF\-]+", "-", slug)[:80]
    h = hashlib.md5(u.encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{h}.html"

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 (compatible; MizugProMigration/1.0)"})

index = []
for i, u in enumerate(ordered, 1):
    fn = fname(u)
    dest = os.path.join(RAW, fn)
    if os.path.exists(dest) and os.path.getsize(dest) > 2000:
        index.append({"url": u, "file": fn, "status": "cached"})
        print(f"[{i}/{len(ordered)}] cached {fn}", flush=True)
        continue
    try:
        r = s.get(u, timeout=60)
        open(dest, "w", encoding="utf-8").write(r.text)
        index.append({"url": u, "file": fn, "status": r.status_code})
        print(f"[{i}/{len(ordered)}] {r.status_code} {len(r.text)} {fn}", flush=True)
    except Exception as e:
        index.append({"url": u, "file": fn, "status": "ERR " + str(e)})
        print(f"[{i}/{len(ordered)}] ERROR {u}: {e}", flush=True)
    time.sleep(0.4)

json.dump(index, open(os.path.join(HERE, "crawl-index.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("DONE", len(index), flush=True)
