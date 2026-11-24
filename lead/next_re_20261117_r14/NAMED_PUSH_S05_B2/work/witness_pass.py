# -*- coding: utf-8 -*-
"""对两个 PASS 行核实 ④：构造安装点（regdisp，非 atexit）+ 派发站点。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
WORK = os.path.dirname(os.path.abspath(__file__))

def check(e, vt_hex, off):
    vt = int(vt_hex, 16)
    print("="*90)
    print("%s vt=%s off=%d(slot%d)" % (e, vt_hex, off, off//4))
    w = W.find_vtable_writes(vt)
    print("  regdisp writes (C7 r/m32,imm):", ["%08X"%x for x in w["regdisp"]])
    print("  global writes:", [g.get("write_va") if isinstance(g,dict) else g for g in w["global"]])
    print("  imm loads:", ["%08X"%x for x in w["imm_load"]])
    for x in w["regdisp"]:
        f = W.find_containing_atlas_func(x)
        at = bool(W.is_atexit_registered(f[0])) if f else False
        print("    regdisp %08X in func=%s atexit=%s" % (x, ("%08X"%f[0]) if f else None, at))
    # dispatch
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    from capstone.x86 import X86_INS_CALL, X86_OP_MEM, X86_REG_INVALID
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
    disp=[]
    for ins in md.disasm(R.TEXT_DATA, R.TEXT_VA):
        if ins.id==X86_INS_CALL and ins.operands and ins.operands[0].type==X86_OP_MEM:
            m=ins.operands[0].mem
            if m.disp==off and m.base not in (X86_REG_INVALID,0) and m.index in (X86_REG_INVALID,0):
                disp.append("%08X"%ins.address)
    print("  dispatch [reg+%d] total=%d first=%s" % (off, len(disp), disp[:8]))

check("00524D70", "007EB610", 32)
check("005F9950", "007EF2D8", 24)
