#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C10 反坑(d)：self_known 类名 vs RTTI 实测 vtable 类名交叉校验。
反坑(d)两机制：①前向声明泄漏 ②按头文件文件名推断类名（C05 错 31）。
本卡 self_known 名来自 YRpp JMP_THIS / kb 具名地址，vtable 类名来自 RTTI 实测；
同一地址两者类名不一致则列出，人工判读。"""
import os
from collections import defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C10_census")
E = os.path.join(CARD, "EVIDENCE")

vt = defaultdict(set)
for ln in open(os.path.join(E, "vtmap_hits.tsv"), encoding="utf-8"):
    p = ln.rstrip("\n").split("\t")
    if len(p) == 4 and p[0] != "entry":
        vt[p[0]].add(p[1])

conflict = 0; agree = 0; novt = 0
for ln in open(os.path.join(E, "known_hits.tsv"), encoding="utf-8"):
    p = ln.rstrip("\n").split("\t")
    if len(p) != 3 or p[1] != "self": continue
    addr, names = p[0], p[2]
    cls_set = set()
    for nm in names.split(" | "):
        if "::" in nm:
            cls_set.add(nm.split("::")[0])
    vset = vt.get(addr, set())
    if not vset:
        novt += 1
        continue
    ok = False
    for c in cls_set:
        for v in vset:
            if c and (c in v or v in c or c.replace("_", "") in v.replace("_", "")):
                ok = True
    if ok: agree += 1
    else:
        conflict += 1
        print("CONFLICT %s self=%s rtti=%s" % (addr, sorted(cls_set), sorted(vset)))
print("self_known with RTTI agree=%d conflict=%d no-vtable=%d" % (agree, conflict, novt))
