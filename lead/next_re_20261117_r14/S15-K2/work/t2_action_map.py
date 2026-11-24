#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Map each S15 sub_ row to TActionClass action number: find dispatcher target whose
handler body contains the call site. Also dump all ACTION table targets with their
first instructions. Computational (function-interval containment), not entry_at_or_before."""
import sys, os, csv, struct
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

ACTION_BASE=0x6DFDEC
action=[b.u32(ACTION_BASE+4*i) for i in range(145)]
# handler extent: from target to next distinct target (sorted) OR use atlas size if target is a known entry
# Build a map: for a call site X in [0x6DD8EE,0x6DFDDD], find the action index whose
# target is the greatest target <= X (targets are ordered in .text mostly).
sorted_targets=sorted(set(action))
def which_action_for_site(site):
    # find candidate action indices whose target <= site and site < next handler start
    cands=[]
    for idx,t in enumerate(action):
        if t<=site:
            # handler body: from t to next greater distinct target
            nxt=min([x for x in sorted_targets if x>t], default=0x6DFDDB+9)
            if site<nxt:
                cands.append(idx)
    return cands

def dis(va,n=80):
    return " | ".join(f"{i.mnemonic} {i.op_str}" for i in m.disasm(b.read(va,n),va) if i.id!=0)

out=[]
def emit(s=""): out.append(str(s))
emit("=== ACTION table target -> first insns ===")
for idx,t in enumerate(action):
    emit(f"  A[{idx:3d}] {t:#x}  {dis(t,32)}")

emit("\n=== sub_ rows -> caller sites -> action index ===")
mapping={}
for r in sorted(sub,key=lambda x:norm(x["entry"])):
    e=norm(r["entry"]); va=int(e,16)
    sites=calls.get(va,[])
    acts=set()
    for s in sites:
        for a in which_action_for_site(s):
            acts.add(a)
    mapping[e]=sorted(acts)
    emit(f"  {e} ncall={len(sites)} actions={sorted(acts)} sites={[hex(s) for s in sites[:8]]}")

with open(os.path.join(CARD,"EVIDENCE","T2_action_map.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("Wrote EVIDENCE/T2_action_map.txt")
# summary
print("\n=== sub_ rows with a unique action index ===")
for e,a in sorted(mapping.items()):
    if len(a)==1: print(f"  {e} -> action {a[0]}")
    elif len(a)>1: print(f"  {e} -> actions {a} (AMBIG)")
    else: print(f"  {e} -> (no action; caller outside Execute)")
