#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extra T3 spot check: 0x410410 AbstractClass::Save (foundational Save)."""
import sys,io,os
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_IMM,X86_OP_MEM,X86_OP_REG
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
out=[]
out.append("===== 0x00410410 AbstractClass::Save (atlas size 35) =====")
out.append("claim: serialize +0x10 dword and +0x20 bool to IStream")
out.append("evidence_path cited: EVIDENCE/evidence_raw.json#00410410 (generic census 'region guess')")
out.append("bytes: "+P.read(0x410410,35).hex(' '))
for ins in md.disasm(P.read(0x410410,35),0x410410):
    line=f"{ins.address:08X}: {ins.bytes.hex():<18s} {ins.mnemonic:<7s} {ins.op_str}"
    if ins.mnemonic in ('call','jmp') and ins.operands and ins.operands[0].type==X86_OP_IMM:
        nm=P.iat_name(ins.operands[0].imm)
        if nm:line+=f" ; IAT={nm}"
    out.append("  "+line)
# vtable slot13 on AbstractClass
col=P.u32(0x7E1F4C);td=P.u32(col+0xC) if col else None
out.append(f"vt 0x7E1F50 slot13 = {P.u32(0x7E1F50+0x34):08X}; pCOL={col:08X}")
if td:
    o=P.va2off(td+8)
    if o is not None:
        with open(P.EXE,'rb') as f:f.seek(o);nm=f.read(40)
        z=nm.find(b'\x00');out.append(f"RTTI={nm[:z if z>=0 else 30]!r}")
txt="\n".join(out)+"\n"
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K3"
with io.open(os.path.join(CARD,"EVIDENCE","t3_spot_410410.txt"),"w",encoding="utf-8") as f:f.write(txt)
sys.stdout.write(txt)
