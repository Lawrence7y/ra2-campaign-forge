#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C07 证据分析：列出本片 vt 类族、具名、源文件模块、导入、字符串线索，供 classify.py 定规则。可复跑。"""
import os, json, re
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C07_census")
WORK = os.path.join(CARD, "work")
D = json.load(open(os.path.join(WORK, "evidence.json"), encoding="utf-8"))
F = D["funcs"]

print("== top vt classes (count of funcs whose best vt class) ==")
vc = Counter()
for f in F:
    for cls, slot, vt in f["vt"]:
        vc[cls] += 1
for cls, n in vc.most_common(80):
    print("  %4d  %s" % (n, cls))

print("\n== self_known names (count %d) ==" % sum(1 for f in F if f["self_known"]))
sc = Counter()
for f in F:
    for nm in f["self_known"]:
        sc[nm] += 1
for nm, n in sc.most_common(120):
    print("  %3d  %s" % (n, nm))

print("\n== source modules ==")
mc = Counter(f["module"] for f in F if f["module"])
for m, n in mc.most_common():
    print("  %4d  %s" % (n, m))

print("\n== imports ==")
ic = Counter(f["first_import"] for f in F if f["first_import"])
for m, n in ic.most_common(60):
    print("  %4d  %s" % (n, m))

print("\n== strings sample (functions with *.CPP / keyword) ==")
kw = re.compile(r'\.CPP|\.cpp|\.Cpp|\.MIX|\.INI|EVA_|TXT_|Cmnd:|GUI:|SHP|VXL|WOL|MP[A-Z]', re.I)
n = 0
for f in F:
    if f["strings"] and kw.search(f["strings"]):
        print("  %08X  %s" % (f["entry"], f["strings"][:100]))
        n += 1
        if n >= 60: break
