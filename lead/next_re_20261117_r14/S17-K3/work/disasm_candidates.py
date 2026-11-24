#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble all 11 NOT-named candidates with full bytes and resolve calls/strings."""
import sys, os, io, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

cands = {
 0x004068E0:1, 0x0040E340:75, 0x00427940:315, 0x0042E410:32, 0x00431B80:64,
 0x00433CF0:437, 0x004355B0:25, 0x0043AE50:40, 0x0049F740:88, 0x0049F8B0:101, 0x00773450:169,
}
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True

out=[]
for va, size in cands.items():
    b = P.read(va, size)
    out.append(f"\n===== {va:08X} (size {size}) =====")
    out.append("raw: "+b.hex(' '))
    for ins in md.disasm(b, va):
        line = f"{ins.address:08X}: {ins.bytes.hex():<20s} {ins.mnemonic:<8s} {ins.op_str}"
        # annotate call/jmp imm target with IAT name
        if ins.mnemonic in ('call','jmp') and ins.operands and ins.operands[0].type==X86_OP_IMM:
            t = ins.operands[0].imm
            nm = P.iat_name(t)
            if nm: line += f"  ; IAT {nm}"
            line += f"  ; ->{t:08X}"
        # annotate string pointer pushes: push imm that maps to cstr
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            t = ins.operands[0].imm
            off=P.va2off(t)
            if off is not None:
                with open(P.EXE,'rb') as f:
                    f.seek(off); sb=f.read(80)
                if sb and 4<=sb.find(b'\x00')<=70:
                    st=sb[:sb.find(b'\x00')]
                    if all(32<=c<127 or c in (9,10,13) for c in st):
                        line += f"  ; str@{t:08X}={st!r}"
        out.append(line)

txt="\n".join(out)+"\n"
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K3"
with io.open(os.path.join(CARD,"EVIDENCE","candidate_disasm.txt"),"w",encoding="utf-8") as f:
    f.write(txt)
sys.stdout.write(f"written {len(txt)} chars\n")
