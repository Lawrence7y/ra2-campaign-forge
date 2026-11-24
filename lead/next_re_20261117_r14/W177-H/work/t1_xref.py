#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static read-only xref: verify hover global 0x88095C feeding GetCellAt 0x5657A0.
Uses capstone 5.0.7 + pefile. Disassembles 0x6DBE20 function and prints the chain.
Does NOT trust prior cards; re-derives from bytes."""
import pefile, capstone
P=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
HOVER=0x0088095C; GETCELL=0x005657A0
pe=pefile.PE(P); ib=pe.OPTIONAL_HEADER.ImageBase
def off(va): return pe.get_offset_from_rva(va-ib)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
# disassemble 0x6DBE20..0x6DBE40
base=0x006DBE20; code=pe.get_data(off(base),0x120)
hits=[]
for i in md.disasm(code,base):
    if i.address>0x6DBF30: break
    mark=""
    if ("0x88095c" in i.op_str.lower()) or ("0x%x"%HOVER in i.op_str.lower()): mark=" <== hover 0x88095C"
    if "call" in i.mnemonic and ("0x%x"%GETCELL in i.op_str.lower() or str(GETCELL) in i.op_str): mark=" <== call GetCellAt"
    if mark or i.mnemonic in ("mov","lea","push","call"):
        print("%08X: %-8s %-30s%s"%(i.address,i.mnemonic,i.op_str,mark))
    if mark: hits.append((i.address,i.mnemonic,i.op_str))
print("\nHOVER_REFS",sum(1 for a,m,o in hits if "88095c" in o.lower()))
print("GETCELL_CALL_REFS",sum(1 for a,m,o in hits if "call" in m and "5657a0" in o.lower()))
