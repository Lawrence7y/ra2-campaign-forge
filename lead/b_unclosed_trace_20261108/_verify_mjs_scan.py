# -*- coding: utf-8 -*-
"""_verify_mjs_scan.py — 独立复核：全量遍历 .zcode/workflow-runs/dwfrun-*.mjs
检索两个尾串，逐处给出偏移/行号/上下文，并核验 utf-8 解码状态。
只读；不复用接线员的 _bt_scan_mjs.py 实现。
运行: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b_unclosed_trace_20261108/_verify_mjs_scan.py
"""
import hashlib
import json
import os
import sys

RUNS = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"
TAILS = ["26f3fb61829756dfeecf", "b6f95763794"]

names = sorted(n for n in os.listdir(RUNS)
               if n.startswith("dwfrun-") and n.endswith(".mjs"))
print(f"total_dwfrun_mjs={len(names)}")

# also list any other .mjs in the dir (to check the "10 dwfeval" claim)
others = sorted(n for n in os.listdir(RUNS)
                if n.endswith(".mjs") and not n.startswith("dwfrun-"))
print(f"other_mjs={len(others)} names={others}")

total_hits = {t: 0 for t in TAILS}
hit_files = {}

for n in names:
    p = os.path.join(RUNS, n)
    with open(p, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode("utf-8")
        dec = "strict_ok"
    except UnicodeDecodeError as e:
        text = raw.decode("utf-8", errors="replace")
        dec = "REPLACE:" + str(e)
    found = []
    for t in TAILS:
        offs = []
        i = text.find(t)
        while i != -1:
            offs.append(i)
            i = text.find(t, i + 1)
        total_hits[t] += len(offs)
        for i in offs:
            ln = text.count("\n", 0, i) + 1
            a, b = max(0, i - 160), min(len(text), i + len(t) + 160)
            ctx = text[a:b].replace("\n", "\\n").replace("\r", "\\r")
            found.append((t, i, ln, ctx))
    if found:
        hit_files[n] = (len(raw), hashlib.sha256(raw).hexdigest(), dec, found)
        print(f"\n== HITFILE {n} bytes={len(raw)} sha256={hashlib.sha256(raw).hexdigest()} decode={dec}")
        for t, i, ln, ctx in found:
            print(f"  {t} off={i} line={ln}")
            print(f"    CTX[{a if False else ''}]: {ctx}")

print("\n--- SUMMARY ---")
for t in TAILS:
    print(f"tail={t} total_occurrences={total_hits[t]}")
print(f"hit_files={len(hit_files)}")
for n in hit_files:
    print(f"HITFILE\t{n}")
# per-file counts
print("--- per-file per-tail counts ---")
for n, (_, _, _, found) in hit_files.items():
    for t in TAILS:
        c = sum(1 for x in found if x[0] == t)
        if c:
            print(f"{n}\t{t}\tcount={c}")

# cross-check: scan other *.mjs too (literal bytes)
print("--- other *.mjs literal scan ---")
for n in others:
    p = os.path.join(RUNS, n)
    with open(p, "rb") as f:
        raw = f.read()
    c = [raw.count(t.encode()) for t in TAILS]
    if any(c):
        print(f"OTHER_HIT\t{n}\t{c}")
print("other_scan_done")
sys.stdout.flush()
