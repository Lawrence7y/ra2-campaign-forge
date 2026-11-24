"""_rsv_scope.py — reconcile the scanned=623 / 18 files / 70 or 73 lines numbers
against the CURRENT tree, using mtime cutoffs to reconstruct the author's corpus.
Run: python -I -X utf8 ".../_rsv_scope.py"
"""
import os, hashlib, time, datetime
from collections import defaultdict
ROOT = r"D:/Project/ra2-campaign-forge/lead"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]
WD = "refsync_scope_20261109/"

def cutoff(ts):
    return datetime.datetime(2026,11,9,ts[0],ts[1],ts[2]).timestamp()

def mdlist():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        d = 0 if rel == "." else rel.count("/") + 1
        for f in fn:
            if not f.lower().endswith(".md"): continue
            p = os.path.join(dp, f)
            out.append((p, os.path.relpath(p, ROOT).replace("\\", "/"), d, os.path.getmtime(p)))
    return out

ALL = mdlist()
print("CURRENT .md total =", len(ALL), " d<=2 =", sum(1 for x in ALL if x[2] <= 2))
for hh,mm,ss,label in [(12,0,0,"<=12:00"),(12,10,0,"<=12:10 (author scan era)"),(12,19,0,"<=12:19 (before CARRIER_MAP)"),(12,25,0,"<=12:25")]:
    t = cutoff((hh,mm,ss))
    sub = [x for x in ALL if x[3] <= t]
    print(f"  {label}: total={len(sub)} d<=2={sum(1 for y in sub if y[2]<=2)}")

def scan(items, excl_wd=False, label=""):
    scanned=0; hits=defaultdict(list)
    for p,rel,d,m in items:
        if excl_wd and rel.startswith(WD): continue
        b=open(p,'rb').read()
        scanned+=1
        ls=b.decode('utf-8','replace').splitlines()
        ln=[i for i,L in enumerate(ls,1) if any(n in L for n in NEEDLES)]
        if ln: hits[rel]=ln
    tot=sum(len(v) for v in hits.values())
    print(f"  [{label}] scanned={scanned} carrier_files={len(hits)} hit_lines={tot}")
    return scanned,len(hits),tot,hits

print()
print("=== A. CURRENT corpus, exact author scope (dir-depth<=2, .md) ===")
a=scan([x for x in ALL if x[2]<=2], False, "current d2 all")
print("=== B. CURRENT corpus d2 EXCLUDING write domain (author's actual universe) ===")
b=scan([x for x in ALL if x[2]<=2], True, "current d2 minus writedomain")
print("=== C. PRE-WRITE-DOMAIN corpus (mtime<=12:10), d2, all ===")
c=scan([x for x in ALL if x[2]<=2 and x[3]<=cutoff((12,10,0))], False, "12:10 d2 all")
print("=== D. PRE-WRITE-DOMAIN corpus (mtime<=12:10), d2, minus writedomain ===")
d=scan([x for x in ALL if x[2]<=2 and x[3]<=cutoff((12,10,0))], True, "12:10 d2 minus writedomain")
print()
print("=== WHICH d2 .md files are inside write domain? ===")
for x in ALL:
    if x[2]<=2 and x[1].startswith(WD):
        print("   ",x[1],datetime.datetime.fromtimestamp(x[3]).strftime('%H:%M:%S'))
print()
print("=== HIT-LINE DELTAS (author claimed 18 files / 70 lines; reply 18/73) ===")
print("  my B (current d2 minus writedomain) per-file lines:")
for r in sorted(b[3]): print("   ",r,b[3][r])
print()
print("  my D (12:10 d2 minus writedomain) per-file lines:")
for r in sorted(d[3]): print("   ",r,d[3][r])
