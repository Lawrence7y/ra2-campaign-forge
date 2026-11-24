# -*- coding: utf-8 -*-
"""_bt_extract_1c93.py v2 — 只读抽取 1c93b364 payload 中调查任务/维度清单片段。"""
import re
P = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs\dwfrun-1c93b364-e57c-405d-a271-66cd59e4b850.mjs"
with open(P, "r", encoding="utf-8") as f:
    t = f.read()
for pat in [r'锚补算', r'_dB', r'd\.key', r'调查', r'DIMS', r'dimensions']:
    idxs = [m.start() for m in re.finditer(pat, t)]
    print(f"pat={pat!r} hits={len(idxs)} offs={idxs[:12]}")
# 打印『锚补算』前后各 1200 字符（解码 \n 仅用于阅读，标注原文含转义）
i = t.find("锚补算")
if i != -1:
    seg = t[max(0, i-1200):i+1200]
    print("=" * 30)
    print(seg)
