#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rigorous vtable slot verification for S15 GetSize candidates.
For each slot12 function VA, find .rdata dwords == VA, reconstruct vtable bounds via
contiguous function-pointer run + COL (vtable[-1] -> COL -> TD name), report slot index.
Also find operator new call targets from push->call sites.
"""
import sys, os, csv, re, struct
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
import capstone
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S15-K2")
b=A.Bin()

SLOT12 = {0x6E4630:"TActionClass",0x6E5890:"TagClass",0x6E64A0:"TagTypeClass",
          0x71FA50:"TEventClass",0x726930:"TriggerClass",0x727CB0:"TriggerTypeClass"}
SLOT11 = {0x6E4640:"TActionClass",0x6E58A0:"TagClass",0x6E6490:"TagTypeClass",
          0x71FA60:"TEventClass",0x726940:"TriggerClass",0x727CA0:"TriggerTypeClass"}

# .rdata section
rdata=None
for s in b.sections:
    if s["name"]==".rdata": rdata=s
print("rdata:",rdata)

# read all .rdata bytes
rbuf=b.pe.__data__[rdata["raw"]:rdata["raw"]+rdata["rawsize"]]
def u32_at_off(o): return struct.unpack_from("<I",rbuf,o)[0]

def find_rdata_refs(va):
    refs=[]
    pat=struct.pack("<I",va)
    off=0
    while True:
        i=rbuf.find(pat,off)
        if i<0: break
        refs.append(rdata["va"]+i)
        off=i+1
    return refs

out=[]
def emit(s=""): out.append(str(s))

emit("=== RTTI TypeDescriptor names present (.?AU/.?AV) ===")
# find .?A strings
for m in re.finditer(rb"\.\?A[UV][ -~]{0,80}",rbuf):
    s=m.group().decode(errors="replace")
    if any(c in s for c in ("TActionClass","TagClass","TagTypeClass","TEventClass","TriggerClass","TriggerTypeClass")):
        emit(f"  off={m.start():#x} va={rdata['va']+m.start():#x}  {s}")

emit("\n=== vtable refs for each slot12 / slot11 function ===")
for fa,cn in sorted({**SLOT12,**SLOT11}.items()):
    role = "slot12/GetSize?" if fa in SLOT12 else "slot11/WhatAmI?"
    refs=find_rdata_refs(fa)
    emit(f"{cn} {role} fn={fa:#x} refs_in_rdata={[hex(x) for x in refs]}")
    for ref in refs:
        # scan backwards to find vtable start: contiguous dwords that look like code ptrs 0x4xxxxx..0x7Exxxx
        start=ref
        while start-4>=rdata["va"]:
            pv=u32_at_off((start-4)-rdata["va"])
            if 0x401000<=pv<0x7E2000: start-=4
            else: break
        # scan forward
        end=ref+4
        while end+4<=rdata["va"]+rdata["rawsize"]:
            pv=u32_at_off((end)-rdata["va"])
            if 0x401000<=pv<0x7E2000: end+=4
            else: break
        nslots=(end-start)//4
        slot=(ref-start)//4
        colva=u32_at_off(start-4-rdata["va"]) if start-4>=rdata["va"] else 0
        emit(f"    ref={ref:#x} vtable_guess=[{start:#x},{end:#x}) nslots={nslots} slot_index={slot} COL(vtable[-1])={colva:#x}")

# Now: operator new targets. Re-scan push->call and record CALL TARGET
emit("\n=== push <size> -> call TARGET (real callee) ===")
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
t=b.text
data=b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
insns=[i for i in m.disasm(data,t["va"]) if i.id!=0]
SIZES={0x94:"TActionClass",0x38:"TagClass",0xA4:"TagTypeClass",0x58:"TEventClass",0x48:"TriggerClass",0xB4:"TriggerTypeClass"}
from collections import Counter
tgt_counter=Counter()
examples={}
for k,i in enumerate(insns):
    if i.mnemonic!="push" or not i.op_str.startswith("0x"): continue
    try: v=int(i.op_str,16)
    except: continue
    if v not in SIZES: continue
    for j in range(k+1,min(k+9,len(insns))):
        n=insns[j]
        if n.mnemonic=="call" and n.op_str.startswith("0x"):
            tg=int(n.op_str,16); tgt_counter[tg]+=1
            examples.setdefault((v,tg),(i.address,n.address))
            break
        if n.mnemonic in ("ret","jmp"): break
for tg,c in tgt_counter.most_common(20):
    emit(f"  call_target={tg:#x} count={c}")
emit("\n  size->target examples:")
for (v,tg),(ps,cs) in sorted(examples.items()):
    emit(f"    size={v:#x}({SIZES[v]}) push@{ps:#x} callsite@{cs:#x} target={tg:#x}")

with open(os.path.join(CARD,"EVIDENCE","T2_vtable_verify.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("Wrote EVIDENCE/T2_vtable_verify.txt")
print("\n".join(out[:60]))
