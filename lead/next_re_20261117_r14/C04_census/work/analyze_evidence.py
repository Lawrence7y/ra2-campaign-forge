#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""勘察 evidence.json：完整类名分布、已知名样例、字符串关键词分布，供 build CLASS_RULES。"""
import os, json, re
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C04_census")
WORK = os.path.join(CARD, "work")
D = json.load(open(os.path.join(WORK, "evidence.json"), encoding="utf-8"))
F = D["funcs"]
print("n funcs:", len(F), "range", D["lo"], D["hi"])

# 完整类名分布（vtable）
cc = Counter()
for f in F:
    for cls, slot, vt in f["vt"]:
        cc[cls] += 1
print("\n== ALL vtable classes (%d distinct) ==" % len(cc))
for cls, n in cc.most_common():
    print("  %4d  %s" % (n, cls))

# 已知名样例
print("\n== self_known samples (%d funcs) ==" % sum(1 for f in F if f["self_known"]))
kn = Counter()
for f in F:
    for nm in f["self_known"]:
        kn[nm] += 1
for nm, n in kn.most_common(80):
    print("  %3d  %s" % (n, nm))

# 字符串里出现的 .CPP / 关键 token 频率
tok = Counter()
for f in F:
    for t in f["strings"].split("|"):
        t = t.strip()
        if t: tok[t] += 1
print("\n== top string tokens (%d distinct) ==" % len(tok))
for t, n in tok.most_common(80):
    print("  %3d  %s" % (n, t[:90]))
