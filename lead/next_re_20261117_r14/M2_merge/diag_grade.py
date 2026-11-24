# -*- coding: utf-8 -*-
"""Diagnose DGRD direction: compare coverage vs delta grade, cross-check PENDING/UNSOURCED."""
import csv, os, sys, glob, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.reader(f,delimiter="\t"))
def ne(e):
    e=e.strip().upper()
    try: return "%08X"%int(e,16)
    except: return e
covrows=rd(os.path.join(ROOT,"COVERAGE","coverage.tsv"))[1:]
cov={ne(r[0]):r for r in covrows}
RANK={"[已证]":3,"[静态推断]":2,"[未证]":1}
def grank(g):
    g=g.strip()
    return RANK.get(g, 0)

# Build lookups
pending=rd(os.path.join(ROOT,"COVERAGE","PENDING_CORRECTIONS.tsv"))[1:]
pend_entries=collections.defaultdict(list)
for r in pending:
    pend_entries[ne(r[1])].append((r[2],r[3],r[4]))
unsourced=rd(os.path.join(ROOT,"COVERAGE","UNSOURCED_PROVED.tsv"))[1:]
uns_entries={ne(r[0]):r for r in unsourced}
conflicts=rd(os.path.join(ROOT,"COVERAGE","CONFLICTS.tsv"))[1:]
conf_entries=collections.defaultdict(list)
for r in conflicts:
    conf_entries[ne(r[0])].append((r[1],r[2],r[3]))

# classify all DGRD across all deltas: cov higher / delta higher / non-standard grade
upgrades=[]   # delta grade > cov grade (candidate upgrade)
downgrades=[] # delta grade < cov grade
nonstd=[]
for dpath in sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True)):
    card=os.path.basename(os.path.dirname(dpath))
    for r in rd(dpath)[1:]:
        if not r or not r[0].strip(): continue
        e=ne(r[0]); dg=r[4].strip() if len(r)>4 else ""
        if e not in cov: continue
        cg=cov[e][4].strip()
        cr,dr=grank(cg),grank(dg)
        if dr==0 and dg not in ("","high"):
            nonstd.append((card,e,cg,dg,cov[e][2],r[2] if len(r)>2 else ""))
            continue
        if dg=="high":
            nonstd.append((card,e,cg,dg,cov[e][2],r[2] if len(r)>2 else ""))
            continue
        if dr>cr: upgrades.append((card,e,cg,dg,cov[e][2],r[2] if len(r)>2 else ""))
        elif dr<cr: downgrades.append((card,e,cg,dg,cov[e][2],r[2] if len(r)>2 else ""))

print("=== UPGRADE candidates (delta grade > coverage grade) count=%d ==="%len(upgrades))
for x in upgrades: print("  ",x)
print("\n=== DOWNGRADE cases (delta grade < coverage grade) count=%d (first 20) ==="%len(downgrades))
for x in downgrades[:20]: print("  ",x)
print("\n=== NON-STANDARD grade ('high'/no-bracket etc) count=%d ==="%len(nonstd))
for x in nonstd[:50]: print("  ",x)

# Check a few specific DGRD entries in pending/unsourced
print("\n=== Cross-check: are upgrade candidates in PENDING or UNSOURCED? ===")
for x in upgrades:
    card,e,cg,dg,cn,dn=x
    print("  ",e,"PEND=",pend_entries.get(e,[]),"UNSRC=",("YES" if e in uns_entries else "no"))
