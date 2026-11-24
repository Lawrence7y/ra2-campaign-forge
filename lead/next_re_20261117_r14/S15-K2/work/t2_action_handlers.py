#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify: for each sub_ row mapped to a unique action, disassemble the ACTION handler
body (from dispatch target up to the call site + few insns) to see if it's a thin wrapper."""
import sys, os, csv
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
import capstone
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S15-K2")
b=A.Bin()
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
action=[b.u32(0x6DFDEC+4*i) for i in range(145)]
def dis(va,n): return " | ".join(f"{i.address:#x}:{i.mnemonic} {i.op_str}" for i in m.disasm(b.read(va,n),va) if i.id!=0)

# selected actions with unique sub_ mapping from t2_action_map
sel={113:0x6E4100,114:0x6E4150,128:0x6E42D0,131:0x6E4320,132:0x6E4360,133:0x6E43A0,
     134:0x6E43E0,135:0x6E4440,139:0x6E4460,140:0x6E44C0,136:0x6E44E0,137:0x6E4540,
     130:0x6E4560,141:0x6E2E60,142:0x6E2EB0,143:0x6E2F00,138:0x6E3B40,117:0x6E2C20,
     52:0x6E2AF0,80:0x6E01C0,98:0x6E1830,115:0x6E1980,127:0x6E1A40,31:0x6E2050}
out=[]
for idx,subva in sorted(sel.items()):
    t=action[idx]
    out.append(f"A[{idx:3d}] target={t:#x} expected_sub={subva:#x}")
    out.append(f"   {dis(t,80)}")
with open(os.path.join(CARD,"EVIDENCE","T2_action_handlers.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("Wrote EVIDENCE/T2_action_handlers.txt")
print("\n".join(out[:40]))
