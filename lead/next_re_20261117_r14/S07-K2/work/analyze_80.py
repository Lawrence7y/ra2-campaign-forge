"""Analyze 0x80 writes: classify into 4 categories, check index!=0, funcs."""
import os
from collections import Counter, defaultdict
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S07-K2\EVIDENCE"

rows = []
with open(os.path.join(OUTDIR, "sweep_0x80_access.tsv"), encoding="utf-8") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        rows.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))

writes = [r for r in rows if r["kind"] == "WRITE"]
reads = [r for r in rows if r["kind"] == "READ"]

print("total writes:", len(writes), "funcs:", len(set(r["func"] for r in writes if r["func"] != "-")))
print("total reads:", len(reads))

# value distribution
print("\n-- write value dist (valstr) --")
for k, v in Counter(r["valstr"] for r in writes).most_common():
    print("  %-12s %d" % (k, v))

# classify 4 categories per task:
# 写0消费 / 写1有比较 / 写1无比较 / 写寄存器
# Need context: for each write, look at nearby instructions for cmp/jcc of the value.
print("\n-- all writes with value=0 (写0) count --", sum(1 for r in writes if r["valstr"]=="0x0"))
print("-- all writes with value=1 (写1) count --", sum(1 for r in writes if r["valstr"]=="0x1"))
print("-- register writes --", sum(1 for r in writes if r["valstr"]=="REG/OTHER"))

# index!=0 forms (e.g. [reg+ecx*N+0x80])
print("\n-- writes with index in hins (contains '*') --")
idx = [r for r in writes if "*" in r["hins"]]
for r in idx[:20]:
    print("  ", r["va"], r["hins"])
print("  count:", len(idx))

# Dump all writes with value 0 and 1 for manual context
print("\n-- WRITE 0x1 sites (first 60) --")
c=0
for r in writes:
    if r["valstr"]=="0x1":
        print("  ", r["va"], r["hins"], "fn="+r["func"]); c+=1
        if c>=60: break
