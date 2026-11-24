#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补充复算：342 来源排查 + 42 行命中分支标注 + 对称差逐行明细。"""
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
PB=r"(_before_|\.before|before_|_bak|backup/)"
PE=r"(_before_|\.before|before_|_bak|\bbak\b|backup/|_backup)"
bi=re.compile(PB,re.I); bs=re.compile(PB)
ei=re.compile(PE,re.I); es=re.compile(PE)
out=re.compile(r"/[^/]*_out\.txt$",re.I)
def sub(rows,rx,notout=False):
    return [(r,b) for r,b in rows if rx.search(r) and (not notout or not out.search(r))]
def sh(n,s): print(f"{n}: {len(s)} / {sum(b for _,b in s)} B")
print("=== 追查 342 / 258,682,186 ===")
sh("extra caseS tierA", sub(A,es))
sh("extra re.I  tierA", sub(A,ei))
sh("extra caseS tierA not_out", sub(A,es,True))
sh("extra re.I  tierA not_out", sub(A,ei,True))
sh("band  caseS tierA", sub(A,bs))
sh("band  re.I  tierA", sub(A,bi))
# tierA minus tierC
cset={r for r,_ in C}
AnotC=[(r,b) for r,b in A if r not in cset]
sh("A-notC rows(all)", AnotC)
sh("extra caseS A-notC", sub(AnotC,es))
sh("extra re.I  A-notC", sub(AnotC,ei))
sh("band  caseS A-notC", sub(AnotC,bs))
sh("band  re.I  A-notC", sub(AnotC,bi))
print("\n=== 42 行命中分支标注 (band re.I 命中但 band caseS 不命中) ===")
si={(r,b) for r,b in sub(C,bi)}
ss={(r,b) for r,b in sub(C,bs)}
diff=sorted(si-ss)
print("diff rows",len(diff),"bytes",sum(b for _,b in diff))
from collections import Counter
branch=Counter()
for r,b in diff:
    m=bi.search(r)
    branch[m.group(0)]+=1
print("命中片段分布:",dict(branch))
for r,b in diff:
    m=bi.search(r)
    print(f"  {b}\t{repr(m.group(0))}\t{r}")
print("\n=== 42 行是否全部 *_out.txt？ ===")
print("out.txt count:", sum(1 for r,b in diff if out.search(r)))
