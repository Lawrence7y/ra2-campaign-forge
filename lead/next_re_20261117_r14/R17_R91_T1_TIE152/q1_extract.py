#!/usr/bin/env python3
"""R51-T1-TIE152 / Q1: 从三份源清单做集合减法，取出剩余 152 件平票，落 tie152.tsv。

源（均只读 lead\\ 下既有目录）：
  S0  R17_R78_T1_RECLASS\\files_excluded_prime.tsv   列 rel,label,bytes  -> label=UNDECIDED 且 rel 含 EVIDENCE = 1242 件（基线）
  S1  R17_R81_T2_EVID\\_verdicts.tsv                 列 rel,verdict      -> verdict∈{对象抄本,过程输出} = 976 件（R44 已裁）
  S2  R17_R84_T2_EVID2\\q3_final.py 的同目录多数派规则（≥3 已裁件 ∧ 同向≥75%）-> R46 再裁 114 件
      复算后取 266 − 114 = 152，不硬编码 114，先复现 R46 的 114 再减。
输出：tie152.tsv（列 rel/bytes/parent_dir/cn_lines/va_lines/first_line）
"""
import csv, os, re
from collections import defaultdict, Counter

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R = os.path.join(LEAD, "next_re_20261117_r14")
OUT = os.path.join(R, "R17_R91_T1_TIE152")

EP = os.path.join(R, "R17_R78_T1_RECLASS", "files_excluded_prime.tsv")
VD = os.path.join(R, "R17_R81_T2_EVID", "_verdicts.tsv")
UD = os.path.join(R, "R17_R81_T2_EVID", "_undead_evid.tsv")


def load(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


ep = load(EP)
vd = load(VD)
ud = {r["rel"]: r for r in load(UD)}

# ---- S0 基线 1242 ----
base = [r for r in ep if "EVIDENCE" in r["rel"].upper() and r["label"] == "UNDECIDED"]
base_b = sum(int(r["bytes"]) for r in base)

# ---- S1 已裁 976 ----
dec = [r for r in vd if r["verdict"] in ("对象抄本", "过程输出")]
obj = [r for r in dec if r["verdict"] == "对象抄本"]
prc = [r for r in dec if r["verdict"] == "过程输出"]
dec_b = sum(int(ud[r["rel"]]["bytes"]) for r in dec)
obj_b = sum(int(ud[r["rel"]]["bytes"]) for r in obj)
prc_b = sum(int(ud[r["rel"]]["bytes"]) for r in prc)

# ---- 平票 266 ----
tie266 = [r for r in vd if r["verdict"] == "无法判定"]
tie266_b = sum(int(ud[r["rel"]]["bytes"]) for r in tie266)


def parent(rel):
    p = os.path.dirname(rel)
    return p if p else "(root)"


# ---- S2 R46 同目录多数派复算（与 R17_R84_T2_EVID2/q3_final.py 同规则）----
dcount = defaultdict(Counter)
for r in dec:
    dcount[parent(r["rel"])][r["verdict"]] += 1


def maj_of(d, minn=3, q=0.75):
    c = dcount[d]
    n = c["对象抄本"] + c["过程输出"]
    if n < minn:
        return None
    o, p = c["对象抄本"], c["过程输出"]
    if o == p:
        return None
    lab = "对象抄本" if o > p else "过程输出"
    if max(o, p) / n < q:
        return None
    return lab


r46_taken, r46_left = [], []
for r in tie266:
    (r46_taken if maj_of(parent(r["rel"])) else r46_left).append(r)
r46_b = sum(int(ud[r["rel"]]["bytes"]) for r in r46_taken)
left_b = sum(int(ud[r["rel"]]["bytes"]) for r in r46_left)

# ---- 落 tie152.tsv ----
ADDR = re.compile(r"0x[0-9A-Fa-f]{6,8}")
CN = re.compile(r"[\u4e00-\u9fff]")


def read8k(rel):
    try:
        with open(os.path.join(LEAD, rel.replace("/", os.sep)), "rb") as f:
            return f.read(8192)
    except Exception:
        return None


rows = []
for r in sorted(r46_left, key=lambda x: x["rel"]):
    rel = r["rel"]
    b = read8k(rel)
    if b is None:
        cn = va = -1
        first = "未取得"
    else:
        t = b.decode("utf-8", errors="replace")
        lines = t.splitlines()
        cn = sum(1 for l in lines if CN.search(l))
        va = sum(1 for l in lines if ADDR.search(l))
        first = ""
        for l in lines:
            if l.strip():
                first = l.strip()
                break
    rows.append({
        "rel": rel,
        "bytes": ud[rel]["bytes"],
        "parent_dir": parent(rel),
        "cn_lines": cn,
        "va_lines": va,
        "first_line": first,
    })

with open(os.path.join(OUT, "tie152.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, delimiter="\t", fieldnames=["rel", "bytes", "parent_dir", "cn_lines", "va_lines", "first_line"])
    w.writeheader()
    for x in rows:
        w.writerow(x)

lines = []
lines.append("=== Q1 逐步算式 ===")
lines.append(f"S0 基线  : 1242 件 / {base_b} B   [files_excluded_prime.tsv, label=UNDECIDED ∧ rel含EVIDENCE]")
lines.append(f"S1 已裁  : {len(dec)} 件 / {dec_b} B   [R17_R81_T2_EVID/_verdicts.tsv verdict∈{{对象抄本,过程输出}}]")
lines.append(f"           = 对象抄本 {len(obj)} 件 / {obj_b} B + 过程输出 {len(prc)} 件 / {prc_b} B")
lines.append(f"减法一   : 1242 − {len(dec)} = {len(tie266)} 件 ; {base_b} − {dec_b} = {tie266_b} B")
lines.append(f"S2 R46   : 同目录多数派规则再裁 {len(r46_taken)} 件 / {r46_b} B")
lines.append(f"减法二   : {len(tie266)} − {len(r46_taken)} = {len(r46_left)} 件 ; {tie266_b} − {r46_b} = {left_b} B")
lines.append(f"对账     : 1242−976−114={1242-976-len(r46_taken)} ; {base_b}−{dec_b}−{r46_b}={base_b-dec_b-r46_b} B")
lines.append("")
lines.append(f"实际落盘 tie152.tsv: {len(rows)} 行 / {sum(int(x['bytes']) for x in rows)} B")
lines.append(f"平票件跨目录数: {len(set(x['parent_dir'] for x in rows))}")
with open(os.path.join(OUT, "q1_arith.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
import sys
sys.stdout.reconfigure(encoding="utf-8")
print("\n".join(lines))
