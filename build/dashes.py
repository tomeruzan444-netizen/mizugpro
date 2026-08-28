# -*- coding: utf-8 -*-
"""
One dash on the whole site: the ASCII hyphen.

The migrated copy carried three different dashes over from WordPress — an em
dash in prose, an en dash in price ranges, and a stray Hebrew maqaf — which is
three ways of writing the same mark. This flattens all of them to "-".

It runs over the rendered output rather than over the content, because the long
dashes come from three places: the copy in content.json, the templates, and
strings built in Python. Fixing only the copy would leave the other two, and
would leave the next person free to reintroduce them.

Character replacement only. Spacing is left exactly as the copy has it, so
"250 – 400" becomes "250 - 400" and "250–400" becomes "250-400".
"""
import io
import os
import re

# every dash-like character Unicode defines, mapped to the plain hyphen
DASHES = {
    "֊": "-",  # armenian hyphen
    "־": "-",  # hebrew punctuation maqaf
    "᐀": "-",  # canadian syllabics hyphen
    "᠆": "-",  # mongolian todo soft hyphen
    "‐": "-",  # hyphen
    "‑": "-",  # non-breaking hyphen
    "‒": "-",  # figure dash
    "–": "-",  # en dash
    "—": "-",  # em dash
    "―": "-",  # horizontal bar
    "−": "-",  # minus sign
    "⸺": "-",  # two-em dash
    "⸻": "-",  # three-em dash
    "﹘": "-",  # small em dash
    "﹣": "-",  # small hyphen-minus
    "－": "-",  # fullwidth hyphen-minus
}
TABLE = {ord(k): v for k, v in DASHES.items()}
FIND = re.compile("[%s]" % "".join(DASHES))

# style, and any script that is not structured data. JSON-LD is normalised
# along with everything else — it restates the visible copy, so the two would
# otherwise disagree.
_SKIP = re.compile(
    r"(<style\b[^>]*>.*?</style>"
    r"|<script\b(?![^>]*application/ld\+json)[^>]*>.*?</script>)",
    re.S | re.I)

TEXT_FILES = (".html", ".xml", ".txt", ".json", ".webmanifest")

# "6,400 –9,500" was merely lopsided while the dash was long; as "6,400 -9,500"
# it reads as a negative number. Even the spacing up whenever the copy put a
# space on either side, and leave a tight range tight — which also keeps dates,
# phone numbers and filenames ("2026-05-09", "03-3820923", "1-32x32.png")
# untouched, since none of them carry a space.
_RANGE = re.compile(r"(\d[\d,]*)([ \t]*)-([ \t]*)(?=\d)")


def _even_spacing(m):
    joiner = " - " if (m.group(2) or m.group(3)) else "-"
    return m.group(1) + joiner


def normalize(text):
    """Flatten every long dash in a plain string."""
    return _RANGE.sub(_even_spacing, text.translate(TABLE))


def normalize_html(markup):
    """Flatten every long dash in markup, leaving script and style alone."""
    stash = []

    def park(m):
        stash.append(m.group(0))
        return "\x00%d\x00" % (len(stash) - 1)

    text = _SKIP.sub(park, markup)
    text = _RANGE.sub(_even_spacing, text.translate(TABLE))
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)


def count(text):
    return len(FIND.findall(text))


def sweep(root):
    """Rewrite every text file under `root` in place. Returns (files, dashes)."""
    files = dashes = 0
    for folder, _, names in os.walk(root):
        for name in sorted(names):
            if not name.endswith(TEXT_FILES):
                continue
            path = os.path.join(folder, name)
            try:
                s = io.open(path, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            out = normalize_html(s) if name.endswith(".html") else normalize(s)
            if out == s:
                continue
            io.open(path, "w", encoding="utf-8", newline="").write(out)
            files += 1
            dashes += count(s)
    return files, dashes


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
    f, d = sweep(target)
    print("normalised %d dashes across %d files" % (d, f))
