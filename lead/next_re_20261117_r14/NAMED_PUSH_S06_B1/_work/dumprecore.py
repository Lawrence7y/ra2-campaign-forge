# -*- coding: utf-8 -*-
"""Dump full function body for given entries + follow jmp targets of interest."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
from capstone import *

def dump(va, cap, label):
    print("="*100)
    print("%s  va=%08X cap=%s" % (label, va, cap))
    for ins in R.disasm(va, R.read_va(va, cap)):
        if ins.id==0:
            print("  %08X: .byte %s" % (ins.address, ins.bytes.hex(" ")))
            continue
        print("  %08X: %-8s %-34s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" ")))
        if ins.address - va >= cap: break

for e in sys.argv[1:]:
    va = int(e,16)
    cap = R.ATLAS.get(R.hx(va),{}).get("size")
    dump(va, cap or 256, "FUNC "+e)

# follow 0x485010 jmp -> 0x5fdd20
print("\n\n##### follow 0x485010 -> 0x005FDD20 #####")
dump(0x5fdd20, 120, "JMPTARGET 005FDD20")
