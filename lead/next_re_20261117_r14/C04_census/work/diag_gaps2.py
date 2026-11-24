#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断 69 个 short-jmp-only 洞目标的来源：地址分布、引用站点、首指令、是否跳表case标签。"""
import os, json, bisect
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C04_census")
WORK  = os.path.join(CARD, "work")
sys_path = os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit")
import sys
sys.path.insert(0, sys_path)
import audit_lib

D = json.load(open(os.path.join(WORK, "gap_detail.json"), encoding="utf-8"))
detail = D["detail"]
sjo = [d for d in detail if d["conf"].startswith("SHORT")]
rel32 = [d for d in detail if d["has_rel32"]]

# 地址分布（每 0x1000）
print("== short-jmp-only 地址分布 (每 0x1000) ==")
c = Counter(d["target"] >> 12 for d in sjo)
for k in sorted(c):
    print("  %05X000  %d" % (k, c[k]))

print("\n== rel32 命中 26 个 (target conf first sites) ==")
for d in sorted(rel32, key=lambda x: x["target"]):
    sites = ("C:"+" ".join("%08X"%x for x in d["call"][:3]) +
             " J32:"+" ".join("%08X"%x for x in d["jmp32"][:3]))
    print("  %08X %-16s vt=%d sites_in_fn=%d  %s  | %s" % (
        d["target"], d["conf"], d["in_vt"], d["sites_in_fn"], d["first"][:40], sites))

print("\n== short-jmp-only 样例 (前 30) ==")
for d in sjo[:30]:
    print("  %08X  op=%s  jmp8sites=%s  first=%s" % (
        d["target"], ",".join(d["opcodes"]),
        " ".join("%08X"%x for x in d["jmp8"][:3]), d["first"][:44]))

# 引用站点来源：是否都在洞内（owner=None）
rows, hdr = audit_lib.load_func_atlas()
starts = [va for va,_ in rows]; sizes = {va:int(rec["size"]) for va,rec in rows}
def owner(x):
    i = bisect.bisect_right(starts,x)-1
    return starts[i] if i>=0 and starts[i]<=x<starts[i]+sizes[starts[i]] else None
print("\n== short-jmp 引用站点归属统计 ==")
tot_sites=0; in_fn=0; in_hole=0
for d in sjo:
    for s in d["jmp8"]:
        tot_sites+=1
        if owner(s) is not None: in_fn+=1
        else: in_hole+=1
print("  total jmp8 sites(first8 kept):",tot_sites," in_fn:",in_fn," in_hole:",in_hole)
