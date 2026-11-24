#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3: 找 HouseClass 深处的 accessor (Power_Output/Power_Drain/Color/Side/Counts)。
   扫所有 vtable text 槽指向的小函数, 找 mov eax,[ecx+disp]; ret 形态。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W
from capstone.x86 import X86_OP_REG, X86_OP_MEM

def vtext_slots(vt,n):
    out=[]
    for i in range(n):
        v=W.rd32(vt+i*4)
        if v and W.in_text(v): out.append((i,v))
    return out

def small_accessor(va):
    """反汇编一个函数前 40B, 找 (a) mov reg,[ecx+disp]; (b) 随后 ret; 返回 disp 集"""
    disps=[]
    ins=list(W.disasm(va,0x40,stop_ret=False))
    if not ins: return None
    for a,m,o,ii in ins:
        if ii.id==0 or m.startswith("."): continue
        if m in ("ret","retf"):
            break
        # ops 里 [ecx+disp] / [esi+disp] / [edi+disp] (deep fields)
        for op in ii.operands:
            if op.type==X86_OP_MEM and op.mem.base:
                bn=ii.reg_name(op.mem.base)
                if bn in ("ecx","esi","edi"):
                    if 0x300<=op.mem.disp<=0x16100:
                        disps.append(op.mem.disp)
        if len(ins)>14: break
    return disps

if __name__=="__main__":
    vt=0x7EA8A0
    slots=vtext_slots(vt,60)
    print("HouseClass text vtable slots:",len(slots))
    for i,va in slots:
        d=small_accessor(va)
        if d:
            print("slot[%d] 0x%08X -> disps %s"%(i,va,[hex(x) for x in sorted(set(d))]))
