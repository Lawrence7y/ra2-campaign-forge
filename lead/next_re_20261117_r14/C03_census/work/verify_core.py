#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立复核三个核心数字（尽量用不同数据通路）。供审计对照。可复跑。"""
import os, sys, json, bisect
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C03_census")
WORK = os.path.join(CARD, "work")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib

# 核心数字 1：本片函数数 = coverage_delta.tsv 行数 = atlas 逻辑行 2585..3876
cd = os.path.join(CARD, "coverage_delta.tsv")
n_delta = sum(1 for ln in open(cd, encoding="utf-8") if ln.strip())
rows, hdr = audit_lib.load_func_atlas()
n_slice = len(rows[2584:3876])
print("CORE1 本片函数数: coverage_delta=%d  atlas[2584:3876]=%d  match=%s" %
      (n_delta, n_slice, n_delta == n_slice == 1292))

# 核心数字 2：high 置信数（从 trace 独立数 + 从 coverage_delta grade 交叉）
tr = json.load(open(os.path.join(WORK, "classification.json"), encoding="utf-8"))["trace"]
n_high_trace = sum(1 for t in tr if t["conf"] == "high")
grade_c = Counter(t["grade"] for t in tr)
src_c = Counter(t["source"] for t in tr)
print("CORE2 high 置信数: trace=%d  grade=%s  source=%s" % (n_high_trace, dict(grade_c), dict(src_c)))
# 交叉：从 classification_trace.tsv 直接数第 3 列 conf==high
trf = os.path.join(CARD, "EVIDENCE", "classification_trace.tsv")
n_high_file = 0
with open(trf, encoding="utf-8") as f:
    header = f.readline()
    ci = header.rstrip("\n").split("\t").index("conf")
    for ln in f:
        if ln.rstrip("\n").split("\t")[ci] == "high":
            n_high_file += 1
print("CORE2b high 从 trace 文件独立数: %d  match=%s" % (n_high_file, n_high_file == n_high_trace == 427))
# high 按信号来源分解
print("CORE2 high 来源分解:", dict(Counter(t["source"] for t in tr if t["conf"]=="high")))
print("CORE2 high 按子系统:", dict(Counter(t["sub"] for t in tr if t["conf"]=="high")))

# 核心数字 3：atlas 空洞入口数（独立用 sweep_targets.json + 重算 owner）
gaps = json.load(open(os.path.join(WORK, "gaps_raw.json"), encoding="utf-8"))
lo = int(gaps["lo"], 16); hi = int(gaps["hi"], 16)
starts = [va for va, _ in rows]
sizes  = {va: int(rec["size"]) for va, rec in rows}
def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None
sw = json.load(open(os.path.join(WORK, "sweep_targets.json"), encoding="utf-8"))
tset = set(int(k, 16) for k in list(sw["calls"]) + list(sw["jmps"]))
holes = sorted(x for x in tset if lo <= x < hi and owner(x) is None)
n_gap_file = sum(1 for ln in open(os.path.join(CARD, "atlas_gaps.tsv"), encoding="utf-8") if ln.strip()) - 1
print("CORE3 atlas 空洞入口数: recompute=%d  atlas_gaps.tsv=%d  match=%s  4824D4_in=%s" %
      (len(holes), n_gap_file, len(holes) == n_gap_file, 0x4824D4 in holes))

# PROGRESS 统计
print("\n== 子系统计数 / high / 占比 ==")
by = Counter(t["sub"] for t in tr)
H = sum(1 for t in tr if t["conf"]=="high")
for s in sorted(by):
    hi_n = sum(1 for t in tr if t["sub"] == s and t["conf"] == "high")
    print("%s\t%d\t%d\t%.1f%%" % (s, by[s], hi_n, 100.0*hi_n/H))
print("无法归类(source=none):", src_c["none"], " 其中真零证据:",
      sum(1 for t in tr if t["source"]=="none" and not (t["vt"] or t["strings"] or t["imp"] or t["vote"] or t["self_strong"] or t["self_ledger"] or t["module"])))
