#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict criterion: for each action-impl promotion, check the handler block [target,handler_end)
contains EXACTLY ONE direct `call` and that call targets the sub_."""
import sys,os,csv,re
ROOT=r"D:\Project\ra2-campaign-forge"
sys.path.insert(0,os.path.join(ROOT,r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
import capstone
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S15-K2")
b=A.Bin(); m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
action=[b.u32(0x6DFDEC+4*i) for i in range(145)]
uniq=sorted(set(action))
def hend(t):
    for u in uniq:
        if u>t: return u
    return 0x6DFDDB+9
proms=list(csv.DictReader(open(os.path.join(CARD,"EVIDENCE","PROMOTIONS.tsv"),encoding="utf-8-sig"),delimiter="\t"))
out=[]
keep=[]
for p in proms:
    if not p["new_name"].startswith("TActionClass::") or p["new_name"] in ("TActionClass::GetSize","TActionClass::WhatAmI"):
        keep.append(p); continue
    mm=re.search(r"handler (0x[0-9a-fA-F]+)",p["reason"])
    if not mm:
        out.append(f"  {p['entry']} {p['new_name']:<38} NO handler target in reason"); continue
    ht=int(mm.group(1),16)
    calls=[]
    for ins in m.disasm(b.read(ht,hend(ht)-ht),ht):
        if ins.id==0: continue
        if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
            calls.append((ins.address,int(ins.op_str,16)))
    subva=int(p["entry"],16)
    only=[c for c in calls if c[1]==subva]
    passes = len(calls)==1 and len(only)==1
    out.append(f"  {p['entry']} {p['new_name']:<38} handler={ht:#x} calls={[hex(c[1]) for c in calls]} STRICT={'PASS' if passes else 'FAIL'}")
    if passes: keep.append(p)
open(os.path.join(CARD,"EVIDENCE","T2_strict_filter.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")
print("\n".join(out))
print(f"\nSTRICT PASS action impls: {sum(1 for p in keep if p['new_name'].startswith('TActionClass::') and p['new_name'] not in ('TActionClass::GetSize','TActionClass::WhatAmI'))}")
print(f"Total kept (incl GetSize/WhatAmI): {len(keep)}")
# write kept back
import csv as csvmod
with open(os.path.join(CARD,"EVIDENCE","PROMOTIONS_STRICT.tsv"),"w",encoding="utf-8-sig",newline="") as f:
    w=csvmod.DictWriter(f,fieldnames=list(proms[0].keys()),delimiter="\t"); w.writeheader()
    for p in keep: w.writerow(p)
