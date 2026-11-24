#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3: 找 HouseClass 的 Power_Output/Power_Drain/颜色/阵营字段。
   扫全文针对已知 HouseClass 方法(虚表全槽 + accessor), 找读两个相邻 int 后 cmp 的函数。"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W
from capstone.x86 import X86_OP_REG, X86_OP_MEM, X86_OP_IMM

def dump_vt(vt,n):
    out=[]; prev_txt=0
    for i in range(n):
        v=W.rd32(vt+i*4)
        out.append((i,v))
    return out

def dump_fn(va,n=0x80):
    lines=[]
    for a,m,o,insn in W.disasm(va,n,stop_ret=False):
        if insn.id==0 or m.startswith("."): continue
        lines.append("0x%08X %-18s %-6s %s"%(a,W.bytes_at(a,insn.size).hex(),m,o))
    return "\n".join(lines)

if __name__=="__main__":
    vt=0x7EA8A0
    print("=== HouseClass vtable slots 24..60 ===")
    for i,v in dump_vt(vt,60):
        if i<24: continue
        kind="text" if (v and W.in_text(v)) else "DATA"
        print("slot[%d] 0x%08X = 0x%08X (%s)"%(i,vt+i*4,v or 0,kind))
