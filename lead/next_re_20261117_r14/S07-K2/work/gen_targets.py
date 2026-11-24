"""Generate TARGETS.tsv: S07 ∩ atlas entries with gap + evidence plan."""
import os

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\S07-K2\TARGETS.tsv")

def load_atlas():
    d = {}
    with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            p = line.split("\t")
            rec = dict(zip(hdr, p))
            try:
                va = int(rec["entry"], 16)
            except Exception:
                continue
            d[va] = rec
    return d

def is_sub_name(name):
    return (not name) or name.startswith("sub_") or ("Class::sub_" in name)

atlas = load_atlas()
rows = []
with open(COV, "r", encoding="utf-8", errors="replace") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        rec = dict(zip(hdr, line.split("\t")))
        if rec.get("subsystem") != "S07":
            continue
        try:
            va = int(rec["entry"], 16)
        except Exception:
            continue
        if va not in atlas:
            continue
        name = rec.get("name", "")
        grade = rec.get("grade", "")
        # 缺什么 + 取证计划
        if grade == "[已证]":
            miss = "已证(维持)"
            plan = "n/a"
        elif not is_sub_name(name):
            miss = "缺字节级证据: 已有名/语义但无读写指令或独立复算"
            plan = "定点反汇编+RTTI/vtable或imm32或读写指令双支撑;优先T2六机制"
        else:
            miss = "缺真名+语义+证据: sub_占位"
            plan = "RTTI静态vtable初始化链定名(C7 05->vt[-1]->COL->TD)+双支撑"
        a = atlas[va]
        rows.append((va, rec["entry"], name, grade, a.get("size", ""), miss, plan))

rows.sort()
with open(OUT, "w", encoding="utf-8", newline="") as f:
    # no header (consistent with project's TSVs; but this one is a list -> include header for readability)
    f.write("entry\tname\tgrade\tatlas_size\tmissing\tevidence_plan\n")
    for va, entry, name, grade, size, miss, plan in rows:
        f.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (entry, name, grade, size, miss, plan))

print("TARGETS.tsv written:", OUT, "data rows:", len(rows))
# quick distribution
from collections import Counter
print("grade dist:", Counter(r[3] for r in rows))
