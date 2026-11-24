#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 C05 evidence：类分布、具名函数、模块、字符串、导入，供分类规则设计。可复跑。"""
import os, json
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
WORK = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C05_census\\work")
D = json.load(open(os.path.join(WORK, "evidence.json"), encoding="utf-8"))
F = D["funcs"]

# vtable 类分布
cls_c = Counter()
for f in F:
    for cls, slot, vt in f["vt"]:
        cls_c[cls] += 1
print("== vtable classes (top 80) ==")
for c, n in cls_c.most_common(80):
    print("%5d  %s" % (n, c))

# self_known 名字
print("\n== self_known names (all %d) ==" % sum(1 for f in F if f["self_known"]))
for f in F:
    if f["self_known"]:
        print("%08X  %s" % (f["entry"], " | ".join(f["self_known"])))

# module 分布
mod_c = Counter(f["module"] for f in F if f["module"])
print("\n== modules ==")
for m, n in mod_c.most_common():
    print("%5d  %s" % (n, m))

# 字符串关键词（ Extract .CPP / notable）
print("\n== funcs with strings (top sample) ==")
ns = [f for f in F if f["n_strings"] > 0]
print("n funcs with strings:", len(ns))
str_c = Counter()
for f in F:
    str_c[f["strings"]] += 1
for s, n in str_c.most_common(60):
    if s.strip(): print("%5d  %s" % (n, s[:160]))

# 导入 API
imp_c = Counter(f["first_import"] for f in F if f["first_import"])
print("\n== imports ==")
for i, n in imp_c.most_common():
    print("%5d  %s" % (n, i))
