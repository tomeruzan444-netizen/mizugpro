# -*- coding: utf-8 -*-
"""
Answer one question: is the live site running my latest commit?

Every build writes /version.json with the commit it came from. This asks the
domain for that file and compares it to the head of the deploy branch, then
spot-checks that pages are actually being served.

    python check_live.py                      # against mizugpro.co.il
    python check_live.py https://new.mizugpro.co.il
"""
import json, os, subprocess, sys, urllib.parse
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = (sys.argv[1] if len(sys.argv) > 1 else "https://mizugpro.co.il").rstrip("/")
REMOTE = "https://github.com/tomeruzan444-netizen/mizugpro"

OK, BAD, WARN = "✓", "✗", "!"


def remote_head(branch):
    out = subprocess.run(["git", "ls-remote", REMOTE, "refs/heads/" + branch],
                         cwd=ROOT, capture_output=True, text=True, timeout=60)
    line = out.stdout.strip().split("\n")[0]
    return line.split("\t")[0] if line else ""


def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "mizugpro-deploy-check"})

    print("site   :", SITE)
    print()

    # --- what is live? ------------------------------------------------------
    live = None
    try:
        r = session.get(SITE + "/version.json", timeout=30)
        if r.status_code == 200:
            live = r.json()
    except Exception as e:
        print(BAD, "version.json unreachable:", str(e)[:70])

    if live is None:
        print(BAD, "the live site is not serving /version.json")
        print("     either the new site is not deployed yet, or the deploy did not finish")
        return 1

    print(OK, "live build : %s  (%s, %s)" % (live.get("short"), live.get("built_at"),
                                             live.get("built_by")))

    # --- what should be live? ----------------------------------------------
    head = remote_head("deploy")
    main_head = remote_head("main")
    print("  deploy branch head :", head[:7] or "unknown")
    print("  main branch head   :", main_head[:7] or "unknown")
    print()

    # deploy is built *from* main, so the stamp carries the main commit
    if live.get("commit") == main_head:
        print(OK, "the live site is running the latest commit")
        status = 0
    else:
        print(WARN, "the live site is behind main")
        print("     live is %s, main is %s" % (live.get("short"), main_head[:7]))
        print("     if a build just ran, give Hostinger a minute and re-check")
        status = 1

    # --- is it actually serving the site? -----------------------------------
    print()
    checks = [("/", "home"), ("/sitemap.xml", "sitemap"), ("/robots.txt", "robots"),
              ("/מחירון-מזגנים/", "a Hebrew URL"), ("/assets/css/site.min.css", "stylesheet")]
    for path, label in checks:
        try:
            r = session.get(SITE + urllib.parse.quote(path), timeout=30)
            mark = OK if r.status_code == 200 else BAD
            print("%s %-14s %s  %s bytes" % (mark, label, r.status_code, len(r.content)))
            if r.status_code != 200:
                status = 1
        except Exception as e:
            print(BAD, label, str(e)[:60])
            status = 1

    return status


if __name__ == "__main__":
    sys.exit(main())
