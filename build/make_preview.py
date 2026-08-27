# -*- coding: utf-8 -*-
"""
Bundle the whole built site into ONE self-contained HTML file so it can be
published as a shareable preview link (works on mobile, no server needed).

The shell (header/footer) is shared; each page contributes only its <main>.
Images and fonts are inlined as data URIs.
"""
import os, re, json, base64, glob, urllib.parse, mimetypes

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(ROOT, "preview", "mizugpro-preview.html")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

MAIN_RE = re.compile(r'<main id="main">(.*?)</main>', re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="(.*?)"', re.S)


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    if path.endswith(".woff2"):
        mime = "font/woff2"
    with open(path, "rb") as fh:
        return "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode())


def build_asset_map():
    """/assets/... url -> data: uri, for every image and font in the build."""
    mapping = {}
    for folder in ("img", "fonts"):
        base = os.path.join(DIST, "assets", folder)
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            if name.endswith((".json", ".css")):
                continue
            url = "/assets/%s/%s" % (folder, name)
            mapping[url] = data_uri(os.path.join(base, name))
            mapping[urllib.parse.quote(url)] = mapping[url]
    return mapping


def inline_assets(text, mapping):
    for url in sorted(mapping, key=len, reverse=True):
        if url in text:
            text = text.replace(url, mapping[url])
    return text


def page_path(html_file):
    rel = os.path.relpath(html_file, DIST).replace("\\", "/")
    rel = rel[: -len("index.html")]
    return "/" + rel if rel else "/"


def main():
    mapping = build_asset_map()

    home_html = open(os.path.join(DIST, "index.html"), encoding="utf-8").read()
    body = home_html.split("<body", 1)[1].split(">", 1)[1].rsplit("</body>", 1)[0]
    before_main, rest = body.split('<main id="main">', 1)
    _, after_main = rest.split("</main>", 1)
    after_main = re.sub(r'<script src="[^"]*"[^>]*></script>', "", after_main)
    # the artifact sandbox blocks third-party hosts, and a design preview has no
    # business firing the client's analytics — strip Tag Manager from the bundle
    before_main = re.sub(r"<noscript><iframe src=\"https://www\.googletagmanager\.com.*?</noscript>",
                         "", before_main, flags=re.S)

    pages = {}
    for html_file in sorted(glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True)):
        raw = open(html_file, encoding="utf-8").read()
        m = MAIN_RE.search(raw)
        if not m:
            continue
        path = page_path(html_file)
        pages[path] = {
            "t": (TITLE_RE.search(raw).group(1) if TITLE_RE.search(raw) else ""),
            "d": (DESC_RE.search(raw).group(1) if DESC_RE.search(raw) else ""),
            "h": m.group(1),
        }

    css = open(os.path.join(DIST, "assets", "css", "site.min.css"), encoding="utf-8").read()
    js = open(os.path.join(DIST, "assets", "js", "site.min.js"), encoding="utf-8").read()

    css = inline_assets(css, mapping)
    before_main = inline_assets(before_main, mapping)
    after_main = inline_assets(after_main, mapping)
    for p in pages.values():
        p["h"] = inline_assets(p["h"], mapping)

    router = """
(function(){
  var PAGES = window.__MP_PAGES, main = document.getElementById('main');
  document.documentElement.setAttribute('dir','rtl');
  document.documentElement.setAttribute('lang','he');

  function norm(p){
    try { p = decodeURIComponent(p); } catch (e) {}
    if (!p) return '/';
    if (p[0] !== '/') p = '/' + p;
    if (p.slice(-1) !== '/' && p.indexOf('.') === -1) p += '/';
    return p;
  }
  function render(path, push){
    path = norm(path);
    var page = PAGES[path] || PAGES['/'];
    main.innerHTML = page.h;
    // innerHTML never runs <script>; the legacy calculators need theirs re-created
    main.querySelectorAll('script').forEach(function(old){
      var s = document.createElement('script');
      for (var i = 0; i < old.attributes.length; i++) {
        s.setAttribute(old.attributes[i].name, old.attributes[i].value);
      }
      s.textContent = old.textContent;
      old.replaceWith(s);
    });
    document.title = page.t;
    if (push !== false) location.hash = '#' + path;
    document.querySelectorAll('.nav__link, .drawer__list a').forEach(function(a){
      var href = a.getAttribute('href');
      if (href === path) a.setAttribute('aria-current','page');
      else a.removeAttribute('aria-current');
    });
    window.scrollTo(0,0);
    if (window.MizugPro) window.MizugPro.init();
  }
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var href = a.getAttribute('href');
    if (!href || href[0] === '#' || /^(tel:|mailto:|https?:)/.test(href)) return;
    if (!PAGES[norm(href)]) return;
    e.preventDefault();
    render(href);
  });
  window.addEventListener('hashchange', function(){
    render(location.hash.slice(1) || '/', false);
  });
  render(location.hash.slice(1) || '/', false);
})();
"""

    parts = [
        "<title>מיזוג פרו</title>",
        "<style>%s</style>" % css,
        '<div dir="rtl">',
        before_main,
        '<main id="main"></main>',
        after_main,
        "</div>",
        # "</" is escaped so a page containing </script> cannot close this block
        "<script>window.__MP_PAGES=%s;</script>"
        % json.dumps(pages, ensure_ascii=False).replace("</", "<\/"),
        "<script>%s</script>" % js,
        "<script>%s</script>" % router,
    ]
    out = "\n".join(parts)
    open(OUT, "w", encoding="utf-8").write(out)
    size = os.path.getsize(OUT)
    print("pages bundled:", len(pages))
    print("preview file :", OUT)
    print("size         : %.2f MB" % (size / 1048576))


if __name__ == "__main__":
    main()
