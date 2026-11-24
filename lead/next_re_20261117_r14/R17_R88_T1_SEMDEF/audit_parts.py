#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_parts.py — 审计「甲」的三个减项：SELF 16 件与 disk_not_A 200 件的实际内容归属。

不做任何改动，只打印事实（路径/字节/所属输入的 label 与 why）。
"""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = r"D:\Project\ra2-campaign-forge\lead"
R14 = R + r"\next_re_20261117_r14"


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


A = {r["rel"] for r in rows(R14 + r"\R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv")}
CP = {r["rel"]: r["why"] for r in rows(R14 + r"\R17_R78_T1_RECLASS\files_tier_Cprime.tsv")}
VD = {r["rel"]: r for r in rows(R14 + r"\R17_R81_T2_EVID\_verdicts.tsv")}
EX = {r["rel"]: r for r in rows(R14 + r"\R17_R78_T1_RECLASS\files_excluded_prime.tsv")}

SELF = set()
for f in ("files_tier_A_snap2.tsv", "files_tier_A.tsv", "files_tier_A_snap1.tsv",
          "files_tier_B.tsv", "files_tier_C.tsv", "files_tier_Cprime.tsv",
          "files_excluded_prime.tsv", "selfartifacts_detail.tsv", "summary_snap2.json",
          "summary.json", "q1_tie_detail.tsv", "tie_dump.txt", "_verdicts.tsv",
          "_content_metrics.tsv", "_undead_evid.tsv", "scale_vs_baseline.json",
          "decide_semdef.py", "posctrl_py.py"):
    for d in ("R17_R72_T1_CLEANSCALE", "R17_R78_T1_RECLASS", "R17_R84_T2_EVID2",
              "R17_R81_T2_EVID", "R17_R70_T1_REPRO", "R17_R88_T1_SEMDEF"):
        SELF.add("next_re_20261117_r14/%s/%s" % (d, f))

SIX = (".md", ".txt", ".json", ".tsv", ".log", ".csv")
disk = {}
for root, ds, fs in os.walk(R):
    for fn in fs:
        if os.path.splitext(fn)[1].lower() in SIX:
            p = os.path.join(root, fn)
            disk[os.path.relpath(p, R).replace(os.sep, "/")] = os.path.getsize(p)

print("=== SELF 命中（实盘） ===")
for r in sorted(SELF):
    if r in disk:
        tag = "A+C′" if r in CP else ("A+EXCL" if r in EX else ("A无裁定" if r in A else "不在A"))
        print(f"{disk[r]:>12,}\t{tag}\t{r}")

print("=== disk_not_A 逐件 ===")
tot = 0
for r in sorted(disk):
    if r not in A:
        e = EX.get(r)
        tag = "EXCL:" + e["why"] if e else "不在任何清单"
        print(f"{disk[r]:>12,}\t{tag}\t{r}")
        tot += disk[r]
print("TOTAL", tot)
