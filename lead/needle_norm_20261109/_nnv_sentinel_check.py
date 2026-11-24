# -*- coding: utf-8 -*-
"""检查 L1 哨兵码位 \x01\x02\x03 在语料中是否出现（撰写人 REPORT:425 标「未验」）。"""
import os
ROOT = r"D:/Project/ra2-campaign-forge/lead"
tot = 0
hit = []
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
        found = [ord(c) for c in (b"\x01", b"\x02", b"\x03") if c in b]
        if found:
            hit.append((r, found))
print("scanned (excl needle_norm_20261109/ write domain) =", tot)
print("files containing SENTINEL \\x01 / \\x02 / \\x03 =", len(hit))
for x in hit[:30]:
    print("   ", x)
