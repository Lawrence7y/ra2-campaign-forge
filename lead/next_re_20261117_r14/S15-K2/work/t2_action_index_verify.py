#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify dispatch index semantics: disassemble Execute prologue to see how edx (action idx) is computed;
disassemble handlers for actions 1,2,9 and the ratio-global writers (141-143)."""
import sys, os
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
import capstone
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S15-K2")
b=A.Bin()
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
action=[b.u32(0x6DFDEC+4*i) for i in range(145)]
def dis(va,n): return " | ".join(f"{i.address:#x}:{i.mnemonic} {i.op_str}" for i in m.disasm(b.read(va,n),va) if i.id!=0)
out=[]
out.append("=== Execute prologue 0x6DD8B0..0x6DD8EE (how is edx computed?) ===")
out.append(dis(0x6DD8B0,0x50))
for idx in (0,1,2,9,38,91,92,141,142,143):
    t=action[idx]
    out.append(f"\nA[{idx}] target={t:#x}: {dis(t,56)}")
with open(os.path.join(CARD,"EVIDENCE","T2_action_index_verify.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("\n".join(out))
