# -*- coding: utf-8 -*-
"""
Compare every image the live site references (src, srcset, data-src, inline
style backgrounds, og:image, schema) against what the migration downloaded and
against what the built pages actually use.
"""
import os, re, json, glob, urllib.parse, collections
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(HERE, "raw")
IMGDIR = os.path.join(ROOT, "assets", "img")
DIST = os.path.join(ROOT, "dist")

UPLOAD = re.compile(r"https?://mizugpro\.co\.il/wp-content/uploads/[^\s\"'()\\]+\.(?:png|jpe?g|gif|webp|svg|avif)",
                    re.I)


def basename(url):
    return urllib.parse.unquote(url.rsplit("/", 1)[-1].split("?")[0])


def strip_size(name):
    """foo-1024x508.png -> foo.png, so resized variants fold into one original."""
    return re.sub(r"-\d{2,4}x\d{2,4}(?=\.[a-z]+$)", "", name, flags=re.I)


live = collections.Counter()
where = collections.defaultdict(set)

for path in glob.glob(os.path.join(RAW, "*.html")):
    html = open(path, encoding="utf-8").read()
    page = os.path.basename(path)
    soup = BeautifulSoup(html, "html.parser")

    urls = set(UPLOAD.findall(html))
    for im in soup.find_all(["img", "source"]):
        for attr in ("src", "data-src", "data-lazy-src", "srcset", "data-srcset"):
            val = im.get(attr) or ""
            for piece in val.split(","):
                piece = piece.strip().split(" ")[0]
                if "wp-content/uploads" in piece:
                    urls.add(piece if piece.startswith("http") else "https://mizugpro.co.il" + piece)
    for el in soup.select("[style*='url(']"):
        for m in re.findall(r"url\(([^)]+)\)", el["style"]):
            m = m.strip("'\"")
            if "wp-content/uploads" in m:
                urls.add(m if m.startswith("http") else "https://mizugpro.co.il" + m)

    for u in urls:
        live[basename(u)] += 1
        where[basename(u)].add(page)

have = {f for f in os.listdir(IMGDIR) if not f.endswith(".json")}
have_stems = {os.path.splitext(f)[0] for f in have}

built = set()
for f in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
    for m in re.findall(r"/assets/img/([^\"')\s]+)", open(f, encoding="utf-8").read()):
        built.add(urllib.parse.unquote(m))

missing, migrated, unused = [], [], []
for name in sorted(live):
    stem = os.path.splitext(name)[0]
    stem_base = os.path.splitext(strip_size(name))[0]
    if stem in have_stems or stem_base in have_stems:
        migrated.append(name)
    else:
        missing.append({"file": name, "uses": live[name],
                        "pages": sorted(where[name])[:3]})

for f in sorted(have):
    if f not in built and os.path.splitext(f)[0] not in {os.path.splitext(b)[0] for b in built}:
        unused.append(f)

report = {"live_images": len(live), "migrated": len(migrated),
          "missing": missing, "unused_in_build": unused,
          "files_on_disk": len(have), "referenced_in_build": len(built)}
json.dump(report, open(os.path.join(ROOT, "image-audit.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("images referenced by the live site :", len(live))
print("migrated                           :", len(migrated))
print("MISSING                            :", len(missing))
for m in missing:
    print("   -", m["file"], "used %dx" % m["uses"], m["pages"][:2])
print("files on disk                      :", len(have))
print("referenced by the new build        :", len(built))
print("on disk but unused                 :", len(unused))
for u in unused[:15]:
    print("   ·", u)
