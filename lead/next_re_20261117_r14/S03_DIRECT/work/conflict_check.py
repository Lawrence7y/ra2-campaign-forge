# -*- coding: utf-8 -*-
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
ROOT=r"D:\Project\ra2-campaign-forge"
WORK=ROOT+r"\lead\next_re_20261117_r14\S03_DIRECT\work"
entries=json.load(open(WORK+r"\candidates.json",encoding="utf8"))
roots=[
  os.path.join(ROOT,"docs","re"),
  os.path.join(ROOT,"re_atlas","kb"),
  os.path.join(ROOT,"re_atlas","LEDGER.md"),
  os.path.join(ROOT,"lead","GOAL_THREE_TARGETS_20261018.md"),
  os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE"),
]
hits={e:[] for e in entries}
def scan_file(fp,label):
    try: txt=open(fp,encoding="utf8",errors="ignore").read()
    except: return
    for e in entries:
        U=txt.upper()
        if e in U or ("0X"+e) in U:
            for i,l in enumerate(txt.splitlines()):
                if e in l.upper() or ("0X"+e) in l.upper():
                    hits[e].append((label,i+1,l.strip()[:220]))
for r in roots:
    if os.path.isfile(r): scan_file(r,"LEDGER")
    elif os.path.isdir(r):
        for dp,dn,fn in os.walk(r):
            for f in fn:
                if f.lower().endswith((".md",".tsv",".txt",".json")):
                    scan_file(os.path.join(dp,f),os.path.relpath(os.path.join(dp,f),ROOT))
json.dump(hits,open(WORK+r"\conflict_hits.json","w",encoding="utf8"),ensure_ascii=False,indent=1)
for e in entries:
    print("==",e,"hits",len(hits[e]))
    for lab,ln,lt in hits[e][:5]:
        print("   ",lab,":",ln,lt)
