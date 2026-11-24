#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最后补充：extra 相对 band 多出的行；342 归属确认。"""
from __future__ import annotations
import os,re
BASE=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
def load(p):
    o=[]
    with open(p,"r",encoding="utf-8") as f:
        f.readline()
        for l in f:
            q=l.rstrip("\n").split("\t")
            if len(q)>=3:o.append((q[0],int(q[2])))
    return o
C=load(os.path.join(BASE,"files_tier_C.tsv")); A=load(os.path.join(BASE,"files_tier_A_snap2.tsv"))
bi=re.compile(r"(_before_|\.before|before_|_bak|backup/)",re.I)
ei=re.compile(r"(_before_|\.before|before_|_bak|\bbak\b|backup/|_backup)",re.I)
sc={(r,b) for r,b in C if bi.search(r)}; se={(r,b) for r,b in C if ei.search(r)}
print("extra-only in C:",len(se-sc),"/",sum(b for _,b in se-sc))
for r,b in sorted(se-sc): print("  ",b,repr(ei.search(r).group(0)),r)
print("\n342 归属: band case-sensitive on tier A =",len([1 for r,b in A if re.compile(r"(_before_|\.before|before_|_bak|backup/)").search(r)]))
print("           其字节 =",sum(b for r,b in A if re.compile(r"(_before_|\.before|before_|_bak|backup/)").search(r)))
print("footnote 384 归属: band re.I on tier A =",len([1 for r,b in A if bi.search(r)]),"/",sum(b for r,b in A if bi.search(r)))
