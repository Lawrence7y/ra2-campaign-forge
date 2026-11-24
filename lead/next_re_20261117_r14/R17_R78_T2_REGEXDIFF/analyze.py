#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R43-T2-REGEXDIFF 复算脚本（只读 lead\ 清单，结果仅打印到 stdout）。"""
from __future__ import annotations
import os, re, sys

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
TC = os.path.join(BASE, "files_tier_C.tsv")
TA = os.path.join(BASE, "files_tier_A_snap2.tsv")

def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 3: 
                continue
            rows.append((p[0], int(p[2]), p[1], p[4] if len(p) > 4 else ""))
    return header, rows

hc, C = load(TC)
ha, A = load(TA)
print("HEADER_C", hc)
print("C rows", len(C), "sum bytes", sum(b for _,b,_,_ in C))
print("A rows", len(A), "sum bytes", sum(b for _,b,_,_ in A))

# Patterns (verbatim from source files)
P_BAND = r"(_before_|\.before|before_|_bak|backup/)"              # band_c_wide.py:21
P_EXTRA = r"(_before_|\.before|before_|_bak|\bbak\b|backup/|_backup)"  # rollback_extra.py:19
RX_BAND_I = re.compile(P_BAND, re.I)
RX_BAND_S = re.compile(P_BAND)            # case-sensitive (PowerShell [regex]::IsMatch default)
RX_EXTRA_I = re.compile(P_EXTRA, re.I)
RX_EXTRA_S = re.compile(P_EXTRA)
RX_OUT = re.compile(r"/[^/]*_out\.txt$", re.I)

def sel(rows, rx, scope="full", not_out=False):
    out = []
    for r,b,e,k in rows:
        target = r if scope=="full" else os.path.basename(r)
        if rx.search(target) and (not not_out or not RX_OUT.search(r)):
            out.append((r,b))
    return out

def show(name, s):
    print(f"{name}: {len(s)} 行 / {sum(b for _,b in s)} B")

print("\n=== files_tier_C.tsv (rel 全路径) ===")
show("band  re.I  full", sel(C, RX_BAND_I))
show("band  re.I  full  not_out", sel(C, RX_BAND_I, not_out=True))
show("band  caseS full", sel(C, RX_BAND_S))
show("extra re.I  full", sel(C, RX_EXTRA_I))
show("extra caseS full", sel(C, RX_EXTRA_S))
show("band  re.I  basename", sel(C, RX_BAND_I, scope="base"))
show("band  caseS basename", sel(C, RX_BAND_S, scope="base"))

print("\n=== files_tier_A_snap2.tsv ∩ tierC relset (bytes from A) ===")
cset = {r for r,_,_,_ in C}
AinC = [(r,b,e,k) for r,b,e,k in A if r in cset]
print("AinC rows", len(AinC), "bytes", sum(b for _,b,_,_ in AinC))
show("band  re.I  full  not_out  [band_c_wide set1]", sel(AinC, RX_BAND_I, not_out=True))
show("band  re.I  full", sel(AinC, RX_BAND_I))
show("band  caseS full", sel(AinC, RX_BAND_S))
show("extra re.I  full", sel(AinC, RX_EXTRA_I))

# symmetric differences on tier C: band re.I vs band caseS
si = {(r,b) for r,b in sel(C, RX_BAND_I)}
ss = {(r,b) for r,b in sel(C, RX_BAND_S)}
only_i = sorted(si - ss)
only_s = sorted(ss - si)
print("\n=== SymDiff band re.I vs band caseS on tier C ===")
print("only re.I (case-insensitive extra):", len(only_i), "行 /", sum(b for _,b in only_i), "B")
for r,b in only_i:
    print("  I_ONLY", b, r)
print("only caseS (should be empty):", len(only_s), "行 /", sum(b for _,b in only_s), "B")
for r,b in only_s:
    print("  S_ONLY", b, r)

# compare with documented numbers
print("\n=== Compare to documented ===")
print("Lead 375/184618279 ; auditor 333/184506382 ; diff 42/111897")
print("band re.I on C =", len(si), "/", sum(b for _,b in si))
print("band caseS on C =", len(ss), "/", sum(b for _,b in ss))
