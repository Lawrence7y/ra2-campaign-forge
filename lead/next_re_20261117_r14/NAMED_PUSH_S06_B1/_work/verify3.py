# -*- coding: utf-8 -*-
"""Full callee dumps for -1 sentinel sites + ④ constructor/destructor verification."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
import core2 as C2
from capstone import *

def dump(va, cap, label, maxi=400):
    print("="*90)
    print("%s va=%08X cap=%s" % (label, va, cap))
    for i,ins in enumerate(R.disasm(va, R.read_va(va,cap))):
        if i>maxi: print("  ...(truncated)"); break
        if ins.id==0:
            print("  %08X: .byte %s" % (ins.address, ins.bytes.hex(" ")))
            continue
        print("  %08X: %-8s %-32s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" ")))
        if ins.address-va>=cap: break

mode=sys.argv[1] if len(sys.argv)>1 else "callees"
if mode=="callees":
    dump(0x7514D0, R.ATLAS.get('007514D0',{}).get('size') or 100, "ROW12 Find 0x7514D0")
    dump(0x5FDD20, 190, "ROW13 Find 0x5FDD20")
elif mode=="ring4":
    # vtable write funcs and their callers for candidate rows
    # Row1/Row2 CellClass vt 0x7E4EEC write funcs 0x47BB60(dtor?),0x47BBF0(ctor?),0x4839F0(load)
    # Row12 vt 0x7ECC48 write funcs 0x544A70,0x549C80
    # Row13 vt 0x7EF3D4 write funcs 0x5FC380,0x5FD8F0,0x5FDF70
    for va in (0x47BBF0, 0x47BD40, 0x544A70, 0x549C80, 0x5FC380, 0x5FD8F0):
        cap=R.ATLAS.get(R.hx(va),{}).get('size') or 60
        dump(va, min(cap,96), "write-func %08X (cap=%d)"%(va,cap), maxi=40)
        # is it atexit registered?
        ax=C2.is_atexit_registered(va)
        print("   atexit_registered=%s" % ax)
elif mode=="wctx":
    # exact bytes around write points
    for a in (0x47BD5C, 0x544A77, 0x549D02, 0x5FC38F, 0x5FD917):
        print("="*80)
        print("WRITE SITE %08X" % a)
        st=a-6
        for ins in R.disasm(st, R.read_va(st,20)):
            print("  %08X: %-8s %-30s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" ")))
