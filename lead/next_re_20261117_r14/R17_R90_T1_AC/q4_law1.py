#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Q4 · 正控 法1（Python，独立实现，不复用 q1/q2 的分支逻辑）：
  只用「读清单 + 纯算术」重算两笔：
    A = R17_R81_T2_EVID\_verdicts.tsv 里 verdict=无法判定 且 父目录已裁件>=3 且 同向>=75%
    C = R17_R84_T1_NARRATIVE\narrative_candidates.tsv 里 basename 命中回滚标记正则
  输出件数与字节，并同时复算 majority_114.tsv / u1_126.tsv 的行数与字节和，
  三者必须互相相等（清单自洽 + 源头重算）。
"""
from __future__ import annotations
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
EVID = os.path.join(R14, "R17_R81_T2_EVID")
NAR = os.path.join(R14, "R17_R84_T1_NARRATIVE")
RE_ROLLBACK = re.compile(r"(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)", re.I)


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        head = f.readline().rstrip("\r\n").split("\t")
        for line in f:
            yield dict(zip(head, line.rstrip("\r\n").split("\t")))


# ---- A ----
bytes_of = {r["rel"].replace("\\", "/"): int(r["bytes"]) for r in rows(os.path.join(EVID, "_undead_evid.tsv"))}
by_dir = {}
for r in rows(os.path.join(EVID, "_verdicts.tsv")):
    if r["verdict"] in ("对象抄本", "过程输出"):
        d = os.path.dirname(r["rel"])
        by_dir.setdefault(d, [0, 0])
        by_dir[d][0 if r["verdict"] == "对象抄本" else 1] += 1

a_n = a_b = 0
for r in rows(os.path.join(EVID, "_verdicts.tsv")):
    if r["verdict"] != "无法判定":
        continue
    o, p = by_dir.get(os.path.dirname(r["rel"]), [0, 0])
    n = o + p
    if n >= 3 and max(o, p) / n >= 0.75 and o != p:
        a_n += 1
        a_b += bytes_of[r["rel"].replace("\\", "/")]

# ---- C ----
c_n = c_b = 0
for r in rows(os.path.join(NAR, "narrative_candidates.tsv")):
    if RE_ROLLBACK.search(r["rel"].rsplit("/", 1)[-1]):
        c_n += 1
        c_b += int(r["bytes"])

# ---- 清单自洽 ----
def tsv_sum(p):
    n = b = 0
    for r in rows(os.path.join(HERE, p)):
        n += 1
        b += int(r["bytes"])
    return n, b


res = {
    "law": "python_q4_posctrl.py",
    "A_from_source": {"n": a_n, "bytes": a_b},
    "C_from_source": {"n": c_n, "bytes": c_b},
    "A_from_tsv": dict(zip(("n", "bytes"), tsv_sum("majority_114.tsv"))),
    "C_from_tsv": dict(zip(("n", "bytes"), tsv_sum("u1_126.tsv"))),
}
print(json.dumps(res, ensure_ascii=False, indent=2))
with open(os.path.join(HERE, "q4_law1_py.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)
