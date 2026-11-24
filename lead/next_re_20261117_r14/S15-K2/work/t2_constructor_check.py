#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Examine 5 sub_ rows with vtable writes: are they genuine constructors?
Evidence: writes class vtable to [this], RTTI COL confirms class, caller is factory/new site,
function writes base-class vtables too (multi-level ctor chain)."""
import sys,os,csv,struct,re
ROOT=r"D:\Project\ra2-campaign-forge"
sys.path.insert(0,os.path.join(ROOT,r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
import capstone
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S15-K2")
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)
cov=rd(COV); atl={norm(r["entry"]):r for r in rd(ATL)}
calls,jmps,_=A.sweep_calls(A.Bin())
b=A.Bin(); m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
cands=["006E4DE0","006E4F60","006E5B60","00725FA0","00726C80"]
VT={0x7F443C:"TActionClass",0x7F44E0:"TagClass",0x7F45C4:"TagTypeClass",
    0x7F5578:"TEventClass",0x7F5858:"TriggerClass",0x7F5904:"TriggerTypeClass"}
out=[]
def dis(va,n): return " | ".join(f"{i.address:#x}:{i.mnemonic} {i.op_str}" for i in m.disasm(b.read(va,n),va) if i.id!=0)
for e in cands:
    r=next(x for x in cov if norm(x["entry"])==e)
    va=int(e,16); size=int(atl[e]["size"])
    out.append(f"\n=== {e} sz={size} name={r['name']} grade={r['grade']} ===")
    out.append(f"  full dis: {dis(va,min(size,450))}")
    out.append(f"  callers ({len(calls.get(va,[]))}): {[hex(s) for s in calls.get(va,[])[:10]]}")
    # find vtable writes
    data=b.read(va,min(size,450))
    for vt,cn in VT.items():
        p=struct.pack("<I",vt); off=0
        while True:
            i=data.find(p,off)
            if i<0:break
            # find the instruction containing this offset
            ctx=dis(va+max(0,i-12),24)
            out.append(f"  VT WRITE {cn} {vt:#x} at {va+i:#x}: ...{ctx}")
            off=i+1
open(os.path.join(CARD,"EVIDENCE","T2_constructor_candidates.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")
for l in out: print(l[:400])
