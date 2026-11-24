# -*- coding: utf-8 -*-
"""_bt_scan_mjs.py — 只读遍历 .zcode/workflow-runs/dwfrun-*.mjs，检索两个尾串。
运行: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b_unclosed_trace_20261108/_bt_scan_mjs.py
输出: 每命中一处打印 HIT 摘要行 + CTX 上下文行（\\n/\\r 转义显示，不改原文）。
"""
import hashlib
import os
import sys

RUNS = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"
TAILS = ["26f3fb61829756dfeecf", "b6f95763794"]

files = sorted(f for f in os.listdir(RUNS) if f.startswith("dwfrun-") and f.endswith(".mjs"))
print(f"total_mjs={len(files)}")
sys.stdout.flush()

hit_files = []
for fn in files:
    p = os.path.join(RUNS, fn)
    with open(p, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode("utf-8")
        dec = "strict_ok"
    except UnicodeDecodeError as e:
        text = raw.decode("utf-8", errors="replace")
        dec = f"replace:{e}"
    any_hit = False
    for tail in TAILS:
        idxs = []
        i = text.find(tail)
        while i != -1:
            idxs.append(i)
            i = text.find(tail, i + 1)
        if not idxs:
            continue
        if not any_hit:
            hit_files.append(fn)
            any_hit = True
        lines = [text.count("\n", 0, i) + 1 for i in idxs]
        print(
            f"HIT\t{fn}\t{tail}\tcount={len(idxs)}"
            f"\tlines={','.join(str(x) for x in lines)}"
            f"\tbytes={len(raw)}\tsha256={hashlib.sha256(raw).hexdigest()}\tdecode={dec}"
        )
        for i, ln in zip(idxs, lines):
            a = max(0, i - 220)
            b = min(len(text), i + len(tail) + 220)
            ctx = text[a:b].replace("\r", "\\r").replace("\n", "\\n")
            print(f"CTX\t{fn}\t{tail}\tline={ln}\toff={i}\t{ctx}")
    sys.stdout.flush()

print(f"hit_files={len(hit_files)}")
for fn in hit_files:
    print(f"HITFILE\t{fn}")
sys.stdout.flush()
