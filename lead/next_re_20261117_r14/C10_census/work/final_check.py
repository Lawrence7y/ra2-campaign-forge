#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C10 交付自检：文件存在、列数、核心数字复算、写域卫生。"""
import os, json
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead", "next_re_20261117_r14", "C10_census")

def p(*a): return os.path.join(CARD, *a)

# 文件存在
need = ["PROGRESS.md", "coverage_delta.tsv", "atlas_gaps.tsv", "UNKNOWNS.md", "DISAGREE.md",
        "EVIDENCE/slice_raw.tsv", "EVIDENCE/vtmap_hits.tsv", "EVIDENCE/known_hits.tsv",
        "EVIDENCE/callgraph.tsv", "EVIDENCE/classification_trace.tsv", "EVIDENCE/gap_channels.tsv",
        "EVIDENCE/gaps_raw.tsv", "EVIDENCE/entry_criteria.tsv", "EVIDENCE/vt_direct_entries.tsv",
        "work/verify_core.py", "work/collect.py", "work/classify.py", "work/rtti_independent.py",
        "work/sweep_independent.py", "work/gap_full.py", "work/entry_criteria.py", "work/vt_direct.py"]
missing = [f for f in need if not os.path.isfile(p(*f.split("/")))]
print("MISSING:", missing if missing else "none")

# coverage_delta 列数
bad = 0
for ln in open(p("coverage_delta.tsv"), encoding="utf-8"):
    if ln.strip() and len(ln.rstrip("\n").split("\t")) != 6: bad += 1
print("coverage_delta rows=%d malformed=%d" % (
    sum(1 for ln in open(p("coverage_delta.tsv"), encoding="utf-8") if ln.strip()), bad))

# atlas_gaps 列数 + 通道计数
gc = Counter(); nrow = 0; badg = 0
addrs = set()
for ln in open(p("atlas_gaps.tsv"), encoding="utf-8"):
    if not ln.strip(): continue
    nrow += 1
    cols = ln.rstrip("\n").split("\t")
    if len(cols) != 5: badg += 1; continue
    gc[cols[1]] += 1; addrs.add(cols[0])
print("atlas_gaps rows=%d malformed=%d chan=%s distinct_addr=%d" % (nrow, badg, dict(gc), len(addrs)))

# classification high
th = open(p("EVIDENCE", "classification_trace.tsv"), encoding="utf-8").read().splitlines()
hdr = th[0].split("\t"); ci = hdr.index("conf")
high = sum(1 for l in th[1:] if l.split("\t")[ci] == "high")
print("trace high=%d" % high)

# 核心 json
gap = json.load(open(p("work", "gap_stats.json"), encoding="utf-8"))
vd = json.load(open(p("work", "vt_direct.json"), encoding="utf-8"))
ec = json.load(open(p("work", "entry_criteria.json"), encoding="utf-8"))
print("gap_stats: rows=%d chan=%s distinct=%d r14_strict=%d" % (
    gap["rows"], gap["chan_rows"], gap["total_distinct_addresses"], gap["r14_strict_suspect"]))
print("entry_criteria pass=%d" % ec["pass_count"])
print("vt_direct: A=%d B=%d union=%d" % (vd["n_true_entry_A"], vd["n_true_entry_B"], vd["union_true"]))

# PROGRESS 行数
pl = open(p("PROGRESS.md"), encoding="utf-8").read().splitlines()
print("PROGRESS lines=%d (<=60: %s)" % (len(pl), len(pl) <= 60))

# 关键数字一致性断言
assert sum(1 for ln in open(p("coverage_delta.tsv"), encoding="utf-8") if ln.strip()) == 1288
assert high == 254
assert gc == Counter({"jmp8":169, "call32":36, "jmp32":71})
assert nrow == 276 and len(addrs) == 264
assert ec["pass_count"] == 12
assert vd["union_true"] == 6
assert len(pl) <= 60
print("ALL ASSERTIONS PASS")
