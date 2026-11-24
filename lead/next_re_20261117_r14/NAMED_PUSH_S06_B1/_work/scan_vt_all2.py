# -*- coding: utf-8 -*-
"""For each imm32 occurrence of a vtable in .text, decode the exact instruction and its containing func."""
import os, sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
import core2 as C2
from capstone import *

def find_insn_covering(va):
    # try starts from va-8..va to find instruction whose [addr,addr+size) covers va
    for st in range(va-8, va+1):
        if st < R.TEXT_VA: continue
        ins=list(R.disasm(st, R.read_va(st, 12)))
        if ins and ins[0].address<=va<ins[0].address+ins[0].size:
            return ins[0]
    return None

def dump_func(va,limit=48):
    cap=min(R.ATLAS.get(R.hx(va),{}).get("size") or limit, 0x200)
    for ins in R.disasm(va, R.read_va(va, min(cap,limit))):
        if ins.id==0: continue
        print("       %08X: %-8s %-32s | %s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex(" ")))
        if ins.address-va>=limit: break

for vt in (0x7ECC48, 0x7E4EEC, 0x7EC258, 0x7EF3D4):
    needle=struct.pack("<I",vt); D=R.TEXT_DATA; V=R.TEXT_VA
    print("="*95); print("VT %08X"%vt)
    start=0
    while True:
        i=D.find(needle,start)
        if i<0: break
        va=V+i
        ins=find_insn_covering(va)
        f=C2.find_containing_atlas_func(va)
        fva=f[0] if f else None
        print("  imm@%08X  insn=%s  func=%s"%(va,
            ("%s %s"%(ins.mnemonic,ins.op_str)) if ins else "?", ("%08X"%fva) if fva else "?"))
        if ins:
            print("     %08X: %-8s %-32s | %s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex(" ")))
        start=i+1
