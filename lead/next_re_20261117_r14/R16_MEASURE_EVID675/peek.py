#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""peek.py — 只看产物，辅助人工判读（不写任何权威文件）。"""
import collections
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "buckets675.tsv"
rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8")]
hdr, rows = rows[0], rows[1:]
print(f"[{path}] n={len(rows)}  cols={hdr}")
print("bucket counts:", dict(collections.Counter(r[3] for r in rows)))

mode = sys.argv[2] if len(sys.argv) > 2 else "strong"
if mode == "strong":
    print("\n--- STRONG ---")
    for r in rows:
        if r[3] == "CTX_STRONG":
            print(f"{r[0]} {r[1]:5s} files={r[4]:>2}  {r[5][:80]}")
elif mode == "medium-dist":
    print("\n--- MEDIUM 行的提供文件分布 ---")
    c = collections.Counter(r[5].split(";")[0].strip() for r in rows
                            if r[3] == "CTX_MEDIUM")
    for f, n in c.most_common(25):
        print(f"{n:5d}  {f}")
    print(f"共 {len(c)} 个不同文件提供 MEDIUM")
elif mode == "none":
    print("\n--- NONE / WEAK ---")
    for r in rows:
        if r[3] in ("CTX_NONE", "CTX_WEAK"):
            print(f"{r[3]:10s} {r[0]} {r[1]:5s} {r[6][:100]}")
elif mode == "by-sub":
    print("\n--- 按 subsystem × bucket ---")
    c = collections.Counter((r[1], r[3]) for r in rows)
    for sub in sorted({r[1] for r in rows}):
        tot = sum(v for (s, _b), v in c.items() if s == sub)
        print(f"{sub:5s} n={tot:4d}  " + "  ".join(
            f"{b.replace('CTX_','')}={c.get((sub,b),0)}" for b in
            ("CTX_STRONG", "CTX_MEDIUM", "CTX_WEAK", "CTX_NONE")))
