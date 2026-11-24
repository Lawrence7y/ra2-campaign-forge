# -*- coding: utf-8 -*-
"""检查给定 callee 的返回约定（ imm 哨兵 / ret 处 eax 来源），以及站点附近字节。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone.x86 import *

cals = sys.argv[1:]
for c in cals:
    va = int(c,16)
    size = R.ATLAS.get(R.hx(va),{}).get('size')
    print("="*80)
    print("CALLEE %s atlas_size=%s" % (R.hx(va), size))
    if not size:
        size = 256
    data = R.read_va(va, size)
    insns = R.disasm(va, data)
    for ins in insns:
        if ins.id==0: continue
        print("  %08X: %-22s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic+" "+ins.op_str))
    prof = R.callee_return_profile(va)
    print("  profile:", prof)
