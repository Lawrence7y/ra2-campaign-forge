# -*- coding: utf-8 -*-
"""核查 MPCooperative 非 CRT callee 的返回约定，判断是否可伪证错误码。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True
WORK = os.path.dirname(os.path.abspath(__file__))

def ret_profile(target, cap=400):
    if not target or not R.in_text(target):
        return "NOT_IN_TEXT"
    size = R.ATLAS.get(R.hx(target), {}).get("size", cap)
    insns = list(MD.disasm(R.read_va(target, size), target))
    eax="?"; out=[]
    for ins in insns:
        if ins.id==0: continue
        m,o = ins.mnemonic, ins.op_str
        if m in ("xor","sub") and o=="eax, eax": eax="0"
        elif m=="mov" and o.startswith("eax, ") and o[5:].isdigit(): eax=o[5:]
        elif m=="mov" and o=="eax, 0xffffffff": eax="-1"
        elif m=="or" and o=="eax, 0xffffffff": eax="-1"
        elif m=="mov" and o.startswith("eax, 0x"): eax=o[5:]
        elif m=="call": eax="(call)"
        elif m=="ret":
            out.append("%08X:ret(eax=%s)"%(ins.address,eax)); eax="?"
    return out[:8]

for t in [0x775940, 0x7CD680, 0x5E26C0, 0x49BC80, 0x49D000]:
    print("%08X: %s" % (t, ret_profile(t)))
