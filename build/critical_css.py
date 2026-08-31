# -*- coding: utf-8 -*-
"""
Work out which CSS the first screen actually needs, so the rest can stop
blocking the render.

PageSpeed put 940ms on the stylesheet sitting in front of the first paint. The
file is not big - twelve kilobytes over the wire - but it costs a round trip
before anything can be drawn, and on a throttled phone that round trip is most
of the delay.

Rather than guess at a list of "above the fold" selectors, which rots the first
time someone edits a template, this asks the browser. It loads the built pages
at a phone viewport, records which rules Chrome actually used to paint the
first screen, and keeps those.

Coverage comes back as byte ranges, which can land mid-rule, so the stylesheet
is parsed into whole rules first and a rule is kept if any used byte falls
inside it. @media blocks keep their wrapper and only the inner rules that were
used. A short always-keep list covers what paints before any element matches -
the custom properties, the reset, the fonts.

    python critical_css.py          # writes assets/css/critical.css

Then build.py inlines that file and loads the full stylesheet asynchronously.
"""
import functools
import http.server
import io
import json
import os
import re
import socketserver
import sys
import threading
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(ROOT, "assets", "css", "critical.css")
PORT = 8971

# Sampled rather than exhaustive: the homepage and an article page between them
# exercise every above-the-fold component the site has.
SAMPLE = ["/", "/מחירון-מזגנים/", "/טכנאי-מזגנים-בתל-אביב/"]

# Rules that must survive whatever coverage says, because they paint the page
# before any of their selectors is interesting - tokens, the reset, the fonts.
ALWAYS = re.compile(
    r"^(:root|html|body|\*|\*::before|\*::after|@font-face|@charset"
    r"|\.container|\.skip-link|img|svg|a|h1|h2|h3|p|ul|ol|li|button)\b")


def parse_rules(css):
    """Split a stylesheet into top-level rules, keeping their byte offsets."""
    rules, depth, start = [], 0, 0
    in_str = None
    i = 0
    while i < len(css):
        c = css[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
        elif c in "\"'":
            in_str = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                rules.append((start, i + 1, css[start:i + 1]))
                start = i + 1
        i += 1
    return rules


def used_offsets(entries):
    """Flatten Chrome's coverage ranges into a set of used byte offsets."""
    spans = []
    for e in entries:
        for r in e.get("ranges", []):
            spans.append((r["start"], r["end"]))
    return spans


def touched(spans, lo, hi):
    return any(s < hi and e > lo for s, e in spans)


def main():
    css_files = [f for f in os.listdir(os.path.join(DIST, "assets", "css"))
                 if f.endswith(".css")]
    if not css_files:
        print("no built stylesheet - run build.py first", file=sys.stderr)
        return 1
    sheet = max(css_files, key=lambda f: os.path.getsize(
        os.path.join(DIST, "assets", "css", f)))
    css = io.open(os.path.join(DIST, "assets", "css", sheet),
                  encoding="utf-8").read()
    rules = parse_rules(css)
    print("stylesheet %s  %d rules  %.1f KiB"
          % (sheet, len(rules), len(css.encode()) / 1024))

    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=DIST)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    srv.RequestHandlerClass.log_message = lambda *a, **k: None
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    from playwright.sync_api import sync_playwright

    # CDP rule-usage reports every rule that matched anywhere in the document,
    # which is "used CSS" and not the same thing at all - it came back at 66%
    # of the sheet. What the first paint needs is the rules matching elements
    # inside the first viewport, so that is what gets asked for, in the page.
    EXTRACT = """() => {
      const SHEET = SHEET_NAME_PLACEHOLDER;
      const vh = window.innerHeight;
      // Hidden elements matter as much as visible ones: the rule that hides
      // the desktop nav on a phone has no box to measure, and leaving it out
      // paints the whole menu expanded before the deferred sheet lands.
      const above = [...document.querySelectorAll('*')].filter(e => {
        const r = e.getBoundingClientRect();
        const hidden = r.width === 0 || r.height === 0;
        return hidden || (r.top < vh && r.bottom > 0);
      });
      // A pseudo-element has no node to match against, so .burger::before
      // fails every test and the rule vanishes - which is how the hamburger
      // came out with one bar instead of three. Test the element part.
      const PSEUDO = /::?(before|after|marker|selection|placeholder|backdrop|first-line|first-letter|file-selector-button)(?![a-z-])([(][^)]*[)])?/g;
      const hit = sel => sel.split(',').some(part => {
        const bare = part.replace(PSEUDO, '').trim();
        // a part that was only a pseudo-element, like ::selection, has no
        // node to test against and is kept rather than thrown away
        if (!bare) return true;
        try { return above.some(e => e.matches(bare)); } catch (err) { return false; }
      });
      const out = [];
      const walk = (rule, i) => {
        if (rule.type === 1) {                         // style rule
          if (hit(rule.selectorText)) out.push([i, rule.cssText]);
        } else if (rule.type === 4 || rule.type === 12) {   // @media, @supports
          const inner = [];
          for (const r of rule.cssRules || []) {
            if (r.type === 1 && hit(r.selectorText)) inner.push(r.cssText);
          }
          if (inner.length) {
            out.push([i, '@media ' + rule.conditionText + '{' + inner.join('') + '}']);
          }
        } else if (rule.type === 5) {                  // @font-face
          out.push([i, rule.cssText]);
        }
      };
      // only the real stylesheet: once this has run once, the page also carries
      // an inline copy of the output, and walking both scrambles the order
      for (const sheet of document.styleSheets) {
        if (!sheet.href || !sheet.href.includes(SHEET)) continue;
        let rules;
        try { rules = sheet.cssRules; } catch (err) { continue; }
        [...rules].forEach((rule, i) => walk(rule, i));
      }
      return out;
    }"""

    collected = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for path in SAMPLE:
            pg = b.new_page(viewport={"width": 412, "height": 915})
            pg.goto("http://127.0.0.1:%d%s" % (PORT, urllib.parse.quote(path)),
                    wait_until="networkidle")
            # Once this pass has run, the pages it re-reads have their own
            # output inlined and the rest of the sheet deferred. Measuring that
            # would extract from a half-styled page and shrink a little further
            # every run, so the deferred sheet is forced on before anything is
            # measured. The extraction is then the same whatever the build state.
            pg.evaluate("""() => {
              document.querySelectorAll('link[rel="preload"][as="style"]')
                      .forEach(l => { l.rel = 'stylesheet'; });
            }""")
            pg.wait_for_function(
                "() => [...document.styleSheets].every(s => { "
                "try { return s.cssRules.length >= 0; } catch (e) { return false; } })")
            pg.wait_for_timeout(300)
            collected += pg.evaluate(
                EXTRACT.replace("SHEET_NAME_PLACEHOLDER", json.dumps(sheet)))
            pg.close()
        b.close()
    srv.shutdown()

    # merged on the rule's index in the source sheet, so what comes out is in
    # the order the author wrote it and the cascade still resolves the same way
    chosen = {}
    for i, (lo, hi, text) in enumerate(rules):
        if ALWAYS.match(text.split("{", 1)[0].strip()):
            chosen[i] = text.strip()
    for i, text in collected:
        chosen.setdefault(i, text.strip())

    kept = [chosen[i] for i in sorted(chosen) if chosen[i]]
    critical = "".join(kept)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(critical)
    print("kept %d of %d rules   critical = %.1f KiB (%.0f%% of the sheet)"
          % (len(kept), len(rules), len(critical.encode()) / 1024,
             100 * len(critical) / len(css)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
