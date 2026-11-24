# -*- coding: utf-8 -*-
"""_verify_1c93_payload.py — 抽取 1c93b364 payload 的 DIR/DOC/铁律9/调查任务要求。只读。"""
import json, re
p = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs\dwfrun-1c93b364-e57c-405d-a271-66cd59e4b850.mjs"
t = open(p, encoding="utf-8").read()
L = t.split("\n")[8]
pat = re.compile(r'"((?:[^"\\]|\\.)*)"')
for mm in pat.finditer(L):
    s = mm.group(1)
    if len(s) > 500:
        d = json.loads('"' + s + '"')
        for i, l in enumerate(d.split("\n"), 1):
            if any(k in l for k in ("const DIR", "const DOC", "铁律 9", "铁律9", "被核对象 SHA256", "前缀 _dB_", "调查员")):
                print(f"P{i:03d}| {l[:300]}")
        break
print("---- check: does payload contain the two tails or require script-hash-tail reporting? ----")
for k in ("26f3fb61829756dfeecf", "b6f95763794", "脚本 hash 尾", "hash 尾", "脚本指纹"):
    print(repr(k), "count =", t.count(k))
