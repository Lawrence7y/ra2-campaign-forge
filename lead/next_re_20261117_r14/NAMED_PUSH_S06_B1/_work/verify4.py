# -*- coding: utf-8 -*-
"""For each cmp eax,-1 site, find the preceding call and whether it is direct/indirect."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
from capstone import *
from capstone.x86 import *

sites = [(0x543B9A,5),(0x543BE3,5),(0x5F93BA,12),(0x5F93F6,12),
         (0x5FD1C0,13),(0x5FDFAD,15)]
for a,row in sites:
    print("="*90)
    print("ROW %d cmp-1 @%08X" % (row,a))
    st=a-24
    for ins in R.disasm(st, R.read_va(st,40)):
        mark=""
        if ins.address==a: mark=" <== CMP -1"
        if ins.id==X86_INS_CALL:
            if ins.operands and ins.operands[0].type==X86_OP_IMM:
                mark+=" <== DIRECT CALL %08X"%(ins.operands[0].imm&0xffffffff)
            else:
                mark+=" <== INDIRECT CALL (%s)"%ins.op_str
        print("  %08X: %-8s %-30s | %s%s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex(" "),mark))
