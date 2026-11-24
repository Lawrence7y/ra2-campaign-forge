#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q4_spot.py — R44-T1 审计 Q1/Q3/Q4 补充取证（小范围定点，不重跑全树分类）

只读；只写本目录 q4_spot.json。
1) 候选 A：VA 阈值的两个绑定件（50/55.8%），验证「降阈会把 E2 横幅流出物放进来」
2) 候选 B：纯 P1b 冲突件 —— P1b 是否够判「对象抄本」（列出被它保住/排掉的最大件与首两行）
3) 候选 C：'EVIDENCE 声明 vs 名字/内容' 三向冲突 —— P3 把它们送 UNDECIDED 是否符合判据文本
4) 候选 D：E5 的那件 self-measurement 表（REPORT 说「必须排」，实留）—— 确定性缺陷定量
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AUD = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"
REC = os.path.join(LEAD, "next_re_20261117_r14", "R17_R78_T1_RECLASS")
import audit_sample as AS


def head_text(rel, n=8192):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as fh:
            return fh.read(n).decode("utf-8", "replace")
    except OSError:
        return None


def first_lines(rel, k=2):
    t = head_text(rel, 4096)
    if t is None:
        return None
    return [x.rstrip()[:150] for x in t.split("\n")[:k]]


out = {}

# ---- 1) 阈值绑定件
out["va_threshold_bound"] = []
for rel in ["next_re_20261117_r14/S02-K2/_audit/out/D_initterm_console.txt",
            "next_re_20261117_r14/S11-K2/work/fresh_closure_run.log"]:
    out["va_threshold_bound"].append(dict(rel=rel, rejudge=AS.rejudge(rel)[:3],
                                          head=first_lines(rel, 2)))

# ---- 2) 纯 P1b 冲突件（P1a 不命中，只靠 P1b 才进 C′）
q = json.load(open(os.path.join(AUD, "q1_q3_q4.json"), encoding="utf-8"))
rows = q["q4"]["rows"]
pure_p1b = [r for r in rows if "P1b" in r["keep"] and "P1a" not in r["keep"]]
pure_p1b.sort(key=lambda r: -r["bytes"])
pick = pure_p1b[:1] + [r for r in pure_p1b if "_hygiene" in r["rel"]][:1] + \
       [r for r in pure_p1b if "P0_CLOSE" in r["rel"] or "S09-K1" in r["rel"]][:1]
out["pure_p1b_conflicts"] = dict(
    n=len(pure_p1b), bytes=sum(r["bytes"] for r in pure_p1b),
    picked=[dict(rel=r["rel"], bytes=r["bytes"], keep=r["keep"], excl=r["excl"],
                 j = AS.rejudge(r["rel"])[1], head=first_lines(r["rel"], 2)) for r in pick])

# ---- 3) 三向冲突：名字说流出物 / 内容说对象 / 路径说证据
e1_va = [r for r in rows if r["ev"] and "E1" in r["excl"].split(",")]
e1_va.sort(key=lambda r: -r["bytes"])
out["three_way"] = dict(
    n=len(e1_va), bytes=sum(r["bytes"] for r in e1_va),
    picked=[dict(rel=r["rel"], bytes=r["bytes"], keep=r["keep"], va_ratio=r["va_ratio"],
                 j=AS.rejudge(r["rel"])[:2], head=first_lines(r["rel"], 2))
            for r in e1_va[:3]])

# ---- 4) E5 的 files_scale_today.tsv（自测量表）
rel = "next_re_20261117_r14/R17_R70_T1_REPRO/files_scale_today.tsv"
t = head_text(rel, 4096)
nl = t.count("\n") if t else 0
out["e5_selfmeasure"] = dict(
    rel=rel, bytes=os.path.getsize(os.path.join(LEAD, rel.replace("/", os.sep))),
    mine=AS.rejudge(rel)[:2], head=first_lines(rel, 3), head_lines=nl)

json.dump(out, open(os.path.join(AUD, "q4_spot.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1)[:6000])
