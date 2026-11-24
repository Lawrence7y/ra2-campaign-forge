#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rigorous verification of the 42 promotions:
 - for each promoted action-impl, print exact call site + enclosing handler target + handler first call
 - detect duplicate action names
 - negative control: how many non-promoted sub_ rows have a call site inside the handler region?
 - hunt remaining sub_ rows for vtable writes (constructor evidence)
"""
import sys, os, csv, re, struct
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
b=A.Bin(); m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
action=[b.u32(0x6DFDEC+4*i) for i in range(145)]
uniq=sorted(set(action))
def hend(t):
    for u in uniq:
        if u>t: return u
    return 0x6DFDDB+9
region_start=min(action); region_end=0x6DFDDB+9
data=b.read(region_start,region_end-region_start)
call_sites={}
for ins in m.disasm(data,region_start):
    if ins.id==0: continue
    if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
        call_sites.setdefault(int(ins.op_str,16),[]).append(ins.address)
def act_for(site):
    for i,t in enumerate(action):
        if t<=site<hend(t): return i
    return None
def dis(va,n): return " | ".join(f"{i.mnemonic} {i.op_str}" for i in m.disasm(b.read(va,n),va) if i.id!=0)

# read promotions
proms=list(csv.DictReader(open(os.path.join(CARD,"EVIDENCE","PROMOTIONS.tsv"),"r",encoding="utf-8-sig"),delimiter="\t"))
out=[]
out.append("=== verify each promoted action-impl ===")
from collections import Counter
namec=Counter()
for p in proms:
    if "TActionClass::" not in p["new_name"] or p["new_name"].endswith(("GetSize","WhatAmI")): continue
    e=p["entry"]; va=int(e,16); sites=call_sites.get(va,[])
    for s in sites:
        ai=act_for(s)
        out.append(f"  {e} {p['new_name']:<38} call@{s:#x} handler_idx={ai} target={action[ai] if ai is not None else '?'} : {dis(action[ai],40) if ai is not None else ''}")
    namec[p["new_name"]]+=1
out.append("\n=== duplicate new names ===")
for n,c in namec.items():
    if c>1: out.append(f"  DUP {n} x{c}")

out.append("\n=== detailed: the two PlayMovie rows ===")
for e in ("0072DDB0","0072DEF0"):
    va=int(e,16)
    out.append(f"  {e}: {dis(va,60)}")
    for s in call_sites.get(va,[]):
        out.append(f"    called from {s:#x}, handler_idx={act_for(s)}")

# negative control
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]
sub_remaining=[r for r in s15 if r["name"].strip().startswith("sub_") and r["grade"].strip()=="[未证]"]
promoted_entries={p["entry"] for p in proms}
out.append(f"\n=== negative control: {len(sub_remaining)} remaining sub_ rows; how many have call in handler region? ===")
for r in sorted(sub_remaining,key=lambda x:norm(x["entry"])):
    e=norm(r["entry"]); va=int(e,16); sites=call_sites.get(va,[])
    if sites:
        out.append(f"  {e} ncall_in_region={len(sites)} sites={[hex(s) for s in sites[:6]]} acts={[act_for(s) for s in sites[:6]]}")

# constructor hunt: vtable writes 0x7Fxxxx in remaining sub_
out.append("\n=== remaining sub_ rows with vtable write (mov [reg],0x7Fxxxx) ===")
for r in sorted(sub_remaining,key=lambda x:norm(x["entry"])):
    e=norm(r["entry"]); va=int(e,16); size=int(atl[e]["size"])
    bytes_=b.read(va,min(size,400))
    pat=re.findall(rb"\xc7\x00(..)\x7f\x00",bytes_) # C7 0x modrm ... imm32 low bytes 7f000000 not simple
    # simpler: look for the 4-byte little-endian value of any known vtable
    vts=[0x7F443C,0x7F44E0,0x7F45C4,0x7F5578,0x7F5858,0x7F5904]
    found=[]
    for vt in vts:
        p=struct.pack("<I",vt); off=0
        while True:
            i=bytes_.find(p,off)
            if i<0:break
            found.append((hex(vt),hex(va+i))); off=i+1
    if found: out.append(f"  {e} vtrefs={found}")

open(os.path.join(CARD,"EVIDENCE","T2_verify_promotions.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")
print("\n".join(out))
