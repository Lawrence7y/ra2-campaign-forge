# -*- coding: utf-8 -*-
"""细看两个非零『构造->ecx』信号，判定是否真把对象交给本行 entry。只读。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

def dump_range(v0,v1,label):
    print("===== %s [%08X,%08X) ====="%(label,v0,v1))
    for ins in MD.disasm(R.read_va(v0,v1-v0),v0):
        mark=" <== CALL" if ins.mnemonic=="call" else ""
        print("  %08X: %s %s%s"%(ins.address,ins.mnemonic,ins.op_str,mark))

# 00476B20 caller site 00644FA7, func 00644F50
dump_range(0x00644F50,0x00644FD0,"caller 00644F50 -> 00476B20 @644FA7")
# 00475D70 caller sites in 0066BBB0 family
dump_range(0x0066C820,0x0066C8E0,"caller ~0066C852 -> 00475D70")
