#!/usr/bin/env python3
"""R51-T1-TIE152 / Q5 正控 · 法1（Python）：独立于 q1_extract.py 重算一遍。
不复用 q1_extract.py 的任何函数；三份源清单各自独立读盘、独立算集合差、独立 stat 字节。
"""
import csv, os, sys
sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R = os.path.join(LEAD, "next_re_20261117_r14")
OUT = os.path.join(R, "R17_R91_T1_TIE152")


def rd(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# 基线 1242（files_excluded_prime.tsv: label=UNDECIDED ∧ rel 含 EVIDENCE）
base = [r["rel"] for r in rd(os.path.join(R, "R17_R78_T1_RECLASS", "files_excluded_prime.tsv"))
        if r["label"] == "UNDECIDED" and "evidence" in r["rel"].lower()]
base_b = sum(os.path.getsize(os.path.join(LEAD, p.replace("/", os.sep))) for p in base)

# R44 已裁 976（_verdicts.tsv: verdict ∈ {对象抄本, 过程输出}）
vd = rd(os.path.join(R, "R17_R81_T2_EVID", "_verdicts.tsv"))
obj = [r["rel"] for r in vd if r["verdict"] == "对象抄本"]
prc = [r["rel"] for r in vd if r["verdict"] == "过程输出"]
obj_b = sum(os.path.getsize(os.path.join(LEAD, p.replace("/", os.sep))) for p in obj)
prc_b = sum(os.path.getsize(os.path.join(LEAD, p.replace("/", os.sep))) for p in prc)
tie266 = [r["rel"] for r in vd if r["verdict"] == "无法判定"]
tie266_b = sum(os.path.getsize(os.path.join(LEAD, p.replace("/", os.sep))) for p in tie266)

# R46 同目录多数派：分母=已裁件，>=3 且同向 >=75%
dec_by_dir = {}
for rel, lab in [(r, "O") for r in obj] + [(r, "P") for r in prc]:
    d = os.path.dirname(rel)
    o, p = dec_by_dir.get(d, (0, 0))
    dec_by_dir[d] = (o + (lab == "O"), p + (lab == "P"))

r46 = []
left = []
for rel in tie266:
    d = os.path.dirname(rel)
    o, p = dec_by_dir.get(d, (0, 0))
    n = o + p
    ok = n >= 3 and o != p and max(o, p) / n >= 0.75
    (r46 if ok else left).append(rel)
r46_b = sum(os.path.getsize(os.path.join(LEAD, q.replace("/", os.sep))) for q in r46)
left_b = sum(os.path.getsize(os.path.join(LEAD, q.replace("/", os.sep))) for q in left)

# 与落盘 tie152.tsv 对照
disk = [r["rel"] for r in rd(os.path.join(OUT, "tie152.tsv"))]
disk_b = sum(int(r["bytes"]) for r in rd(os.path.join(OUT, "tie152.tsv")))

print(f"base1242   = {len(base)} 件 / {base_b} B")
print(f"R44 已裁    = {len(obj)+len(prc)} 件 / {obj_b+prc_b} B  (对象 {len(obj)}/{obj_b} + 过程 {len(prc)}/{prc_b})")
print(f"1242-976   = {len(base)-len(obj)-len(prc)} 件 / {base_b-obj_b-prc_b} B  (=平票266: {len(tie266)}/{tie266_b})")
print(f"R46 再裁    = {len(r46)} 件 / {r46_b} B")
print(f"1242-976-114 = {len(base)-len(obj)-len(prc)-len(r46)} 件 / {base_b-obj_b-prc_b-r46_b} B")
print(f"161 落盘    = {len(disk)} 件 / {disk_b} B ; 集合相同={sorted(disk)==sorted(left)}")
print(f"字节算式闭合={base_b-obj_b-prc_b-r46_b == left_b == disk_b}")
with open(os.path.join(OUT, "q5_posctrl_py.txt"), "w", encoding="utf-8") as f:
    f.write(f"法1 Python: 152 件 / {left_b} B ; 1242−976−114 件 {len(left)} ; 字节 {base_b}-{obj_b+prc_b}-{r46_b}={base_b-obj_b-prc_b-r46_b}\n")
