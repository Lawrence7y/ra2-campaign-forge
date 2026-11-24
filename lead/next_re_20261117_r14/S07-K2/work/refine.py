"""Refine: value dist among 49 object-field +0x94 writes; +0x80 base-reg+value cross."""
import os, re
from collections import Counter
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S07-K2\EVIDENCE"

def base_reg(hins):
    mm = re.search(r"\[(\w+)", hins)
    return mm.group(1) if mm else "?"

# +0x94 object writes
rows=[]
with open(os.path.join(OUTDIR,"sweep_0x94_access.tsv"),encoding="utf-8") as f:
    h=f.readline().rstrip("\n").split("\t")
    for l in f: rows.append(dict(zip(h,l.rstrip("\n").split("\t"))))
objw=[r for r in rows if r["is_write"]=="1" and base_reg(r["hins"])!="esp"]
print("+0x94 object-field writes:", len(objw))
print("  value dist:", Counter(r["valstr"] for r in objw).most_common())
print("  -1 count:", sum(1 for r in objw if r["valstr"]=="0xffffffff"))
print("  imm0 count:", sum(1 for r in objw if r["valstr"]=="0x0"))
print("  register count:", sum(1 for r in objw if r["valstr"]=="REG/OTHER"))

# +0x80 writes: cross value x base-reg
w80=[]
with open(os.path.join(OUTDIR,"sweep_0x80_access.tsv"),encoding="utf-8") as f:
    h=f.readline().rstrip("\n").split("\t")
    for l in f:
        r=dict(zip(h,l.rstrip("\n").split("\t")))
        if r["kind"]=="WRITE": w80.append(r)
print("\n+0x80 writes total:", len(w80))
print("  base-reg dist:", Counter(base_reg(r["hins"]) for r in w80).most_common())
print("  byte value dist:", Counter(r["valstr"] for r in w80).most_common())
# non-esp only
nonstack=[r for r in w80 if base_reg(r["hins"])!="esp"]
print("  non-stack writes:", len(nonstack), " funcs:", len(set(r["func"] for r in nonstack if r['func']!='-')))
print("  non-stack value dist:", Counter(r["valstr"] for r in nonstack).most_common())
