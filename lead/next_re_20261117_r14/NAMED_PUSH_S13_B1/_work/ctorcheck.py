# -*- coding: utf-8 -*-
"""判定给定函数是否为构造器：体内是否写带 RTTI 的 vtable，或其早期 call 目标是否写了带 RTTI 的 vtable。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C2
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

def installs_rtti_vt(va):
    size = R.ATLAS.get("%08X"%va, {}).get("size") or 192
    insns = R.disasm_body(va, min(size,256))
    hits = []
    for ins in insns:
        if ins.mnemonic != "mov" or len(ins.operands)!=2: continue
        a,b = ins.operands
        if a.type != X86_OP_MEM or b.type != X86_OP_IMM: continue
        imm = b.imm & 0xFFFFFFFF
        c = C2.u32(imm-4) if imm else None
        ci = C2.parse_col(c) if c else None
        if ci and ci["sig"]==0:
            tdi = C2.parse_td(ci["td"])
            if tdi and ".?AV" in (tdi["name"] or ""):
                hits.append((ins.address, imm, tdi["name"]))
    return hits

targets = [0x5F3900,0x4E1100,0x410230,0x5F5E80,0x5F3B50,0x46B640,
           0x5F7090,0x410230,0x410170,0x4101C0,0x410800,
           0x5F9720,0x5F7320,0x5F8110,0x5F9070,0x6CF240,
           0x410380,0x410320,0x5F9950,0x10960+0x400000,
           0x7258D0,0x7C8B3D,0x5F7400]
for t in targets:
    n = "%08X" % t
    sz = R.ATLAS.get(n,{}).get("size")
    hits = installs_rtti_vt(t) if sz else []
    calls=[]
    if sz:
        for ins in R.disasm_body(t, min(sz,120))[:20]:
            if ins.mnemonic=="call" and ins.operands and ins.operands[0].type==X86_OP_IMM:
                calls.append("%08X"%(ins.operands[0].imm & 0xFFFFFFFF))
    print("%08X size=%-6s rtti_vt_installs=%-3s early_calls=%s" % (
        t, sz, len(hits), ",".join(calls[:8])))
    for h in hits[:3]:
        print("      @%08X vt=%08X %s" % h)
