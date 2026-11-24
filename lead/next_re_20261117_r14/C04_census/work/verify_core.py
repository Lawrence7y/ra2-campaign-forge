#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C04 独立复核三个核心数字（尽量用不同数据通路）。供审计对照。可复跑。"""
import os, sys, json, bisect
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C04_census")
WORK = os.path.join(CARD, "work")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib

# 核心数字 1：本片函数数 = coverage_delta.tsv 行数 = atlas 逻辑行 3877..5168
cd = os.path.join(CARD, "coverage_delta.tsv")
n_delta = sum(1 for ln in open(cd, encoding="utf-8") if ln.strip())
rows, hdr = audit_lib.load_func_atlas()
n_slice = len(rows[3876:5168])
print("CORE1 本片函数数: coverage_delta=%d  atlas[3876:5168]=%d  match=%s" %
      (n_delta, n_slice, n_delta == n_slice == 1292))

# 核心数字 2：high 置信数（从 trace 独立数 + 从 coverage_delta grade 交叉）
tr = json.load(open(os.path.join(WORK, "classification.json"), encoding="utf-8"))["trace"]
n_high_trace = sum(1 for t in tr if t["conf"] == "high")
grade_c = Counter(t["grade"] for t in tr)
src_c = Counter(t["source"] for t in tr)
# 交叉：high = self_known(具名) + vtable-core；从 source 近似验证（vtable 中 core 部分需 classify 判据）
print("CORE2 high 置信数: trace=%d  grade=%s  source=%s" % (n_high_trace, dict(grade_c), dict(src_c)))
print("       high = self_known(%d) + vtable-core(%d)" % (
      src_c["self_known"], n_high_trace - src_c["self_known"]))

# 核心数字 3：atlas 空洞入口数（严格 rel32）—— 独立用 sweep_targets.json 重算 owner + 重扫 opcode
gaps = json.load(open(os.path.join(WORK, "gaps_raw.json"), encoding="utf-8"))
lo = int(gaps["lo"], 16); hi = int(gaps["hi"], 16)
starts = [va for va, _ in rows]
sizes  = {va: int(rec["size"]) for va, rec in rows}
def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None
# 独立通道：用 gap_detail.json 的 opcode 分类（E8 call / E9 jmp32）重数 rel32 owner=None
det = json.load(open(os.path.join(WORK, "gap_detail.json"), encoding="utf-8"))["detail"]
holes_rel32 = sorted(d["target"] for d in det if d["has_rel32"] and owner(d["target"]) is None)
n_gap_file = sum(1 for ln in open(os.path.join(CARD, "atlas_gaps.tsv"), encoding="utf-8") if ln.strip()) - 1
print("CORE3 atlas 空洞入口数(严格rel32): recompute=%d  atlas_gaps.tsv=%d  match=%s" %
      (len(holes_rel32), n_gap_file, len(holes_rel32) == n_gap_file))
print("       0x4824D4 in slice range:", lo <= 0x4824D4 < hi, "(expect False: C02 range)")
sjo = json.load(open(os.path.join(WORK, "gap_detail.json"), encoding="utf-8"))["short_jmp_only"]
print("       excluded SHORT-JMP-ONLY(EB rel8):", len(sjo), "→ 见 UNKNOWNS.md")
# 交叉：把 EB 也算进去会是 95（C01/C02 宽松口径）
all_holes = [d for d in det if owner(d["target"]) is None]
print("       loose口径(call/jmp含EB)会得:", len(all_holes), "(本卡不采用)")

# PROGRESS 统计
print("\n== 子系统计数 / high / 占比 ==")
by = Counter(t["sub"] for t in tr)
H = sum(1 for t in tr if t["conf"] == "high")
for s in sorted(by):
    hi_n = sum(1 for t in tr if t["sub"] == s and t["conf"] == "high")
    print("%s\t%d\t%d\t%.2f%%" % (s, by[s], hi_n, 100.0*hi_n/H if H else 0))
print("无法归类(source=none):", src_c["none"])
print("high 占比: %d/%d = %.2f%%" % (n_high_trace, len(tr), 100.0*n_high_trace/len(tr)))
