# -*- coding: utf-8 -*-
"""dump 005C46E0 两个跳表的各 case 目标代码，判 ③b① 每路可否单独验证。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True
def dis(va, n=48):
    return list(MD.disasm(R.read_va(va, n), va))
for va in [0x5C49B7,0x5C49D7,0x5C49F7,0x5C49FE,0x5C4A05,0x5C4A1B,0x5C4B41,0x5C4B45,0x5C4B4D]:
    print("=== case target %08X ===" % va)
    for i in dis(va, 40):
        print("   %08X %-7s %s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))
        if i.address - va >= 30: break
