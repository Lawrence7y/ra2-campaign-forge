# -*- coding: utf-8 -*-
"""Verify 0x410380/0x410320 direction, failure paths, and vtable write-point functions."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
from capstone import *

def dump(va, cap, label):
    print("="*90)
    print("%s va=%08X cap=%s" % (label, va, cap))
    for ins in R.disasm(va, R.read_va(va, cap)):
        if ins.id==0:
            print("  %08X: .byte %s" % (ins.address, ins.bytes.hex(" ")))
            continue
        print("  %08X: %-8s %-32s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" ")))
        if ins.address-va>=cap: break

# direction of validators
dump(0x410380, 90, "VALIDATOR 0x410380")
dump(0x410320, 90, "VALIDATOR 0x410320")

# row1 failure path near 0x483c00
dump(0x483BF0, 0x30, "ROW1 failure path 0x483C00")

# CellClass vtable write-point functions
for f in (0x47BB60, 0x47BBF0, 0x4839F0):
    dump(f, 0x80, "CELL vt write func %08X" % f)
