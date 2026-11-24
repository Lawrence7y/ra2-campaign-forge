# -*- coding: utf-8 -*-
"""M70 compute exact post-merge panel numbers and verify no DoD status flip."""
import csv, os, re, sys, math, collections
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except ValueError: return e
atlas=set()
with open(ATLAS,encoding="utf-8-sig") as f:
    for i,l in enumerate(f):
        if i==0: continue
        p=l.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))
with open(COV,encoding="utf-8-sig",newline="") as f:
    cov=[r for r in list(csv.reader(f,delimiter="\t"))[1:] if len(r)>=8]
d=collections.defaultdict(collections.Counter)
for r in cov:
    e=ne(r[0]); s=r[1].strip()
    if e not in atlas: continue
    name=r[2].strip(); sem=r[3]; grade=r[4].strip()
    d[s]["atlas_n"]+=1
    if name and not name.startswith("sub_"):
        d[s]["named_L"]+=1
        if not RE_CSUB.search(name):
            d[s]["named_S14"]+=1
            if not RE_SLOT.search(name): d[s]["named_strict"]+=1
    if grade=="[已证]":
        d[s]["proved"]+=1
        if "[未证]" not in sem: d[s]["strict"]+=1
print("--- post-merge exact percentages ---")
for s in ("S22",):
    c=d[s]; a=c["atlas_n"]
    print(f"{s}: proved={c['proved']}/{a}={round(100.0*c['proved']/a,2)}  strict={c['strict']}/{a}={round(100.0*c['strict']/a,2)}")
tot=collections.Counter()
for s in d:
    for k in ("atlas_n","named_L","named_S14","named_strict","proved","strict"): tot[k]+=d[s][k]
a=tot["atlas_n"]
print(f"TOTAL: proved={tot['proved']}/{a}={round(100.0*tot['proved']/a,2)}  strict={tot['strict']}/{a}={round(100.0*tot['strict']/a,2)}")

print("\n--- DoD flip check (all S01..S21; S22 excluded from ranking) ---")
nom=[]; st=[]
for s in sorted(k for k in d if re.match(r"^S\d\d$",k) and k!="S22"):
    c=d[s]; an=c["atlas_n"]; tn=math.ceil(0.9*an); tp=math.ceil(0.5*an)
    ok_n=c["named_S14"]>=tn; ok_p=c["proved"]>=tp; ok_ps=c["strict"]>=tp
    nm = ok_n and ok_p; sm = ok_n and ok_ps
    if nm: nom.append(s)
    if sm: st.append(s)
print("nominal 达标:", nom, f"({len(nom)}/22)")
print("strict 达标:", st, f"({len(st)}/22)")
print("EXPECTED nominal = [S15,S16,S17], strict = [S17]")
print("NO_FLIP:", nom==["S15","S16","S17"] and st==["S17"])
# S22 threshold
c=d["S22"]; print(f"S22 threshold ceil(0.5*4851)={math.ceil(0.5*c['atlas_n'])}; proved={c['proved']} strict={c['strict']} (far below; S22 not ranked)")
