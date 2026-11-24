#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble all S15 [静态推断] slot rows (capstone skipdata=True) to find GetSize/WhatAmI patterns."""
import sys, os, csv, re
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
import capstone
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S15-K2")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)
cov=rd(COV); atl={norm(r["entry"]):r for r in rd(ATL)}
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]
slotrows=[r for r in s15 if r["grade"].strip()=="[静态推断]" and "::" in r["name"]]
b=A.Bin()
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True

out=[]
def emit(s=""): out.append(s)

for r in sorted(slotrows,key=lambda x:norm(x["entry"])):
    e=norm(r["entry"]); va=int(e,16); size=int(atl[e]["size"])
    data=b.read(va,size)
    insns=list(m.disasm(data,va))
    txt=" | ".join(f"{i.mnemonic} {i.op_str}" for i in insns if i.id!=0)
    emit(f"{e} {r['name']:<40} sz={size:<5} bytes={data.hex()}")
    emit(f"     {txt}")
with open(os.path.join(CARD,"EVIDENCE","T2_slot_disasm.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print(f"Wrote {len(slotrows)} slot disassemblies to EVIDENCE/T2_slot_disasm.txt")
# print a compact summary of slot12/slot11 patterns
print("\n=== slot12 / slot11 bodies (GetSize / WhatAmI candidates) ===")
for r in sorted(slotrows,key=lambda x:norm(x["entry"])):
    nm=r["name"]
    if re.search(r"::slot(11|12|16)$",nm):
        e=norm(r["entry"]); va=int(e,16); size=int(atl[e]["size"])
        data=b.read(va,size)
        print(f"{e} {nm:<40} {data.hex()}")
