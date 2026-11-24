# -*- coding: utf-8 -*-
"""Comprehensive scan for every occurrence of a vtable address as imm32 in .text,
with instruction context, to catch constructors that load via mov reg,imm then mov [mem],reg."""
import os, sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
from capstone import *

def scan(vt):
    needle=struct.pack("<I",vt)
    D=R.TEXT_DATA; V=R.TEXT_VA
    print("="*90); print("VT %08X : occurrences in .text"%vt)
    start=0
    while True:
        i=D.find(needle,start)
        if i<0: break
        va=V+i
        # show context from i-8 to i+8, disassembled aligned back a few starts
        st=max(0,i-8)
        print("  --- imm @%08X (raw %s) ---"%(va, D[max(0,i-6):i+6].hex(" ")))
        for off in range(st,i+2):
            # find an instruction that covers position i by disassembling from off
            ins=list(R.disasm(off, D[off:off+12], ))
            if ins and ins[0].address<=va<ins[0].address+ins[0].size:
                x=ins[0]
                print("     %08X: %-8s %-34s | %s"%(x.address,x.mnemonic,x.op_str,x.bytes.hex(" ")))
                break
        start=i+1

for vt in (0x7ECC48, 0x7E4EEC, 0x7EC258, 0x7EF3D4):
    scan(vt)
