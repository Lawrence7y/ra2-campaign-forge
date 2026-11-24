#!/usr/bin/env python3
"""Q4 out-of-sample check: pick 10 files NOT in the 20-sample, stratified across verdict categories, dump head for manual judgment."""
import csv, os, re
LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID")
with open(os.path.join(OUT,"_verdicts.tsv"), encoding="utf-8", newline="") as f:
    v = list(csv.DictReader(f, delimiter="\t"))
with open(os.path.join(OUT,"_samples20.txt"), encoding="utf-8") as f:
    used = set(re.match(r"\[\d\d\]\s+(.+)", l).group(1).strip() for l in f if re.match(r"\[\d\d\]\s+(.+)", l))
from collections import defaultdict
byv = defaultdict(list)
for r in v:
    if r["rel"] not in used:
        byv[r["verdict"]].append(r)
# 每类取若干：对象4 过程3 无法判定3
quota = {"对象抄本":4,"过程输出":3,"无法判定":3}
picks=[]
for k,q in quota.items():
    pool = sorted(byv[k], key=lambda x:x["rel"])
    step=len(pool)/q
    for i in range(q):
        picks.append(pool[int(i*step)])
with open(os.path.join(OUT,"_oos10.txt"),"w",encoding="utf-8") as fo:
    for i,r in enumerate(picks,1):
        p=os.path.join(LEAD, r["rel"].replace("/",os.sep))
        with open(p,"rb") as fh: t=fh.read(8192).decode("utf-8",errors="replace")
        lines=[l for l in t.splitlines() if l.strip()]
        fo.write(f"[{i:02d}] {r['rel']}\n   criterion={r['verdict']} O={r['O']} P={r['P']} why={r['reason']}\n")
        for j,l in enumerate(lines[:12]):
            fo.write(f"   {j+1:2d}| {l[:150]}\n")
        fo.write("\n")
print("wrote", len(picks))
