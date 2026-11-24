#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三条候选正则复算。"""
from __future__ import annotations
import os, re
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
def load(p):
    out=[]
    with open(p,"r",encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            q=line.rstrip("\n").split("\t")
            if len(q)>=3: out.append((q[0],int(q[2])))
    return out
C=load(os.path.join(BASE,"files_tier_C.tsv"))
A=load(os.path.join(BASE,"files_tier_A_snap2.tsv"))
def sub(rows,rx): return [(r,b) for r,b in rows if rx.search(r)]
def sh(n,s): print(f"{n}: {len(s)} / {sum(b for _,b in s)} B")

P3 = r"(_before_|\.before|before_|_bak|backup/)(?!AFTER)"   # 排除 BEFORE_AFTER 对照记录族
P4 = r"(_before_|\.before|before_|_bak|bad|backup/)"        # 按 band_c_wide docstring 的 before/bak/bad
for name,pat in [("P3 exclude BEFORE_AFTER",P3),("P4 docstring bad",P4)]:
    rx=re.compile(pat,re.I)
    sh("tier C "+name, sub(C,rx))
    sh("tier A "+name, sub(A,rx))
# 确认 P3 相对 band re.I 只少那 42 行
bi=re.compile(r"(_before_|\.before|before_|_bak|backup/)",re.I)
p3=re.compile(P3,re.I)
s_bi={(r,b) for r,b in sub(C,bi)}; s_p3={(r,b) for r,b in sub(C,p3)}
print("P3 removed:",len(s_bi-s_p3),"/",sum(b for _,b in s_bi-s_p3))
for r,b in sorted(s_bi-s_p3)[:60]: print("   ",b,r)
