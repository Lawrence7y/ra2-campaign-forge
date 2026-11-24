# -*- coding: utf-8 -*-
"""_tpv_agg.py — 从 stdin 读 rg -l 文件列表，按仓库内前两级目录聚合计数。"""
import sys, collections
c = collections.Counter()
PFX = "D:/Project/ra2-campaign-forge/"
for ln in sys.stdin:
    p = ln.strip()
    if p.upper().startswith("D:\\PROJECT\\RA2-CAMPAIGN-FORGE\\"):
        p = "lead-ish/" + p.split("\\", 1)[1]
    elif p.startswith(PFX):
        p = p[len(PFX):]
    p = p.replace("\\", "/")
    if p.startswith("D:/"):
        p = p  # 越出仓库根的绝对路径原样保留
    c["/".join(p.split("/")[:2]) if "/" in p else p] += 1
for k, v in sorted(c.items()):
    print("%4d  %s" % (v, k))
print("TOTAL files:", sum(c.values()))
