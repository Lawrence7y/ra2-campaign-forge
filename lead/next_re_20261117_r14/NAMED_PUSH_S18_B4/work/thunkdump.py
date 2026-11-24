# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
for d in sys.argv[1:]:
    print("%10d = 0x%08X" % (int(d), int(d)))
print()
def dump(ea, n, tag):
    print("--- %s %08X len=%d ---" % (tag, ea, n))
    for i in MD.disasm(R.read_va(ea, n), ea):
        print("  %08X  %-8s %-40s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))
# thunk cluster
dump(0x7C8960, 0x60, "thunks 7c8960")
print()
# constructor install site region
dump(0x7B0D90, 0x60, "ctor 7B0D90")
