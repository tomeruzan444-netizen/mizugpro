# -*- coding: utf-8 -*-
import os, re, json, urllib.parse
from bs4 import BeautifulSoup, Tag

HERE = os.path.dirname(os.path.abspath(__file__))
RAW  = os.path.join(HERE, "raw")


def rel(u):
    """Normalize an internal URL to a decoded site-relative path."""
    if not u:
        return u
    u = u.strip()
    if u.startswith("#") or u.startswith("tel:") or u.startswith("mailto:"):
        return u
    p = urllib.parse.urlparse(u)
    if p.netloc and "mizugpro.co.il" not in p.netloc:
        return u
    path = urllib.parse.unquote(p.path) or "/"
    last = path.rsplit("/", 1)[-1]
    if not path.endswith("/") and "." not in last:
        path += "/"
    return path + (("#" + p.fragment) if p.fragment else "")


SKIP_CLASSES = re.compile(
    r"elementor-widget-(form|shortcode)|elementor-nav-menu|acwp-|privacy-popup"
    r"|elementor-location-(header|footer)"
)

BLOCK_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table",
              "blockquote", "img", "figure"]

KEEP_TAGS = {"a", "img", "li", "ul", "ol", "p", "td", "th", "tr", "thead", "tbody",
             "table", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "figure",
             "figcaption", "sup", "sub", "small", "strong", "b", "em", "u", "br"}
UNWRAP_TAGS = {"span", "div", "i", "section", "article", "font", "center"}


def clean_inline(el):
    """Inner HTML limited to safe semantic tags, with links rewritten to relative."""
    # Wrap in a sentinel that never gets unwrapped, so the whole fragment
    # survives — not just its first child.
    frag = BeautifulSoup("<x-root>" + el.decode_contents() + "</x-root>", "html.parser")
    root = frag.find("x-root")
    for t in root.find_all(["script", "style", "noscript", "svg"]):
        t.decompose()
    for t in root.find_all(True):
        if t.name in UNWRAP_TAGS:
            if t.name == "i" and not t.get_text(strip=True):
                t.decompose()
            else:
                t.unwrap()
    for t in root.find_all(True):
        if t.name == "a":
            t["href"] = rel(t.get("href"))
            for attr in list(t.attrs):
                if attr not in ("href", "title", "target", "rel"):
                    del t[attr]
            if t.get("target") == "_blank":
                t["rel"] = "noopener"
        elif t.name == "img":
            for attr in list(t.attrs):
                if attr not in ("src", "alt", "width", "height"):
                    del t[attr]
        elif t.name in KEEP_TAGS:
            t.attrs = {}
        else:
            t.unwrap()
    html = root.decode_contents()
    html = re.sub(r"\s+", " ", html).strip()
    html = re.sub(r"<(p|li|td|th)>\s*</\1>", "", html)
    return html


def img_data(im):
    src = im.get("src") or im.get("data-src") or ""
    if src.startswith("data:"):
        src = im.get("data-src") or ""
    return {"type": "image", "src": src, "alt": (im.get("alt") or "").strip(),
            "width": im.get("width"), "height": im.get("height")}


def extract_blocks(container):
    blocks = []
    seen = []

    def push_primitive(child):
        txt = child.get_text(" ", strip=True)
        if child.name == "img":
            blocks.append(img_data(child))
            return
        if child.name == "figure":
            im = child.find("img")
            if im:
                blocks.append(img_data(im))
            return
        if not txt:
            return
        # Elementor renders some widgets twice (desktop / mobile variants); drop
        # only a repeat that lands right next to its twin, never distant repeats
        # that are genuinely part of the copy.
        key = (child.name, txt[:150])
        if key in seen[-4:]:
            return
        seen.append(key)
        if child.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            blocks.append({"type": "heading", "level": int(child.name[1]),
                           "text": txt, "html": clean_inline(child)})
        elif child.name in ("ul", "ol"):
            blocks.append({"type": "list", "ordered": child.name == "ol",
                           "html": clean_inline(child)})
        elif child.name == "table":
            blocks.append({"type": "table", "html": clean_inline(child)})
        elif child.name == "blockquote":
            blocks.append({"type": "quote", "html": clean_inline(child)})
        else:
            blocks.append({"type": "paragraph", "html": clean_inline(child)})

    def walk(node):
        for child in node.children:
            if not isinstance(child, Tag):
                continue
            if child.name in ("script", "style", "noscript", "form"):
                continue
            cls = " ".join(child.get("class") or [])
            if SKIP_CLASSES.search(cls):
                continue

            classes = child.get("class") or []

            # Hand-written HTML widgets: a handful have structured handlers
            # below and get restyled; anything else is carried over verbatim
            # (own <style>/<script> included) so nothing is lost.
            if "elementor-widget-html" in classes:
                inner = child.select_one(".elementor-widget-container")
                if inner is not None:
                    known = inner.select_one(
                        ".mizug-testimonials, .price-range-widget, "
                        ".service-areas-container, .service-areas-grid, .legend")
                    if known is None:
                        raw = inner.decode_contents().strip()
                        if raw:
                            blocks.append({"type": "custom_html", "html": raw})
                        continue

            # --- custom hand-coded widgets used across the site ---------------
            if "mizug-testimonials" in classes:
                items = []
                for sl in child.select(".mizug-slide"):
                    r = sl.select_one(".mizug-rating")
                    t = sl.select_one(".mizug-text")
                    a = sl.select_one(".mizug-author")
                    l = sl.select_one(".mizug-location")
                    items.append({
                        "stars": (r.get_text(strip=True).count("★") if r else 5),
                        "text": t.get_text(" ", strip=True) if t else "",
                        "author": a.get_text(" ", strip=True) if a else "",
                        "location": l.get_text(" ", strip=True) if l else "",
                    })
                if items:
                    blocks.append({"type": "reviews", "items": items})
                    continue

            if "price-range-widget" in classes:
                labels = []
                for lb in child.select(".price-label"):
                    t = lb.select_one(".price-title")
                    v = lb.select_one(".price-value")
                    labels.append({"label": t.get_text(" ", strip=True) if t else "",
                                   "value": v.get_text(" ", strip=True) if v else ""})
                note = child.select_one(".update-info")
                blocks.append({"type": "price_range", "points": labels,
                               "note": note.get_text(" ", strip=True) if note else ""})
                continue

            if "legend" in classes and child.select_one(".legend-item"):
                items = [li.get_text(" ", strip=True) for li in child.select(".legend-item")]
                blocks.append({"type": "share_chart", "items": items})
                continue

            if "service-areas-container" in classes or "service-areas-grid" in classes:
                links = [{"text": a.get_text(" ", strip=True), "href": rel(a.get("href"))}
                         for a in child.select("a[href]")]
                if links:
                    blocks.append({"type": "linkgrid", "links": links})
                    continue

            if "mini-insert-chart" in classes:
                blocks.append({"type": "raw_chart",
                               "text": child.get_text(" ", strip=True)[:400]})
                continue

            if ("elementor-widget-toggle" in cls or "elementor-widget-accordion" in cls
                    or "e-n-accordion" in cls):
                items = []
                for t in child.select(".elementor-toggle-item, .elementor-accordion-item"):
                    q = t.select_one(".elementor-tab-title")
                    a = t.select_one(".elementor-tab-content")
                    if q and a:
                        items.append({"q": q.get_text(" ", strip=True), "a": clean_inline(a)})
                for d in child.select("details"):
                    su = d.find("summary")
                    if su:
                        rest = BeautifulSoup(
                            "<div>" + "".join(str(x) for x in d.children if x is not su) + "</div>",
                            "html.parser").div
                        items.append({"q": su.get_text(" ", strip=True), "a": clean_inline(rest)})
                if items:
                    blocks.append({"type": "faq", "items": items})
                    continue

            if "elementor-widget-tabs" in cls:
                items = []
                for q, a in zip(child.select(".elementor-tab-title"),
                                child.select(".elementor-tab-content")):
                    items.append({"q": q.get_text(" ", strip=True), "a": clean_inline(a)})
                if items:
                    blocks.append({"type": "faq", "items": items})
                    continue

            if "elementor-widget-icon-box" in cls:
                t = child.select_one(".elementor-icon-box-title")
                d = child.select_one(".elementor-icon-box-description")
                lnk = child.select_one(".elementor-icon-box-title a") or child.select_one("a")
                blocks.append({"type": "card",
                               "title": t.get_text(" ", strip=True) if t else "",
                               "text": d.get_text(" ", strip=True) if d else "",
                               "href": rel(lnk.get("href")) if lnk else None})
                continue

            if "elementor-widget-image-box" in cls:
                t = child.select_one(".elementor-image-box-title")
                d = child.select_one(".elementor-image-box-description")
                im = child.find("img")
                lnk = child.select_one("a")
                blocks.append({"type": "card",
                               "title": t.get_text(" ", strip=True) if t else "",
                               "text": d.get_text(" ", strip=True) if d else "",
                               "img": img_data(im)["src"] if im else None,
                               "href": rel(lnk.get("href")) if lnk else None})
                continue

            if "elementor-widget-button" in cls:
                a = child.find("a")
                if a:
                    blocks.append({"type": "button", "text": a.get_text(" ", strip=True),
                                   "href": rel(a.get("href"))})
                continue

            if "elementor-widget-testimonial" in cls or "elementor-widget-reviews" in cls:
                items = []
                for t in child.select(".elementor-testimonial"):
                    name = t.select_one(".elementor-testimonial__name")
                    text = t.select_one(".elementor-testimonial__text")
                    stars = len(t.select(".elementor-star-full")) or 5
                    items.append({"stars": stars,
                                  "text": text.get_text(" ", strip=True) if text else "",
                                  "author": name.get_text(" ", strip=True) if name else "",
                                  "location": ""})
                if items:
                    blocks.append({"type": "reviews", "items": items})
                else:
                    blocks.append({"type": "reviews_raw", "html": clean_inline(child)})
                continue

            if "elementor-widget-image" in cls:
                im = child.find("img")
                if im:
                    d = img_data(im)
                    a = child.find("a")
                    if a:
                        d["href"] = rel(a.get("href"))
                    blocks.append(d)
                continue

            if child.name in BLOCK_TAGS:
                push_primitive(child)
                continue

            walk(child)

    walk(container)
    return blocks


def parse_head(soup):
    def m(sel, attr="content"):
        e = soup.select_one(sel)
        return e.get(attr) if e else None

    ld = []
    for s_ in soup.find_all("script", type="application/ld+json"):
        raw = s_.string or ""
        try:
            ld.append(json.loads(raw))
        except Exception:
            ld.append({"_raw": raw[:20000]})
    return {
        "meta_title": soup.title.get_text() if soup.title else None,
        "meta_description": m('meta[name="description"]'),
        "robots": m('meta[name="robots"]'),
        "canonical": m('link[rel="canonical"]', "href"),
        "og_title": m('meta[property="og:title"]'),
        "og_description": m('meta[property="og:description"]'),
        "og_image": m('meta[property="og:image"]'),
        "og_type": m('meta[property="og:type"]'),
        "schema": ld,
    }


def main():
    idx = json.load(open(os.path.join(HERE, "crawl-index.json"), encoding="utf-8"))
    pages = []
    for rec in idx:
        path = os.path.join(RAW, rec["file"])
        if not os.path.exists(path):
            continue
        soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
        head = parse_head(soup)
        cont = (soup.select_one(".elementor-location-single")
                or soup.select_one(".elementor-location-archive")
                or soup.select_one("main") or soup.body)
        h1 = cont.find("h1")
        blocks = extract_blocks(cont)
        links = []
        for a in cont.find_all("a", href=True):
            r = rel(a["href"])
            if r and r.startswith("/"):
                links.append({"href": r, "text": a.get_text(" ", strip=True)[:80]})
        images = [b["src"] for b in blocks if b.get("type") == "image" and b.get("src")]
        pages.append({
            "url": rec["url"], "path": rel(rec["url"]), "file": rec["file"],
            **head,
            "h1": h1.get_text(" ", strip=True) if h1 else None,
            "blocks": blocks, "internal_links": links, "images": images,
        })
        print("%-52s blocks=%-4d links=%-3d" % (rec["file"][:50], len(blocks), len(links)), flush=True)
    json.dump(pages, open(os.path.join(HERE, "content.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("TOTAL PAGES", len(pages))


main()
