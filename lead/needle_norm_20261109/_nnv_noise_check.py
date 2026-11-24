# -*- coding: utf-8 -*-
"""_nnv_noise_check.py — 独立复核 W1-U 噪声的质与 不可复原 真实行数。"""
import os, re
ROOT = r"D:/Project/ra2-campaign-forge/lead"
files = {}
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
        if b"\x00" in b:
            continue
        files[r] = b.decode("utf-8", "replace").splitlines()

V = ['只能判「不可复现」','只能判『不可复现』','只能判“不可复现”',
     '只能判不可复现','只能判(不可复现)','只能判 不可复现']
U = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if any(v in L for v in V)}
W1 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if '不可复现' in L}
noise = sorted(W1-U); n = len(noise)
print("W1-U =", n)
cats = {'§604/空档主题':0,'其他主题(门禁/载体/标识符)':0,'含引号(引述候选)':0,
        '含否定/更新信号':0,'仍含锚词':0}
for r,i in noise:
    L = files[r][i-1]
    if re.search(r'§604|空档|空档差|缺口列|逐窗', L): cats['§604/空档主题'] += 1
    if re.search(r'不可复原|T55k|载体清单|门禁|APPROVE|守卫', L): cats['其他主题(门禁/载体/标识符)'] += 1
    if re.search(r'[「『“`]', L): cats['含引号(引述候选)'] += 1
    if re.search(r'不再成立|已撤回|不成立|被推翻|REFUTED|不可复现（REFUTED）|未验', L): cats['含否定/更新信号'] += 1
    if '只能判' in L: cats['仍含锚词'] += 1
for k,v in cats.items():
    print("  %-30s %3d (%.1f%%)" % (k,v,100.0*v/n))
print("=== 不可复原 真实行数 ===")
cnt = [(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if '不可复原' in L]
print("  lines =", len(cnt))
for x in cnt[:8]: print("   ", x)
