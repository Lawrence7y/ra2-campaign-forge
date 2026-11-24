#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C08 证据分析：列出本片 vtable 类族、已知名、字符串关键词、模块、导入，供分类规则设计。"""
import os, json, re
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
WORK = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C08_census\\work")
D = json.load(open(os.path.join(WORK, "evidence.json"), encoding="utf-8"))
F = D["funcs"]

# vtable 类族统计（按函数去重，取每个函数首个类名）
cls_agg = Counter()
cls_examples = defaultdict(list)
for f in F:
    seen = set()
    for cls, slot, vt in f["vt"]:
        base = cls
        # 归一：去模板参数，取主名
        m = re.match(r'T_?(\w+?)_', base) or re.match(r'(\w+?)@@', base)
        key = base
        if key not in seen:
            cls_agg[key] += 1
            seen.add(key)
            if len(cls_examples[key]) < 2:
                cls_examples[key].append((f["entry"], slot))

print("=== vtable 类族（函数数，top 40）===")
for k, n in cls_agg.most_common(40):
    print("%4d  %s" % (n, k))

# 已知名（self）
print("\n=== self_known 具名（全部）===")
kn = Counter()
for f in F:
    for nm in f["self_known"]:
        kn[nm] += 1
for k, n in kn.most_common(80):
    print("%3d  %s" % (n, k))

# 字符串关键词
print("\n=== strings（top 50，按 .CPP / 特征）===")
st = Counter()
for f in F:
    s = f["strings"]
    if not s: continue
    for tok in re.findall(r'[A-Za-z_][\w]*\.(?:CPP|cpp)|[A-Z][A-Z0-9_]{2,}', s):
        st[tok] += 1
for k, n in st.most_common(50):
    print("%3d  %s" % (n, k))

# first_import
print("\n=== first_import 分布 ===")
im = Counter(f["first_import"] for f in F if f["first_import"])
for k, n in im.most_common(40):
    print("%3d  %s" % (n, k))

# module
print("\n=== module 分布 ===")
mo = Counter(f["module"] for f in F if f["module"])
print(dict(mo))

# source
print("\n=== source_files 分布（本片命中）===")
so = Counter(f["source"] for f in F if f.get("source"))
for k,n in so.most_common(40):
    print("%3d  %s" % (n,k))
