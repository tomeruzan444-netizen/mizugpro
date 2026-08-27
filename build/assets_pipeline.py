# -*- coding: utf-8 -*-
"""
Asset pipeline: self-host the webfont, generate WebP derivatives of every
raster image, and minify CSS/JS. Run once before build.py (build.py picks up
whatever this produced).
"""
import os, re, json, io
import requests
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
IMG = os.path.join(ASSETS, "img")
FONTS = os.path.join(ASSETS, "fonts")
os.makedirs(FONTS, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

MAX_W = 1280
WEBP_Q = 82


# ------------------------------------------------------------------ fonts ---
def fetch_font():
    url = ("https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800"
           "&display=swap")
    css = requests.get(url, headers={"User-Agent": UA}, timeout=60).text
    faces = []
    for m in re.finditer(r"/\* (\S+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        subset, body = m.group(1), m.group(2)
        if subset not in ("hebrew", "latin"):
            continue
        weight = re.search(r"font-weight:\s*(\d+)", body).group(1)
        src = re.search(r"url\((https://[^)]+\.woff2)\)", body).group(1)
        rng = re.search(r"unicode-range:\s*([^;]+);", body)
        name = "assistant-%s-%s.woff2" % (subset, weight)
        dest = os.path.join(FONTS, name)
        if not os.path.exists(dest):
            data = requests.get(src, headers={"User-Agent": UA}, timeout=60).content
            open(dest, "wb").write(data)
            print("font", name, len(data))
        faces.append({"subset": subset, "weight": weight, "file": name,
                      "range": rng.group(1).strip() if rng else None})
    css_out = []
    for f in faces:
        css_out.append(
            "@font-face{font-family:'Assistant';font-style:normal;font-weight:%s;"
            "font-display:swap;src:url('/assets/fonts/%s') format('woff2');%s}"
            % (f["weight"], f["file"],
               ("unicode-range:%s;" % f["range"]) if f["range"] else ""))
    open(os.path.join(FONTS, "assistant.css"), "w", encoding="utf-8").write("\n".join(css_out))
    json.dump(faces, open(os.path.join(FONTS, "faces.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("faces:", len(faces))
    return faces


# ------------------------------------------------------------------ images --
def build_webp():
    manifest = {}
    for name in sorted(os.listdir(IMG)):
        if not name.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        path = os.path.join(IMG, name)
        try:
            im = Image.open(path)
        except Exception as e:
            print("skip", name, e)
            continue
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
        w, h = im.size
        if w > MAX_W:
            h = round(h * MAX_W / w)
            im = im.resize((MAX_W, h), Image.LANCZOS)
            w = MAX_W
        out = os.path.splitext(name)[0] + ".webp"
        dest = os.path.join(IMG, out)
        im.save(dest, "WEBP", quality=WEBP_Q, method=6)
        before, after = os.path.getsize(path), os.path.getsize(dest)
        # WebP is not always smaller for flat-colour PNGs — keep whichever wins
        if after >= before:
            os.remove(dest)
            manifest[name] = {"best": name, "width": w, "height": h,
                              "bytes_before": before, "bytes_after": before}
            print("%-58s %7d  (kept png)" % (name, before))
            continue
        manifest[name] = {"best": out, "webp": out, "width": w, "height": h,
                          "bytes_before": before, "bytes_after": after}
        print("%-58s %7d -> %7d  (%d%%)" % (name, before, after,
                                            round(100 * after / before)))
    json.dump(manifest, open(os.path.join(IMG, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    total_before = sum(v["bytes_before"] for v in manifest.values())
    total_after = sum(v["bytes_after"] for v in manifest.values())
    print("TOTAL %d -> %d bytes (%d%%)" % (total_before, total_after,
                                           round(100 * total_after / max(total_before, 1))))
    return manifest


# ---------------------------------------------------------------- minifiers -
def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{}:;,>~])\s*", r"\1", css)
    css = re.sub(r";}", "}", css)
    return css.strip()


def minify_js(js):
    js = re.sub(r"^\s*//.*$", "", js, flags=re.M)
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    js = re.sub(r"\n\s*\n", "\n", js)
    js = re.sub(r"^[ \t]+", "", js, flags=re.M)
    return js.strip()


def minify():
    src = open(os.path.join(ASSETS, "css", "site.css"), encoding="utf-8").read()
    faces = open(os.path.join(FONTS, "assistant.css"), encoding="utf-8").read()
    legacy_path = os.path.join(ASSETS, "css", "legacy-widgets.css")
    legacy = open(legacy_path, encoding="utf-8").read() if os.path.exists(legacy_path) else ""
    out = minify_css(faces + "\n" + src + "\n" + legacy)
    open(os.path.join(ASSETS, "css", "site.min.css"), "w", encoding="utf-8").write(out)
    print("css %d -> %d" % (len(src) + len(faces) + len(legacy), len(out)))

    js = open(os.path.join(ASSETS, "js", "site.js"), encoding="utf-8").read()
    jm = minify_js(js)
    open(os.path.join(ASSETS, "js", "site.min.js"), "w", encoding="utf-8").write(jm)
    print("js  %d -> %d" % (len(js), len(jm)))


if __name__ == "__main__":
    fetch_font()
    build_webp()
    minify()
