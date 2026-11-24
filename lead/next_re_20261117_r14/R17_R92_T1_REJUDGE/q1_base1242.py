#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R92-T1-REJUDGE / Q1: 取出 EVIDENCE\ 全集 1242 件 + 旧裁决，落 base1242.tsv。

来源（全部只读 lead\ 既有目录）：
  S0  R17_R78_T1_RECLASS\\files_excluded_prime.tsv   列 rel,ext,bytes,...,label
      -> 取 label==UNDECIDED 且 rel 含 EVIDENCE 的行 = 1242 件（§2.46 的口径，与
         R17_R91_T1_TIE152\\q1_extract.py 的 S0 完全同一条取法）
  S1  R17_R81_T2_EVID\\_verdicts.tsv                  列 rel,verdict,O,P,reason  = R44 的 1242 行旧裁决
  S2  R17_R81_T2_EVID\\_undead_evid.tsv               列 rel,...,bytes,...        = 字节数来源
  S3  R17_R91_T1_TIE152\\tie152_verdicts.tsv          列 rel,...,verdict(应留/应排/判不了/混合)
      -> 仅用于标出「R46 之后被判为平票的 152 件」以及 §2.49 点名的 10 件

输出：base1242.tsv  列 rel / bytes / old_verdict / R44_basis
  另附两列（便于后续追溯，不影响卡里要求的四列）:
      old_reason   —— _verdicts.tsv 的 reason 列（objdom/proc-only/... 判据分支名）
      old_O / old_P —— R44 判据算出的对象信号行数 / 过程信号行数
      tie152       —— 是否属 R46 之后的 152 平票件
"""
import csv, os, sys

sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R = os.path.join(LEAD, "next_re_20261117_r14")
OUT = os.path.join(R, "R17_R92_T1_REJUDGE")

EP = os.path.join(R, "R17_R78_T1_RECLASS", "files_excluded_prime.tsv")
VD = os.path.join(R, "R17_R81_T2_EVID", "_verdicts.tsv")
UD = os.path.join(R, "R17_R81_T2_EVID", "_undead_evid.tsv")
T152 = os.path.join(R, "R17_R91_T1_TIE152", "tie152_verdicts.tsv")


def load(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


ep = load(EP)
vd = {r["rel"]: r for r in load(VD)}
ud = {r["rel"]: r for r in load(UD)}
t152 = {r["rel"]: r for r in load(T152)}

base = [r for r in ep if "EVIDENCE" in r["rel"].upper() and r["label"] == "UNDECIDED"]
rows = []
for r in sorted(base, key=lambda x: x["rel"]):
    rel = r["rel"]
    b = int(ud[rel]["bytes"]) if rel in ud else int(r["bytes"])
    v = vd.get(rel, {})
    rows.append({
        "rel": rel,
        "bytes": b,
        "old_verdict": v.get("verdict", "未取得"),
        "R44_basis": v.get("reason", "未取得"),
        "old_O": v.get("O", ""),
        "old_P": v.get("P", ""),
        "tie152": "Y" if rel in t152 else "N",
    })

with open(os.path.join(OUT, "base1242.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, delimiter="\t",
                       fieldnames=["rel", "bytes", "old_verdict", "R44_basis",
                                   "old_O", "old_P", "tie152"])
    w.writeheader()
    for x in rows:
        w.writerow(x)

# ---- 对账 ----
from collections import Counter
c = Counter(x["old_verdict"] for x in rows)
cb = {}
for x in rows:
    cb[x["old_verdict"]] = cb.get(x["old_verdict"], 0) + x["bytes"]
cbasis = Counter(x["R44_basis"] for x in rows)

lines = []
lines.append("=== Q1 全集与旧裁决 ===")
lines.append(f"源清单 S0 : {EP}")
lines.append("             取法：label=='UNDECIDED' 且 rel 大写含 'EVIDENCE'")
lines.append(f"旧裁决 S1 : {VD}  （{len(vd)} 行，覆盖全部 1242 件）")
lines.append(f"字节   S2 : {UD}  （bytes 列）")
lines.append(f"平票标记S3 : {T152}  （{len(t152)} 行，R46 之后的 152 件）")
lines.append("")
lines.append(f"全集 base  : {len(rows)} 件 / {sum(x['bytes'] for x in rows)} B")
for k in ("对象抄本", "过程输出", "无法判定"):
    lines.append(f"  {k} : {c.get(k,0)} 件 / {cb.get(k,0)} B")
lines.append("")
lines.append("旧判据分支（R44_basis = _verdicts.tsv 的 reason 列）:")
for k, n in cbasis.most_common():
    lines.append(f"  {k:20s} {n:5d} 件")
lines.append("")
lines.append(f"落盘 base1242.tsv : {len(rows)} 行 / {sum(x['bytes'] for x in rows)} B")
lines.append(f"其中 tie152 标记 Y : {sum(1 for x in rows if x['tie152']=='Y')} 件")
missing = [x["rel"] for x in rows if x["old_verdict"] == "未取得"]
lines.append(f"旧裁决缺失（未取得）: {len(missing)} 件")

with open(os.path.join(OUT, "q1_recon.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
