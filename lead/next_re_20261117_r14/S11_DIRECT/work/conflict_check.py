# -*- coding: utf-8 -*-
import sys, os, re
sys.stdout.reconfigure(encoding="utf-8")
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11_DIRECT\work"
import json
rows=json.load(open(OUT+r"\qualifying.json",encoding="utf8"))
entries=[r["entry"] for r in rows]
ROOT=r"D:\Project\ra2-campaign-forge"
roots=[os.path.join(ROOT,"docs","re"),os.path.join(ROOT,"re_atlas","kb"),os.path.join(ROOT,"lead","GOAL_THREE_TARGETS_20261018.md"),os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE")]
# build a single search for each address token (upper), case-insensitive
hits={e:[] for e in entries}
def scan_file(fp,label):
    try:
        txt=open(fp,encoding="utf8",errors="ignore").read()
    except Exception: return
    for e in entries:
        # search both plain 8-hex and 0x-prefixed
        if e in txt.upper() or ("0X"+e) in txt.upper():
            # collect line numbers (cap 4)
            ls=[(i+1,l.strip()[:200]) for i,l in enumerate(txt.splitlines()) if e in l.upper() or ("0X"+e) in l.upper()]
            for ln,lt in ls[:4]:
                hits[e].append((label,ln,lt))
for r in roots:
    if os.path.isfile(r): scan_file(r,"LEDGER")
    elif os.path.isdir(r):
        for dp,dn,fn in os.walk(r):
            for f in fn:
                if f.lower().endswith((".md",".tsv",".txt",".json")):
                    scan_file(os.path.join(dp,f),os.path.relpath(os.path.join(dp,f),ROOT))
for e in entries:
    print("==",e,"hits",len(hits[e]))
    for lab,ln,lt in hits[e][:6]:
        print("   ",lab,":",ln,lt)