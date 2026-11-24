# -*- coding: utf-8 -*-
"""_nn_corpus_check.py — 语料漂移核对：当前 631 基线 vs 现盘，列出新增 .md。"""
import os
ROOT = r"D:/Project/ra2-campaign-forge/lead"
cur = []
for dp, dn, fn in os.walk(ROOT):
    rel = os.path.relpath(dp, ROOT).replace("\\", "/")
    d = 0 if rel == "." else rel.count("/") + 1
    if d > 2:
        dn[:] = []; continue
    for f in sorted(fn):
        if f.endswith(".md"):
            cur.append(os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/"))
print("current .md depth<=2 =", len(cur))
own = [r for r in cur if r.startswith("needle_norm_20261109/")]
print("own write-domain md =", len(own), own)
print("excluding own =", len(cur) - len(own))
# 六变体在「排除本写域」后的现盘计数，确认 631 基线结论是否仍成立
V = ['只能判「不可复现」','只能判『不可复现』','只能判“不可复现”',
     '只能判不可复现','只能判(不可复现)','只能判 不可复现']
files = {}
for r in cur:
    if r.startswith("needle_norm_20261109/"):
        continue
    files[r] = open(os.path.join(ROOT, r), encoding="utf-8", errors="replace").read().splitlines()
print("")
print("=== 排除本写域后：六变体现盘计数 ===")
U = set()
for nd in V:
    hits = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if nd in L}
    U |= hits
    print("  %-22r files=%2d lines=%2d" % (nd, len({r for r,_ in hits}), len(hits)))
print("  union files=%d lines=%d" % (len({r for r,_ in U}), len(U)))
