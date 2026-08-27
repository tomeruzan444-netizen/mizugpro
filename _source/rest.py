# -*- coding: utf-8 -*-
import json, os, requests
BASE="https://mizugpro.co.il/wp-json/wp/v2/"
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 MizugProMigration"})
out={}
for t in ("pages","posts","categories","tags","media"):
    items=[]; page=1
    while True:
        r=s.get(BASE+t, params={"per_page":100,"page":page}, timeout=90)
        if r.status_code!=200: 
            print(t,"stop at page",page,r.status_code); break
        d=r.json()
        if not d: break
        items+=d; page+=1
        if page>25: break
    out[t]=items
    print(t, len(items), flush=True)
    json.dump(items, open(f"rest-{t}.json","w",encoding="utf-8"), ensure_ascii=False)
