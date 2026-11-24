# -*- coding: utf-8 -*-
"""检查「合成」引号变体在真实语料是否出现；判定过度归一风险的现实性。"""
import os
ROOT = r"D:/Project/ra2-campaign-forge/lead"
PATS = [
    "只能判‘不可复现’",     # 单弯引号，L1 归入 canon，但 PAIRS 不认
    "只能判『不可复现」",   # 混合错配，L1 归入 canon，但 spans 为空
    "只能判』不可复现『",   # 反配，L1 不归入 canon
    "只能判“不可复现”",     # curly_double，L1 归入 canon，PAIRS 认
    "只能判`不可复现`",     # 反引号，PAIRS 认但 L1 不归入 canon
]
found = {p: [] for p in PATS}
tot = 0
for dp, dn, fn in os.walk(ROOT):
    rel = os.path.relpath(dp, ROOT).replace("\\", "/")
    d = 0 if rel == "." else rel.count("/") + 1
    if d > 2:
        dn[:] = []
        continue
    for f in sorted(fn):
        if not f.lower().endswith(".md"):
            continue
        p = os.path.join(dp, f)
        r = os.path.relpath(p, ROOT).replace("\\", "/")
        if r.startswith("needle_norm_20261109/"):
            continue
        b = open(p, "rb").read()
        tot += 1
        if b"\x00" in b:
            continue
        for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
            for q in PATS:
                if q in L:
                    found[q].append((r, i))
print("scanned =", tot)
for q, v in found.items():
    print("  %-22r count=%d %s" % (q, len(v), v[:3]))
