#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成正式 atlas_gaps.tsv（可复跑）。
定义：本片地址范围 [lo,hi) 内，被全 .text skipdata=True 扫出的 call/jmp rel32 目标命中，
且用「函数区间包含」判据 owner(target)==None（不属于任何 atlas 函数区间）的入口。
含边界验证 boundary 与置信度分级。已知例 0x4824D4 必须出现。
"""
import os, json, bisect
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C02_census")
WORK  = os.path.join(CARD, "work")
import sys
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib

gaps = json.load(open(os.path.join(WORK, "gaps_raw.json"), encoding="utf-8"))["gaps"]
det  = {x["target"]: x for x in json.load(open(os.path.join(WORK, "gap_holes_detail.json"), encoding="utf-8"))}
H = [g for g in gaps if g["owner"] is None]
H.sort(key=lambda g: g["target"])

def conf(g):
    d = det.get(g["target"], {})
    if g["boundary"] is False: return "reject-inside-insn"
    if g["is_call_tgt"]: return "high(call)"
    if g["target"] == 0x4824D4: return "high(ledger-known)"
    if d.get("in_vt"): return "high(vtable)"
    if d.get("sites_in_fn", 0) >= 1: return "med(jmp-from-fn)"
    return "low(jmp-hole)"

with open(os.path.join(CARD, "atlas_gaps.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tkind\tconfidence\tn_sites\tboundary\tin_vt\tfirst_insn\tsites\n")
    for g in H:
        d = det.get(g["target"], {})
        sites = " ".join("%08X" % s for s in g["sites"][:6])
        f.write("%08X\t%s\t%s\t%d\t%s\t%d\t%s\t%s\n" % (
            g["target"], g["kind"], conf(g), g["n_sites"],
            "unknown" if g["boundary"] is None else str(g["boundary"]).lower(),
            1 if d.get("in_vt") else 0,
            (d.get("first", "")[:24] or "-"),
            sites))

from collections import Counter
print("atlas_gaps entries:", len(H))
print("confidence:", Counter(conf(g) for g in H))
print("0x4824D4 present:", any(g["target"] == 0x4824D4 for g in H))
