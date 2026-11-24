#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""explore.py — R43-T1 档 C' 重新裁决：只读探索器。
读 files_tier_A_snap2.tsv / files_tier_C.tsv，只写本目录。
不重跑全树测量；不 import mev675.py。
"""
from __future__ import annotations
import collections, fnmatch, os, re, sys

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
A = os.path.join(BASE, "files_tier_A_snap2.tsv")
C = os.path.join(BASE, "files_tier_C.tsv")

def load(p):
    rows = []
    with open(p, encoding="utf-8") as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows.append(dict(rel=f[0], ext=f[1], bytes=int(f[2]), mtime_ns=f[3], selfkind=f[4]))
    return hdr, rows

hA, RA = load(A)
hC, RC = load(C)
print("A rows", len(RA), "bytes", sum(r["bytes"] for r in RA))
print("C rows", len(RC), "bytes", sum(r["bytes"] for r in RC))
setA = {r["rel"] for r in RA}
setC = {r["rel"] for r in RC}
print("A-C set diff", len(setA - setC), "C-A", len(setC - setA))
mism = [(r["rel"], r["bytes"], r2["bytes"]) for r, r2 in
        ((x, next(y for y in RC if y["rel"] == x["rel"])) for x in RA if x["rel"] in setC) if r["bytes"] != r2["bytes"]]
print("byte mismatch on shared rows:", len(mism), mism[:5])

# ---- 目录族分布：顶层目录（first segment）----
def topseg(rel):
    p = rel.split("/")
    return p[0]

def fam(rel):
    """工具族：用目录/文件名把 A 全集分成若干个"候选族"，供逐族对账。"""
    base = rel.rsplit("/", 1)[-1]
    low = base.lower()
    dirs = rel.split("/")[:-1]
    d = "/".join(dirs)
    if base == "REPORT.md":
        return "F01_bare_REPORT.md"
    if low.endswith("_report.md"):
        return "F02_star_report.md"
    if any(seg == "_cards" for seg in dirs):
        return "F03__cards/*.md"
    if low in ("changes.md", "readme.md"):
        return "F04_CHANGES/README"
    if low.endswith("_out.txt"):
        return "F05_star_out.txt"
    if low.endswith("_out.json"):
        return "F06_star_out.json"
    if "stdout" in low or "stderr" in low:
        return "F07_stdout_stderr"
    if low.endswith("_probe.json") or low.endswith("_check.txt"):
        return "F08_probe_check"
    if any(seg.split("/")[0] == "EVIDENCE" or "EVIDENCE" in seg.split("/") for seg in dirs) or \
       any("EVIDENCE" == s for s in dirs):
        return "F09_EVIDENCE"
    if any(s == "R17_LEAD_BASELINE" for s in dirs):
        return "F10_R17_LEAD_BASELINE"
    if ".before" in low or "_before_" in low or "before_" in low or "_bak" in low or "backup" in low:
        return "F11_rollback_copy"
    if low.endswith(".tmp"):
        return "F12_tmp"
    return "F99_other"

cnt = collections.Counter(); byt = collections.Counter()
for r in RA:
    f = fam(r["rel"]); cnt[f] += 1; byt[f] += r["bytes"]
print("\n--- A 全集按候选族 ---")
for k in sorted(cnt):
    print(f"{k:26s} n={cnt[k]:6d} b={byt[k]:12d}")

# 交叉：族 × 是否在旧 C
print("\n--- 族 × 旧C状态（留/排） ---")
c2 = collections.Counter(); b2 = collections.Counter()
for r in RA:
    f = fam(r["rel"]); st = "inC" if r["rel"] in setC else "outC"
    c2[(f, st)] += 1; b2[(f, st)] += r["bytes"]
for f in sorted(cnt):
    print(f"{f:26s} inC={c2[(f,'inC')]:5d}/{b2[(f,'inC')]:11d}  outC={c2[(f,'outC')]:5d}/{b2[(f,'outC')]:11d}")
