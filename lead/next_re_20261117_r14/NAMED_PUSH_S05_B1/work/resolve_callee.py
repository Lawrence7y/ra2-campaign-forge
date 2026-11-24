# -*- coding: utf-8 -*-
"""解析间接 call 的被调地址（经 vtable 槽），并给返回常量.profile。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True

def ret_profile(target, cap=400, nmax=40):
    if not target or not R.in_text(target):
        return "NOT_IN_TEXT" if target else None
    size = R.ATLAS.get(R.hx(target), {}).get("size", cap)
    insns = list(MD.disasm(R.read_va(target, size), target))
    eax="?"; out=[]
    for ins in insns:
        if ins.id==0: continue
        m,o = ins.mnemonic, ins.op_str
        if m in ("xor","sub") and o=="eax, eax": eax="0"
        elif m=="mov" and o=="eax, 0xffffffff": eax="ffffffff(-1)"
        elif m=="or" and o=="eax, 0xffffffff": eax="ffffffff(-1)"
        elif m=="mov" and o.startswith("eax, 0x"): eax=o[5:]
        elif m=="mov" and o.startswith("eax, ") and o[5:].isdigit(): eax=o[5:]
        elif m=="call": eax="(call)"
        elif m=="ret":
            out.append("%08X:ret(eax=%s)"%(ins.address,eax)); eax="?"
            if len(out)>=nmax: break
    return out

# 直接 call 目标
for t in [0x410260, 0x410380, 0x4101f0, 0x4df040]:
    print("DIRECT callee %08X: %s" % (t, ret_profile(t)))

# vtable 槽解析: 给出 vtable base + slot off -> callee
print("\n--- aircraft vt slots ---")
vt_ac=0x7E22A4; vt_at=0x7E2868; vt_abs=0x7E2000
for vt,nm in [(vt_ac,"AircraftClass"),(vt_at,"AircraftTypeClass"),(vt_abs,"AbstractTypeClass")]:
    for off in [0x10,0x278,0x18,0x4]:
        p=R.u32(vt+off)
        print("  %-18s vt=%08X +%#x @%08X -> %s  ret=%s"%(nm,vt,off,vt+off,R.hx(p) if p else None, ret_profile(p, nmax=12)))
