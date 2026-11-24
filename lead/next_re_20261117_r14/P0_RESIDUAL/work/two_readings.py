#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双口径交叉核对：严格 R14-R10(c4a OR c4b) vs 基线口径(c4a only)。

不改变主交付 RESIDUAL_ADJUDICATION.tsv（严格口径）。本脚本产出：
  EVIDENCE/TWO_READINGS.tsv   —— 每条 FUNC 的口径标签
  EVIDENCE/CONSERVATIVE_FUNC.tsv —— c4a-only / 有引用 c4b 的 FUNC 清单
"""
import os,sys,csv,collections
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from resid_common import RawPE
OUT=os.path.dirname(HERE);EVID=os.path.join(OUT,"EVIDENCE")
pe=RawPE()

def leaf(b):
    if len(b)<3:return False
    if b[0]==0x8B and (b[1]&0xF0)==0x40 and b[2]==0x24:return True
    if b[0]==0x8B and b[1]==0x41:return True
    if b[0] in (0x57,0x56,0x53):return True
    return False

rows=list(csv.DictReader(open(os.path.join(OUT,"RESIDUAL_ADJUDICATION.tsv"),encoding="utf-8"),delimiter="\t"))
funcs=[r for r in rows if r["verdict"]=="FUNC"]
tag_counts=collections.Counter()
with open(os.path.join(EVID,"TWO_READINGS.tsv"),"w",encoding="utf-8",newline="") as f, \
     open(os.path.join(EVID,"CONSERVATIVE_FUNC.tsv"),"w",encoding="utf-8",newline="") as g:
    f.write("addr\tchan\tstrict_verdict\treading\tfirst_byte\tevidence\n")
    g.write("addr\tchan\treason\tevidence\n")
    for r in funcs:
        A=int(r["addr"],16); d=pe.read(A,4)
        c4a=(d[0]==0x55 or d[:2] in (b"\x83\xec",b"\x81\xec"))
        lf=leaf(d)
        ev=r["evidence"]
        import re
        m=re.search(r"sem=([NY])/([NY])/([NY])",ev)
        sem1,sem2,sem3=(m.group(1),m.group(2),m.group(3)) if m else ("N","N","N")
        has_ref=(sem1=="Y" or sem2=="Y")
        if c4a:
            tag="c4a-prologue"
        elif has_ref:
            tag="c4b-with-reference"
        else:
            tag="c4b-leaf-only(no-reference)"
        tag_counts[tag]+=1
        f.write("%s\t%s\tFUNC\t%s\t%02X\t%s\n"%(r["addr"],r["chan"],tag,d[0],ev))
        if tag!="c4b-leaf-only(no-reference)":
            g.write("%s\t%s\t%s\t%s\n"%(r["addr"],r["chan"],tag,ev))
print("FUNC strict total:",len(funcs))
for k,v in sorted(tag_counts.items()):print("  ",k,v)
print("conservative (c4a + c4b-with-reference):",tag_counts["c4a-prologue"]+tag_counts["c4b-with-reference"])
