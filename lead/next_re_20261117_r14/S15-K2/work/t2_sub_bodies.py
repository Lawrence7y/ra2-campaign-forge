#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump: (a) all slot function bodies, (b) all 51 sub_ bodies + short disasm.
Group sub_ by caller region (Action-Execute inside 0x6DD8B0..0x6DFFFA etc)."""
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
sub=[r for r in s15 if r["name"].strip().startswith("sub_") and r["grade"].strip()=="[未证]"]
b=A.Bin()
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
calls,jmps,stats=A.sweep_calls(b)

def dis(va,size):
    return " | ".join(f"{i.mnemonic} {i.op_str}" for i in m.disasm(b.read(va,min(size,200)),va) if i.id!=0)

out=[]
def emit(s=""): out.append(str(s))

emit("=== 51 sub_ rows: body bytes + short disasm + caller-context region ===")
for r in sorted(sub,key=lambda x:norm(x["entry"])):
    e=norm(r["entry"]); va=int(e,16); size=int(atl[e]["size"])
    sites=calls.get(va,[])
    # classify callers by which atlas function contains them (interval containment)
    regs=[]
    for s in sites:
        # find containing atlas function by interval
        cont=None
        for ae,ar in atl.items():
            av=int(ae,16); asz=int(ar["size"])
            if av<=s<av+asz: cont=(ae,ar); break
        regs.append(f"{s:#x}->{cont[0] if cont else '?'}")
    emit(f"{e} sz={size:<5} ncall={len(sites)}")
    emit(f"   bytes={b.read(va,min(size,48)).hex()}")
    emit(f"   dis={dis(va,size)}")
    emit(f"   callers={regs[:12]}")

with open(os.path.join(CARD,"EVIDENCE","T2_sub_bodies.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print(f"Wrote EVIDENCE/T2_sub_bodies.txt ({len(sub)} sub rows)")
