#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final confirmation: byte-compare 0x431B80 vs 0x432610 (vt slot0) and dump tail."""
import sys,io,os
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
b1=P.read(0x431B80,64)
b2=P.read(0x432610,80)
out=[]
out.append(f"0x431B80[0:64] = {b1.hex(' ')}")
out.append(f"0x432610[0:64] = {b2[:64].hex(' ')}")
out.append(f"first 64 bytes identical? {b1==b2[:64]}")
out.append(f"0x432610[64:80] (tail) = {b2[64:80].hex(' ')}")
out.append("\n0x432610 tail disasm:")
for ins in md.disasm(b2,0x432610):
    if ins.address>=0x432648:
        out.append(f"  {ins.address:08X}: {ins.bytes.hex():<16s} {ins.mnemonic} {ins.op_str}")
txt="\n".join(out)+"\n"
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K3"
with io.open(os.path.join(CARD,"EVIDENCE","dtor_bytecmp.txt"),"w",encoding="utf-8") as f:f.write(txt)
sys.stdout.write(txt)
