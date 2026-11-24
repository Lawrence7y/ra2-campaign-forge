#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成正式 atlas_gaps.tsv（可复跑）。
定义（严格 rel32）：本片地址范围 [lo,hi) 内，被全 .text skipdata=True 扫出的
  call rel32(E8) 或 jmp rel32(E9) 目标，且 owner(target)==None（区间包含判据）的入口。
⚠️ 卡纪律：仅由 EB(rel8) 短跳命中的洞入口不得硬算成 rel32 命中 → 排除，
   单列于 UNKNOWNS.md（C01 的 0x4824D4 EB 0A 场景同类）。
输入 work/gap_detail.json；输出 atlas_gaps.tsv。
"""
import os, json
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C04_census")
WORK  = os.path.join(CARD, "work")

D = json.load(open(os.path.join(WORK, "gap_detail.json"), encoding="utf-8"))
detail = D["detail"]
rel32 = [d for d in detail if d["has_rel32"]]   # E8 call 或 E9 jmp
rel32.sort(key=lambda x: x["target"])

def conf(d):
    if d["boundary"] is False: return "reject-inside-insn"
    if d["has_call"] and d["has_jmp32"]: return "high(call+jmp32)"
    if d["has_call"]: return "high(call-rel32)"
    if d["has_jmp32"]: return "high(jmp32-rel32)"
    return "low"

with open(os.path.join(CARD, "atlas_gaps.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tkind\tconfidence\tn_sites\tboundary\tin_vt\tfirst_insn\tsites\n")
    for d in rel32:
        kind = "call" if d["has_call"] and not d["has_jmp32"] else ("call+jmp" if d["has_call"] and d["has_jmp32"] else "jmp32")
        sites = " ".join("%08X" % x for x in (d["call"] + d["jmp32"])[:6])
        f.write("%08X\t%s\t%s\t%d\t%s\t%d\t%s\t%s\n" % (
            d["target"], kind, conf(d), d["n_sites"],
            "unknown" if d["boundary"] is None else str(d["boundary"]).lower(),
            int(d["in_vt"]), (d["first"][:40] or "-"), sites))

from collections import Counter
print("atlas_gaps entries (rel32):", len(rel32))
print("conf:", dict(Counter(conf(d) for d in rel32)))
print("call:", sum(1 for d in rel32 if d["has_call"]), " jmp32:", sum(1 for d in rel32 if d["has_jmp32"]))
print("0x4824D4 present:", any(d["target"] == 0x4824D4 for d in rel32), "(expect False: in C02 range)")
print("excluded SHORT-JMP-ONLY:", len(D["short_jmp_only"]))
