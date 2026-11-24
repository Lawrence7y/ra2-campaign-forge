#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find constructor allocation points (push size -> operator new) for S15 classes.
Covers 6A imm8 AND 68 imm32 (small-immediate trap §972). Function-interval containment for attribution.
"""
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
b=A.Bin()
# GetSize sizes from slot12
SIZES = {0x94:"TActionClass", 0x38:"TagClass", 0xA4:"TagTypeClass",
         0x58:"TEventClass", 0x48:"TriggerClass", 0xB4:"TriggerTypeClass"}
print("Target sizes:", {hex(k):v for k,v in SIZES.items()})

# full .text scan for push imm followed (within 8 insns) by a direct call
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
t=b.text
data=b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
insns=[i for i in m.disasm(data,t["va"]) if i.id!=0]
print(f"insns scanned={len(insns)}")
# index by address for neighbor lookups
addr2idx={i.address:k for k,i in enumerate(insns)}
# find push imm (6A/68) with a value in SIZES, then next direct call within 6 instructions
hits=[]
for k,i in enumerate(insns):
    if i.mnemonic!="push" or not i.op_str.startswith("0x"): continue
    try: v=int(i.op_str,16)
    except: continue
    if v not in SIZES: continue
    # look ahead up to 8 insns for a direct call
    for j in range(k+1, min(k+9,len(insns))):
        n=insns[j]
        if n.mnemonic=="call" and n.op_str.startswith("0x"):
            hits.append((i.address, v, SIZES[v], n.address, i.bytes.hex()))
            break
        if n.mnemonic in ("ret","jmp"): break
print(f"\n=== push <size> -> call sites (size in S15 GetSize set) ===")
for site,v,cn,callt,raw in hits:
    print(f"  push@{site:#x} raw={raw:<12} size={v:#x}({cn})  call@{callt:#x}")
print(f"total={len(hits)}")

# Which distinct call targets (operator new candidates)?
from collections import Counter
cc=Counter(h[3] for h in hits)
print("\n=== distinct call targets after push ===")
for tgt,c in cc.most_common():
    print(f"  {tgt:#x} : {c}")

with open(os.path.join(CARD,"EVIDENCE","T2_alloc_sites.txt"),"w",encoding="utf-8") as f:
    f.write("size_class_map\t"+repr({hex(k):v for k,v in SIZES.items()})+"\n")
    f.write(f"insns_scanned\t{len(insns)}\n")
    for site,v,cn,callt,raw in hits:
        f.write(f"{site:#x}\t{raw}\t{v:#x}\t{cn}\tcall={callt:#x}\n")
    f.write("=== call targets ===\n")
    for tgt,c in cc.most_common(): f.write(f"{tgt:#x}\t{c}\n")
print("Wrote EVIDENCE/T2_alloc_sites.txt")
