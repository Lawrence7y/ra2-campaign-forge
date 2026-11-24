# -*- coding: utf-8 -*-
"""M59 simulate merge in memory, compute exact post-merge values."""
import csv, os, re, collections

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
D15  = os.path.join(ROOT, "S15S16_3B2", "S15_delta.tsv")
D16  = os.path.join(ROOT, "S15S16_3B2", "S16_delta.tsv")
OUT  = os.path.join(ROOT, "_cards", "M59-MERGE", "SIMULATE.txt")

PASS = ["006E3DB0","006E4660","006E5730","006E6080","006E6410","00727240","006CE800"]
EVID = "S15S16_3B2/_audit/VERDICT.md"

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

lines=[]
def p(s=""): lines.append(str(s))

# load atlas
atlas=set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i,line in enumerate(f):
        if i==0: continue
        q=line.rstrip("\r\n").split("\t")
        if q and q[0].strip(): atlas.add(ne(q[0]))

# load cov
with open(COV, encoding="utf-8-sig", newline="") as f:
    cov=list(csv.reader(f, delimiter="\t"))[1:]
cov=[r for r in cov if len(r)>=8]

# load delta col4 (one_line_semantics) by entry
delta={}
for df in (D15,D16):
    with open(df, encoding="utf-8-sig", newline="") as f:
        rr=list(csv.reader(f, delimiter="\t"))
    for r in rr[1:]:
        if len(r)>=6:
            delta[ne(r[0])] = r[3]

p("=== delta col4 (one_line_semantics) for 7 PASS; check 未证 marker ===")
for e in PASS:
    sem=delta[e]
    p("%s  含[未证]=%s  含'未证'=%s  len=%d" % (e, "[未证]" in sem, "未证" in sem, len(sem)))

# apply merge in memory
idx={ne(r[0]):i for i,r in enumerate(cov)}
for e in PASS:
    i=idx[e]
    r=cov[i]
    cov[i]=[r[0],r[1],r[2],delta[e],"[已证]",EVID,r[6],r[7]]

# recompute
full=sum(1 for r in cov if r[4].strip()=="[已证]")
ain =sum(1 for r in cov if r[4].strip()=="[已证]" and ne(r[0]) in atlas)
aout=full-ain
p("")
p("改后 全表[已证]=%d  atlas内=%d  atlas外=%d" % (full,ain,aout))

d=collections.defaultdict(collections.Counter)
for r in cov:
    e=ne(r[0]); s=r[1].strip()
    if e not in atlas: continue
    if r[4].strip()=="[已证]":
        d[s]["proved"]+=1
        if "[未证]" not in r[3]: d[s]["strict"]+=1

import math
for s in ("S15","S16"):
    a=d[s]["proved"]; st=d[s]["strict"]
    n=158 if s=="S15" else 90
    thr=math.ceil(0.5*n)
    p("%s proved=%d/%d=%.4f%%  proved_strict=%d/%d=%.4f%%  thr50=%d  gap(proved)=%d  gap(strict)=%d" % (
        s,a,n,100.0*a/n,st,n,100.0*st/n,thr,thr-a,thr-st))

tprov=sum(d[s]["proved"] for s in d if re.match(r"^S\d\d$",s))
tstr =sum(d[s]["strict"]  for s in d if re.match(r"^S\d\d$",s))
p("S01-S22 proved合计=%d  strict合计=%d" % (tprov,tstr))
p("TOTAL proved_pct (atlas内已证/12916) = %.4f%%" % (100.0*ain/12916))

# verify 7 rows and 4 FAIL rows post state
p("")
p("=== 7 PASS 改后 col4/5/6 (first 50 chars of col4) ===")
for e in PASS:
    r=cov[idx[e]]
    p("%s | %s | %s | %s" % (e, r[3][:50], r[4], r[5]))
p("")
p("=== grade 直方图 ===")
p(repr(dict(collections.Counter(r[4].strip() for r in cov))))

with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
print("WROTE", OUT)
