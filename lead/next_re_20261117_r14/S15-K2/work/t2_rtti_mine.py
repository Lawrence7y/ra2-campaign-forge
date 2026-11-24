#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1) RTTI COL->TD->name for 6 classes (COL+0xC=TD, TD+8=name).
   2) identify operator new (0x7C8E17 / 0x4068E0).
   3) mine 51 sub_ rows: direct callers (byte channel) + .rdata vtable refs + source-file strings.
"""
import sys, os, csv, re, struct
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
COLS={0x80BAF0:"TActionClass",0x80BBA0:"TagClass",0x80BCF0:"TagTypeClass",
      0x80C5E0:"TEventClass",0x80C968:"TriggerClass",0x80CA20:"TriggerTypeClass"}

def cstr(va):
    try:
        data=b.read(va,200)
        return data.split(b"\x00")[0].decode(errors="replace")
    except: return None

out=[]
def emit(s=""): out.append(str(s))

emit("=== RTTI verify COL+0xC -> TD, TD+8 -> name (COL[+8] is CD, do NOT use) ===")
for col,cn in sorted(COLS.items()):
    sig=b.u32(col)
    td=b.u32(col+0xC)
    tdname=cstr(td+8) if td else None
    emit(f"  {cn:<20} COL={col:#x} sig={sig:#x} TD={td:#x} TD+8 name={tdname!r}")

emit("\n=== disassemble operator-new candidates ===")
for va in (0x7C8E17,0x4068E0):
    data=b.read(va,48)
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
    emit(f"  {va:#x}: "+" | ".join(f"{i.mnemonic} {i.op_str}" for i in m.disasm(data,va) if i.id!=0))

# --- mine sub_ rows: callers via sweep_calls (byte channel) ---
cov=rd(COV); atl={norm(r["entry"]):r for r in rd(ATL)}
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]
sub=[r for r in s15 if r["name"].strip().startswith("sub_") and r["grade"].strip()=="[未证]"]
subvas={int(norm(r["entry"]),16):r for r in sub}
emit("\n=== build byte-channel call target map (sweep_calls, skipdata=True) ===")
calls,jmps,stats=A.sweep_calls(b)
emit(f"  stats={stats}")
emit(f"  distinct call targets={len(calls)}")

# name lookup for a VA
name_by_entry={norm(r["entry"]):r["name"] for r in cov}
def fname(va):
    e=f"{va:08X}"
    return name_by_entry.get(e, "(unlabeled)")

emit("\n=== 51 sub_ rows: direct callers ===")
for va,r in sorted(subvas.items()):
    sites=calls.get(va,[])
    callers=[]
    for s in sites:
        callers.append(f"{s:#x}({fname(s)})")
    emit(f"  {va:#x} n_callsites={len(sites)} callers={callers[:12]}")

with open(os.path.join(CARD,"EVIDENCE","T2_rtti_and_sub_callers.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("Wrote EVIDENCE/T2_rtti_and_sub_callers.txt")
print("\n".join(out[:40]))
