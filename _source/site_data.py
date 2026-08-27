# -*- coding: utf-8 -*-
"""Derive the global site model (nav, footer, contact details) from the crawl."""
import json, os, re, urllib.parse
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.join(HERE, "raw", "home-980480e7.html")


def rel(u):
    if not u:
        return u
    u = u.strip()
    if u.startswith(("#", "tel:", "mailto:")):
        return u
    p = urllib.parse.urlparse(u)
    if p.netloc and "mizugpro.co.il" not in p.netloc:
        return u
    path = urllib.parse.unquote(p.path) or "/"
    if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path += "/"
    return path


soup = BeautifulSoup(open(HOME, encoding="utf-8").read(), "html.parser")
header = soup.select_one(".elementor-location-header")
footer = soup.select_one(".elementor-location-footer")

# ---- primary navigation (flattened list from Elementor, rebuilt as a tree) ----
menu = header.select_one(".elementor-nav-menu--main")
flat = []
for li in menu.select("li.menu-item"):
    a = li.find("a", href=True)
    if not a:
        continue
    depth = len(li.find_parents("ul")) - 1
    flat.append({"text": a.get_text(" ", strip=True), "href": rel(a["href"]), "depth": depth})

nav, stack = [], []
for item in flat:
    node = {"text": item["text"], "href": item["href"], "children": []}
    if item["depth"] == 0:
        nav.append(node)
        stack = [node]
    else:
        parent = stack[min(item["depth"], len(stack)) - 1]
        parent["children"].append(node)
        stack = stack[:item["depth"]] + [node]

# ---- footer link columns -----------------------------------------------------
columns = []
for col in footer.select(".elementor-widget-heading h3, h3"):
    title = col.get_text(" ", strip=True)
    holder = col.find_parent(class_=re.compile(r"e-con|elementor-column"))
    if not holder:
        continue
    links, seen = [], set()
    for a in holder.select("a[href]"):
        href = rel(a["href"])
        text = a.get_text(" ", strip=True)
        if not text or href in seen:
            continue
        seen.add(href)
        links.append({"text": text, "href": href})
    if links:
        columns.append({"title": title, "links": links})

# ---- contact block -----------------------------------------------------------
contact_lines = []
for h in footer.find_all(["h2", "h3", "p"]):
    t = h.get_text(" ", strip=True)
    if t and ("@" in t or "טלפון" in t or "כתובת" in t or "24/7" in t):
        contact_lines.append(t)

socials = []
for a in footer.select('a[href*="facebook"], a[href*="youtube"], a[href*="instagram"]'):
    href = a["href"]
    kind = ("facebook" if "facebook" in href else
            "youtube" if "youtube" in href else "instagram")
    if not any(s["kind"] == kind for s in socials):
        socials.append({"kind": kind, "href": href})

logo = None
for im in header.select("img[src]"):
    if im["src"].startswith("http"):
        logo = "/assets/img/" + urllib.parse.unquote(im["src"].rsplit("/", 1)[-1])
        break

site = {
    "name": "מיזוג פרו",
    "base_url": "https://mizugpro.co.il",
    "lang": "he-IL",
    "logo": logo,
    "nav": nav,
    "footer_columns": columns,
    "contact_lines": contact_lines,
    "socials": socials,
    # The live site printed two different numbers; 033820923 is the correct one.
    "phone_cta": "033820923",
    "phone_footer": "033820923",
    "email": "support@mizugpro.co.il",
    "address": "הנביאים 8 תל אביב, ליד דיזינגוף סנטר",
    "hours": "עובדים 24/7",
    # carried over from the old site so measurement and verification survive the move
    "gtm_id": "GTM-PLDQTM22",
    "gsc_verification": "adjj7vW4RoH5JQCDDH-uyrjnqN7wOL61wJgULHFCf1k",
}

json.dump(site, open(os.path.join(HERE, "site.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps({k: (v if not isinstance(v, list) else f"[{len(v)} items]")
                  for k, v in site.items()}, ensure_ascii=False, indent=1))
for c in columns:
    print(" column:", c["title"], len(c["links"]))
print(" nav roots:", [n["text"] + f"({len(n['children'])})" for n in nav])
